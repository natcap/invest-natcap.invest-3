"""Invest overlap analysis filehandler for data passed in through UI"""

import os
import csv
import glob

from osgeo import ogr

def execute(args):
    
    '''This function will take care of preparing files passed into 
    the overlap analysis model. It will handle all files/inputs associated
    with calculations and manipulations. It will create objects to be 
    passed to the overlap_analysis_core.py module. It may write log, 
    warning, or error messages to stdout.
    
    Input:
        args: A python dictionary created by the UI and passed to this method.
            It will contain the following data.
        args['workspace']- The directory in which to place all resulting files,
            will come in as a string.
        args['analysis_zone_type']- integer 0 or 1, where 0 represents Gridded 
            Seascape (GS), and 1 represents Management zones
        args['zone_layer_loc']- A URI pointing to a shapefile with the analysis
            zones on it.
        args['overlap_data_dir_loc']- URI pointing to a directory where multiple
            shapefiles are located. Each shapefile represents an activity of
            interest for the model.
        args['overlap_layer_tbl'] URI to a csv file that holds relational data
            and identifier data for all layers being passed in within the
            overlap analysis directory.
    
        --Optional--
        args['import_field']- string which corresponds to a field within the
            layers being passed in within overlap analysis directory. This is
            the intra-activity importance for each activity.
        args['hum_use_hubs_loc']- URI that points to a shapefile of major hubs
            of human activity. This would allow you to degrade the weight of
            activity zones as they get farther away from these locations.
        args['decay']- float between 0 and 1, representing the decay of interest
            in areas as you get farther away from human hubs.
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
    oa_args['zone_type'] = args['analysis_zone_type']
    oa_args['zone_layer_file'] = ogr.Open(args['zone_layer_loc'])
    
    #Glob.glob gets all of the files that fall into the form .shp, and makes them
    #into a list. Then, each item in the list is added to a dictionary as an open
    #file with the key of it's filename without the extension, and that whole
    #dictionary is made an argument of the oa_args dictionary
    file_names = glob.glob(args['overlap_data_dir_loc'] + os.sep + '/*.shp')
    
    file_dict = {}
    
    for file in file_names:
        
        name = os.path.splitext(file)[0]
        file_dict[name] = ogr.Open(file)
        
    oa_args['overlap_files'] = file_dict
    
    oa_args['over_layer_dict'] = format_over_table(args['overlap_layer_tbl'])
    
def format_over_table(over_tbl):
    
    over_layer_file = open(over_tbl)
    reader = csv.DictReader(over_layer_file)
    
    over_dict = {}
    
    
    
    return over_dict