'''Implementation of the aquaculture calculations, and subsequent outputs. This will
pull from data passed in by aquaculture_biophysical and aquaculture_valuation'''

import os

def biophysical(args):
    ''''Runs the biophysical part of the finfish aquaculture model. This will output:
    1. a shape file showing farm locations w/ addition of # of harvest cycles, total
    processed weight at that farm, and possibly the total discounted net revenue at each
    farm location.
    2. Raster file of total harvested weight for each farm for the total number of years
    the model was run (in kg)
    3. Raster of the total net present value of harvested weight/ farm for the total
    number of years the model was run (thousands of $)
    4. Three HTML tables summarizing all model I/O- summary of user-provided data,
    summary of each harvest cycle, and summary of the outputs/farm
    5. A .txt file that is named according to the date and time the model is run, which
    lists the values used during that run
    
    Data in args should include the following:
    args: a python dictionary containing the following data:
    args['workspace_dir']- The directory in which to place all result files.
    args['ff_farm_file']- An open shape file containing the locations of individual
                        fisheries
    args['g_param_a']- Growth parameter alpha, used in modeling fish growth, 
                            should be int or a float.
    args['g_param_b']- Growth parameter beta, used in modeling fish growth, 
                            should be int or a float.
    args['water_temp_dict']- A dictionary which links a specific date to the farm numbers,
                        and their temperature values on that day. (Note: in this case, the
                        outer keys 1 and 2 are calendar days out of 365, starting 
                        with January 1, and the inner 1, 2, and 3 are farm numbers.)
                           
                        Format: {'1': '{'1': '8.447, '2': '8.447', '3':'8.947', ...}' ,
                                 '2': '{'1': '8.406, '2': '8.406', '3':'8.906', ...}' ,
                                .                        .                    .
                                .                        .                    .
                                .                        .                    .       }
    args['farm_op_dict']- Dictionary which links a specific farm ID # to another
                        dictionary containing operating parameters mapped to their value
                        for that particular farm (Note: in this case, the 1 and 2
                        are farm ID's, not dates out of 365.)
                        
                        Format: {'1': '{'Wt of Fish': '0.06', 'Tar Weight': '5.4', ...}',
                                '2': '{'Wt of Fish': '0.06', 'Tar Weight': '5.4', ...}',
                                .                        .                    .
                                .                        .                    .
                                .                        .                    .       }
    args['frac_post_process']- the fraction of edible fish left after processing is done to
                        remove underirable parts
    args['mort_rate_daily']- mortality rate among fish  in a year, divided by 365
    args['duration']- duration of the simulation, in years
    '''
    
    output_dir = workspace_dir + os.sep + 'Output' + os.sep

    #using a tuple to get data back from function
    weights_and_cycles = calc_farm_cycles(args['g_param_a'], args['g_param_b'], 
                                          args['water_temp_dict'], args['farm_op_dict'],
                                          args['duration'])
    

def calc_farm_cycles(a, b, water_temp_dict, farm_op_dict, dur):
    
    #Two outputs: 
    #1. Want to create a dictionary to hold all of a farm's data from the period of time that
    #the model is simulating. Similar to the two CSV files, it will be a key->dictionary
    #pairing within the outer dictionary, where the keys are farm numbers.
    #2. A dictionary that holds the number of cycles that each farm completed, with a
    #key->value as int->float
    
    fish_weights = {}
    
    for i in range (0, (365*dur)):
        
        #pre-load the t=0 weights into the dictionary, have to go through all the farms,
        #find out how long until outplanting, and go through 0 to that number, and mark
        #fish weight as 
        f_num = len(farm_op_dict.keys())
        
        for f in range(0, f_num):
            
            r
            
            
            
            
            