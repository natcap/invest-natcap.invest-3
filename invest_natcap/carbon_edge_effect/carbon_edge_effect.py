"""InVEST Carbon Edge Effect Model"""

import os

import gdal
import pygeoprocessing

def execute(args):
    """InVEST Carbon Edge Model calculates the carbon due to

        args['workspace_dir'] -
        args['results_suffix'] -
        args['biophysical_table_uri'] -
        args['lulc_uri'] -
        args['regression_coefficient_table'] -
        args['servicesheds_uri'] -
    """

    pygeoprocessing.create_directories([args['workspace_dir']])
    try:
        file_suffix = args['results_suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''

    #TASK: (optional) clip dataset to AOI if it exists
    #TASK: classify forest pixels from lulc
    biophysical_table = pygeoprocessing.get_lookup_from_table(
        args['biophysical_table_uri'], 'lucode')

    lucode_to_carbon = {}
    for lucode in biophysical_table:
        try:
            lucode_to_carbon[int(lucode)] = float(
                biophysical_table[lucode]['c_above'])
        except ValueError:
            #this might be because the c_above parameter is n/a or undefined
            #because of forest
            lucode_to_carbon[int(lucode)] = 0.0

    carbon_map_nodata = -1
    non_edge_carbon_map_uri = os.path.join(
        args['workspace_dir'], 'non_edge_carbon_map%s.tif' % file_suffix)

    pygeoprocessing.reclassify_dataset_uri(
        args['lulc_uri'], lucode_to_carbon, non_edge_carbon_map_uri,
        gdal.GDT_Float32, carbon_map_nodata)

    #TASK: map distance to edge
    #TASK: map aboveground carbon from table to lulc that is not forest
    #TASK: combine maps into output
    carbon_map_uri = os.path.join(
        args['workspace_dir'], 'carbon_map%s.tif' % file_suffix)


    #TASK: generate report (optional) by serviceshed if they exist