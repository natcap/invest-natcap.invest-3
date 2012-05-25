from osgeo import gdal

import invest_test_core
import raster_utils

ds_1 = gdal.Open('./landuse_90')
ds_2 = gdal.Open('./eto')

def adder(a,b):
    return a+b

raster_utils.vectorize_rasters([ds_1, ds_2], adder, 
                               raster_out_uri = 'out.tif', nodata=-1.0)
