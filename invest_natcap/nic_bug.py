from osgeo import gdal
from osgeo import ogr
from osgeo import osr

import raster_utils

aoi_uri = '../../invest-data/CoastalProtection/Input/AOI_BarkClay.shp'
pop_uri = '../../invest-data/Base_Data/Marine/Population/global_pop/w001001.adf'

aoi = ogr.Open(aoi_uri)
pop = gdal.Open(pop_uri)

xRes = 250
yRes = 250
form = gdal.GDT_Float32
nodata = 0

raster_uri = './nic_raster_1.tif'

# use create raster from vector extents to build up raster
raster_1 = raster_utils.create_raster_from_vector_extents(
        xRes, yRes, form, nodata, raster_uri, aoi)

# rasterize aoi layer onto raster from above
gdal.RasterizeLayer(raster_1, [1], aoi.GetLayer(), burn_values=[1])

# project aoi to pop
pop_wkt = pop.GetProjection()

aoi_proj = raster_utils.reproject_datasource(
        aoi, pop_wkt, './nic_aoi_to_pop.shp')

raster_2 = raster_utils.create_raster_from_vector_extents(
        .008333, .008333 , form, nodata, './nic_aoi_proj.tif', aoi_proj)

gdal.RasterizeLayer(raster_2, [1], aoi_proj.GetLayer(), burn_values=[1])

# clip pop from reprojected aoi
clipped_pop = raster_utils.clip_dataset(
        pop, aoi_proj, './nic_pop_clipped.tif')

# reproject clipped pop from aoi
aoi_layer = aoi.GetLayer()
aoi_sr = aoi_layer.GetSpatialRef()
aoi_wkt = aoi_sr.ExportToWkt()

proj_pop = raster_utils.reproject_dataset(
        clipped_pop, 250, aoi_wkt, './nic_raster_2.tif')

proj_aoi_raster = raster_utils.reproject_dataset(
        raster_2, 250, aoi_wkt, './nic_raster_3.tif')

raster_1 = None
proj_pop = None
clipped_pop = None
aoi_proj = None

