"""Invest overlap analysis filehandler for data passed in through UI"""

import os
import csv
import glob
import logging
import re

from osgeo import ogr
from invest_natcap.overlap_analysis import overlap_analysis_core

LOGGER = logging.getLogger('overlap_analysis')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''This function will take care of preparing files passed into 
    the overlap analysis model. It will handle all files/inputs associated
    with calculations and manipulations. It will create objects to be 
    passed to the overlap_analysis_core.py module. It may write log, 
    warning, or error messages to stdout.
    
    Input:
        args: A python dictionary created by the UI and passed to this method.
            It will contain the following data.
        args['workspace_dir']- The directory in which to place all resulting files,
            will come in as a string.
        args['zone_layer_loc']- A URI pointing to a shapefile with the analysis
            zones on it.
        args['do_grid']- Boolean for whether or not gridding of the passed in
            shapefile is desired on the file specified by 'zone_layer_loc'
        args['grid_size']- May or may not be in the args directory. Will only
            exist if 'do_grid' is true. This is an int specifying how large the
            gridded squares over the shapefile should be.
        args['overlap_data_dir_loc']- URI pointing to a directory where multiple
            shapefiles are located. Each shapefile represents an activity of
            interest for the model.
        args['do-inter']-Boolean that indicates whether or not inter-activity
            weighting is desired. This will decide if the overlap table will be
            created.
        args['do_intra']- Boolean which indicates whether or not intra-activity
            weighting is desired. This will will pull attributes from shapefiles
            passed in in 'zone_layer_loc'
            
            
        --Optional--
        args['overlap_layer_tbl'] URI to a CSV file that holds relational data
            and identifier data for all layers being passed in within the
            overlap analysis directory.    
        args['intra_name']- string which corresponds to a field within the
            layers being passed in within overlap analysis directory. This is
            the intra-activity importance for each activity.
        args['hum_use_hubs_loc']- URI that points to a shapefile of major hubs
            of human activity. This would allow you to degrade the weight of
            activity zones as they get farther away from these locations.
        args['decay']- float between 0 and 1, representing the decay of interest
            in areas as you get farther away from human hubs.
            
    Output:
        oa_args- The dictionary of all arguments that are needed by the
            overlap_analysis_core.py class. This is the dictionary that will be
            directly passed to that class in order to do processing for the 
            final output of the model.

    Returns nothing.
    '''
    
    global oa_args
    
    oa_args = {}
    
    workspace = args['workspace_dir']
    output_dir = workspace + os.sep + 'Output'
    inter_dir = workspace + os.sep + 'Intermediate'
        
    if not (os.path.exists(output_dir)):
        os.makedirs(output_dir)
        
    if not (os.path.exists(inter_dir)):
        os.makedirs(inter_dir)
        
    oa_args['workspace_dir'] = args['workspace_dir']
    
    #LOGGER.debug(args['zone_layer_loc'])
    
    #We are passing in the AOi shapefile, as well as the dimension that we want the
    #raster pixels to be. 
    oa_args['zone_layer_file'] = ogr.Open(args['zone_layer_loc'])
    oa_args['grid_size'] = args['grid_size']
    
    #Still need to pass in do_grid because we need to know if we're treating management
    #zones or exact gridded squares....don't we?
    oa_args['do_grid'] = args['do_grid']
    
    
    #Glob.glob gets all of the files that fall into the form .shp, and makes them
    #into a list. Then, each item in the list is added to a dictionary as an open
    #file with the key of it's filename without the extension, and that whole
    #dictionary is made an argument of the oa_args dictionary
    file_names = glob.glob(args['overlap_data_dir_loc'] + os.sep + '*.shp')
    
    file_dict = {}
    
    for file in file_names:
        
        #The return of os.path.split is a tuple where everything after the final slash
        #is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes before
        #the file extension, and the second is the extension itself 
        name = os.path.splitext(os.path.split(file)[1])[0]
        file_dict[name] = ogr.Open(file)
        
    oa_args['overlap_files'] = file_dict
    
    #No need to format the table if no inter-activity weighting is desired.
    oa_args['do_inter'] = args['do_inter']
    
    if args['do_inter']:
        oa_args['over_layer_dict'] = format_over_table(args['overlap_layer_tbl'])
        
    oa_args['do_intra'] = args['do_intra']
    
    if args['do_intra']:
        oa_args['intra_name'] = args['intra_name']
    
    #We don't actually get these yet, so commenting them out
    #oa_args['hubs_loc'] = ogr.Open(args['hum_use_hubs_loc'])
    #oa_args['decay'] = args['decay']
    
    overlap_analysis_core.execute(oa_args)
    
def format_over_table(over_tbl):
    '''This CSV file contains a string which can be used to uniquely identify a .shp
    file to which the values in that string's row will correspond. This string,
    therefore, should be used as the key for the ovlap_analysis dictionary, so that we
    can get all corresponding values for a shapefile at once by knowing its name.
    
        Input:
            over_tbl- A CSV that contains a list of each interest shapefile, and any 
            the optional buffers and weights of the layers.
                
        Returns:
            over_dict- The analysis layer dictionary that maps the unique name of each
                layer to the optional parameter of inter-activity weight. For each entry,
		the key will be the string name of the layer that it represents, and the 
		value will be the inter-activity weight for that layer.                
    '''
    
    over_layer_file = open(over_tbl)
    reader = csv.DictReader(over_layer_file)
    
    over_dict = {}
    
    #USING EXPLICIT STRING CALLS to the layers table (these should not be unique to the
    #type of table, but rather, are items that ALL layers tables should contain). I am
    #casting both of the optional values to floats, since both will be used for later
    #calculations.
    for row in reader:
        
        #Setting the default values for inter-activity weight and buffer, since they
        #are not actually required to be filled in.
        
        #NEED TO FIGURE OUT IF THESE SHOULD BE 0 OR 1
        inter_act = 1
        buffer = 0
        
        for key in row:
            if 'Inter-Activity' in key and row[key] != '':
                inter_act = float(row[key])
                
        name = row['LIST OF HUMAN USES']
        
        over_dict[name] = inter_act
    
    return over_dict
