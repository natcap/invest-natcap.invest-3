"""inVEST finfish aquaculture filehandler"""

import os

def execute(args):
    """This function will take care of preparing files passed into 
    the finfish aquaculture model. It will handle all files/inputs associated
    with biophysical calculations and manipulations. It will create objects
    to be passed to the aquaculture_core.py module. It may write log, 
    warning, or error messages to stdout.
    
    args: a python dictionary containing the following data:
    args['workspace_dir']- The directory in which to place all result files.
    args['ff_farm_loc']- URI that points to a shape file of fishery locations
    args['farm_ID']- column heading used to describe individual farms. Used to link
                            GIS location data to later inputs.
    args['g_param_a']- Growth parameter alpha, used in modeling fish growth, 
                            should be int or a float.
    args['g_param_b']- Growth parameter beta, used in modeling fish growth, 
                            should be int or a float.
    args['water_temp_tbl']- URI to a CSV table where daily water temperature
                            values are stored from one year
    args['farm_op_tbl']- URI to CSV table of static variables for calculations
    """ 
    
    #initialize new dictionary of purely biophysical/general arguments which will be
    #passed to the aquaculture core module. Then get desirable arguments that 
    #are being passed in, and load them into the biophysical dictionary.
    
    biophysical_args = {}
    
    
    
    