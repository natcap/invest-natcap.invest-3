import os

from invest_natcap.sediment import sediment
from invest_natcap.routing import routing_utils

def base_run(workspace_dir):
    args = {}
    args['workspace_dir'] = workspace_dir
    args['dem_uri'] = '../Pucallpa_subset/dem_fill'
    args['erosivity_uri'] = '../Pucallpa_subset/imf_erosivity'
    args['erodibility_uri'] = '../Pucallpa_subset/erod_k'
    args['landuse_uri'] = '../Pucallpa_subset/lulc_bases'
    args['watersheds_uri'] = '../Pucallpa_subset/ws_20.shp'
    args['biophysical_table_uri'] = '../Pucallpa_subset/biophysical.csv'
    args['threshold_flow_accumulation'] = 1000
    args['slope_threshold'] = 70.0
    args['sediment_threshold_table_uri'] = '../Pucallpa_subset/sed_thresh.csv'
    #routing_utils.flow_accumulation(args['dem_uri'], os.path.join(args['workspace_dir'], 'flux_output_uri.tif'))
    sediment.execute(args)

if __name__ == '__main__':
    base_run('./base_sediment_run')
