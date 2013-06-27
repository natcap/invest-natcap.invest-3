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

    hra_args = {}
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    hra_args['workspace_dir'] = args['workspace_dir']

    hra_args['risk_eq'] = args['risk_eq']
    
    #Depending on the risk calculation equatioa, this should return the highest
    #possible value of risk for any given habitat-stressor pairing. The highest
    #risk for a habitat would just be this risk value * the number of stressor
    #pairs that apply to it.
    max_r = calc_max_rating(args['risk_eq'], args['max_rating'])
    hra_args['max_risk'] = max_r
    
    #Create intermediate and output folders. Delete old ones, if they exist.
    for folder in (inter_dir, output_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)
   
    #If using aoi zones are desired, pass the AOI layer directly to core to be
    #dealt with there.
    if 'aoi_tables' in args:

        #Need to check that this shapefile contains the correct attribute name.
        #Later, this is where the uppercase/lowercase dictionary can be
        #implimented.
        shape = ogr.Open(args['aoi_tables'])
        layer = shape.GetLayer()
    
        lower_attrib = None
        for feature in layer:
            
            if lower_attrib == None:
                lower_attrib = dict(zip(map(lambda x: x.lower(), feature.items().keys()), 
                            feature.items().keys()))
            
            if 'name' not in lower_attrib:
                raise ImproperAOIAttributeName("Risk table layer attributes must \
                    contain the attribute \"Name\" in order to be properly used \
                    within the HRA model run.")

        #By this point, we know that the AOI layer contains the 'name' attribute,
        #in some form. Pass that on to the core so that the name can be easily
        #pulled from the layers.
        hra_args['aoi_key'] = lower_attrib['name']        
        hra_args['aoi_tables'] = args['aoi_tables']

    #Since we need to use the h-s, stressor, and habitat dicts elsewhere, want
    #to use the pre-process module to unpack them and put them into the
    #hra_args dict. Then can modify that within the rest of the code.
    #We will also return a dictionary conatining directory locations for all
    #of the necessary shapefiles. This will be used instead of having users
    #re-enter the locations within args.
    unpack_over_dict(args['csv_uri'], hra_args)

    #Where we will store the burned individual habitat and stressor rasters.
    crit_dir = os.path.join(inter_dir, 'Criteria_Rasters')
    hab_dir = os.path.join(inter_dir, 'Habitat_Rasters')
    stress_dir = os.path.join(inter_dir, 'Stressor_Rasters')
    overlap_dir = os.path.join(inter_dir, 'Overlap_Rasters')

    for folder in (crit_dir, hab_dir, stress_dir, overlap_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)
    
    #Criteria, if they exist.
    if 'criteria_dir' in hra_args:
        c_shape_dict = hra_preprocessor.make_crit_shape_dict(hra_args['criteria_dir'])
        add_crit_rasters(crit_dir, c_shape_dict, hra_args['habitats'], 
                    hra_args['h_s_e'], hra_args['h_s_c'], args['grid_size'])

def add_crit_rasters(dir, crit_dict, habitats, h_s_e, h_s_c, grid_size):
    '''This will take in the dictionary of criteria shapefiles, rasterize them,
    and add the URI of that raster to the proper subdictionary within h/s/h-s.

    Input:
        dir- Directory into which the raserized criteria shapefiles should be
            placed.
        crit_dict- A multi-level dictionary of criteria shapefiles. The 
            outermost keys refer to the dictionary they belong with. The
            structure will be as follows:
            
            {'h':
                {'HabA':
                    {'CriteriaName: "Shapefile Datasource URI"...}, ...
                },
             'h_s_c':
                {('HabA', 'Stress1'):
                    {'CriteriaName: "Shapefile Datasource URI", ...}, ...
                },
             'h_s_e'
                {('HabA', 'Stress1'):
                    {'CriteriaName: "Shapefile Datasource URI", ...}, ...
                }
            }
        h_s_c- A multi-level structure which holds numerical criteria
            ratings, as well as weights and data qualities for criteria rasters.
            h-s will hold only criteria that apply to habitat and stressor 
            overlaps. The structure's outermost keys are tuples of 
            (Habitat, Stressor) names. The overall structure will be as 
            pictured:

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
            raster information. The outermost keys are habitat names.
        h_s_e- Similar to the h-s dictionary, a multi-level dictionary 
            containing all stressor-specific criteria ratings and 
            raster information. The outermost keys are tuples of 
            (Habitat, Stressor) names.
        grid_size- An int representing the desired pixel size for the criteria
            rasters. 
    Output:
        A set of rasterized criteria files. The criteria shapefiles will be
            burned based on their 'Rating' attribute. These will be placed in
            the 'dir' folder.
        
        An appended version of habitats, h_s_e, and h_s_c which will include
        entries for criteria rasters at 'Rating' in the appropriate dictionary.
        'Rating' will map to the URI of the corresponding criteria dataset.

    Returns nothing.
    '''

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
           
        h_s_c- A multi-level structure which will hold all criteria ratings, 
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
        h_s_e- Similar to the h-s dictionary, a multi-level dictionary 
            containing habitat stressor-specific criteria ratings and
            weights and data quality for the rasters.
    Returns nothing.
    '''
    dicts = hra_preprocessor.parse_hra_tables(csv_uri)

    for dict_name in dicts:
        args[dict_name] = dicts[dict_name]

