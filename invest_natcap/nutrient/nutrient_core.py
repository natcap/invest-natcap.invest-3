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
