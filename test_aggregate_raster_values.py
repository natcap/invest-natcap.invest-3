import cProfile
import pstats

import os
import glob
import time
import gdal
import numpy
from osgeo import ogr

from invest_natcap import raster_utils

import pyximport
pyximport.install()
raster_uri = 'test/invest-data/Base_Data/Freshwater/dem'
shapefile_uri = 'test/invest-data/Base_Data/Freshwater/subwatersheds.shp'
values = raster_utils.aggregate_raster_values_uri(
    raster_uri, shapefile_uri, shapefile_field='subws_id',
    ignore_nodata=True, threshold_amount_lookup=None,
    ignore_value_list=[], process_pool=None)

output_uri = 'mask.tif'    
mask_nodata = -9999.0
raster_utils.new_raster_from_base_uri(
    raster_uri, output_uri, 'GTiff', mask_nodata, gdal.GDT_Float32, 
    fill_value=mask_nodata)
    
mask_ds = gdal.Open(output_uri, gdal.GA_Update)
mask_band = mask_ds.GetRasterBand(1)
    
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
for fl in glob.glob('layer_out.*'):
    #Do what you want with the file
    os.remove(fl)
ds = driver.CreateDataSource('layer_out.shp')

spat_ref = raster_utils.get_spatial_ref_uri(shapefile_uri)

layer = ds.CreateLayer('layer_out', spat_ref, ogr.wkbPolygon)
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
    
    gdal.RasterizeLayer(
        mask_ds, [1], layer, burn_values=[1],
        options=['ALL_TOUCHED=TRUE'])
    
    layer.DeleteFeature(count)
    count += 1
    
feat = geom = None  # destroy these
# Save and close everything
ds = layer = feat = geom = None
    
    

        
        
#for p1 in poly_list:
#    for p2 in poly_list:
#        print p1.disjoint(p2)
        
        
    
