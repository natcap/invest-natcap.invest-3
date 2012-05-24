from osgeo import gdal

import invest_test_core
import raster_utils

ds_1 = gdal.Open('./data/smooth_rasters/random.tif')
ds_2 = gdal.Open('./data/smooth_rasters/smoothleft.tif')
ds_3 = gdal.Open('./data/smooth_rasters/smoothtop.tif')

adder = lambda(a,b,c): a+b+c

raster_utils.vectorize_rasters([ds_1, ds_2, ds_3], adder, 
                               raster_out_uri = 'out.tif', nodata=-1.0)
