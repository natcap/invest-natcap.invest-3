from invest_natcap.sediment import sediment


def base_run(workspace_dir):
    args = {}
    args['workspace_dir'] = workspace_dir
    args['dem_uri'] = '../Base_Data/Freshwater/dem'
    args['erosivity_uri'] = '../Base_Data/Freshwater/erosivity'
    args['erodibility_uri'] = '../Base_Data/Freshwater/erodibility'
    args['landuse_uri'] = '../Base_Data/Freshwater/landuse_90'
    args['watersheds_uri'] = '../Base_Data/Freshwater/watersheds.shp'
    args['biophysical_table_uri'] = '../Base_Data/Freshwater/biophysical_table.csv'
    args['threshold_flow_accumulation'] = 1000
    args['slope_threshold'] = 70.0
    args['sediment_threshold_table_uri'] = '../Sedimentation/input/sediment_threshold_table.csv'
    sediment.execute(args)

if __name__ == '__main__':
    base_run('./base_sediment_run')
