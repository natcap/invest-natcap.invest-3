import cProfile
import pstats

import os
import shutil
import glob
import time
import gdal
import numpy
from osgeo import ogr

import shapely.wkt
import shapely.ops
from shapely import speedups

from invest_natcap import raster_utils

import pyximport
pyximport.install()


raster_uri = 'test/invest-data/Base_Data/Freshwater/dem'
shapefile_uri = 'test/invest-data/Base_Data/Freshwater/subwatersheds.shp'

mask_uri = raster_utils.temporary_filename()
mask_nodata = 255
raster_utils.new_raster_from_base_uri(
    raster_uri, mask_uri, 'GTiff', mask_nodata, gdal.GDT_Byte, 
    fill_value=mask_nodata)

#Need this for a call to gdal.RasterizeLayer
mask_ds = gdal.Open(mask_uri, gdal.GA_Update)
mask_band = mask_ds.GetRasterBand(1)

shapefile = ogr.Open(shapefile_uri)
shapefile_layer = shapefile.GetLayer()

#make a shapefile that non-overlapping layers can be added to
driver = ogr.GetDriverByName('ESRI Shapefile')

layer_dir = raster_utils.temporary_folder()
layer_datasouce = driver.CreateDataSource(os.path.join(layer_dir, 'layer_out.shp'))
spat_ref = raster_utils.get_spatial_ref_uri(shapefile_uri)
layer = layer_datasouce.CreateLayer('layer_out', spat_ref, ogr.wkbPolygon)
layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
# Add one feature
layer_definition = layer.GetLayerDefn()
#values = raster_utils.aggregate_raster_values_uri(
#    raster_uri, shapefile_uri, shapefile_field='subws_id',
#    ignore_nodata=True, threshold_amount_lookup=None,
#    ignore_value_list=[], process_pool=None)

poly_list = []
for poly_index in range(shapefile_layer.GetFeatureCount()):
    print 'looping'
    poly_feat = shapefile_layer.GetFeature(poly_index)
    # Get the geometry of the polygon in WKT format
    poly_wkt = poly_feat.GetGeometryRef().ExportToWkt()
    # Load the geometry into shapely making it a shapely object
    shapely_polygon = shapely.wkt.loads(poly_wkt)
    # Add the shapely polygon geometry to a list, but first simplify the
    # geometry which smooths the edges making operations a lot faster
    poly_list.append(
        shapely_polygon.simplify(0.01, preserve_topology=False))

    feat = ogr.Feature(layer_definition)
    feat.SetField('id', 123)
    
    geom = ogr.CreateGeometryFromWkb(shapely_polygon.wkb)
    feat.SetGeometry(geom)
    layer.CreateFeature(feat)
    
    gdal.RasterizeLayer(
        mask_ds, [1], layer, burn_values=[1],
        options=['ALL_TOUCHED=TRUE'])
    
    layer.DeleteFeature(feat.GetFID())
    
gdal.Dataset.__swig_destroy__(mask_ds)
ogr.DataSource.__swig_destroy__(layer_datasouce)
#feat = geom = None  # destroy these
# Save and close everything
#ds = layer = feat = geom = None
    
for x in [mask_uri, layer_dir]:
    try:
        shutil.rmtree(x)
    except:
        os.remove(x)
