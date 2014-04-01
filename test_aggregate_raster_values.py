import cProfile
import pstats
import os
import shutil
import glob
import time
import heapq

import gdal
import numpy
from osgeo import ogr

import shapely.wkt
import shapely.ops
import shapely.prepared
from shapely import speedups
from invest_natcap import raster_utils

import pyximport
pyximport.install()

#raster_uri = 'Peru_for_Rich/dem_50km'
shapefile_uri = 'Peru_for_Rich/serv_clip50in.shp'

#raster_uri =    'overlapping_polygons/sample_static_impact_map.tif'
#shapefile_uri = 'overlapping_polygons/servicesheds_col.shp'

#raster_uri = 'test/invest-data/Base_Data/Freshwater/dem'
#shapefile_uri = 'test/invest-data/Base_Data/Freshwater/subwatersheds.shp'

#mask_uri = raster_utils.temporary_filename()
#mask_nodata = 255
#raster_utils.new_raster_from_base_uri(
#    raster_uri, mask_uri, 'GTiff', mask_nodata, gdal.GDT_Byte, 
#    fill_value=mask_nodata)

#Need this for a call to gdal.RasterizeLayer
#mask_ds = gdal.Open(mask_uri, gdal.GA_Update)
#mask_band = mask_ds.GetRasterBand(1)

shapefile = ogr.Open(shapefile_uri)
shapefile_layer = shapefile.GetLayer()

#make a shapefile that non-overlapping layers can be added to
#driver = ogr.GetDriverByName('ESRI Shapefile')
#layer_dir = raster_utils.temporary_folder()
#layer_datasouce = driver.CreateDataSource(os.path.join(layer_dir, 'layer_out.shp'))
#spat_ref = raster_utils.get_spatial_ref_uri(shapefile_uri)
#layer = layer_datasouce.CreateLayer('layer_out', spat_ref, ogr.wkbPolygon)
#layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
# Add one feature
#layer_definition = layer.GetLayerDefn()

#values = raster_utils.aggregate_raster_values_uri(
#    raster_uri, shapefile_uri, shapefile_field='ws_id',
#    ignore_nodata=True, threshold_amount_lookup=None,
#    ignore_value_list=[], process_pool=None)
#print values

poly_intersection_lookup = {}
for poly_feat in shapefile_layer:
    #print 'looping'
    #poly_feat = shapefile_layer.GetFeature(poly_index)
    poly_wkt = poly_feat.GetGeometryRef().ExportToWkt()
    shapely_polygon = shapely.wkt.loads(poly_wkt)
    poly_fid = poly_feat.GetFID()
    print poly_fid
    poly_intersection_lookup[poly_fid] = {
        'poly': shapely_polygon,
        'prepared': shapely.prepared.prep(shapely_polygon),
        'intersects': set(),
    }
    # Get the geometry of the polygon in WKT format
    # Load the geometry into shapely making it a shapely object
    # Add the shapely polygon geometry to a list, but first simplify the
    # geometry which smooths the edges making operations a lot faster
    #poly_list.append(shapely_polygon)

shapefile_layer.ResetReading()

for poly_fid in poly_intersection_lookup:
    print poly_fid
    for intersect_poly_fid in poly_intersection_lookup:
        polygon = poly_intersection_lookup[poly_fid]['prepared']
        if polygon.intersects(
            poly_intersection_lookup[intersect_poly_fid]['poly']):
            poly_intersection_lookup[poly_fid]['intersects'].add(
                intersect_poly_fid)
                
processed_polygons = set()
while len(poly_intersection_lookup) != len(processed_polygons):
    #sort polygons by increasing number of intersections
    heap = []
    for poly_fid, poly_dict in poly_intersection_lookup.iteritems():
        if poly_fid not in processed_polygons:
            heapq.heappush(
                heap, (len(poly_dict['intersects']), poly_fid, poly_dict))

    #build maximal subset
    maximal_set = set()
    while len(heap) > 0:
        _, poly_fid, poly_dict = heapq.heappop(heap)
        polygon = poly_intersection_lookup[poly_fid]['prepared']
        for maxset_fid in maximal_set:
            if polygon.intersects(
                poly_intersection_lookup[maxset_fid]['poly']):
                #it intersects and can't be part of the maximal subset
                break
        else:
            #we made it through without an intersection, add poly_fid to 
            #the maximal set
            maximal_set.add(poly_fid)
            processed_polygons.add(poly_fid)
            #remove that polygon and update the intersections
            #del poly_intersection_lookup[poly_fid]
            for poly_dict in poly_intersection_lookup.itervalues():
                poly_dict['intersects'].discard(poly_fid)
    print maximal_set
        
        
                
#print poly_intersection_lookup
#Clean up temporary files
#gdal.Dataset.__swig_destroy__(mask_ds)
#ogr.DataSource.__swig_destroy__(layer_datasouce)
    
#for x in [mask_uri, layer_dir]:
#    try:
#        shutil.rmtree(x)
#    except:
#        os.remove(x)
