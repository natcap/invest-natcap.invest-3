"""Functions for the InVEST Flood Mitigation model."""

import logging
import math
import os
import shutil
import time

from osgeo import gdal

from invest_natcap import raster_utils
from invest_natcap.invest_core import fileio
from invest_natcap.routing import routing_utils
import routing_cython_core
import flood_mitigation_cython_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(funcName)-20s \
    %(levelname)-8s %(message)s', level=logging.DEBUG,
    datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('flood_mitigation')


class InvalidSeason(Exception):
    """An exception to indicate that an invalid season was used."""
    pass


def execute(args):
    """Perform time-domain calculations to estimate the flow of water across a
    landscape in a flood situation.

    args - a python dictionary.  All entries noted below are required unless
        explicity stated as optional.
        'workspace' - a string URI to the user's workspace on disk.  Any
            temporary files needed for processing will also be saved to this
            folder before they are deleted.  If this folder exists on disk, any
            outputs will be overwritten in the execution of this model.
        'dem' - a string URI to the user's Digital Elevation Model on disk.
            Must be a raster dataset that GDAL can open.
        'landuse' - a string URI to the user's Land Use/Land Cover raster on
            disk.  Must be a raster dataset that GDAL can open.
        'num_intervals' - A python int representing the number of timesteps
            this model should process.
        'time_interval' - a python float representing the duration of the
            desired timestep, in hours.
        'precipitation' a string URI to a table of precipitation data.  Table
            must have the following structure:
                Fieldnames:
                    'STATION' - (string) label for the water gauge station
                    'LAT' - (float) the latitude of the station
                    'LONG' - (float) the longitude of the station
                    [1 ... n] - (int) the rainfall values for the specified
                        time interval.  Note that there should be one column
                        for each time interval.  The label of the column must
                        be an int index for the interval (so 1, 2, 3, etc.).
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
            A raster of the height of flood waters on the landscape at this
            time interval.

    This function returns None."""

    try:
        suffix = args['suffix']
        if len(suffix) == 0:
            suffix = None
    except KeyError:
        suffix = None

    def _add_suffix(file_name):
        """Add a suffix to the input file name and return the result."""
        if suffix is not None:
            file_base, extension = os.path.splitext(file_name)
            return "%s_%s%s" % (file_base, suffix, extension)
        return file_name

    def _intermediate_uri(file_name=''):
        """Make an intermediate URI."""
        return os.path.join(args['workspace'], 'intermediate',
            _add_suffix(file_name))

    def _output_uri(file_name=''):
        """Make an ouput URI."""
        return os.path.join(args['workspace'], 'output',
            _add_suffix(file_name))

    paths = {
        'precip_latlong': raster_utils.temporary_folder(),
        'precip_points': _intermediate_uri('precip_points'),
        'mannings': _intermediate_uri('mannings.tif'),
        'slope': _intermediate_uri('slope.tif'),
        'flow_direction': _intermediate_uri('flow_direction.tif'),
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

    # Remove any shapefile folders that exist, since we don't want any
    # conflicts when creating new shapefiles.
    try:
        shutil.rmtree(paths['precip_points'])
    except OSError:
        pass

    rasters = [args['landuse'], args['dem'], args['curve_numbers']]
    cell_size = raster_utils.get_cell_size_from_uri(args['dem'])
    for raster, resized_uri, func, datatype in [
        (args['landuse'], paths['landuse'], lambda x, y, z: x, gdal.GDT_Int32),
        (args['dem'], paths['dem'], lambda x, y, z: y, gdal.GDT_Float32),
        (args['curve_numbers'], paths['curve_numbers'], lambda x, y, z: z,
            gdal.GDT_Float32)]:

        nodata = raster_utils.get_nodata_from_uri(raster)
        raster_utils.vectorize_datasets(rasters, func, resized_uri,
            datatype, nodata, cell_size, 'intersection')

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
    adjust_cn_for_slope(paths['curve_numbers'], paths['slope'],
        paths['cn_slope'])

    if args['cn_adjust'] is True:
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
            discharge_nodata = raster_utils.get_nodata_from_uri(
                paths['flow_direction'])
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
        mannings_table_uri - a URI to a CSV table on disk.  This table
            must have at least the following columns:
                "LULC" - an integer landcover code matching a code in the
                    inputs land use/land cover raster.
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

        return ((precip - (0.2 * swrc)) ** 2) / (precip + (0.8 * swrc))

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


    cn_uri - a string URI to the user's Curve Numbers raster on disk.  Must
        be a raster that GDAL can open.
    season - a string, either 'dry' or 'wet'.  An exception will be raised if
        any other value is submitted.
    adjusted_uri - a string URI to which the adjusted Curve Numbers to be
        saved.  If the file at this URI exists, it will be overwritten with a
        GDAL dataset.

    This function saves a GDAL dataset to the URI noted by the `adjusted_uri`
    parameter.

    Returns None."""

    # Get the nodata value so we can account for that in our tweaked
    # seasonality functions here.
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
        timestep - an int timestep.  Must be a field in the datasource passed
            in as `precip_points_uri`.
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


def _extract_matrix_and_nodata(uri):
    """Return a tuple of the numpy matrix and the nodata value for the input
    raster at URI."""
    matrix = _extract_matrix(uri)
    nodata = raster_utils.get_nodata_from_uri(uri)
    return(matrix, nodata)


def _write_matrix(raster_uri, matrix):
    """Write a matrix to a raster that already exists on disk.

        raster_uri - a URI to a gdal dataset on disk.
        matrix - a NumPy matrix to be written to the raster at raster_uri

        Returns nothing."""

    dataset = gdal.Open(raster_uri, gdal.GA_Update)
    band = dataset.GetRasterBand(1)
    band.WriteArray(matrix)
    band.FlushCache()
    dataset.FlushCache()
    band = None
    dataset = None
    raster_utils.calculate_raster_stats_uri(raster_uri)


def flood_water_discharge(runoff_uri, flow_direction_uri, time_interval,
    output_uri, outflow_weights_uri, outflow_direction_uri,
    prev_discharge_uri):
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

    start_time = time.time()
    LOGGER.info('Starting to calculate flood water discharge')
    LOGGER.debug('Discharge uri=%s', output_uri)
    LOGGER.debug('Previous discharge uri=%s', prev_discharge_uri)
    LOGGER.debug('Runoff URI=%s', runoff_uri)

    time_interval = float(time_interval)  # must be a float.
    LOGGER.debug('Using time interval %s', time_interval)

    # Determine the pixel area from the runoff raster
    pixel_area = raster_utils.get_cell_size_from_uri(runoff_uri) ** 2
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
    prev_discharge = _extract_matrix(prev_discharge_uri)
    runoff_tuple = _extract_matrix_and_nodata(runoff_uri)
    outflow_weights = _extract_matrix(outflow_weights_uri)
    outflow_direction_tuple = _extract_matrix_and_nodata(outflow_direction_uri)

    discharge_matrix = flood_mitigation_cython_core.flood_discharge(
        runoff_tuple, outflow_direction_tuple, outflow_weights, prev_discharge,
        discharge_nodata, pixel_area, time_interval)

    LOGGER.info('Finished checking neighbors for flood water discharge.')

    _write_matrix(output_uri, discharge_matrix)
    LOGGER.debug('Elapsed time for flood water discharge:%s',
        time.time() - start_time)


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

        flood_height_uri - a URI to a GDAL datset representing flood height
            over the landscape.
        dem_uri - a URI to a GDAL raster of the digital elevation model.
        cn_uri - a URI to a GDAL raster of the user's curve numbers.
        channels_uri - a URI to a GDAL dataset of the channel network.
        outflow_direction_uri - a URI to the outflow direction raster.
        output_uri - a URI to where the output GDAL raster dataset should be
            stored.

        This function returns nothing.
    """

    LOGGER.debug('Starting to calculate flood inundation depth')

    flood_height_tuple = _extract_matrix_and_nodata(flood_height_uri)
    channel_tuple = _extract_matrix_and_nodata(channels_uri)
    dem_tuple = _extract_matrix_and_nodata(dem_uri)
    cn_tuple = _extract_matrix_and_nodata(cn_uri)
    outflow_direction_tuple = _extract_matrix_and_nodata(outflow_direction_uri)
    pixel_size = raster_utils.get_cell_size_from_uri(outflow_direction_uri)

    LOGGER.info('Distributing flood waters')
    fid_matrix = flood_mitigation_cython_core.calculate_fid(flood_height_tuple,
        dem_tuple, channel_tuple, cn_tuple, outflow_direction_tuple,
        pixel_size)
    LOGGER.info('Finished distributing flood waters')

    raster_utils.new_raster_from_base_uri(dem_uri, output_uri, 'GTiff', -1,
        gdal.GDT_Float32)
    _write_matrix(output_uri, fid_matrix)
    LOGGER.debug('Finished calculating flood inundation depth')
