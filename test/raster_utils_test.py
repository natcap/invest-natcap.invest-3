from osgeo import gdal
from osgeo import ogr

import invest_test_core
import raster_utils

ds_1 = gdal.Open('./landuse_90')
ds_2 = gdal.Open('./eto')

aoi_geo = ogr.Open('./data/raster_utils_data/aoi_raster_utils.shp')

def adder(a,b):
    return a+b

raster_utils.vectorize_rasters([ds_1, ds_2], adder, 
                               raster_out_uri = 'out.tif', nodata=-1.0, aoi=aoi_geo)
