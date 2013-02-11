'''This will be the preperatory module for HRA. It will take all unprocessed
and pre-processed data from the UI and pass it to the hra_core module.'''

import os
import re
import shutil
import logging
import glob
import numpy as np
import math

from osgeo import gdal, ogr
from scipy import ndimage
from invest_natcap.habitat_risk_assessment import hra_core
from invest_natcap.habitat_risk_assessment import hra_preprocessor
from invest_natcap import raster_utils

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
        args['csv_uri']- The location of the directory containing the CSV files
            of habitat, stressor, and overlap ratings.         
        args['habitat_dir']- The string describing a directory location of all
            habitat shapefiles. These will be parsed though and rasterized to 
            be passed to hra_core module.
        args['stressors_dir']- The string describing a directory location of
            all stressor shapefiles. Will be parsed through and rasterized
            to be passed on to hra_core.'
        args['grid_size']- Int representing the desired pixel dimensions of
            both intermediate and ouput rasters. 
        args['risk_eq']- A string identifying the equation that should be used
            in calculating risk scores for each H-S overlap cell.
        args['decay_eq']- A string identifying the equation that should be used
            in calculating the decay of stressor buffer influence.
        args['max_rating']- An int representing the highest potential value that
            should be represented in rating, data quality, or weight in the
            CSV table.
        args['crit_uri']- The location of the shapefile criteria that we will
            use in our model. These will be rasterized and added to their
            approipriate dictionaries.

    Intermediate:
        hra_args['buffer_dict']- A dictionary that links the string name of each
            stressor shapefile to the desired buffering for that shape when
            rasterized.  This will get unpacked by the hra_preprocessor module.

            {'Stressor 1': 50,
             'Stressor 2': ...,
            }
    Output:
        hra_args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        hra_args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be supfolders of this one.
        hra_args['h-s']- A multi-level structure which holds all criteria ratings, 
            both numerical and raster that apply to habitat and stressor 
            overlaps. The structure, whose keys are tuples of 
            (Habitat, Stressor) names and map to an inner dictionary will have
            3 outer keys containing numeric-only criteria, raster-based
            criteria, and a dataset that shows the potentially buffered overlap
            between the habitat and stressor. The overall structure will be as
            pictured:

            {(Habitat A, Stressor 1): 
                    {'Crit_Ratings': 
                        {'CritName': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters': 
                        {'CritName':
                            {'DS': <CritName Raster>, 'Weight': 1.0, 'DQ': 1.0}
                        },
                    'DS':  <Open A-1 Raster Dataset>
                    }
            }
        args['habitats']- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile provided by the user.
        args['stressors']- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            name, and stressors['stressorName']['DS'] points to the rasterized
            stressor shapefile provided by the user that will be buffered by
            the indicated amount in buffer_dict['stressorName'].
        hra_args['risk_eq']- String which identifies the equation to be used
            for calculating risk.  The core module should check for 
            possibilities, and send to a different function when deciding R 
            dependent on this.
        args['max_risk']- The highest possible risk value for any given pairing
            of habitat and stressor.
    Returns nothing.
    '''
    hra_args = {}
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    hra_args['workspace_dir'] = args['workspace_dir']

    #Create intermediate and output folders. Delete old ones, if they exist.
    for folder in (inter_dir, output_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)
    
    #Since we need to use the h-s, stressor, and habitat dicts elsewhere, want
    #to use the pre-process module to unpack them.
    unpack_over_dict(args['csv_uri'], hra_args)

    #Where we will store the burned individual habitat and stressor rasters.
    hab_dir = os.path.join(inter_dir, 'Habitat_Rasters')
    stress_dir = os.path.join(inter_dir, 'Stressor_Rasters')
    burned_crit_dir = os.path.join(inter_dir, 'Temp_Burned_Criteria')

    for folder in (hab_dir, stress_dir, burned_crit_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)

    #Habitats
    hab_list = []
    for ele in ('habitat_dir', 'species_dir'):
        if ele in args:
            hab_list.append(glob.glob(os.path.join(args[ele], '*.shp'))
    
    add_hab_rasters(hab_dir, hra_args['habitats'], hab_list, args['grid_size'])

    #Stressors

def add_hab_rasters(dir, habitats, hab_list, grid_size):
    '''Want to get all shapefiles within any directories in hab_list, and burn
    them to a raster.'''
    
    for shape in hab_list:
        
        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself
        name = os.path.splitext(os.path.split(shape)[1])[0]

        out_uri = os.path.join(dir, name + '.tif')
        
        datasource = ogr.Open(shape)
        layer = datasource.GetLayer()
        
        #Making the nodata value 0 so that it's easier to combine the 
        #layers later.
        r_dataset = \
            raster_utils.create_raster_from_vector_extents(grid_size, grid_size,
                    gdal.GDT_Int32, 0, out_uri, datasource)

        band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
        band.Fill(nodata)

        gdal.RasterizeLayer(r_dataset, [1], layer, burn_values=[1], 
                                                options=['ALL_TOUCHED=TRUE'])

        habitats[name]['DS'] = r_dataset

def unpack_over_dict(csv_uri, args):
    '''This throws the dictionary coming from the pre-processor into the
    equivalent dictionaries in args so that they can be processed before being
    passed into the core module.
    
    Input:
        csv_uri- Reference to the folder location of the CSV tables containing
            all habitat and stressor rating information.
        args- The dictionary into which the individual ratings dictionaries
            should be placed.
    Output:
        A modified args dictionary containing dictionary versions of the CSV
        tables located in csv_uri. The dictionaries should be of the forms as
        follows.
           
        h-s- A multi-level structure which will hold all criteria ratings, 
            both numerical and raster that apply to habitat and stressor 
            overlaps. The structure, whose keys are tuples of 
            (Habitat, Stressor) names and map to an inner dictionary will have
            2 outer keys containing numeric-only criteria, and raster-based
            criteria. At this time, we should only have two entries in a
            criteria raster entry, since we have yet to add the rasterized
            versions of the criteria.

            {(Habitat A, Stressor 1): 
                    {'Crit_Ratings': 
                        {'CritName': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters': 
                        {'CritName':
                            {'Weight': 1.0, 'DQ': 1.0}
                        },
                    }
            }
        habitats- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            weights and data quality for the rasters.         
        stressors- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            weights and data quality for the rasters.w
    Returns nothing.
    '''
    dicts = hra_preprocessor.parse_hra_tables(csv_uri)
    LOGGER.debug(csv_uri)
    LOGGER.debug("DICTIONARIES:")
    LOGGER.debug(dicts)


    for dict_name in dicts:
     
       args[dict_name] = dicts[dict_name]
