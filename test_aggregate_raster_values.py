import cProfile
import pstats

import time
import gdal
import numpy
from invest_natcap import raster_utils

import pyximport
pyximport.install()
raster_uri = 'overlapping_polygons/sample_static_impact_map.tif'
shapefile_uri = 'overlapping_polygons/servicesheds_col.shp'
values = raster_utils.aggregate_raster_values_uri(
    raster_uri, shapefile_uri, shapefile_field='OBJECTID',
    ignore_nodata=True, threshold_amount_lookup=None,
    ignore_value_list=[], process_pool=None)

print values

from osgeo import ogr
import shapely.wkt
import shapely.ops
from shapely import speedups

shapefile = ogr.Open(shapefile_uri)
shapefile_layer = shapefile.GetLayer()
poly_list = []

for poly_feat in shapefile_layer:
    # Get the geometry of the polygon in WKT format
    poly_wkt = poly_feat.GetGeometryRef().ExportToWkt()
    # Load the geometry into shapely making it a shapely object
    shapely_polygon = shapely.wkt.loads(poly_wkt)
    # Add the shapely polygon geometry to a list, but first simplify the
    # geometry which smooths the edges making operations a lot faster
    poly_list.append(
        shapely_polygon.simplify(0.01, preserve_topology=False))
        
for p1 in poly_list:
    for p2 in poly_list:
        print p1.disjoint(p2)
        


