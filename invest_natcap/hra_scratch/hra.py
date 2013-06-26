'''This will be the preperatory module for HRA. It will take all unprocessed
and pre-processed data from the UI and pass it to the hra_core module.'''

import os
import shutil
import logging
import fnmatch
import numpy as np
import math

from osgeo import gdal, ogr, osr
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
            of habitat, stressor, and overlap ratings. Will also contain a .txt
            JSON file that has directory locations (potentially) for habitats,
            species, stressors, and criteria.
        args['grid_size']- Int representing the desired pixel dimensions of
            both intermediate and ouput rasters. 
        args['risk_eq']- A string identifying the equation that should be used
            in calculating risk scores for each H-S overlap cell. This will be
            either 'Euclidean' or 'Multiplicative'.
        args['decay_eq']- A string identifying the equation that should be used
            in calculating the decay of stressor buffer influence. This can be
            'None', 'Linear', or 'Exponential'.
        args['max_rating']- An int representing the highest potential value that
            should be represented in rating, data quality, or weight in the
            CSV table.
        args['aoi_tables']- A shapefile containing one or more planning regions
            for a given model. This will be used to get the average risk value
            over a larger area. Each potential region MUST contain the
            attribute "name" as a way of identifying each individual shape.

    Intermediate:
        hra_args['habitats_dir']- The directory location of all habitat 
            shapefiles. These will be parsed though and rasterized to be passed
            to hra_core module. This may not exist if 'species_dir' exists.
        hra_args['species_dir']- The directory location of all species
            shapefiles. These will be parsed though and rasterized to be passed
            to hra_core module. This may not exist if 'habitats_dir' exists.
        hra_args['stressors_dir']- The string describing a directory location of
            all stressor shapefiles. Will be parsed through and rasterized
            to be passed on to hra_core.
        hra_args['criteria_dir']- The directory which holds the criteria 
            shapefiles. May not exist if the user does not desire criteria 
            shapefiles. This will be in a VERY specific format, which shall be
            described in the user's guide.
        hra_args['buffer_dict']- A dictionary that links the string name of each
            stressor shapefile to the desired buffering for that shape when
            rasterized.  This will get unpacked by the hra_preprocessor module.

            {'Stressor 1': 50,
             'Stressor 2': ...,
            }
        hra_args['h_s_c']- A multi-level structure which holds numerical criteria
            ratings, as well as weights and data qualities for criteria rasters.
            h-s will hold criteria that apply to habitat and stressor overlaps, 
            and be applied to the consequence score. The structure's outermost 
            keys are tuples of (Habitat, Stressor) names. The overall structure 
            will be as pictured:

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
        hra_args['habitats']- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            raster information. The outermost keys are habitat names.
        hra_args['h_s_e']- Similar to the h_s dictionary, a multi-level
            dictionary containing habitat-stressor-specific criteria ratings and
            raster information which should be applied to the exposure score. 
            The outermost keys are tuples of (Habitat, Stressor) names.

   Output:
        hra_args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        hra_args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be subfolders of this one.
        hra_args['h_s_c']- The same as intermediate/'h-s', but with the addition
            of a 3rd key 'DS' to the outer dictionary layer. This will map to
            a dataset URI that shows the potentially buffered overlap between the 
            habitat and stressor. Additionally, any raster criteria will
            be placed in their criteria name subdictionary. The overall 
            structure will be as pictured:

            {(Habitat A, Stressor 1): 
                    {'Crit_Ratings': 
                        {'CritName': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters': 
                        {'CritName':
                            {'DS': "CritName Raster URI", 'Weight': 1.0, 'DQ': 1.0}
                        },
                    'DS':  "A-1 Dataset URI"
                    }
            }
        hra_args['habitats']- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile URI provided by the user.
        hra_args['h_s_e']- Similar to the h_s_c dictionary, a multi-level
            dictionary containing habitat-stressor-specific criteria ratings and
            shapes. The same as intermediate/'h-s', but with the addition
            of a 3rd key 'DS' to the outer dictionary layer. This will map to
            a dataset URI that shows the potentially buffered overlap between the 
            habitat and stressor. Additionally, any raster criteria will
            be placed in their criteria name subdictionary. 
        hra_args['risk_eq']- String which identifies the equation to be used
            for calculating risk.  The core module should check for 
            possibilities, and send to a different function when deciding R 
            dependent on this.
        hra_args['max_risk']- The highest possible risk value for any given pairing
            of habitat and stressor.
    
    Returns nothing.
    '''

