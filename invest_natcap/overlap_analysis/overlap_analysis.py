"""Invest overlap analysis filehandler for data passed in through UI"""

import os
import csv

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