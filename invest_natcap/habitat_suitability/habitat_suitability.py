"""Habitat suitability model"""

import os
import logging

from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('sediment')


def execute(args):
    """Calculates habitat suitability scores and patches given biophysical 
        rasters and classification curves. 
        
        workspace_dir - uri to workspace directory for output files
        output_cell_size - (optional) size of output cells
        depth_biophysical_uri - uri to a depth raster 
        salinity_biophysical_uri - uri to salinity raster
        temperature_biophysical_uri - uri to temperature raster
        oyster_habitat_suitability_depth_table_uri - uri to a csv table that
            has that has columns "Suitability" in (0,1) and "Depth" in
            range(depth_biophysical_uri)
        oyster_habitat_suitability_salinity_table_uri -  uri to a csv table that
            has that has columns "Suitability" in (0,1) and "Salinity" in 
            range(salinity_biophysical_uri)
        oyster_habitat_suitability_temperature_table_uri - uri to a csv table
            that has that has columns "Suitability" in (0,1) and  "Temperature"
            in range(temperature_biophysical_uri)
           """
    try:
        file_suffix = args['suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''
        
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'output')

    #Sets up the intermediate and output directory structure for the workspace
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            LOGGER.info('creating directory %s', directory)
            os.makedirs(directory)
            
    aligned_raster_stack = {
        'salinity_biophysical_uri': os.path.join(
            intermediate_dir, 'aligned_salinity.tif'),
        'temperature_biophysical_uri': os.path.join(
            intermediate_dir, 'aligned_temperature.tif'),
        'depth_biophysical_uri':  os.path.join(
            intermediate_dir, 'algined_depth.tif')
    }
    biophysical_keys = [
        'salinity_biophysical_uri', 'temperature_biophysical_uri',
        'depth_biophysical_uri']
    dataset_uri_list = [args[x] for x in biophysical_keys]
    dataset_out_uri_list = [aligned_raster_stack[x] for x in biophysical_keys]
    
    out_pixel_size = min(
        [raster_utils.get_cell_size_from_uri(x) for x in dataset_uri_list])
    
    raster_utils.align_dataset_list(
        dataset_uri_list, dataset_out_uri_list,
        ['nearest'] * len(dataset_out_uri_list),
        out_pixel_size, 'intersection', 0)
    