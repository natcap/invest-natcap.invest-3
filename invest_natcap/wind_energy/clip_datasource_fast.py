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

output_uri = './clip_datasource_fast.shp'

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
        ogr.wkbMultiPoint)

#LOGGER.info('Creating new field')
# We only create one general field here because this function assumes that
# only the geometries and shapes themselves matter. It uses a faster
# clipping approach such that the specific field values can not be tracked
output_field = ogr.FieldDefn('id', ogr.OFTReal)
output_layer.CreateField(output_field)

# A list to hold the original shapefiles geometries
original_datasource_geoms = []
#LOGGER.info('Build up original datasources geometries with Shapely')
for original_feat in orig_layer:
    original_geom = shapely.wkt.loads(
            original_feat.GetGeometryRef().ExportToWkt())
    # The commented line below simplies the geometry by smoothing it which
    # allows the union operation to run much faster. Until accuracy is
    # decided upon, we will do it straight up
    original_datasource_geoms.append(original_geom.simplify(0.001, preserve_topology=False))
    
    #original_datasource_geoms.append(original_geom)

#LOGGER.info('Taking Unary Union on original geometries')
# Calculate the union on the list of geometries to get one collection of
# geometries
original_geom_collection = unary_union(original_datasource_geoms)

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

#LOGGER.info('Take the intersection of the AOI geometry collection and the
#        original geometry collection')
# Take the intersection of the geometry collections which will give us our
# 'clipped' geometry set
clipped_geom = aoi_geom_collection.intersection(original_geom_collection)

#LOGGER.debug('Dump the Shapely geometry to Well Known Binary format')
# Dump the unioned Shapely geometry into a Well Known Binary format so that
# it can be read and used by OGR
wkb_geom = dumps(clipped_geom)

# Create a new OGR geometry from the Well Known Binary
ogr_geom = ogr.CreateGeometryFromWkb(wkb_geom)
output_feature = ogr.Feature(output_layer.GetLayerDefn())
output_layer.CreateFeature(output_feature)

field_index = output_feature.GetFieldIndex('id')
# Arbitrarily set the field to 1 since there is just one feature that has
# the clipped geometry
output_feature.SetField(field_index, 1)
output_feature.SetGeometry(ogr_geom)

output_layer.SetFeature(output_feature)
output_feature = None

#LOGGER.info('Leaving clip_datasource_fast')
output_datasource = None
elapsed = time.time() - start
print elapsed
