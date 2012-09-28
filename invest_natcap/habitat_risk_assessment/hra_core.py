import math

'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''

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
            /intermediate/S[stressorname]_buff.tif- A version of the named
                stressor file with the user speficied buffer applied.
            /intermediate/H[habitatname]_S[stressorname].tif- A raster file of
                the overlap between the named habitat and the named stressor.
        --Output--
            /output/maps/recov_potent.tif- Raster layer depicting the recovery
                potential of the predominant habitat for a given cell.
            /output/maps/cum_risk_H[habitatname]- Raster layer depicting the
                cumulative risk for all stressors in a cell for the given 
                habitat.
            /output/maps/ecosys_risk- Raster layer that depicts the sum of all 
                cumulative risk scores of all habitats for that cell.
    
    Returns nothing.
    '''
    



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

