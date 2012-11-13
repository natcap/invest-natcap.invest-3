"""Entry point for the Habitat Risk Assessment module"""

import os
import glob
import logging

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('hra_preprocessor')


def execute(args):
    """Read two directories for habitat and stressor layers and make
        appropriate output csv files

        args['workspace_dir'] - The directory to dump the output CSV files to
        args['habitat_dir'] - A directory of ArcGIS shapefiles that are habitats
        args['stressor_dir'] - A directory of ArcGIS shapefiles that are stressors

        returns nothing"""

    #Make the workspace directory if it doesn't exist
    if not os.path.exists(args['workspace_dir']):
        os.makedirs(args['workspace_dir'])

    habitat_names = [
        os.path.basename(f.split('.')[0]) for f in 
        glob.glob(os.path.join(args['habitat_dir'], '*.shp'))]
    
    stressor_names = [
        os.path.basename(f.split('.')[0]) for f in 
        glob.glob(os.path.join(args['stressor_dir'], '*.shp'))]
    

    LOGGER.debug(habitat_names)
    LOGGER.debug(stressor_names)
