import os

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import shapely.wkt
from shapely.ops import unary_union
from shapely.wkb import dumps
from shapely.wkb import loads
from shapely import speedups
import time

speedups.enable()
start = time.time()

aoi_ds = \
    ogr.Open('../../../invest-data/WaveEnergy/Input/WaveData/Global_extract.shp')

orig_ds = \
    ogr.Open('../../../invest-data/WaveEnergy/Input/WaveData/Global.shp')

output_uri = './clip_datasource_original.shp'

#LOGGER.info('Entering clip_datasource')

orig_layer = orig_ds.GetLayer()
aoi_layer = aoi_ds.GetLayer()

# If the file already exists remove it
if os.path.isfile(output_uri):
    os.remove(output_uri)

#LOGGER.info('Creating new datasource')
# Create a new shapefile from the orginal_datasource 
output_driver = ogr.GetDriverByName('ESRI Shapefile')
output_datasource = output_driver.CreateDataSource(output_uri)

# Get the original_layer definition which holds needed attribute values
original_layer_dfn = orig_layer.GetLayerDefn()

# Create the new layer for output_datasource using same name and geometry
# type from original_datasource as well as spatial reference
output_layer = output_datasource.CreateLayer(
        original_layer_dfn.GetName(), orig_layer.GetSpatialRef(), 
        original_layer_dfn.GetGeomType())

# Get the number of fields in original_layer
original_field_count = original_layer_dfn.GetFieldCount()

#LOGGER.info('Creating new fields')
# For every field, create a duplicate field and add it to the new 
# shapefiles layer
for fld_index in range(original_field_count):
    original_field = original_layer_dfn.GetFieldDefn(fld_index)
    output_field = ogr.FieldDefn(
            original_field.GetName(), original_field.GetType())
    # NOT setting the WIDTH or PRECISION because that seems to be unneeded
    # and causes interesting OGR conflicts
    output_layer.CreateField(output_field)

# Get the feature and geometry of the aoi
aoi_geom_list = []
for aoi_feat in aoi_layer:
    aoi_geom = aoi_feat.GetGeometryRef()
    aoi_geom_list.append(aoi_geom.Clone())
    #aoi_feat = None
print len(aoi_geom_list)
#print aoi_geom_list
#LOGGER.info('Starting iteration over geometries')
# Iterate over each feature in original layer
count = 1
for orig_feat in orig_layer:
    if count % 100 is 0:
        print count
    count = count + 1
    for aoi_geom in aoi_geom_list:
        # Get the geometry for the feature
        orig_geom = orig_feat.GetGeometryRef()
        # Check to see if the feature and the aoi intersect. This will return a
        # new geometry if there is an intersection. If there is not an
        # intersection it will return an empty geometry or it will return None
        # and print an error to standard out
        #print 'Getting intersection'
        intersect_geom = aoi_geom.Intersection(orig_geom)
        #print 'Got intersection' 
        #if intersect_geom:
        if not intersect_geom == None and not intersect_geom.IsEmpty():
            # Copy original_datasource's feature and set as new shapes feature
            output_feature = ogr.Feature(
                    feature_def=output_layer.GetLayerDefn())
            #output_layer.CreateFeature(output_feature)
        
            # Since the original feature is of interest add it's fields and
            # Values to the new feature from the intersecting geometries
            #for fld_index2 in range(output_feature.GetFieldCount()):
            #    orig_field_value = orig_feat.GetField(fld_index2)
            #    output_feature.SetField(fld_index2, orig_field_value)
            output_feature.SetFrom(orig_feat, False)
            output_feature.SetGeometry(intersect_geom)
            output_layer.CreateFeature(output_feature)
            #output_layer.SetFeature(output_feature)
            output_feature = None
            break

    orig_feat = None

#LOGGER.info('Leaving clip_datasource')
output_datasource = None
elapsed =  time.time() - start
print elapsed
