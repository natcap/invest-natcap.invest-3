'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''

import math
import datetime
import logging
import os

from osgeo import gdal, ogr
from invest_natcap import raster_utils

LOGGER = logging.getLogger('HRA_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''The overarching function that will call all parts of the HRA model.

    Inputs:
        args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be supfolders of this one.
        args['ratings']- A structure which holds all exposure and consequence
            rating for each combination of habitat and stressor. The inner
            structure is a dictionary whose key is a tuple which points to a
            tuple of lists which contain tuples.

            {(Habitat A, Stressor 1): ([(E1Rating, E1DataQuality, E1Weight), ...],
                                       [(C1Rating, C1DataQuality, C1Weight), ...],
                                       <Open A-1 Raster Dataset>)
                                       .
                                       .
                                       . }

    Outputs:
        --Intermediate--
            These should be the temp risk add files for the final output calcs.
        --Output--
            /output/maps/recov_potent.tif- Raster layer depicting the recovery
                potential of the predominant habitat for a given cell.
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
            
            /output/Parameters_[TIME].txt- Lists the parameters that the model
                was run with.
    Returns nothing.
    '''
    
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    #This will pre-calculate the risk value for each of the stressor layers
    #and re-burn the raster. Should be noted that the H-S overlap raster for
    #each pair already exists within the inter_dir file, but can be accessed
    #by using the ratings structure, since there is an open version of the
    #raster dataset there.
    burn_risk_values(args['ratings'])

def burn_risk_values(ratings):
    '''This will re-burn the intermediate files of the H-S intersection with
    the risk value for that given layer. This will be calculated based on the
    ratings withing the 'ratings' structure.

    Input:
        ratings- A multi-level structure which contains E/C ratings for each of
            the criteria applicable to the given H-S overlap. It also contains
            the open dataset that shows the raster overlap between the habitat
            and the stressor. The ratings structue is laid out as follows:

            {(Habitat A, Stressor 1): ([(E1Rating, E1DataQuality, E1Weight), ...],
                                       [(C1Rating, C1DataQuality, C1Weight), ...],
                                       <Open A-1 Raster Dataset>)
                                       .
                                       .
                                       . }
    '''
    
    #Want to run this for each of the H-S layers
    for pair in ratings:

        #one loop for calculating all ratings within E. E is the first element
        #in the H-S value tuple.
        E = calculate_exposure_value(pair[0])

        #second loop for calculating all ratings within C. C is the second
        #element in the H-S value tuple.
        C = calculate_consequence_value(pair[1])

        R = calculate_risk_value(E, C)

def calculate_exposure_value(iterable):
    '''This is the weighted average exposure value for all criteria for a given
    H-S combination as determined on a run by run basis. The equation is 
    as follows:

    E = SUM{i=1, N} (e{i}/(d{i}*w{i}) / SUM{i=1, N} 1/(d{i}*w{i})
        
        i = The current criteria that we are evaluating.
        e = Exposure value for criteria i.
        N = Total number of criteria being evaluated for the combination of
            habitat and stressor.
        d = Data quality rating for criteria i.
        w = The importance weighting for that criteria relative to other
            criteria being evaluated.
    '''
    sum_top, sum_bottom = 0.0

    for criteria in iterable:
        
        #For this imaginary data structure, imagine that each criteria maps
        #to a tuple of (value, data quality, weight)
        e_i, d_i, w_i = iterable[criteria]
        
        sum_top += e_i / (d_i * w_i)
        sum_bottom += 1 / (d_i * w_i)

    E = sum_top / sum_bottom

    return E

def calculate_consequence_value(iterable):
    '''Structure of this equation will be the same as the exposure values.
    However, the iterable passed in should contain criteria specific to the
    consequences of that particular H-S interraction.'''

    sum_top, sum_bottom = 0.0

    for criteria in iterable:
        
        #For this imaginary data structure, imagine that each criteria maps
        #to a tuple of (value, data quality, weight)
        c_i, d_i, w_i = iterable[criteria]
        
        sum_top += c_i / (d_i * w_i)
        sum_bottom += 1 / (d_i * w_i)

    C = sum_top / sum_bottom

    return C

#For this, I am assuming that something is running the risk values as a loop,
#and passing in the E and C values that it wants us to use.
def calculate_risk_value(exposure, consequence):
    '''Takes an individual exposure value and consequence value (we assume they are
    from the same H-S space, and finds their euclidean distance from the origin of
    the exposure-consequence space.

        Input:
            exposure- Avg. of exposure values within a H-S space.
            consequence- Avg. of consequence values within a H-S space.

        Returns:
            R - The risk value for the given E and C.
    '''

    R = math.sqrt((exposure - 1)**2 + (consequence - 1)**2)

    return R

