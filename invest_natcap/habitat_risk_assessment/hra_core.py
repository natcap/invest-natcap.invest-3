'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''

def calculate_exposure_value(SOME VARS):
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
