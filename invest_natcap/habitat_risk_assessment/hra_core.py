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
'''
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
