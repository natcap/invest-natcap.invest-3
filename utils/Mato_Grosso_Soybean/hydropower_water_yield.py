import os

import invest_natcap.hydropower.hydropower_water_yield


args = {
        u'biophysical_table_uri': u'Water_Yield/Parameters.csv',
        u'depth_to_root_rest_layer_uri': u'Water_Yield/mg_sdepth_proj.tif',
        u'eto_uri': u'Water_Yield/mg_pet',
        u'lulc_uri': u'MG_Soy_Exp_07122013/mg_lulc0',
        u'pawc_uri': u'Water_Yield/mg_pawc_proj.tif',
        u'precipitation_uri': u'Water_Yield/mg_precipe',
        u'results_suffix': u'',
        u'seasonality_constant': u'5',
        u'sub_watersheds_uri': u'',
        u'water_scarcity_container': False,
        u'watersheds_uri': u'Water_Yield/mg_boundary.shp',
        u'workspace_dir': u'\Water_Yield\workspace',
}

base_landcover_table_uri = os.path.join(args['workspace_dir'], 'base_landcover_scenario.csv')

base_landcover_table = open(base_landcover_table_uri, 'wb')
base_landcover_table.write('percent expansion,water yield volume\n')

invest_natcap.hydropower.hydropower_water_yield.execute(args)
water_yield_shapefile_uri = os.path.join(
    args['workspace_dir'], 'output', 'wyield_sheds.shp')
ws_table = raster_utils.extract_datasource_table_by_key(
    water_yield_shapefile_uri, 'ws_id')
base_landcover_table.write('0,%.2f\n' % ws_table['wyield_vol'])