from invest_natcap import raster_utils

shapefile_uri = 'test/invest-data/Base_Data/Freshwater/subwatersheds.shp'
raster_uri = 'test/invest-data/Base_Data/Freshwater/landuse_90' 
r=raster_utils.aggregate_raster_values_uri(
    raster_uri, shapefile_uri, shapefile_field='Shape_Area')
    
print r