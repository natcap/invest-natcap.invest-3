from invest_natcap import raster_utils

raster_uri = "C:/Users/rich/Documents/unilever_output/Mato_Grosso_global/output/sed_export_mato_grosso.tif"
shapefile_uri = "C:/Users/rich/Dropbox/Unilever_data_from_Stacie/Input_MatoGrosso_global/Mato_Grosso.shp"

print raster_utils.aggregate_raster_values_uri(
    raster_uri, shapefile_uri, shapefile_field='ws_id', ignore_nodata=False,
    threshold_amount_lookup=None, ignore_value_list=[], process_pool=None,
    all_touched=False)

    