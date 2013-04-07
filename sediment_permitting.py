import os

from invest_natcap.sediment import sediment
from invest_natcap.routing import routing_utils

def base_run(workspace_dir):
    args = {}
    args['workspace_dir'] = os.path.join(workspace_dir, 'base_run')
    args['dem_uri'] = '../Pucallpa_subset/dem_fill'
    args['erosivity_uri'] = '../Pucallpa_subset/imf_erosivity'
    args['erodibility_uri'] = '../Pucallpa_subset/erod_k'
    args['landuse_uri'] = '../Pucallpa_subset/lulc_bases'
    args['watersheds_uri'] = '../Pucallpa_subset/ws_20.shp'
    args['biophysical_table_uri'] = '../Pucallpa_subset/biophysical.csv'
    args['threshold_flow_accumulation'] = 1000
    args['slope_threshold'] = 70.0
    args['sediment_threshold_table_uri'] = '../Pucallpa_subset/sed_thresh.csv'

    #First calculate the base sediment run
    sediment.execute(args)
    pixel_export_uri = os.path.join(workspace_dir, 'base_run', 'Output', 'sed_export.tif')


    


if __name__ == '__main__':
    base_run('./base_sediment_run')
