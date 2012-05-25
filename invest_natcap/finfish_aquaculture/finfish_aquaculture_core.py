'''Implementation of the aquaculture calculations, and subsequent outputs. This will
pull from data passed in by aquaculture_biophysical and aquaculture_valuation'''

import os

from osgeo import ogr
from osgeo import gdal

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
                        remove undesirable parts
    args['mort_rate_daily']- mortality rate among fish  in a year, divided by 365
    args['duration']- duration of the simulation, in years
    '''
    
    output_dir = args['workspace_dir'] + os.sep + 'Output'
    
    #using a tuple to get data back from function, then update the shape files 
    #to reflect these new attributes
    cycles_completed, cycle_lengths, weights = calc_farm_cycles(args['g_param_a'], 
                                          args['g_param_b'], args['water_temp_dict'], 
                                          args['farm_op_dict'], args['duration'])
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    out_path = output_dir + os.sep + 'Finfish_Harvest.shp'
    curr_shp_file = args['ff_farm_file']
    
    #If already exists, remove so we can re-create
    if (os.path.isfile(out_path)):
        os.remove(out_path)

    sf_copy = driver.CopyDataSource(curr_shp_file, out_path)
    layer = sf_copy.GetLayer()
    
    #This adds the number of cycles completed by each farm to their shapefile feature
    cycle_field = ogr.FieldDefn('Tot_Cycles', ogr.OFTReal)
    layer.CreateField(cycle_field)
    
    for feature in layer:
        
        feature_ID = feature.items()[args['farm_ID']]
        #casting to string because it's coming out of a CSV
        feature.SetField('Tot_Cycles', cycles_completed[str(feature_ID)])
        
        layer.SetFeature(feature)
        
    #Now want to add the total processed weight of each farm as a second feature on the
    #outgoing shapefile- abstracting the calculation of this to a separate function,
    #but it will return a dictionary with a int->float mapping for 
    #farm_ID->processed weight
    proc_weight = calc_proc_weight(args['farm_op_dict'], args['frac_post_process'], 
                                   args['mort_rate_daily'], cycles_completed, cycle_lengths)
    
    #Now, add the total processed weight as a shapefile feature
    hrv_field = ogr.FieldDefn('Hrvwght_kg', ogr.OFTReal)
    layer.CreateField(hrv_field)
    
    for feature in layer:
        
        feature_ID = feature.items()[args['farm_ID']]
        feature.SetField('Hrvwght_kg', proc_weight[feature_ID])
        
        layer.SetFeature(feature)
        
    #Want to create a raster file of the same size/shape as the shapefile you used
    #as input, then use the harvest weight as the info to burn into raster pixels
    r_driver = gdal.GetDriverByName('GTIFF')
    r_out_path = output_dir + os.sep + "hrvwght_kg"
    
    
    gdal.RasterizeLayer()

def calc_farm_cycles(a, b, water_temp_dict, farm_op_dict, dur):
    
    #Two outputs: 
    #1. Want to create a dictionary to hold all of a farm's data from the period of time that
    #the model is simulating. Similar to the two CSV files, it will be a key->dictionary
    #pairing within the outer dictionary, where the keys are farm numbers.
    #2. A dictionary that holds the number of cycles that each farm completed, with a
    #key->value as int->float
    
    #tau is explicitly defined in the model documentation
    fish_weights = {}
    tau = 0.8
    cycles_completed = {}
    cycle_lengths= {}
     
    for f in range (1, len(farm_op_dict)+1):
        #pre-load vars for fallowing period and pre-fish
        #print farm_op_dict
        
        #casting f to string because farm_op_dict came from biophysical with
        #keys as strings, and then casting result back to int
        start_day = int(farm_op_dict[str(f)]['start day for growing'])
        fallow_per = int(farm_op_dict[str(f)]['Length of Fallowing period'])
        spec_farm_weights = {}
        cycle_lengths[f] = {}
        curr_cycle = 0
        dur = int(dur)
        
        fall_count = fallow_per
        
        #this just establishes zero weights for when the fish aren't there during the
        #initial pre-fishception period
        for i in range(1, start_day):
            spec_farm_weights[i] = 0
            
        #Now, for the remaining time, need to cycle through fish growth and fallowing
        for i in range (start_day, (365*dur)):
            
            #this is the day that the fish are placed in the pens, should catch the 
            #fisheries where there is no fallowing period. One you put down today as 
            #fishception, then want to reset fallow count so you don't get caught in 
            #this statement again
            if fall_count == 0:
                spec_farm_weights[i] = \
                    farm_op_dict[str(f)]['weight of fish at start (kg)']
                fall_count = fallow_per
                curr_cycle = curr_cycle + 1
                cycle_lengths[f][curr_cycle] = 1
            
            #Marks the completion of a growth cycle
            elif spec_farm_weights[i-1] >= 5.4:
                spec_farm_weights[i] = 0
                fall_count -= 1
                
                x = 1
                if cycles_completed.has_key(f):
                    x = cycles_completed[f] + 1
                    cycles_completed[f] = x   
                    
            elif spec_farm_weights[i-1] == 0:
                spec_farm_weights[i] = 0
                fall_count -= 1
                
            #Grow 'dem fishies!
            else:
                g_weight = (a * (spec_farm_weights[i-1] ** b) * 
                    water_temp_dict[(i % 365)][f] * tau) + spec_farm_weights[i-1]
                
                spec_farm_weights[i] = g_weight
                cycle_lengths[f][curr_cycle] = cycle_lengths[f][curr_cycle] + 1        
        
        fish_weights[f] = spec_farm_weights
        
    #Now, want to make a tuple from the three dictionaries, and send them back 
    #to the main function
    return (cycles_completed, cycle_lengths, fish_weights)

def calc_proc_weight(farm_op_dict, frac, mort, cycles_comp, cycle_lengths):
    #This will yield one output- a dictionary which will hold a mapping from every farm
    # (as identified by farm_ID) to the total processed weight of each farm
    
    curr_cycle_totals = {}
        
    for f in range (1, len(farm_op_dict)+1):
        
        #pre-load farm specific vars
        curr_cycle_totals[f] = 0
        f_hv_wt = farm_op_dict[f]['target weight of fish at harvest (kg)']
        f_num_fish = farm_op_dict[f]['number of fish in farm']
        
        for c in range (1, cycles_comp[f]):
        
            #get cycle-lengths for this specific cycle
            c_len = cycle_lengths[f[c]]
            
            #Now do the computation for each cycle individually, then add it to the total
            #within the dictionary
            e_exponent =  -mort * cycle_lengths[f][c]
            curr_cy_twp = f_hv_wt * frac * f_num_fish * exp(e_exponent)
            
            curr_cycle_totals[f] = curr_cycle_totals[f] + curr_cy_twp
            
    return curr_cycle_totals
        
        
        