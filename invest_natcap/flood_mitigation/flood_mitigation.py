"""Functions for the InVEST Flood Mitigation model."""

import logging
import math
import os

from osgeo import gdal

from invest_natcap import raster_utils


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
    pixel_size = raster_utils.get_cell_size_from_uri(cn_uri)

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

    adjustments = {
        'dry': _dry_season_adjustment,
        'wet': _wet_season_adjustment
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
