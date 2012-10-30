"""File for core operations of the InVEST Nutrient Retention model."""

from osgeo import gdal
import numpy as np

import invest_cython_core
from invest_natcap import raster_utils as raster_utils

def biophysical(args):
    """This function executes the biophysical Nutrient Retention model.

        args - a python dictionary with the following entries:"""
    print args
    pass

def get_flow_accumulation(dem):
    # According to the OSGEO python bindings, [0, 0, None, None] should extract
    # the entire matrix.
    # trac.osgeo.org/gdal/browser/trunk/gdal/swig/python/osgeo/gdal.py#L767
    bounding_box = [0, 0, None, None]

    # Create a flow_direction raster for use in the flow_direction function.
    flow_direction = raster_utils.new_raster_from_base(dem,
        '/tmp/flow_direction', 'GTiff', -1.0, gdal.GDT_Float32)
    invest_cython_core.flow_direction_inf(dem, bounding_box, flow_direction)

    # INSERT FLOW ACCUMULATION/RETENION RASTER CALCULATION HERE
    # do the flow_accumulation
    flow_accumulation = raster_utils.flow_accumulation_dinf(flow_direction, dem,
        '/tmp/flow_accumulation.tif')

def adjusted_loading_value(export_raster, wyield_raster, watersheds):
    """Calculate the adjusted loading value (ALV_x).

        export_raster - a gdal raster where pixel values represent the nutrient
            export for that pixel.  This is likely to be a reclassified LULC
            raster.
        wyield_raster - a gdal raster of water yield per pixel.
        watersheds - a list of OGR shapefiles representing watersheds and/or
            subwatersheds

        returns a GDAL rasterband representing the ALV."""

        # Substituting the actual runoff index here by just taking the
        # per-element natural log of the water yield raster. [wyield_raster]
        # should eventually be replaced with the water_yield_upstream_sum
        # raster (the sigma Y_u in the nutrient retention documentation)
        runoff_idx = raster_utils.vectorize_rasters([wyield_raster],
            lambda x: math.log(x, 2))

def mean_runoff_index(runoff_index, watersheds):
    """Calculate the mean runoff index per watershed.

        runoff_index - a GDAL raster of the runoff index per pixel.
        watersheds - a list of OGR shapefiles.

        Returns a list of shapefiles where the 'mean_runoff' field contains the
        calculated runoff index."""
    pass


