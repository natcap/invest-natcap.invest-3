"""InVEST Wind_Energy model core function  module"""
import math
import os.path
import logging

from osgeo import gdal
import numpy as np
import scipy.ndimage as ndimage

from invest_natcap import raster_utils
LOGGER = logging.getLogger('wind_energy_core')

def biophysical(args):
    """This is where the doc string lives
    
        args[workspace_dir] - uri for workspace directory
        args[bathymetry] - a GDAL raster of elevation values
        args[aoi] - an OGR polygon shapefile of the area of interest
        args[min_depth] - a float of the minimum depth required for the turbines
        args[max_depth] - a float of the maximum depth the turbines can be
            placed

        returns - 
    """
    workspace = args['workspace_dir']
    inter_dir = os.path.join(workspace, 'intermediate')

    # get a mask for the min and max depths allowed for the turbines
    bathymetry = args['bathymetry']
    aoi = args['aoi']
    min_depth = args['min_depth'] * -1.0
    max_depth = args['max_depth'] * -1.0
    
    # clip the size of the bathymetry raster to aoi
    def clip_bath_op(bath):
        if bath >= max_depth and bath <= min_depth:
            return bath
        else:
            return out_nodata

    out_nodata = bathymetry.GetRasterBand(1).GetNoDataValue()
    clipped_bath_uri = os.path.join(inter_dir, 'clipped_bath.tif')
    clipped_bath = \
        raster_utils.vectorize_rasters([bathymetry], clip_bath_op, aoi=aoi, \
            raster_out_uri = clipped_bath_uri, nodata = out_nodata)
    

    # fill in skeleton below

def valuation(args):
    """This is where the doc string lives"""

    # fill in skeleton below
