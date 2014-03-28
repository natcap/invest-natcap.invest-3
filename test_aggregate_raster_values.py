import cProfile
import pstats

import time
import gdal
import numpy
from osgeo import ogr


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
        

out_shape = raster_utils.temporary_folder()
driver = ogr.GetDriverByName('ESRI Shapefile')
datasource = driver.CreateDataSource(out_shape)

# Create the layer name from the uri paths basename without the extension
layer_name = 'temporary_shapefile'
layer = datasource.CreateLayer(layer_name, spat_ref, ogr.wkbLineString)

# Add a single ID field
field = ogr.FieldDefn('id', ogr.OFTReal)
layer.CreateField(field)

# Create the 3 other points that will make up the vertices for the lines 
top_left = (start_point[0], start_point[1] + y_len)
top_right = (start_point[0] + x_len, start_point[1] + y_len)
bottom_right = (start_point[0] + x_len, start_point[1])

# Create a new feature, setting the field and geometry
line = ogr.Geometry(ogr.wkbLineString)
line.AddPoint(start_point[0], start_point[1])
line.AddPoint(top_left[0], top_left[1])
line.AddPoint(top_right[0], top_right[1])
line.AddPoint(bottom_right[0], bottom_right[1])
line.AddPoint(start_point[0], start_point[1])

feature = ogr.Feature(layer.GetLayerDefn())
feature.SetGeometry(line)
feature.SetField(0, 1)
layer.CreateFeature(feature)

feature = None
layer = None

datasource.SyncToDisk()
datasource = None        
        
        
        
for p1 in poly_list:
    for p2 in poly_list:
        print p1.disjoint(p2)
        
        
gdal.RasterizeLayer(
    mask_dataset, [1], shapefile_layer,
    options=['ATTRIBUTE=%s' % shapefile_field, 'ALL_TOUCHED=TRUE'])

    
