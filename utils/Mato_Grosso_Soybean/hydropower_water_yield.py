""""
This is a saved model run from invest_natcap.hydropower.hydropower_water_yield.
Generated: 09/09/13 09:26:11
InVEST version: 2.5.6
"""

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

invest_natcap.hydropower.hydropower_water_yield.execute(args)
