from osgeo import gdal
from osgeo import ogr
from osgeo import osr

import raster_utils

aoi_uri = '../../invest-data/CoastalProtection/Input/AOI_BarckClay.shp'
pop_uri = '../../invest-data/Base_Data/Marine/Land/global_polygon.shp'

aoi = ogr.Open(aoi_uri)
pop = ogr.Open(pop_uri)
# use create raster from vector extents to build up raster

# rasterize aoi layer onto raster from above
gdal.RasterizeLayer

# project aoi to pop

# clip pop from reprojected aoi

# reproject clipped pop from aoi

# use create raster from vector extents to build up a raster

# rasterize pop onto raster from above
