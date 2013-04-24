"""Functions for the InVEST Flood Mitigation model."""

import logging
import math
import os
import shutil

from osgeo import gdal

from invest_natcap import raster_utils
from invest_natcap.invest_core import fileio

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

    The following files are saved to the user's disk, relative to the defined
    workspace:
        Rasters produced during preprocessing:
        <workspace>/intermediate/mannings_coeff.tif
            A raster of the user's input Land Use/Land Cover, reclassified
            according to the user's defined table of Manning's numbers.
        <workspace>/intermediate/slope.tif
            A raster of the slope on the landscape.  Calculated from the DEM
            provided by the user as input to this model.
        <workspace>/intermediate/flow_length.tif
            TODO: Figure out if this is even an output raster.
        <workspace>/intermediate/flow_direction.tif
            TODO: Figure out if this is even an output raster.
        <workspace>/intermediate/fractional_flow.tif
            TODO: Figure out if this is even an output raster.

        Rasters produced while calculating the Soil and Water Conservation
        Service's stormflow estimation model:
        <workspace>/intermediate/cn_season_adjusted.tif
            A raster of the user's Curve Numbers, adjusted for the user's
            specified seasonality.
        <workspace>/intermediate/cn_slope_adjusted.tif
            A raster of the user's Curve Numbers that have been adjusted for
            seasonality and then adjusted for slope.
        <workspace>/intermediate/soil_water_retention.tif
            A raster of the capcity of a given pixel to retain water in the
            soils on that pixel.
        <workspace>/output/<time_step>/runoff_depth.tif
            A raster of the storm runoff depth per pixel in this timestep.

        Rasters produced while calculating the flow of water on the landscape
        over time:
        <workspace>/output/<time_step>/floodwater_discharge.tif
            A raster of the floodwater discharge on the landscape in this time
            interval.
        <workspace>/output/<time_step>/hydrograph.tif
            A raster of the height of flood waters on the landscape at this time
            interval.

    This function returns None."""

    workspace = args['workspace']
    intermediate = os.path.join(workspace, 'intermediate')
    output = os.path.join(workspace, 'output')

    # Create folders in the workspace if they don't already exist
    for folder in [workspace, intermediate, output]:
        try:
            os.makedirs(folder)
            LOGGER.debug('Created folder %s', folder)
        except OSError:
            LOGGER.debug('Folder %s already exists', folder)

    # Remove any shapefile folders that exist, since we don't want any conflicts
    # when creating new shapefiles.
    precip_points_uri = os.path.join(intermediate, 'precip_points')
    try:
        shutil.rmtree(precip_points_uri)
    except OSError:
        pass

    # We need a slope raster for several components of the model.
    slope_uri = os.path.join(intermediate, 'slope.tif')
    raster_utils.calculate_slope(args['dem'], slope_uri)

    # Adjust Curve Numbers according to user input
    # If the user has not selected a seasonality adjustment, only then will we
    # adjust for slope.  Rich and I made this decision, as Equation 5
    # (slope adjustments to curve numbers) is not clear which seasonality
    # adjustment to use or how to use it when the user choses a non-average
    # seasonality adjustment.  Until we figure this out, we are only adjusting
    # CNs for slope IFF the user has not selected a seasonality adjustment.
    if args['cn_adjust'] == True:
        season = args['cn_season']
        cn_adjusted_uri = os.path.join(intermediate, 'cn_season_%s.tif' % season)
        adjust_cn_for_season(args['curve_numbers'], season, cn_adjusted_uri)
    else:
        cn_adjusted_uri = os.path.join(intermediate, 'cn_slope.tif')
        adjust_cn_for_slope(args['curve_numbers'], slope_uri, cn_adjusted_uri)

    # Calculate the Soil Water Retention Capacity (equation 2)
    swrc_uri = os.path.join(intermediate, 'swrc.tif')
    soil_water_retention_capacity(cn_adjusted_uri, swrc_uri)

    # Convert precipitation table to a points shapefile.
    precip_points_latlong_uri = raster_utils.temporary_folder()
    convert_precip_to_points(args['precipitation'], precip_points_latlong_uri)

    # Project the precip points from latlong to the correct projection.
    dem_wkt = raster_utils.get_dataset_projection_wkt_uri(args['dem'])
    raster_utils.reproject_datasource_uri(precip_points_latlong_uri, dem_wkt,
        precip_points_uri)

    # our timesteps start at 1.
    for timestep in range(1, args['num_intervals'] + 1):
        LOGGER.info('Starting timestep %s', timestep)
        # Create the timestamp folder name and make the folder on disk.
        timestep_dir = os.path.join(intermediate, 'timestep_%s' % timestep)
        raster_utils.create_directories([timestep_dir])

        # make the precip raster, since it's timestep-dependent.
        precip_raster_uri = os.path.join(timestep_dir, 'precip.tif')
        make_precip_raster(precip_points_uri, args['dem'], timestep,
            precip_raster_uri)

        # Calculate storm runoff once we have all the data we need.
        # TODO: commit a regression storm runoff raster.
        runoff_uri = os.path.join(timestep_dir, 'storm_runoff.tif')
        storm_runoff(precip_raster_uri, swrc_uri, runoff_uri)


def _get_raster_wkt_from_uri(raster_uri):
    """Local function to get a raster's well-known text from a URI.

        raster_uri - a string URI to a raster on disk.

        Returns a string with the raster's well-known text projection
        information."""
    raster = gdal.Open(raster_uri)
    return raster.GetProjection()

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

    return ((4.2 - curve_num) / (10.0 - (0.058 * curve_num)))

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
