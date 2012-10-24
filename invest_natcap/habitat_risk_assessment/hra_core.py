'''This is #the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''
import math
import datetime
import logging
import os
import numpy as np

from osgeo import gdal, ogr
from invest_natcap import raster_utils

LOGGER = logging.getLogger('HRA_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''This provides the main functionaility of the hra_core program. This
    will call all parts necessary for calculation of final outputs.

    Inputs:
        args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be subfolders of this one.
        args['risk_eq']-  A string representing the equation to be used for
            risk calculation. We should check for possibilities, and send to a 
            different function when deciding R dependent on this.
        args['h-s']- A structure which holds all exposure and consequence
            ratings that are applicable to habitat and stressor overlaps. The
            outermost key is a tuple of two strings, the habitat and the
            stressor. This points to a dictionary whose keys include 'E' for
            exposure criteria, 'C' for consequence criteria, and 'DS', which
            will point directly to an open raster depicting the overlap between
            the habitat and the stressor. E/C will each point to a dictionary
            where the keys are strings names of the criteria, and the values
            are dictionaries. These dictionaries will have keys of 'Rating',
            'DQ' for data quality, and 'Weight', and will point to double
            values which correspond to those qualities of the criteria. The
            structure will be as pictured below:

            {(Habitat A, Stressor 1): 
                    {'E': 
                        {'Spatital Overlap': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'C': {C's Criteria Dictionaries},
                    'DS':  <Open A-1 Raster Dataset>
                    }
            }
        args['habitats']- A structure which will hold exposure and consequence
            criteria data for criteria which are habitat specific. The
            dictionary will not contain an open raster dataset, but will
            otherwise be the same structure as the args['h-s'] dictionary.
        args['stressors'] A structure which will hold exposure and consequence
            criteria data for criteria which are stressor specific. The
            dictionary will not contain an open raster dataset, but will
            otherwise be the same structure as the args['h-s'] dictionary.

    Outputs:
        --Intermediate--
            These should be the temp risk add files for the final output calcs.
        --Output--
            /output/maps/recov_potent_H[habitatname].tif- Raster layer depicting
                the recovery potential of each individual habitat. 
            /output/maps/cum_risk_H[habitatname]- Raster layer depicting the
                cumulative risk for all stressors in a cell for the given 
                habitat.
            /output/maps/ecosys_risk- Raster layer that depicts the sum of all 
                cumulative risk scores of all habitats for that cell.
   
            /output/html_plots/output.html- HTML page containing a matlab plot
                has cumulative exposure value for each habitat, as well as risk
                of each habitat plotted per stressor.
            /output/html_plots/plot_ecosys_risk.html- Plots the ecosystem risk
                value for each habitat.
            /output/html_plots/plot_risk.html- Risk value for each habitat
                plotted on a per-stressor graph.
            
    Returns nothing.
    '''

    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    make_risk_rasters(inter_dir, args['h-s'], args['habitats'], 
                args['stressors'], args['risk_eq'])


def make_risk_rasters(direct, h_s, habitats, stressors, risk_eq)
    '''This will re-burn the intermediate files of the H-S intersection with
    the risk value for that given layer. This will be calculated based on the
    three ratings dictionaries.

    Input:
        direct- The directory into which the completed raster files should be 
            placed.
        risk_eq- This is a string description of the desired equation to use
            when performing risk calculation.
        h_s- A multi-level structure which contains E/C ratings for each of
            the criteria applicable to the given H-S overlap. It also contains
            the open dataset that shows the raster overlap between the habitat
            and the stressor. The ratings structue is laid out as follows:

            {(Habitat A, Stressor 1): 
                    {'E': 
                        {'Spatital Overlap': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'C': {C's Criteria Dictionaries},
                    'DS':  <Open A-1 Raster Dataset>
                    }
            }
        habitats- A multi level dictionary with the same structure as h_s, but
            which only contaings ratings applicable to habitats.
        stressors- A multi-level dictionary with the same structure as h_s, but
            which only contains reatings applicable to stressors. 

    Output:
        Updated versions of the H-S datasets with the risk value burned to the
            overlap area of the given habitat and stressor.

    Returns nothing.
    '''
    #We will call one of the risk creation equations based on the string
    #passed in by 'risk_eq'. This will return a dataset, and we will then
    #write that out to a file within 'direct'

    #We are going to us the h_s dictionary as our way of running through all H-S
    #possibilities, and then run through individual criteria from H/S separately.
    for pair in h_s:
        
        #need to identify which is which to be used as a key to the other two
        #dictionaries
        h = pair[0]
        s = pair[1]

        #We will have calc_score_value take in three things- one
        #sub dictionary based on that pair from h_s, one sub dictionary from
        #habitats based on that particular habitat, and one sub dictionary
        #from stressors based on that particular stressor.
        E = calc_score_value(h_s[pair]['E'], habitats[h]['E'], stressors[s]['E'])

        C = calc_score_value(h_s[pair]['C'], habitats[h]['C'], stressors[s]['C'])

        #Need to remember that E should be applied to the decayed raster values,
        #then the decayed value per pixel can be used for the risk value. These
        #functions should return a modified dataset which will be written to a
        #new file.
        if risk_eq == 'Euclidean':
            ds = make_risk_ds_euc(h_s[pair]['DS'], E, C) 
        elif risk_eq == 'Multiplicative':
            ds = make_risk_ds_mult(h_s[pair]['DS'], E, C)


        #Now want to take this dataset and write it back to the raster file
        #conatining the H-S overlap.

def calc_score_value(h_s_sub, hab_sub, stress_sub):
    '''This will take in 3 sub-dictionaries and use the criteria that they
    contain to calculate an overall score based on the following equation.
    
    Value = SUM{i=1, N} (r{i}/(d{i}*w{i}) / SUM{i=1, N} 1/(d{i}*w{i})
        
        i = The current criteria that we are evaluating.
        r = Rating value for criteria i.
        N = Total number of criteria being evaluated for the combination of
            habitat and stressor.
        d = Data quality rating for criteria i.
        w = The importance weighting for that criteria relative to other
            criteria being evaluated.
    Inputs:
        Three sub-dictionaries, each of which will have the following form:
            
            {'Criteria Name 1' : {'Rating': 2.0, 'Weight': 1.0, 'DQ': 2.0},
             'Criteria Name 2' : { . . .}
            }
   
    Returns:
        A score value that represents E or C based on the above equation.
    '''
        
    sum_top = 0.0
    sum_bottom = 0.0

    for criteria in h_s_sub:
        
        r = h_s_sub[criteria]['Rating']
        d = h_s_sub[criteria]['DQ']
        w = h_s_sub[criteria]['Weight']

        sum_top += (r / d * w)
        sum_bottom += (1 / d * w)

    for criteria in hab_sub:

        r = hab_sub[criteria]['Rating']
        d = hab_sub[criteria]['DQ']
        w = hab_sub[criteria]['Weight']

        sum_top += (r / d * w)
        sum_bottom += (1 / d * w)

    for criteria in stress_sub:

        r = stress_sub[criteria]['Rating']
        d = stress_sub[criteria]['DQ']
        w = stress_sub[criteria]['Weight']

        sum_top += (r / d * w)
        sum_bottom += (1 / d * w)

    
    S = sum_top / sum_bottom
        
    return S
