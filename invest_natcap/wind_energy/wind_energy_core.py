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

        # make raster from the AOI and then rasterize land polygon ontop of it
        bath_prop = raster_utils.get_raster_properties(bathymetry)
        land_ds_uri = os.path.join(inter_dir, 'land_ds.tif')
        land_ds = \
            raster_utils.create_raster_from_vector_extents(bath_prop['width'],
                bath_prop['height'], gdal.GDT_Float32, out_nodata, land_ds_uri,
                aoi)

        # burn the whole area of interest onto the raster setting everything to
        # 0 which will represent our ocean values.
        gdal.RasterizeLayer(land_ds, [1], aoi, burn_values = [0])
        # create a nodata mask
        aoi_nodata_mask = land_ds.GetRasterBand(1).ReadAsArray() == out_nodata
        # burn the land polygon ontop of the ocean values as 1 so that we now
        # have an accurate mask of where the land, ocean, and nodata values
        # should be
        gdal.RasterizeLayer(land_ds, [1], land_polygon, burn_values = [1])
        # read in the raster so we can set back the nodata values
        # I don't think that reading back in the whole raster is a great idea
        # maybe there is a better way to handle this
        land_ds_array = land_ds.GetRasterBand(1).ReadAsArray()
        # reset our nodata values
        land_ds_array[aoi_nodata_mask] = out_nodata
        # write back our matrix to the band
        land_ds.GetRasterBand(1).WriteArray(land_ds_array)
        # create new raster that is 2 rows/columns bigger than before
        land_prop = raster_utils.get_raster_properties(land_ds)
        boundary_ds_uri = os.path.join(inter_dir, 'boundary.tif')
        boundary_ds = raster_utils.new_raster(land_prop['x_size'] + 2,
                land_prop['y_size'] + 2, land_ds.GetProjection(),
                land_ds.GetGeoTransform(), 'GTiff', out_nodata,
                gdal.GDT_Float32, 1, boundary_ds_uri)

        boundary_ds.GetRasterBand(1).WriteArray(land_ds_array, xoff=1, yoff=1)

        boundary_matrix = boundary_ds.GetRasterBand(1).ReadAsArray()
        
        # create a nodata mask for the boundary_ds
        boundary_nodata_mask = boundary_matrix == out_nodata

        # boundary_ds should have nodata values replaced with 1.0 (land values)
        # so that the special cases are handled properly
        boundary_matrix[boundary_matrix == out_nodata] = 1
                
        # do awesome convolution magic
        kernel = np.array([[-1, -1, -1],
                           [-1,  8, -1],
                           [-1, -1, -1]])

        # run convolution on the boundary_ds with the above kernel where we want
        # values that are greater than 0
        shoreline_matrix = \
                (signal.convolve2d(boundary_matrix, kernel, mode='same') >0)

        # now mask out where the nodata values should be
        shoreline_matrix[boundary_nodata_mask] = out_nodata

        # set nodata values this way : borders[mask] = ount_nodata

        # do some gaussian blurring with min and max distances to get the range
        # of where we can place the wind farms
        # for now I am going to use the sigma that I derived in biodiversity to
        # use for the gaussian filter.
        pixel_size = .03333 #PROBLEM : Raster is in degrees and not meters
        min_dist_pixel = min_distance / pixel_size
        sigma_min = math.sqrt(dr_pixel / 2.0)

        # copy the shoreline matrix to set nodata values and do guassian
        # filtering
        blur_matrix = np.copy(shoreline_matrix)
        # where the blur_matrix is equal to nodata put a 0. This is so when
        # blurring we don't factor in nodata values
        np.putmask(blur_matrix, blur_matrix == out_nodata, 0)
        # run the gaussian filter
        min_dist_matrix = ndimage.gaussian_filter(blur_matrix, sigma)
        # set back the nodata values that were set to 0
        np.putmask(min_dist_matrix, shoreline_matrix==out_nodata,
            out_nodata)
         


    except KeyError:
        # looks like distances weren't provided, too bad!
        pass

    # fill in skeleton below

def valuation(args):
    """This is where the doc string lives"""

    # fill in skeleton below
