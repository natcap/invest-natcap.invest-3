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
    args['farm_ID']- column heading used to describe individual farms. Used to link
                            GIS location data to later inputs.
    args['g_param_a']- Growth parameter alpha, used in modeling fish growth, 
                            should be int or a float.
    args['g_param_b']- Growth parameter beta, used in modeling fish growth, 
                            should be int or a float.
    args['water_temp_rdr']- An iterable containing dictionaries which link the column
                        headings (date, day/month, and individual farm #'s) of the water
                        temperature table to their value (either specific day or the
                        temperature itself at a farm on that day.
                        
                        Format: {'date':'1', 'Day/Month':'1-Jan', '1':'8.447', ...}
                                {'date':'2', 'Day/Month':'2-Jan', '1':'8.406', ...}
                                .                        .                    .
                                .                        .                    .
                                .                        .                    .
    args['farm_op_dict']- Dictionary which links a specific farm ID # to another
                        dictionary containing operating parameters mapped to their value
                        for that particular farm
                        
                        Format: {'1': '{'Wt of Fish': '0.06', 'Tar Weight': '5.4', ...}',
                                '2': '{'Wt of Fish': '0.06', 'Tar Weight': '5.4', ...}',
                                .                        .                    .
                                .                        .                    .
                                .                        .                    .       }
    '''
    
    workspace_dir = args[workspace_dir]
    output_dir = workspace_dir + os.sep + 'Output' + os.sep
    
    