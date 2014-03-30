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

# Make a geometry, from Shapely object
# Now convert it to a shapefile with OGR    
driver = ogr.GetDriverByName('ESRI Shapefile')
ds = driver.CreateDataSource('layer_out.shp')
layer = ds.CreateLayer('layer_out', None, ogr.wkbPolygon)
layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
count = 0
for poly_feat in shapefile_layer:
    print 'looping'
    # Get the geometry of the polygon in WKT format
    poly_wkt = poly_feat.GetGeometryRef().ExportToWkt()
    # Load the geometry into shapely making it a shapely object
    shapely_polygon = shapely.wkt.loads(poly_wkt)
    # Add the shapely polygon geometry to a list, but first simplify the
    # geometry which smooths the edges making operations a lot faster
    poly_list.append(
        shapely_polygon.simplify(0.01, preserve_topology=False))
        
    # Add one feature
    defn = layer.GetLayerDefn()
    feat = ogr.Feature(defn)
    feat.SetField('id', 123)
    
    geom = ogr.CreateGeometryFromWkb(shapely_polygon.wkb)
    feat.SetGeometry(geom)
    layer.CreateFeature(feat)
    
    #gdal.RasterizeLayer(
    #    mask_dataset, [1], shapefile_layer,
    #    options=['ATTRIBUTE=%s' % shapefile_field, 'ALL_TOUCHED=TRUE'])
    
    layer.DeleteFeature(count)
    count += 1
    
feat = geom = None  # destroy these
# Save and close everything
ds = layer = feat = geom = None
    
    

        
        
#for p1 in poly_list:
#    for p2 in poly_list:
#        print p1.disjoint(p2)
        
        
    
