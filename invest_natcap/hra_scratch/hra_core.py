'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''

from osgeo import gdal, ogr, osr
from invest_natcap import raster_utils
 
LOGGER = logging.getLogger('HRA_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
   %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''This provides the main calculation functionaility of the HRA model. This
    will call all parts necessary for calculation of final outputs.

    Inputs:
        args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        args['workspace_dir']- Directory in which all data resides. Output
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
        args['risk_eq']- String which identifies the equation to be used
            for calculating risk.  The core module should check for 
            possibilities, and send to a different function when deciding R 
            dependent on this.
        args['max_risk']- The highest possible risk value for any given pairing
            of habitat and stressor.
        args['aoi_tables']- May or may not exist within this model run, but if it
            does, the user desires to have the average risk values by 
            stressor/habitat using E/C axes for each feature in the AOI layer
            specified by 'aoi_tables'. If the risk_eq is 'Euclidea', this will
            create risk plots, otherwise it will just create the standard HTML
            table for either 'Euclidean' or 'Multiplicative.'
        args['aoi_key']- The form of the word 'Name' that the aoi layer uses
            for this particular model run. 
    
    Outputs:
        --Intermediate--
            These should be the temp risk and criteria files needed for the 
            final output calcs.
        --Output--
            /output/maps/recov_potent_H[habitatname].tif- Raster layer depicting
                the recovery potential of each individual habitat. 
            /output/maps/cum_risk_H[habitatname]- Raster layer depicting the
                cumulative risk for all stressors in a cell for the given 
                habitat.
            /output/maps/ecosys_risk- Raster layer that depicts the sum of all 
                cumulative risk scores of all habitats for that cell.
            /output/maps/[habitatname]_HIGH_RISK- A raster-shaped shapefile
                containing only the "high risk" areas of each habitat, defined
                as being above a certain risk threshold. 

    Returns nothing.
    '''


    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')
    
    crit_lists, denoms = pre_calc_denoms_and_criteria(inter_dir, args['h_s_c'],
                                    args['habitats'], args['h_s_e'])

def pre_calc_denoms_and_criteria(dir, h_s_c, hab, h_s_e):
    '''Want to return two dictionaries in the format of the following:
    (Note: the individual num raster comes from the crit_ratings
    subdictionary and should be pre-summed together to get the numerator
    for that particular raster. )

    Input:
        dir- Directory into which the rasterized criteria can be placed. This
            will need to have a subfolder added to it specifically to hold the
            rasterized criteria for now.
        h_s_c- A multi-level structure which holds all criteria ratings, 
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
                            {'DS': "CritName Raster URI", 'Weight': 1.0, 'DQ': 1.0}
                        },
                    'DS':  "A-1 Raster URI"
                    }
            }
        hab- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile URI provided by the user.
        h_s_e- Similar to the h_s_c dictionary, a multi-level
            dictionary containing habitat-stressor-specific criteria ratings and
            rasters. The outermost key is by (habitat, stressor) pair, but the
            criteria will be applied to the exposure portion of the risk calcs.
    
    Output:
        Creates a version of every criteria for every h-s paring that is
        burned with both a r/dq*w value for risk calculation, as well as a
        r/dq burned raster for recovery potential calculations.
    
    Returns:     
        crit_lists- A dictionary containing pre-burned criteria URI which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h_s_c': { (hab1, stressA): ["indiv num raster", "raster 1", ...],
                                   (hab1, stressB): ...
                                 },
                        'h':   { hab1: ["indiv num raster URI", "raster 1 URI", ...],
                                ...
                               },
                        'h_s_e': { (hab1, stressA): ["indiv num raster URI", ...]
                                 }
                     }
             'Recovery': { hab1: ["indiv num raster URI", ...],
                           hab2: ...
                         }
            }
        denoms- Dictionary containing the combined denominator for a given
            H-S overlap. Once all of the rasters are combined, each H-S raster
            can be divided by this. This dictionary will be the same structure
            as crit_lists, but the innermost values will be floats instead of
            lists.
    '''
