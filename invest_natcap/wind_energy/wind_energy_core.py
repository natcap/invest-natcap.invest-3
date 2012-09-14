"""InVEST Wind_Energy model core function  module"""
import math
import os.path
import logging

from osgeo import gdal
import numpy as np
import scipy.ndimage as ndimage
from scipy import signal

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
    
    # mask out any values that are out of the range of the depth values
    def depth_op(bath):
        if bath >= max_depth and bath <= min_depth:
            return bath
        else:
            return out_nodata

    depth_mask_uri = os.path.join(inter_dir, 'depth_mask.tif')
    depth_mask = \
        raster_utils.vectorize_rasters([bathymetry], depth_op, \
            raster_out_uri = depth_mask_uri, nodata = out_nodata)

    # construct the coastline from the AOI and bathymetry using the min and max
    # distance values provided
    try:
        # do some awesome coastline finding if distances are provided
        min_distance = args['min_distance']
        max_distance = args['max_distance']
        land_polygon = args['land_polygon']
        
        # make raster from the AOI and then rasterize land polygon ontop of it
        bath_prop = raster_utils.get_raster_properties(bathymetry)
        land_ds_uri = os.path.join(inter_dir, 'land_ds.tif')
        land_ds = raster_utils.create_raster_from_vector_extents(
                bath_prop['width'], abs(bath_prop['height']), gdal.GDT_Float32,
                out_nodata, land_ds_uri, aoi)

        # burn the whole area of interest onto the raster setting everything to
        # 0 which will represent our ocean values.
        gdal.RasterizeLayer(land_ds, [1], aoi.GetLayer(), burn_values = [1])
        # create a nodata mask
        aoi_nodata_mask = land_ds.GetRasterBand(1).ReadAsArray() == out_nodata
        # burn the land polygon ontop of the ocean values as 1 so that we now
        # have an accurate mask of where the land, ocean, and nodata values
        # should be
        gdal.RasterizeLayer(
                land_ds, [1], land_polygon.GetLayer(), burn_values = [0])
        # read in the raster so we can set back the nodata values
        # I don't think that reading back in the whole raster is a great idea
        # maybe there is a better way to handle this
        land_ds_array = land_ds.GetRasterBand(1).ReadAsArray()
        # reset our nodata values
        land_ds_array[aoi_nodata_mask] = out_nodata
        # write back our matrix to the band
        land_ds.GetRasterBand(1).WriteArray(land_ds_array)
        
        # calculate distances using distance transform
        
        distance_calc_uri = os.path.join(inter_dir, 'distance_factored.tif')
        dist_raster = raster_utils.new_raster_from_base(land_ds,
                distance_calc_uri, 'GTiff', out_nodata, gdal.GDT_Float32)
       
        dist_band = dist_raster.GetRasterBand(1)

        dist_matrix = np.copy(land_ds_array)
        np.putmask(dist_matrix, dist_matrix == out_nodata, 1)
        
        dist_matrix = \
                ndimage.distance_transform_edt(dist_matrix) * pixel_size
                
        LOGGER.debug('minimum distance : %s', dist_matrix.min()) 
        LOGGER.debug('maximum distance : %s', dist_matrix.max()) 
        dist_copy = np.copy(dist_matrix)

        mask_min = dist_matrix <= min_distance
        mask_max = dist_matrix >= max_distance
        mask_dist = np.ma.mask_or(mask_min, mask_max)
        LOGGER.debug('any distances work? : %s', mask_dist.all())
        np.putmask(dist_matrix, mask_dist, out_nodata)

        dist_band.WriteArray(dist_matrix)

    except KeyError:
        # looks like distances weren't provided, too bad!
        pass

    # fill in skeleton below

def valuation(args):
    """This is where the doc string lives"""

    # fill in skeleton below
