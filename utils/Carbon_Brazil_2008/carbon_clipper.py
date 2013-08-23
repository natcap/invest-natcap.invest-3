from invest_natcap import raster_utils
import gdal
import ogr

#clip lulc
#clip biomass


BASE_BIOMASS_FILENAME = './braz_bio_08'
BASE_LANDCOVER_FILENAME = './braz_lulc_08'
AOI_FILENAME = './ecoregions_project.shp'
CLIPPED_BIOMASS_FILENAME = './clipped_bio.tif'
CLIPPED_BASE_LANDCOVER_FILENAME = './clipped_lulc.tif'
ECOREGIONS_FILENAME = 'ecoregions.tif'


raster_utils.clip_dataset_uri(
	BASE_BIOMASS_FILENAME, AOI_FILENAME, CLIPPED_BIOMASS_FILENAME,
	False)
	
raster_utils.clip_dataset_uri(
	BASE_LANDCOVER_FILENAME, AOI_FILENAME, CLIPPED_BASE_LANDCOVER_FILENAME,
	False)
	
raster_utils.new_raster_from_base_uri(
	CLIPPED_BASE_LANDCOVER_FILENAME, ECOREGIONS_FILENAME, 'GTiff', -1, gdal.GDT_Int32, 0)

	
ecoregions_dataset = gdal.Open(ECOREGIONS_FILENAME, gdal.GA_Update)
ecoregions_layer = ogr.Open(AOI_FILENAME)
gdal.RasterizeLayer(
	ecoregions_dataset, [1], ecoregions_layer, options=['ATTRIBUTE=region_id'])