"""inVEST finfish aquaculture filehandler for biophysical and valuation data"""

import os
import csv
import logging

from osgeo import gdal
from osgeo import ogr

from invest_natcap.finfish_aquaculture import finfish_aquaculture_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('finfish_aquaculture_test')

def execute(args):
    """This function will take care of preparing files passed into 
    the finfish aquaculture model. It will handle all files/inputs associated
    with biophysical and valuation calculations and manipulations. It will create objects
    to be passed to the aquaculture_core.py module. It may write log, 
    warning, or error messages to stdout.
    
    --Biophysical Args--
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
    
    --Valuation Args--
    args['do_valuation']- Boolean that indicates whether or not valuation should be
                    performed on the aquaculture model
    args['p_per_kg']: Market price per kilogram of processed fish
    args['frac_p']: Fraction of market price that accounts for costs rather than
                    profit
    args['discount']: Daily market discount rate
    
    returns nothing
    """ 
    
    #initialize new dictionary of purely biophysical/general arguments which will be
    #passed to the aquaculture core module. Then get desirable arguments that 
    #are being passed in, and load them into the biophysical dictionary.
    
    ff_aqua_args = {}
    
    workspace = args['workspace_dir']
    output_dir = workspace + os.sep + 'Output'
        
    if not (os.path.exists(output_dir)):
        os.makedirs(output_dir)
        
    ff_aqua_args['workspace_dir'] = args['workspace_dir']
    ff_aqua_args['ff_farm_file'] = ogr.Open(args['ff_farm_loc'])
    ff_aqua_args['farm_ID'] = args['farm_ID']
    ff_aqua_args['g_param_a'] = args['g_param_a']
    ff_aqua_args['g_param_b'] = args['g_param_b']
    
    #Both CSVs are being pulled in, but need to do some maintenance to remove undesirable
    #information before they can be passed into core

    format_ops_table(args['farm_op_tbl'], "Farm #:", ff_aqua_args)
    format_temp_table(args['water_temp_tbl'], ff_aqua_args)
    
    ff_aqua_args['do_valuation'] = args['do_valuation']

    #Valuation arguments
    key = 'do_valuation'
    
    if ff_aqua_args['do_valuation'] == True:

        ff_aqua_args['p_per_kg'] = args['p_per_kg']
        ff_aqua_args['frac_p'] = args['frac_p']
        ff_aqua_args['discount'] = args['discount']

    #Fire up the biophysical function in finfish_aquaculture_core with the 
    #gathered arguments
    finfish_aquaculture_core.execute(ff_aqua_args)

def format_ops_table(op_path, farm_ID, ff_aqua_args):
    '''Takes in the path to the operating parameters table as well as the
    keyword to look for to identify the farm number to go with the parameters,
    and outputs a 2D dictionary that contains all parameters by farm and
    description. The outer key is farm number, and the inner key is a string
    description of the parameter.'''
    
    #NOTE: Have to do some explicit calls to strings here. This is BAD. Don't do it if
    #you don't have to. THESE EXPLICIT STRINGS COME FROM THE "Farm Operations" 
    #table.

    new_dict_op = {}
    csv_file = open(op_path)
    
    #this will be separate arguments that are passed along straight into 
    #biophysical_args
    general_ops = {}
    line = None
    
    dialect = csv.Sniffer().sniff(csv_file.read())
    csv_file.seek(0)
    delim = dialect.delimiter
    #LOGGER.debug("delim: " + delim)
    
    end_line = dialect.lineterminator
    #LOGGER.debug("end: " + end_line)
    
    while True:
        line = csv_file.readline().rstrip(end_line)

        if farm_ID in line:
            break
    
        split_line = line.split(delim)
        if 'Fraction of fish remaining after processing' in split_line[0]:
            general_ops['frac_post_process'] = float(split_line[1][:-1])/100
    
        if 'Natural mortality rate on the farm (daily)' in split_line[0]:
            general_ops['mort_rate_daily'] = split_line[1]
    
        if 'Duration of simulation (years)' in split_line[0]:
            general_ops['duration'] = split_line[1]
    
    #this is explicitly telling it the fields that I want to get data for
    #want to remove the 'Total Value' field, since there is not data inside 
    #there, then tell the dictreader to set up a reader with dictionaries of 
    #only those fields, where the overarching dictionary uses the Farm ID as the key for each of the sub dictionaries
    fieldnames =  line.split(delim)
    
    reader = csv.DictReader(csv_file, fieldnames=fieldnames, dialect = dialect)

    for row in reader:
        
        sub_dict = {}
        
        for key in row:
            if (key != farm_ID):
                sub_dict[key] = row[key]
    
        del sub_dict['Total mass in farm (kg)']
        del sub_dict['Total dressed wt.']
        del sub_dict['Total value']
        
        if row[farm_ID]!= '':
            new_dict_op[row[farm_ID]] = sub_dict
    
    ff_aqua_args['farm_op_dict'] = new_dict_op
    #LOGGER.debug(ff_aqua_args['farm_op_dict'])

    #add the gen args in
    for key in general_ops.keys():
        ff_aqua_args[key] = general_ops[key]    
    
def format_temp_table(temp_path, ff_aqua_args):
    
    #EXPLICIT STRINGS FROM "Temp_Daily"
    
    water_temp_file = open(temp_path)
   
    new_dict_temp = {}
    line = None
    
    dialect = csv.Sniffer().sniff(water_temp_file.read())
    water_temp_file.seek(0)
    delim = dialect.delimiter
    LOGGER.debug("delim: " + delim)
    
    end_line = dialect.lineterminator
    #LOGGER.debug("end: " + end_line)
    
    #This is what I will use at the key for the key->dictionary pairing w/in the
    #outer dictionary
    day_marker = 'Day #'
    
    while True:
        line = water_temp_file.readline().rstrip(end_line)
        if day_marker in line:
            break
    
    #this is explicitly telling it the fields that I want to get data for, and am removing
    #the Day/Month Field Since it's unnecessary

    fieldnames =  line.split(delim)
    #fieldnames.remove('Day/Month')
    
    reader = csv.DictReader(water_temp_file, fieldnames, dialect = dialect)
    
    #LOGGER.debug(fieldnames)
    
    for row in reader:
       
        sub_dict = {}
        
        for key in row:
            if (key != day_marker and key != ''):
                sub_dict[key] = row[key]
        
        del sub_dict['Day/Month']
        
        #Subtract 1 here so that the day in the temp table allows for % 365
        new_dict_temp[str(int(row[day_marker]) - 1)] = sub_dict
    #LOGGER.debug(new_dict_temp)
        
    ff_aqua_args['water_temp_dict'] = new_dict_temp
    