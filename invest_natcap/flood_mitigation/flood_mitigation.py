"""Functions for the InVEST Flood Mitigation model."""

import logging
import math
import os
import shutil

from osgeo import gdal
import numpy

from invest_natcap import raster_utils
from invest_natcap.invest_core import fileio
from invest_natcap.routing import routing_utils
import routing_cython_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(funcName)-20s \
    %(levelname)-8s %(message)s', level=logging.DEBUG,
    datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('flood_mitigation')

# This dictionary represents the outflow_matrix values that flow into the
# current pixel.  It's used in several of the flood_mitigation functions.
INFLOW_NEIGHBORS = {
    0: [3, 4],
    1: [4, 5],
    2: [5, 6],
    3: [6, 7],
    4: [7, 0],
    5: [0, 1],
    6: [1, 2],
    7: [2, 3],
}

class InvalidSeason(Exception):
    """An exception to indicate that an invalid season was used."""
    pass

def execute(args):
    """Perform time-domain calculations to estimate the flow of water across a
    landscape in a flood situation.

    args - a python dictionary.  All entries noted below are required unless
        explicity stated as optional.
        'workspace' - a string URI to the user's workspace on disk.  Any temporary
            files needed for processing will also be saved to this folder before
            they are deleted.  If this folder exists on disk, any outputs will
            be overwritten in the execution of this model.
        'dem' - a string URI to the user's Digital Elevation Model on disk.
            Must be a raster dataset that GDAL can open.
        'landuse' - a string URI to the user's Land Use/Land Cover raster on
            disk.  Must be a raster dataset that GDAL can open.
        'num_intervals' - A python int representing the number of timesteps this
            model should process.
        'time_interval' - a python float representing the duration of the
            desired timestep, in hours.
        'precipitation' a string URI to a table of precipitation data.  Table
            must have the following structure:
                Fieldnames:
                    'STATION' - (string) label for the water gauge station
                    'LAT' - (float) the latitude of the station
                    'LONG' - (float) the longitude of the station
                    [1 ... n] - (int) the rainfall values for the specified time
                        interval.  Note that there should be one column for each
                        time interval.  The label of the column must be an int
                        index for the interval (so 1, 2, 3, etc.).
            This table must be a CSV.
        'curve_numbers' - a string URI pointing to a raster of the user's curve
            numbers.  See the user's guide for documentation on constructing
            this intput.
        'cn_adjust' - A python boolean indicating whether to adjust the
            args['curve_numbers'] input according to the user's defined
            seasonality adjustment.
        'cn_season' - A string indicating for which season the Curve Numbers
            should be adjusted.  One of ['Growing', 'Dormant'].  Required only
            if args['cn_adjust'] == True.
        'cn_amc_class' - A string indicating the Antecedent Soil Moisture class
            that should be used for CN adjustment.  One of ['Wet', 'Dry',
            'Average'].  Required only if args['cn_adjust'] == True.
        'flow_threshold' - a number representing the flow threshold before the
            flow becomes a stream.
        'suffix' - (optional) a string to add to the end of all outputs from
            this model

    The following files are saved to the user's disk, relative to the defined
    workspace:
        Rasters produced during preprocessing:
        <workspace>/intermediate/mannings_coeff_<suffix>.tif
            A raster of the user's input Land Use/Land Cover, reclassified
            according to the user's defined table of Manning's numbers.
        <workspace>/intermediate/slope_<suffix>.tif
            A raster of the slope on the landscape.  Calculated from the DEM
            provided by the user as input to this model.
        <workspace>/intermediate/flow_length_<suffix>.tif
            TODO: Figure out if this is even an output raster.
        <workspace>/intermediate/flow_direction_<suffix>.tif
            TODO: Figure out if this is even an output raster.
        <workspace>/intermediate/fractional_flow_<suffix>.tif
            TODO: Figure out if this is even an output raster.

        Rasters produced while calculating the Soil and Water Conservation
        Service's stormflow estimation model:
        <workspace>/intermediate/cn_season_adjusted_<suffix>.tif
            A raster of the user's Curve Numbers, adjusted for the user's
            specified seasonality.
        <workspace>/intermediate/cn_slope_adjusted_<suffix>.tif
            A raster of the user's Curve Numbers that have been adjusted for
            seasonality and then adjusted for slope.
        <workspace>/intermediate/soil_water_retention_<suffix>.tif
            A raster of the capcity of a given pixel to retain water in the
            soils on that pixel.
        <workspace>/output/<time_step>/runoff_depth_<suffix>.tif
            A raster of the storm runoff depth per pixel in this timestep.

        Rasters produced while calculating the flow of water on the landscape
        over time:
        <workspace>/output/<time_step>/floodwater_discharge_<suffix>.tif
            A raster of the floodwater discharge on the landscape in this time
            interval.
        <workspace>/output/<time_step>/flood_height_<suffix>.tif
            A raster of the height of flood waters on the landscape at this time
            interval.

    This function returns None."""

    try:
        suffix = args['suffix']
        if len(suffix) == 0:
            suffix = None
    except KeyError:
        suffix = None

    def _add_suffix(file_name):
        """Add a suffix to the input file name and return the result."""
        if suffix != None:
            file_base, extension = os.path.splitext(file_name)
            return "%s_%s%s" % (file_base, suffix, extension)
        return file_name

    def _intermediate_uri(file_name=''):
        """Make an intermediate URI."""
        return os.path.join(args['workspace'], 'intermediate',
            _add_suffix(file_name))

    def _output_uri(file_name=''):
        """Make an ouput URI."""
        return os.path.join(args['workspace'], 'output', _add_suffix(file_name))

    paths = {
        'precip_latlong': raster_utils.temporary_folder(),
        'precip_points' : _intermediate_uri('precip_points'),
        'mannings' : _intermediate_uri('mannings.tif'),
        'slope' : _intermediate_uri('slope.tif'),
        'flow_direction' : _intermediate_uri('flow_direction.tif'),
        'flow_length': _intermediate_uri('flow_length.tif'),
        'cn_slope': _intermediate_uri('cn_slope.tif'),
        'swrc': _intermediate_uri('swrc.tif'),
        'prev_discharge': _intermediate_uri('init_discharge.tif'),
        'outflow_weights': _intermediate_uri('outflow_weights.tif'),
        'outflow_direction': _intermediate_uri('outflow_direction.tif'),
        'channels': _intermediate_uri('channels.tif'),
        'landuse': _intermediate_uri('landuse_resized.tif'),
        'dem': _intermediate_uri('dem_resized.tif'),
        'curve_numbers': _intermediate_uri('cn_resized.tif'),
        'timesteps': {}
    }

    for timestep in range(1, args['num_intervals'] + 1):
        def _timestep_uri(file_name=''):
            """Make a URI for a timestep-based folder."""
            if file_name != '':
                file_base, extension = os.path.splitext(file_name)
                file_name = "%s_%s%s" % (file_base, timestep, extension)

            return os.path.join(_intermediate_uri(), 'timestep_%s' % timestep,
                _add_suffix(file_name))

        paths['timesteps'][timestep] = {
            'precip': _timestep_uri('precip.tif'),
            'runoff': _timestep_uri('storm_runoff.tif'),
            'discharge': _timestep_uri('flood_water_discharge.tif'),
            'flood_height': _timestep_uri('flood_height.tif'),
            'inundation': _timestep_uri('flood_inundation.tif')
        }

        # Create the timestamp folder name and make the folder on disk.
        raster_utils.create_directories([_timestep_uri()])

    # Create folders in the workspace if they don't already exist
    raster_utils.create_directories([args['workspace'], _intermediate_uri(),
        _output_uri()])

    # Remove any shapefile folders that exist, since we don't want any conflicts
    # when creating new shapefiles.
    try:
        shutil.rmtree(paths['precip_points'])
    except OSError:
        pass

    def _get_datatype_uri(raster_uri):
        dataset = gdal.Open(raster_uri)
        band = dataset.GetRasterBand(1)
        return band.DataType

    rasters = [args['landuse'], args['dem'], args['curve_numbers']]
    cell_size = raster_utils.get_cell_size_from_uri(args['dem'])
    for raster, resized_uri, func in [
        (args['landuse'], paths['landuse'], lambda x,y,z:x),
        (args['dem'], paths['dem'], lambda x,y,z:y),
        (args['curve_numbers'], paths['curve_numbers'], lambda x,y,z:z)]:

        datatype = _get_datatype_uri(raster)
        nodata = raster_utils.get_nodata_from_uri(raster)
        raster_utils.vectorize_datasets(rasters, func, resized_uri, datatype,
            nodata, cell_size, 'intersection')

    #######################
    # Preprocessing
    mannings_raster(paths['landuse'], args['mannings'], paths['mannings'])
    raster_utils.calculate_slope(paths['dem'], paths['slope'])
    routing_utils.flow_direction_inf(paths['dem'], paths['flow_direction'])
    routing_utils.calculate_flow_length(paths['flow_direction'],
        paths['flow_length'])
    routing_utils.calculate_stream(paths['dem'], args['flow_threshold'],
        paths['channels'])

    # Convert the precip table from CSV to ESRI Shapefile and reproject it.
    convert_precip_to_points(args['precipitation'], paths['precip_latlong'])
    dem_wkt = raster_utils.get_dataset_projection_wkt_uri(paths['dem'])
    raster_utils.reproject_datasource_uri(paths['precip_latlong'], dem_wkt,
        paths['precip_points'])

    #######################
    # Adjusting curve numbers
    adjust_cn_for_slope(paths['curve_numbers'], paths['slope'], paths['cn_slope'])

    if args['cn_adjust'] == True:
        season = args['cn_season']
        cn_season_adjusted_uri = _intermediate_uri('cn_season_%s.tif' % season)
        adjust_cn_for_season(paths['cn_slope'], season, cn_season_adjusted_uri)
    else:
        # If the user did not select seasonality adjustment, just use the
        # adjusted slope CN numbers instead.
        cn_season_adjusted_uri = paths['cn_slope']

    # Calculate the Soil Water Retention Capacity (equation 2)
    soil_water_retention_capacity(cn_season_adjusted_uri, paths['swrc'])

    # our timesteps start at 1.
    for timestep, ts_paths in paths['timesteps'].iteritems():
        LOGGER.info('Starting timestep %s', timestep)

        # make the precip raster, since it's timestep-dependent.
        make_precip_raster(paths['precip_points'], paths['dem'], timestep,
            ts_paths['precip'])

        # Calculate storm runoff once we have all the data we need.
        storm_runoff(ts_paths['precip'], paths['swrc'], ts_paths['runoff'])

        ##################
        # Channel Routing.
        if timestep == 1:
            # We need a previous flood water discharge raster to be created
            # before we actually start iterating through the timesteps.
            discharge_nodata = raster_utils.get_nodata_from_uri(paths['flow_direction'])
            raster_utils.new_raster_from_base_uri(ts_paths['runoff'],
                paths['prev_discharge'], 'GTiff', discharge_nodata,
                gdal.GDT_Float32, fill_value=0.0)


        flood_water_discharge(ts_paths['runoff'], paths['flow_direction'],
            args['time_interval'], ts_paths['discharge'],
            paths['outflow_weights'], paths['outflow_direction'],
            paths['prev_discharge'])

        # Set the previous discharge path to the discharge_uri so we can use it
        # later on.
        paths['prev_discharge'] = ts_paths['discharge']

        ###########################
        # Flood waters calculations
        flood_height(ts_paths['discharge'], paths['mannings'], paths['slope'],
            ts_paths['flood_height'])

        flood_inundation_depth(ts_paths['flood_height'], paths['dem'],
            cn_season_adjusted_uri, paths['channels'],
            paths['outflow_direction'], ts_paths['inundation'])

def mannings_raster(landcover_uri, mannings_table_uri, mannings_raster_uri):
    """Reclassify the input land use/land cover raster according to the
        mannings numbers table passed in as input.

        landcover_uri - a URI to a GDAL dataset with land use/land cover codes
            as pixel values.
        mannings_table_uri - a URI to a CSV table on disk.  This table must have
            at least the following columns:
                "LULC" - an integer landcover code matching a code in the inputs
                    land use/land cover raster.
                "ROUGHNESS" - a floating-point number indicating the roughness
                    of the pixel.  See the user's guide for help on creating
                    this number for your landcover classes.
        mannings_raster_uri - a URI to a location on disk where the output
            raster should be saved.  If this file exists on disk, it will be
            overwritten.  This output raster will be a reclassified version of
            the raster at `landcover_uri`.

        Returns none."""
    mannings_table = fileio.TableHandler(mannings_table_uri)
    mannings_mapping = mannings_table.get_map('lulc', 'roughness')

    lulc_nodata = raster_utils.get_nodata_from_uri(landcover_uri)

    raster_utils.reclassify_dataset_uri(landcover_uri, mannings_mapping,
        mannings_raster_uri, gdal.GDT_Float32, lulc_nodata)

def _get_cell_size_from_datasets(uri_list):
    """Get the minimum cell size of all the input datasets.

        uri_list - a list of URIs that all point to GDAL datasets on disk.

        Returns the minimum cell size of all the rasters in `uri_list`."""

    min_cell_size = min(map(raster_utils.get_cell_size_from_uri, uri_list))
    LOGGER.debug('Minimum cell size of input rasters: %s', min_cell_size)
    return min_cell_size


def storm_runoff(precip_uri, swrc_uri, output_uri):
    """Calculate the storm runoff from the landscape in this timestep.  This
        function corresponds with equation 1 in the Flood Mitigation user's
        guide.

        precip_uri - a URI to a GDAL dataset on disk, representing rainfall
            across the landscape within this timestep.
        swrc_uri - a URI to a GDAL dataset on disk representing a raster of the
            soil water retention capacity.
        output_uri - a URI to the desired location of the output raster from
            this function.  If this file exists on disk, it will be overwritten
            with a GDAL dataset.

        This function saves a GDAL dataset to the URI `output_uri`.

        Returns nothing."""

    LOGGER.info('Calculating storm runoff')
    precip_nodata = raster_utils.get_nodata_from_uri(precip_uri)
    swrc_nodata = raster_utils.get_nodata_from_uri(swrc_uri)
    precip_pixel_size = raster_utils.get_cell_size_from_uri(precip_uri)

    def calculate_runoff(precip, swrc):
        """Calculate the runoff on a pixel from the precipitation value and
        the ability of the soil to retain water (swrc).  Both inputs are
        floats.  Returns a float."""

        # Handle when precip or swrc is nodata.
        if precip == precip_nodata or swrc == swrc_nodata:
            return precip_nodata

        # In response to issue 1913.  Rich says that if P <= 0.2S, we should
        # just clamp it to 0.0.
        if precip <= 0.2 * swrc:
            return 0.0

        return ((precip - (0.2 * swrc))**2)/(precip + (0.8 * swrc))

    raster_utils.vectorize_datasets([precip_uri, swrc_uri],
        calculate_runoff, output_uri, gdal.GDT_Float32, precip_nodata,
        precip_pixel_size, 'intersection')
    LOGGER.debug('Finished calculating storm runoff')


def soil_water_retention_capacity(cn_uri, swrc_uri):
    """Calculate the capacity of the soil to retain water on the landscape from
        the user's adjusted curve numbers.  These curve numbers are assumed to
        have already been adjusted properly according to slope and/or
        seasonality.

        cn_uri - a URI to a GDAL dataset on disk.
        swrc_uri - a URI.  If this file exists on disk, it will be overwritted
            with a GDAL dataset.

        This function saves a GDAL dataset to the URI `swrc_uri`.

        Returns nothing.
        """

    cn_nodata = raster_utils.get_nodata_from_uri(cn_uri)
    cn_pixel_size = raster_utils.get_cell_size_from_uri(cn_uri)

    def calculate_swrc(curve_num):
        """This function calculates the soil water retention capacity on a
            per-pixel level based on the input curve number, as long as the
            `curve_num` is not the nodata value.  This is equation 2
            in the Flood Mitigation user's guide.

            curve_num - a number.

            Returns a float."""

        if curve_num == cn_nodata:
            return cn_nodata
        return ((25400.0 / curve_num) - 254.0)

    raster_utils.vectorize_datasets([cn_uri], calculate_swrc, swrc_uri,
        gdal.GDT_Float32, cn_nodata, cn_pixel_size, 'intersection')

def _dry_season_adjustment(curve_num):
    """Perform dry season curve number adjustment on the pixel level.  This
        corresponds with equation 3 in the user's guide.

        This is a local function, as it should really only be used for
        vectorized operations if you _really_ know what you're doing.

        Returns a float."""

    return ((4.2 * curve_num) / (10.0 - (0.058 * curve_num)))

def _wet_season_adjustment(curve_num):
    """Perform wet season adjustment on the pixel level.  This corresponds with
        equation 4 in the user's guide.

        This is a local function, as it should really only be used for
        vectorized operations if you _really_ know what you're doing.

        Returns a float."""

    return ((23 * curve_num) / (10.0 + (0.13 * curve_num)))

def adjust_cn_for_season(cn_uri, season, adjusted_uri):
    """Adjust the user's Curve Numbers raster for the specified season's soil
    antecedent moisture class.

    Typical accumulated 5-day rainfall for AMC classes:

    AMC Class   | Dormant Season | Growing Season |
    ------------+----------------+----------------+
    Dry (AMC-1) |    < 12mm      |    < 36mm      |
    ------------+----------------+----------------+
    Wet (AMC-3) |    > 28mm      |    > 53mm      |


    cn_uri - a string URI to the user's Curve Numbers raster on disk.  Must be a
        raster that GDAL can open.
    season - a string, either 'dry' or 'wet'.  An exception will be raised if
        any other value is submitted.
    adjusted_uri - a string URI to which the adjusted Curve Numbers to be saved.
        If the file at this URI exists, it will be overwritten with a GDAL
        dataset.

    This function saves a GDAL dataset to the URI noted by the `adjusted_uri`
    parameter.

    Returns None."""

    # Get the nodata value so we can account for that in our tweaked seasonality
    # functions here.
    cn_nodata = raster_utils.get_nodata_from_uri(cn_uri)

    def adjust_for_dry_season(curve_num):
        """Custom function to account for nodata values when adjusting curve
        numbers for the dry season.  curve_num is a float.  Returns a float."""
        if curve_num == cn_nodata:
            return cn_nodata
        return _dry_season_adjustment(curve_num)


    def adjust_for_wet_season(curve_num):
        """Custom function to account for nodata values when adjusting curve
        numbers for the wet season.  curve_num is a float.  Returns a float."""
        if curve_num == cn_nodata:
            return cn_nodata
        return _wet_season_adjustment(curve_num)

    adjustments = {
        'dry': adjust_for_dry_season,
        'wet': adjust_for_wet_season
    }

    try:
        season_function = adjustments[season]
    except KeyError:
        raise InvalidSeason('Season must be one of %s, but %s was used' %
            (adjustments.keys(), season))

    cn_nodata = raster_utils.get_nodata_from_uri(cn_uri)
    cn_pixel_size = raster_utils.get_cell_size_from_uri(cn_uri)

    raster_utils.vectorize_datasets([cn_uri], season_function, adjusted_uri,
        gdal.GDT_Float32, cn_nodata, cn_pixel_size, 'intersection')

def adjust_cn_for_slope(cn_avg_uri, slope_uri, adjusted_uri):
    """Adjust the input curve numbers raster for slope.  This corresponds with
        equation 5 in the Flood Mitigation user's guide.

        cn_avg_uri - a string URI a curve number raster on disk.  Must be a
            raster than GDAL can open.
        slope_uri - a string URI to a slope raster on disk.  Must be a raster
            that GDAL can open.
        adjusted_uri - a string URI to the location on disk where the output
            raster should be saved.  If this file exists on disk, it will be
            overwritten.

        This function saves a GDAL dataset to the URI passed in by the argument
        `adjusted_uri`.

        Returns nothing."""

    cn_nodata = raster_utils.get_nodata_from_uri(cn_avg_uri)
    slope_nodata = raster_utils.get_nodata_from_uri(slope_uri)

    def adjust_for_slope(curve_num, slope):
        """Adjust the input curve number for slope according to use
        Williams' empirical equation.  This function returns nodata if either
        the curve_num or slope is nodata.

        Returns a float."""

        if curve_num == cn_nodata or slope == slope_nodata:
            return cn_nodata

        ratio = (_wet_season_adjustment(curve_num) - curve_num) / 3.0
        quotient = 1.0 - 2.0 * math.exp(-13.86 * slope)

        return ratio * quotient + curve_num

    # Using the max of the two pixel sizes.
    cn_pixel_size = raster_utils.get_cell_size_from_uri(cn_avg_uri)
    slope_pixel_size = raster_utils.get_cell_size_from_uri(slope_uri)
    pixel_size = max(cn_pixel_size, slope_pixel_size)

    raster_utils.vectorize_datasets([cn_avg_uri, slope_uri], adjust_for_slope,
        adjusted_uri, gdal.GDT_Float32, cn_nodata, pixel_size, 'intersection')

def convert_precip_to_points(precip_uri, points_uri):
    """Convert the CSV at `precip_uri` to a points shapefile.

        precip_uri - a uri to a CSV on disk, which must have the following
            columns:
            "STATION" - a string raingauge identifier.
            "LATI" - the latitude
            "LONG" - the longitude
            ["1", "2", ... ] - fieldnames corresponding with each time step.
                Must start at 1.
        points_uri - a string URI to which the output points shapefile will be
            saved as an OGR datasource.

    Returns nothing."""


    # Extract the data from the precip CSV using the TableHandler class.
    table_object = fileio.TableHandler(precip_uri)
    table_dictionary = dict((i, d) for (i, d) in
        enumerate(table_object.get_table()))

    raster_utils.dictionary_to_point_shapefile(table_dictionary,
        'precip_points', points_uri)

def make_precip_raster(precip_points_uri, sample_raster_uri, timestep,
    output_uri):
    """Create a precipitation raster from a points shapefile for the specified
        timestep.

        precip_points_uri - a URI to an OGR Datasource on disk.
        sample_raster_uri - a URI to a GDAL dataset on disk.
        timestep - an int timestep.  Must be a field in the datasource passed in
            as `precip_points_uri`.
        output_uri - a URI to where the output raster will be saved.

        This function saves a GDAL raster dataset to `output_uri`.  This output
        raster will carry many of the characteristics of the sample_raster_uri,
        including pixel size and projection.

        This function returns nothing."""

    LOGGER.info('Starting to make the precipitation raster')
    precip_nodata = raster_utils.get_nodata_from_uri(sample_raster_uri)
    raster_utils.new_raster_from_base_uri(sample_raster_uri, output_uri,
        'GTiff', precip_nodata, gdal.GDT_Float32, precip_nodata)

    raster_utils.vectorize_points_uri(precip_points_uri, timestep, output_uri)
    LOGGER.info('Finished making the precipitation raster')

def _extract_matrix(raster_uri):
    """Extract the Numpy matrix from a GDAL dataset.  The returned matrix is a
    memory-mapped matrix."""
    memory_file = raster_utils.temporary_filename()
    return raster_utils.load_memory_mapped_array(raster_uri, memory_file)

def _write_matrix(raster_uri, matrix):
    dataset = gdal.Open(raster_uri, gdal.GA_Update)
    band = dataset.GetRasterBand(1)
    band.WriteArray(matrix)
    band.FlushCache()
    dataset.FlushCache()
    band = None
    dataset = None
    raster_utils.calculate_raster_stats_uri(raster_uri)

def flood_water_discharge(runoff_uri, flow_direction_uri, time_interval,
    output_uri, outflow_weights_uri, outflow_direction_uri, prev_discharge_uri):
    """Calculate the flood water discharge in a single timestep.  This
    corresponds to equation 11 in the user's guide.

        runoff_uri - a URI to a GDAL dataset on disk.  This is a raster of the
            stormwater runoff from the landscape as modeled by the SCS model.
        flow_direction_uri - a URI to a GDAL dataset of the flow direction on
            the landscape, calculated from the user's DEM.
        time_interval - a number indicating the length of this timestep (in
            seconds).
        output_uri - a URI to the file location where the output raster should
            be saved.  If a file exists at this location, it will be
            overwritten.
        outflow_weights_uri - a URI to the target outflow weights raster.
        outflow_direction_uri - a URI to the target outflow direction raster.
        prev_discharge_raster - a URI to the discharge raster from the previous
            step.  This should be a raster filled with 0's (or nodata) if there
            was no previous step.

        Returns nothing."""

    LOGGER.info('Starting to calculate flood water discharge')
    LOGGER.debug('Discharge uri=%s', output_uri)
    LOGGER.debug('Previous discharge uri=%s', prev_discharge_uri)
    LOGGER.debug('Runoff URI=%s', runoff_uri)

    time_interval = float(time_interval)  # must be a float.
    LOGGER.debug('Using time interval %s', time_interval)

    # Determine the pixel area from the runoff raster
    pixel_area = raster_utils.get_cell_area_from_uri(runoff_uri)
    LOGGER.debug('Discharge pixel area: %s', pixel_area)

    # Get the flow graph
    routing_cython_core.calculate_flow_graph(flow_direction_uri,
        outflow_weights_uri, outflow_direction_uri)

    # make a new numpy matrix of the same size and dimensions as the outflow
    # matrices and fill it with 0's.
    discharge_nodata = raster_utils.get_nodata_from_uri(flow_direction_uri)
    raster_utils.new_raster_from_base_uri(runoff_uri, output_uri,
        'GTiff', discharge_nodata, gdal.GDT_Float32, fill_value=0.0)

    # Get the numpy matrix of the new discharge raster.
    discharge_matrix = _extract_matrix(output_uri)
    prev_discharge = _extract_matrix(prev_discharge_uri)
    runoff_matrix = _extract_matrix(runoff_uri)
    outflow_weights = _extract_matrix(outflow_weights_uri)
    outflow_direction = _extract_matrix(outflow_direction_uri)

    LOGGER.debug('Output discharge matrix size=%s', discharge_matrix.shape)
    LOGGER.debug('Previous discharge matrix size=%s', prev_discharge.shape)
    LOGGER.debug('Runoff matrix size=%s', runoff_matrix.shape)

    runoff_nodata = raster_utils.get_nodata_from_uri(runoff_uri)
    LOGGER.debug('Runoff nodata=%s', runoff_nodata)
    # A mapping of which indices might flow into this pixel. If the neighbor
    # pixel's value is 
    outflow_direction_nodata = raster_utils.get_nodata_from_uri(
        outflow_direction_uri)

    # list of neighbor ids and their indices relative to the current pixel
    # index offsets are row, column.
    neighbor_indices = {
        0: (0, 1),
        1: (-1, 1),
        2: (-1, 0),
        3: (-1, -1),
        4: (0, -1),
        5: (1, -1),
        6: (1, 0),
        7: (1, 1)
    }
    neighbors = list(neighbor_indices.iteritems())

    class NeighborHasNoData(Exception):
        """An exception for skipping a neighbor when that neighbor's
        value is nodata."""
        pass

    # Using a Numpy N-dimensional iterator to loop through the runoff matrix.
    # numpy.nditer allows us to index into the matrix while always knowing the
    # index that we are currently accessing.  This way we can easily access
    # pixels immediately adjacent to this pixel by index (the index offsets for
    # which are in the neighbors list, made from the neighbor_indices dict).
    iterator = numpy.nditer([runoff_matrix], flags=['multi_index'])
    LOGGER.info('Checking neighbors for flow contributions to storm runoff')
    for runoff in iterator:
        index = iterator.multi_index

        if runoff == runoff_nodata:
            discharge_sum = discharge_nodata
        elif outflow_direction[index] == outflow_direction_nodata:
            discharge_sum = discharge_nodata
        else:
            discharge_sum = 0.0  # re-initialize the discharge sum
            for neighbor_id, index_offset in neighbors:
                # Add the index offsets to the current index to get the
                # neighbor's index.
                neighbor_index = tuple(map(sum, zip(index, index_offset)))
                try:
                    if neighbor_index[0] < 0 or neighbor_index[1] < 0:
                        # The neighbor index is beyond the bounds of the matrix
                        # We need a special case check here because a negative
                        # index will actually return a correct pixel value, just
                        # from the other side of the matrix, which we don't
                        # want.
                        raise IndexError

                    neighbor_value = outflow_direction[neighbor_index]
                    possible_inflow_neighbors = INFLOW_NEIGHBORS[neighbor_value]

                    if neighbor_id in possible_inflow_neighbors:
                        # Only get the neighbor's runoff value if we know that
                        # the neighbor flows into this pixel.
                        neighbor_runoff = runoff_matrix[neighbor_index]
                        if neighbor_runoff == runoff_nodata:
                            raise NeighborHasNoData

                        neighbor_prev_discharge = prev_discharge[neighbor_index]
                        if neighbor_prev_discharge == discharge_nodata:
                            raise NeighborHasNoData

                        # determine fractional flow from this neighbor into this
                        # pixel.
                        first_neighbor_weight = outflow_weights[neighbor_index]

                        if possible_inflow_neighbors[0] == neighbor_id:
                            fractional_flow = 1.0 - first_neighbor_weight
                        else:
                            fractional_flow = first_neighbor_weight

                        discharge = (((neighbor_runoff * pixel_area) +
                            (neighbor_prev_discharge * time_interval)) *
                            fractional_flow)

                        discharge_sum += discharge

                except (IndexError, KeyError, NeighborHasNoData):
                    # IndexError happens when the neighbor does not exist.
                    # In this case, we assume there is no inflow from this
                    # neighbor.
                    # KeyError happens when the neighbor has a nodata value.
                    # When this happens, we assume there is no inflow from this
                    # neighbor.
                    # NeighborHasNoRunoffData happens when the neighbor's runoff
                    # value is nodata.
                    pass

            discharge_sum = discharge_sum / time_interval

        # Set the discharge matrix value to the calculated discharge value.
        discharge_matrix[index] = discharge_sum
    LOGGER.info('Finished checking neighbors for flood water discharge.')

    _write_matrix(output_uri, discharge_matrix)

def flood_height(discharge_uri, mannings_uri, slope_uri, output_uri):
    """Calculate the flood_height according to equation 19 in the user's guide.

        discharge_uri - a URI to a GDAL dataset on disk representing the flood
            water discharge in this timestep.
        mannings_uri - a URI to a GDAL dataset representing the soil roughness.
        slope_uri - a URI to a GDAL dataset of slope
        output_uri - an output URI to where the flood_height raster will be
            writte on disk.

        Returns nothing."""

    raster_list = [discharge_uri, mannings_uri, slope_uri]
    min_pixel_size = _get_cell_size_from_datasets(raster_list)

    discharge_nodata = raster_utils.get_nodata_from_uri(discharge_uri)
    mannings_nodata = raster_utils.get_nodata_from_uri(mannings_uri)
    slope_nodata = raster_utils.get_nodata_from_uri(slope_uri)

    def _vectorized_flood_height(discharge, mannings, slope):
        """Per-pixel operation to get the flood_height.  All inputs are floats.
        Returns a float."""
        if discharge == discharge_nodata:
            return discharge_nodata

        if mannings == mannings_nodata:
            return discharge_nodata

        if slope == slope_nodata:
            return discharge_nodata

        if slope == 0:
            return 0.0

        return ((discharge * mannings) / slope ** (0.5)) ** (0.375)

    raster_utils.vectorize_datasets(raster_list, _vectorized_flood_height,
        output_uri, gdal.GDT_Float32, discharge_nodata, min_pixel_size,
        'intersection')

def flood_inundation_depth(flood_height_uri, dem_uri, cn_uri,
    channels_uri, outflow_direction_uri, output_uri):
    """This function estimates flood inundation depth from flood height,
        elevation, and curve numbers.  This is equation 20 from the flood
        mitigation user's guide.

        flood_height_uri - a URI to a GDAL datset representing flood height over
            the landscape.
        dem_uri - a URI to a GDAL raster of the digital elevation model.
        cn_uri - a URI to a GDAL raster of the user's curve numbers.
        channels_uri - a URI to a GDAL dataset of the channel network.
        outflow_direction_uri - a URI to the outflow direction raster.
        output_uri - a URI to where the output GDAL raster dataset should be
            stored.

        This function returns nothing.
    """

    LOGGER.debug('Starting to calculate flood inundation depth')
    def _extract_matrix_and_nodata(uri):
        """Return a tuple of the numpy matrix and the nodata value for the input
        raster at URI."""
        matrix = _extract_matrix(uri)
        nodata = raster_utils.get_nodata_from_uri(uri)
        return(matrix, nodata)

    flood_height_tuple = _extract_matrix_and_nodata(flood_height_uri)
    channel_tuple = _extract_matrix_and_nodata(channels_uri)
    dem_tuple = _extract_matrix_and_nodata(dem_uri)
    cn_tuple = _extract_matrix_and_nodata(cn_uri)
    outflow_direction_tuple = _extract_matrix_and_nodata(outflow_direction_uri)
    pixel_size = raster_utils.get_cell_size_from_uri(outflow_direction_uri)

    LOGGER.info('Distributing flood waters')
    fid_matrix = _calculate_fid(flood_height_tuple, dem_tuple,
        channel_tuple, cn_tuple, outflow_direction_tuple, pixel_size)[0]
    LOGGER.info('Finished distributing flood waters')

    raster_utils.new_raster_from_base_uri(dem_uri, output_uri, 'GTiff', -1,
        gdal.GDT_Float32)
    _write_matrix(output_uri, fid_matrix)
    LOGGER.debug('Finished calculating flood inundation depth')

def _calculate_fid(flood_height, dem, channels, curve_nums, outflow_direction,
    pixel_size):
    """Actually perform the matrix calculations for the flood inundation depth
        function.  This is equation 20 from the flood mitigation user's guide.

        flood_height - a numpy matrix of flood water heights.
        dem - a numpy matrix of elevations.
        channels - a numpy matrix of channels.
        curve_nums - a numpy matrix of curve numbers.
        outflow_direction - a numpy matrix indicating which pixels flow into one
            another.  See routing_utils for details on this matrix.
        pixel_size -a numpy indicating the mean of the height and width of a
            pixel.

        All matrices MUST have the same sizes.

        Returns a numpy matrix of the calculated flood inundation height."""

    flood_height_matrix, flood_height_nodata = flood_height
    dem_matrix, dem_nodata = dem
    channels_matrix, channels_nodata = channels
    cn_matrix, cn_nodata = curve_nums
    outflow_direction_matrix, outflow_direction_nodata = outflow_direction

    output = numpy.copy(flood_height_matrix)
    visited = numpy.zeros(flood_height_matrix.shape, dtype=numpy.int)
    travel_distance = numpy.zeros(flood_height_matrix.shape, dtype=numpy.float)

    for name, matrix, nodata in [
        ('flood height', flood_height_matrix, flood_height_nodata),
        ('dem', dem_matrix, dem_nodata),
        ('channels', channels_matrix, channels_nodata),
        ('curve numbers', cn_matrix, cn_nodata),
        ('outflow direction',outflow_direction_matrix, outflow_direction_nodata),
        ('output', output, -1),
        ('visited', visited, None),
        ('travel distance', travel_distance, None)]:
        LOGGER.debug('Matrix %s, sise=%s, nodata=%s', name, matrix.shape,
            nodata)

    # to track our nearest channel cell, create a matrix that has two values for
    # each of the elements in the 2-d matrix.  These two extra values represent
    # the index of the closes channel cell.
#    nearest_channel = numpy.zeros(flood_height_matrix.shape + (2,),
#        dtype=numpy.int)

    # We know the diagonal distance thanks to trigonometry.  We're assuming that
    # we measure from the center of this pixel to the center of the neighboring
    # pixel.
    diagonal_distance = pixel_size * math.sqrt(2)
    indices = [
        (0, (0, 1), pixel_size),
        (1, (-1, 1), diagonal_distance),
        (2, (-1, 0), pixel_size),
        (3, (-1, -1), diagonal_distance),
        (4, (0, -1), pixel_size),
        (5, (1, -1), diagonal_distance),
        (6, (1, 0), pixel_size),
        (7, (1, 1), diagonal_distance)
    ]

    def _flows_from(source_index, neighbor_id):
        """Indicate whether the source pixel flows into the neighbor identified
        by neighbor_id.  This function returns a boolean."""

        neighbor_value = outflow_direction_matrix[source_index]

        # If there is no outflow direction, then there is no flow to the
        # neighbor and we return False.
        if neighbor_value == outflow_direction_nodata:
            return False

        if neighbor_id in INFLOW_NEIGHBORS[neighbor_value]:
            return False
        return True

    def _fid(index, channel_floodwater, channel_elevation):
        """Calculate the on-pixel flood inundation depth, as represented by
            equation 20 in the flood mitigation user's guide.

            index - the tuple index of the pixel on which to calculate FID
            channel_floodwater - the numeric depth of the closest channel cell's
                floodwaters
            channel_elevation - the numeric depth of the closest channel cell's
                elevation

            Note that for this equation to be accurate, the dem and the
            floodwaters must be in the same units.

            Returns a float."""
        pixel_elevation = dem_matrix[index]
        curve_num = cn_matrix[index]

        if channel_floodwater == 0:
            return 0.0

        if (channel_floodwater == flood_height_nodata or
            pixel_elevation == dem_nodata or
            curve_num == cn_nodata or
            channel_elevation == dem_nodata):
            return 0.0

        elevation_diff = pixel_elevation - channel_elevation
        flooding = channel_floodwater - elevation_diff - curve_num

        if flooding <= 0:
            return 0.0
#        if flooding > channel_floodwater:
#            LOGGER.debug(str('p_elevation=%s, cn=%s, c_floodwater=%s, fid=%s, '
#                'c_elevation=%s'), pixel_elevation, curve_num,
#                channel_floodwater, flooding, channel_elevation)
        return flooding

    class AlreadyVisited(Exception):
        """An exception to indicate that we've already visited this pixel."""
        pass

    class SkipNeighbor(Exception):
        """An exception to indicate that we wish to skip this neighbor pixel"""
        pass


    iterator = numpy.nditer([channels_matrix, flood_height_matrix, dem_matrix],
        flags=['multi_index'])
    for channel, channel_floodwater, channel_elevation in iterator:
        if channel == 1:
            channel_index = iterator.multi_index
            pixels_to_visit = [channel_index]

            visited[channel_index] = 1
#            nearest_channel[channel_index][0] = channel_index[0]
#            nearest_channel[channel_index][1] = channel_index[1]

            while True:
                try:
                    pixel_index = pixels_to_visit.pop(0)
                    #print (pixel_index, pixels_to_visit)
                except IndexError:
                    # No more indexes to process.
                    break

                for n_id, neighbor_offset, n_distance in indices:
                    n_index = tuple(map(sum, zip(pixel_index, neighbor_offset)))

                    try:
                        if n_index[0] < 0 or n_index[1] < 0:
                            raise IndexError

                        if channels_matrix[n_index] in [1, channels_nodata]:
                            raise SkipNeighbor

                        if _flows_from(n_index, n_id):
                            fid = _fid(n_index, channel_floodwater,
                                channel_elevation)

                            if fid > 0:
#                                if fid > channel_floodwater:
#                                    raise Exception('fid=%s, floodwater=%s' %
#                                        (fid, channel_floodwater))
                                dist_to_n = travel_distance[pixel_index] + n_distance
                                if visited[n_index] == 0 or (visited[n_index] == 1 and
                                    dist_to_n < travel_distance[n_index]):
                                    visited[n_index] = 1
                                    travel_distance[n_index] = dist_to_n
#                                    nearest_channel[n_index][0] = channel_index[0]
#                                    nearest_channel[n_index][1] = channel_index[1]
                                    output[n_index] = fid
                                    pixels_to_visit.append(n_index)

                    except SkipNeighbor:
                        pass
                        #LOGGER.debug('Skipping neighbor %s', n_index)
                    except IndexError:
                        pass
                        #LOGGER.warn('index %s does not exist', n_index)
                    except AlreadyVisited:
                        pass
                        #LOGGER.info('Already visited index %s, not distributing.',
                        #    n_index)

    #return (output, travel_distance, nearest_channel)
    return (output, travel_distance)
