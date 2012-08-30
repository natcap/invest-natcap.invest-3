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
        args[min_distance] - a float of the minimum distance the farms have
            to be away from the coastline (m)
        args[max_distance] - a float of the maximum distance the farms can 
            be placed away from the coastline (m)
        args[land_polygon] - an OGR polygon shapefile of the land polygon

        returns - 
    """
    workspace = args['workspace_dir']
    inter_dir = os.path.join(workspace, 'intermediate')

    # get a mask for the min and max depths allowed for the turbines
    bathymetry = args['bathymetry']
    aoi = args['aoi']
    min_depth = args['min_depth'] * -1.0
    max_depth = args['max_depth'] * -1.0
    
    out_nodata = bathymetry.GetRasterBand(1).GetNoDataValue()
    clipped_bath_uri = os.path.join(inter_dir, 'clipped_bath.tif')
    clipped_bath = \
        raster_utils.clip_dataset(bathymetry, aoi, clipped_bath_uri)
  
    clipped_bath = None

    # mask out any values that are out of the range of the depth values
    def depth_op(bath):
        if bath >= max_depth and bath <= min_depth:
            return bath
        else:
            return out_nodata

    depth_mask_uri = os.path.join(inter_dir, 'depth_mask.tif')
    depth_mask = \
        raster_utils.vectorize_rasters([clipped_bath], depth_op, \
            raster_out_uri = depth_mask_uri, nodata = out_nodata)

    # construct the coastline from the AOI and bathymetry using the min and max
    # distance values provided
    try:
        # do some awesome coastline finding if distances are provided
        min_distance = args['min_distance']
        max_distance = args['max_distance']
        land_polygon = args['land_polygon']



    except KeyError:
        # looks like distances weren't provided, too bad!
        pass

    # fill in skeleton below

def valuation(args):
    """This is where the doc string lives"""

    # fill in skeleton below
