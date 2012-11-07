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

#aoi_ds = \
#    ogr.Open('../../test/data/wind_energy_regression_data/aoi_prj_to_land.shp')

#orig_ds = \
#    ogr.Open('../../../invest-data/Base_Data/Marine/Land/global_polygon.shp')

output_uri = './clip_datasource_new2.shp'
    
#LOGGER.info('Entering clip_datasource_new')

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

# A list to hold the aoi shapefiles geometries
aoi_datasource_geoms = []

#LOGGER.info('Build up AOI datasources geometries with Shapely')
for aoi_feat in aoi_layer:
    aoi_geom = shapely.wkt.loads(aoi_feat.GetGeometryRef().ExportToWkt())
    aoi_datasource_geoms.append(aoi_geom.simplify(0.001, preserve_topology=False))
    #aoi_datasource_geoms.append(aoi_geom)

#LOGGER.info('Taking Unary Union on AOI geometries')
# Calculate the union on the list of geometries to get one collection of
# geometries
aoi_geom_collection = unary_union(aoi_datasource_geoms)

#LOGGER.info('Starting iteration over geometries')
# Iterate over each feature in original layer
count = 1
for orig_feat in orig_layer:
    if count % 100 is 0:
        print count

    count = count + 1
    # Get the geometry for the feature
    orig_geom_wkb = orig_feat.GetGeometryRef().ExportToWkb()
    orig_geom_shapely = loads(orig_geom_wkb) 
    
    intersect_geom = aoi_geom_collection.intersection(orig_geom_shapely)
    
    if not intersect_geom.is_empty:
        # Copy original_datasource's feature and set as new shapes feature
        output_feature = ogr.Feature(
                feature_def=output_layer.GetLayerDefn())
        
        geom_to_wkb = dumps(intersect_geom)
        geom_to_ogr = ogr.CreateGeometryFromWkb(geom_to_wkb)

        output_feature.SetFrom(orig_feat, False)
        output_feature.SetGeometry(geom_to_ogr)
        #output_layer.SetFeature(output_feature)
        output_layer.CreateFeature(output_feature)
        output_feature = None

#LOGGER.info('Leaving clip_datasource_new')
output_datasource = None
elapsed = time.time() - start
print elapsed
