from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap import raster_utils
from invest_natcap.wind_energy import wind_energy_biophysical

aoi_uri = '../../invest-data/CoastalProtection/Input/AOI_BarkClay.shp'
pop_uri = '../../invest-data/Base_Data/Marine/Land/global_polygon.shp'

aoi = ogr.Open(aoi_uri)
pop = ogr.Open(pop_uri)

xRes = 200
yRes = 200
form = gdal.GDT_Float32
nodata = 0

raster_uri = './nic_raster_1.tif'

# use create raster from vector extents to build up raster
raster_1 = raster_utils.create_raster_from_vector_extents(
        xRes, yRes, form, nodata, raster_uri, aoi)

# rasterize aoi layer onto raster from above
gdal.RasterizeLayer(raster_1, [1], aoi.GetLayer(), burn_values=[1])

# project aoi to pop
pop_layer = pop.GetLayer()
pop_sr = pop_layer.GetSpatialRef()
pop_wkt = pop_sr.ExportToWkt()

aoi_proj = raster_utils.reproject_datasource(
        aoi, pop_wkt, './nic_aoi_to_pop.shp')

# clip pop from reprojected aoi
clipped_pop = wind_energy_biophysical.clip_datasource(
        aoi_proj, pop, './nic_pop_clipped.shp')


print clipped_pop

# reproject clipped pop from aoi
aoi_layer = aoi.GetLayer()
aoi_sr = aoi_layer.GetSpatialRef()
aoi_wkt = aoi_sr.ExportToWkt()

proj_pop = raster_utils.reproject_datasource(
        clipped_pop, aoi_wkt, './nic_pop_proj.shp')
print proj_pop
# use create raster from vector extents to build up a raster
raster_2 = raster_utils.create_raster_from_vector_extents(
        xRes, yRes, form, nodata, './nic_raster_2.tif', aoi)

# rasterize pop onto raster from above
gdal.RasterizeLayer(raster_2, [1], proj_pop.GetLayer(), burn_values=[1])

raster_1 = None
raster_2 = None
proj_pop = None
clipped_pop = None
aoi_proj = None

