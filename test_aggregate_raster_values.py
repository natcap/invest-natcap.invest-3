import cProfile
import pstats

import time
import gdal
import numpy
from invest_natcap import raster_utils

import pyximport
pyximport.install()
raster_uri = 'overlapping_polygons/sample_stat_impact_map.tif'
shapefile_uri = 'servicesheds_col.shp'
raster_utils.aggregate_raster_values_uri(
    raster_uri, shapefile_uri, shapefile_field=None,
    ignore_nodata=True, threshold_amount_lookup=None,
    ignore_value_list=[], process_pool=None)

print 'if we got here everything passed!'
