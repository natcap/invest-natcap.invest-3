"""Invest overlap analysis filehandler for data passed in through UI"""

import os
import csv
import glob

from osgeo import ogr
from invest_naptcap.overlap_analysis import overlap_analysis_core

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
        args['overlap_layer_tbl'] URI to a CSV file that holds relational data
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
    oa_args['zone_type'] = args['analysis_zone_type']
    
    #This allows for options gridding of the vectors being passed in. The return
    #from core will be a URI to a shapefile with multiple polygons of user specified 
    #size that are in an area stretching over the extent of the polygons
    if (args['do_grid']):
        base_map = overlap_analysis_core.gridder(inter_dir, args['zone_layer_loc'], 
                                    args['grid_size'])
        oa_args['zone_layer_file'] = ogr.Open(base_map)
    else:    
        oa_args['zone_layer_file'] = ogr.Open(args['zone_layer_loc'])
    
    #Still need to pass in do_grid because we need to know if we're treating management
    #zones or exact gridded squares....don't we?
    oa_args['do_grid'] = args['do_grid']
    
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
    
    oa_args['import_field'] = args['import_field']
    oa_args['hubs_loc'] = ogr.Open(args['hum_use_hubs_loc'])
    oa_args['decay'] = args['decay']
    
    overlap_analysis_core.execute(oa_args)
    
def format_over_table(over_tbl):
    ''' While the file actually contains names for the files, we are going to use the ID
    itself as an identifier for the dictionary, then just parse through the names
    of the files to find an int in order to match them up. Since each of the files
    is required to contain an ID at the end, this will allow us to bypass the problem
    of names not being the same (i.e- Fish_CommGF vs CommGF_Fish).
    
        Input:
            over_tbl- A CSV that contains a list of each interest shapefile, as well
                as the unique ID that identifies it, and the optional buffers and
                weights of the layers.
                
        Returns:
            over_dict- The analysis layer dictionary that maps the unique ID of each
                layer to the optional parameters of inter-activity weight and buffer.
                Each ID number will map to a list containing the two values, with the
                form being as follows ({ID: [inter-activity weight, buffer], ...}):
                
                {1: [2.0, 0], 2: [1.50, 0], 3: [1.50, 0], ...}
    '''
    over_layer_file = open(over_tbl)
    reader = csv.DictReader(over_layer_file)
    
    over_dict = {}
    
    #USING EXPLICIT STRING CALLS to the layers table (these should not be unique to the
    #type of table, but rather, are items that ALL layers tables should contain). I am
    #casting both of the optional values to floats, since both will be used for later
    #calculations. Casting ID number to int for ease of access later.
    for row in reader:
        
        #Setting the default values for inter-activity weight and buffer, since they
        #are not actually required to be filled in.
        
        #NEED TO FIGURE OUT IF THESE SHOULD BE 0 OR 1
        inter_act = 1
        buffer = 0
        
        for key in row:
            if 'Inter-Activity' in key:
                inter_act = float(row[key])
            if 'Buffer' in key:
                buffer = float(row[key])
                
        id_num = int(row['ID'])
        
        over_dict[id_num] = [inter_act, buffer]
    
    return over_dict