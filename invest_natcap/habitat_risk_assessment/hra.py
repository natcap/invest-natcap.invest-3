'''This will be the preperatory module for HRA. It will take all unprocessed
and pre-processed data from the UI and pass it to the hra_core module.'''

import os
import shutil
import logging
import glob

from osgeo import gdal, ogr
from invest_natcap.habitat_risk_assessment import hra_core

LOGGER = logging.getLogger('HRA')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''This function will prepare files passed from the UI to be sent on to the
    hra_core module.

    Input:
        args- A python dictionary created by the UI for use in the HRA model. It
            will contain the following data.
        args['workspace_dir']- String which points to the directory into which
            intermediate and output files should be placed.
        args['habitat_dir']- The string describing a directory location of all
            habitat shapefiles. These will be parsed though and rasterized to 
            be passed to hra_core module.
        args['stressors_dir']- The string describing a directory location of
            all stressor shapefiles. Will be parsed through and rasterized
            to be passed on to hra_core.'
        args['grid_size']- Int representing the desired pixel dimensions of
            both intermediate and ouput rasters. 
        args['ratings']- A structure which holds all exposure and consequence
            rating for each combination of habitat and stressor. The inner
            structure is a dictionary whose key is a tuple which points to a
            tuple of lists which contain tuples.

            {(Habitat A, Stressor 1): ([(E1Rating, E1DataQuality, E1Weight), ...],
                                       [(C1Rating, C1DataQuality, C1Weight), ...])
                                       .
                                       .
                                       . }
    Output:
        hra_args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run.

    Returns nothing.
    '''
    hra_args = {}

    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    #Create intermediate and output folders. Delete old ones, if they exist.
    for folder in (inter_dir, output_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)

    hra_args['workspace_dir'] = args['workspace_dir']

    #Take all shapefiles in both the habitats and the stressors folders and
    #make them into rasters of grid_size by grid_size resolution.
    
    #Glob.glob gets all of the files that fall into the form .shp, and makes
    #them into a list.
    file_names = glob.glob(args['habitat_dir'])
    h_rast = os.path.join(inter_dir, 'Habitat_Rasters')

    make_rasters(file_names, h_rast, args['grid_size'])
    
    file_names = glob.glob(args['stressors_dir'])
    s_rast = os.path.join(inter_dir, 'Stressor_Rasters')

    make_rasters(file_names, s_rast, args['grid_size'])


def make_rasters(dir, file_names, grid_size):

    
