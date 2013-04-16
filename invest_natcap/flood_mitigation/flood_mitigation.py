"""Functions for the InVEST Flood Mitigation model."""

import logging


logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('flood_mitigation')

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

    pass
