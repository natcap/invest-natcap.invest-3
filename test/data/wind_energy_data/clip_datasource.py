from osgeo import ogr, gdal, osr
import os

global_poly = \
    ogr.Open('../../../../invest-data/Base_Data/Marine/Land/global_polygon.shp')

aoi = ogr.Open('wind_energy_distance_aoi.shp')

global_lyr = global_poly.GetLayer()
aoi_lyr = aoi.GetLayer()

# create a new shapefile from the orginal_datasource 
output_uri = './intersection_shape.shp'
if os.path.isfile(output_uri):
    os.remove(output_uri)

output_driver = ogr.GetDriverByName('ESRI Shapefile')
output_datasource = output_driver.CreateDataSource(output_uri)

#Get the original_layer definition which holds needed attribute values
original_layer_dfn = global_lyr.GetLayerDefn()

#Create the new layer for output_datasource using same name and geometry
#type from original_datasource, but different projection
output_layer = output_datasource.CreateLayer(
        original_layer_dfn.GetName(), global_lyr.GetSpatialRef(), 
        original_layer_dfn.GetGeomType())

#Get the number of fields in original_layer
original_field_count = original_layer_dfn.GetFieldCount()

#For every field, create a duplicate field and add it to the new 
#shapefiles layer
for fld_index in range(original_field_count):
    original_field = original_layer_dfn.GetFieldDefn(fld_index)
    output_field = ogr.FieldDefn(original_field.GetName(), original_field.GetType())
    output_field.SetWidth(original_field.GetWidth())
    output_field.SetPrecision(original_field.GetPrecision())
    output_layer.CreateField(output_field)

aoi_feat = aoi_lyr.GetFeature(0)
aoi_geom = aoi_feat.GetGeometryRef()

for orig_feat in global_lyr:
    orig_geom = orig_feat.GetGeometryRef()


    intersect = aoi_geom.Intersection(orig_geom)
   
    if not intersect == None:
        #Copy original_datasource's feature and set as new shapes feature
        output_feature = ogr.Feature(feature_def=output_layer.GetLayerDefn())
        output_feature.SetGeometry(intersect)

        for fld_index2 in range(output_feature.GetFieldCount()):
            orig_field_value = orig_feat.GetField(fld_index2)
            output_feature.SetField(fld_index2, orig_field_value)

        output_layer.CreateFeature(output_feature)
        output_feature = None

    else:
        print 'the id that is causing error', str(orig_feat.GetField(0))
