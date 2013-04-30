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

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('flood_mitigation')

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
        <workspace>/output/<time_step>/hydrograph_<suffix>.tif
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
        return os.path.join(args['workspace'], 'intermediate', _add_suffix(file_name))

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
        'swrc': _intermediate_uri('swrc.tif')
    }

    # Create folders in the workspace if they don't already exist
    raster_utils.create_directories([args['workspace'], _intermediate_uri(),
        _output_uri()])

    # Remove any shapefile folders that exist, since we don't want any conflicts
    # when creating new shapefiles.
    try:
        shutil.rmtree(paths['precip_points'])
    except OSError:
        pass

    # Reclassify the LULC to get the manning's raster.
    mannings_raster(args['landuse'], args['mannings'], paths['mannings'])

    # We need a slope raster for several components of the model.
    raster_utils.calculate_slope(args['dem'], paths['slope'])

    # Calculate the flow direction, needed for flow length and for other
    # functions later on.
    routing_utils.flow_direction_inf(args['dem'], paths['flow_direction'])

    # Calculate the flow length here, since we need it for several parts of the
    # model.
    routing_utils.calculate_flow_length(paths['flow_direction'],
        paths['flow_length'])

    # We always want to adjust for slope.
    adjust_cn_for_slope(args['curve_numbers'], paths['slope'], paths['cn_slope'])

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

    # Convert precipitation table to a points shapefile.
    convert_precip_to_points(args['precipitation'], paths['precip_latlong'])

    # Project the precip points from latlong to the correct projection.
    dem_wkt = raster_utils.get_dataset_projection_wkt_uri(args['dem'])
    raster_utils.reproject_datasource_uri(paths['precip_latlong'], dem_wkt,
        paths['precip_points'])

    # our timesteps start at 1.
    for timestep in range(1, args['num_intervals'] + 1):
        LOGGER.info('Starting timestep %s', timestep)
        # Create the timestamp folder name and make the folder on disk.
        timestep_dir = os.path.join(_intermediate_uri(), 'timestep_%s' % timestep)
        raster_utils.create_directories([timestep_dir])

        # make the precip raster, since it's timestep-dependent.
        precip_raster_uri = os.path.join(timestep_dir, 'precip.tif')
        make_precip_raster(paths['precip_points'], args['dem'], timestep,
            precip_raster_uri)

        # Calculate storm runoff once we have all the data we need.
        runoff_uri = os.path.join(timestep_dir, 'storm_runoff.tif')
        storm_runoff(precip_raster_uri, paths['swrc'], runoff_uri)

        # Calculate the overland travel time.
        overland_travel_time_uri = os.path.join(timestep_dir,
            'overland_travel_time.tif')
        overland_travel_time(args['time_interval'], runoff_uri, paths['slope'],
            paths['flow_length'], paths['mannings'], overland_travel_time_uri)


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

def overland_travel_time(time_interval, runoff_depth_uri, slope_uri,
    flow_length_uri, mannings_uri, output_uri):
    """Calculate the overland travel time for this timestep.  This function is a
        combination of equations 8 and 9 from the flood mitigation user's
        guide.

        time_interval - A number.  The number of seconds in this time interval.
        runoff_depth_uri - A string URI to a GDAL dataset on disk representing
            the storm runoff raster.
        slope_uri - A string URI to a GDAL dataset on disk representing the
            slope of the DEM.
        flow_length_uri - A string URI to a GDAL dataset on disk representing the
            flow length, calculated from the DEM.
        mannings_uri - A string URI to a GDAL dataset on disk representing the
            Manning's numbers for the user's Land Use/Land Cover raster.  This
            number corresponds with soil roughness.
        output_uri - A String URI to a GDAL dataset on disk to where the
            overland travel time raster will be saved.

        This function will save a GDAL dataet to the path designated by
        `output_uri`.  If a file exists at that path, it will be overwritten.
            - nodata is taken from the raster at `runoff_depth_uri`

        This function has no return value."""

    raster_list = [flow_length_uri, mannings_uri, slope_uri, runoff_depth_uri]

    # Calculate the minimum cell size
    min_cell_size = _get_cell_size_from_datasets(raster_list)
    LOGGER.debug('Minimum pixel size: %s', min_cell_size)

    # Cast to a float, just in case the user passed in an int.
    time_interval = float(time_interval)

    flow_length_nodata = raster_utils.get_nodata_from_uri(flow_length_uri)
    runoff_depth_nodata = raster_utils.get_nodata_from_uri(runoff_depth_uri)
    slope_nodata = raster_utils.get_nodata_from_uri(slope_uri)
    roughness_nodata = raster_utils.get_nodata_from_uri(mannings_uri)

    def _overland_travel_time(flow_length, roughness, slope, runoff_depth):
        """Calculate the overland travel time on this pixel.  All inputs are
            floats.  Returns a float."""

        if flow_length == flow_length_nodata or\
            runoff_depth == runoff_depth_nodata or\
            slope == slope_nodata or\
            roughness == roughness_nodata:
            return runoff_depth_nodata

        # If we don't check for 0-division errors here, we'll get them if either
        # there is no runoff depth or the slope is 0.  Personally, I think it
        # makes sense to return 0 if either of these is the case.
        if runoff_depth == 0 or slope == 0:
            return 0.0

        stormflow_intensity = runoff_depth / time_interval
        return (((flow_length ** 0.6) * (roughness ** 0.6)) /
            ((stormflow_intensity ** 0.4) * (slope **0.3)))

    LOGGER.info('Calculating overland travel time raster')
    raster_utils.vectorize_datasets(raster_list, _overland_travel_time,
        output_uri,gdal.GDT_Float32, runoff_depth_nodata, min_cell_size,
        'intersection')
    LOGGER.info('Finished calculating overland travel time.')


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

def make_precip_raster(precip_points_uri, sample_raster_uri, timestep, output_uri):
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
    """Extract the Numpy matrix from a GDAL dataset."""
    dataset = gdal.Open(raster_uri)
    band = dataset.GetRasterBand(1)
    return band.ReadAsArray()

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
    output_uri, outflow_weights_uri, outflow_direction_uri):
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

        Returns nothing."""

    time_interval = float(time_interval)  # must be a float.

    # Determine the pixel area from the runoff raster
    pixel_area = raster_utils.get_cell_area_from_uri(runoff_uri)
    LOGGER.debug('Discharge pixel area: %s', pixel_area)

    # Get the flow graph
    routing_cython_core.calculate_flow_graph(flow_direction_uri,
        outflow_weights_uri, outflow_direction_uri)

    # make a new numpy matrix of the same size and dimensions as the outflow
    # matrices.
    discharge_nodata = raster_utils.get_nodata_from_uri(flow_direction_uri)
    raster_utils.new_raster_from_base_uri(flow_direction_uri, output_uri,
        'GTiff', discharge_nodata, gdal.GDT_Float32, fill_value=0.0)

    # Get the numpy matrix of the new discharge raster.
#    discharge_matrix = _extract_matrix(output_uri)[100:103, 150:153]
#    runoff_matrix = _extract_matrix(runoff_uri)[100:103, 150:153]
#    outflow_weights_matrix = _extract_matrix(outflow_weights_uri)[100:103, 150:153]
#    outflow_direction_matrix = _extract_matrix(outflow_direction_uri)[100:103, 150:153]
#
    discharge_matrix = _extract_matrix(output_uri)
    runoff_matrix = _extract_matrix(runoff_uri)
    outflow_weights_matrix = _extract_matrix(outflow_weights_uri)
    outflow_direction_matrix = _extract_matrix(outflow_direction_uri)

    print discharge_matrix
    print runoff_matrix
    print outflow_weights_matrix
    print outflow_direction_matrix


    runoff_nodata = raster_utils.get_nodata_from_uri(runoff_uri)
    discharge_nodata = raster_utils.get_nodata_from_uri(output_uri)
    # A mapping of which indices might flow into this pixel. If the neighbor
    # pixel's value is 
    outflow_direction_nodata = raster_utils.get_nodata_from_uri(outflow_direction_uri)
    inflow_neighbors = {
        0: [3, 4],
        1: [4, 5],
        2: [5, 6],
        3: [6, 7],
        4: [7, 0],
        5: [0, 1],
        6: [1, 2],
        7: [2, 3],
        outflow_direction_nodata: [],
        None: []  # value is None when there is an indexing error.
    }

    # list of neighbor ids and their indices relative to the current pixel
    # index offsets are row, column.
    neighbor_indices = {
        0: {'row_offset': 0, 'col_offset': 1},
        1: {'row_offset': 1, 'col_offset': 1},
        2: {'row_offset': -1, 'col_offset': 0},
        3: {'row_offset': -1, 'col_offset': -1},
        4: {'row_offset': 0, 'col_offset': -1},
        5: {'row_offset': 1, 'col_offset': -1},
        6: {'row_offset': 1, 'col_offset': 0},
        7: {'row_offset': 1, 'col_offset': 1}
    }
    neighbors = list(neighbor_indices.iteritems())

    radius = 1
    iterator = numpy.nditer([discharge_matrix, runoff_matrix],
        flags=['multi_index'], op_flags=['readwrite'])
    for discharge, runoff in iterator:
        index = iterator.multi_index
        #print(discharge, runoff, iterator.multi_index)

        if runoff_matrix[index] == runoff_nodata:
            discharge_sum = discharge_nodata
# TODO: What does a value of nodata in outflow_direction raster mean?
#        elif outflow_direction_matrix[index] == outflow_direction_nodata:
#            discharge_sum = discharge_nodata
        else:
            discharge_sum = 0.0
            for neighbor_id, neighbor_location in neighbors:
                neighbor_index = (index[0] + neighbor_location['row_offset'],
                    index[1] + neighbor_location['col_offset'])
                try:
                    neighbor_value = outflow_direction_matrix[neighbor_index]
                except IndexError:
                    # happens when the neighbor does not exist.
                    neighbor_value = None

                possible_inflow_neighbors = inflow_neighbors[neighbor_value]
                if neighbor_id in possible_inflow_neighbors:
                    # determine fractional flow
                    first_neighbor_weight = outflow_weights_matrix[neighbor_index]
                    if possible_inflow_neighbors.index(neighbor_id) == 0:
                        fractional_flow = first_neighbor_weight
                    else:
                        fractional_flow = 1.0 - first_neighbor_weight
                    discharge = runoff * fractional_flow * pixel_area
                    discharge_sum += discharge

            discharge_sum = discharge_sum / time_interval

        discharge_matrix[index] = discharge_sum

    _write_matrix(output_uri, discharge_matrix)
    print discharge_matrix
