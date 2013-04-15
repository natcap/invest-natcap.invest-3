"""Functions for the InVEST Flood Mitigation model."""

def execute(args):
    """Perform time-domain calculations to estimate the flow of water across a
    landscape in a flood situation.

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

        This function returns None.
        """
    pass
