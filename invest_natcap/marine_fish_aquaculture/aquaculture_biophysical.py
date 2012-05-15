"""inVEST finfish aquaculture filehandler"""

import os
import csv

from osgeo import gdal
from osgeo import ogr

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
    
    workspace = args['workspace_dir']
    output_dir = workspace + os.sep + 'Output'
    
    if not (os.path.exists(output_dir)):
        os.mkdir(output_dir)
        
    biophysical_args['workspace_dir'] = args['workspace_dir']
    biophysical_args['ff_farm_loc'] = ogr.Open(args['ff_farm_loc']);
    biophysical_args['farm_ID'] = args['farms_ID']
    biophysical_args['g_param_a'] = args['g_param_a']
    biophysical_args['g_param_b'] = args['g_param_b']
    
    #Need to create a dictReader for the CSV file, but then can leave it,
    #since there are no arbitrary pairings. Should be noted that this is passed
    #as an iterable, since there is no single key.
    water_temp_file = open(args['water_temp_tbl'])
    reader = csv.DictReader(water_temp_file)
    
    biophysical_args['water_temp_rdr'] = reader
    
    #Now create a dictionary for the operations table, then set up the values so 
    #that they are iterable in a way that makes sense
    
    #TODO: CHECK TO SEE IF WE NEED ALL COLUMNS
    new_dict_temp = {}
    
    farm_op_file = open(args['farm_op_tbl'])
    reader = csv.DictReader(farm_op_file)
    
    for row in reader:
        
        sub_dict = {}
        
        for key in row:
            if (key != row['farm_ID']):
                sub_dict[key] = row[key]
    
        new_dict_op[row['farm_ID']] = sub_dict
    
    biophysical_args['farm_op_dict'] = new_dict_temp
    