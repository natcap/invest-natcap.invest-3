'''Implementation of the aquaculture calculations, and subsequent outputs. This will
pull from data passed in by aquaculture_biophysical and aquaculture_valuation'''

import os
import math

from osgeo import ogr
from osgeo import gdal

def biophysical(args):
    ''''Runs the biophysical and valuation parts of the finfish aquaculture model. 
    This will output:
    1. a shape file showing farm locations w/ addition of # of harvest cycles, total
        processed weight at that farm, and if valuation is true, total discounted net 
        revenue at each farm location.
    2. Three HTML tables summarizing all model I/O- summary of user-provided data,
        summary of each harvest cycle, and summary of the outputs/farm
    3. A .txt file that is named according to the date and time the model is run, which
        lists the values used during that run
    
    Data in args should include the following:
    --Biophysical Arguments--
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
    
    --Valuation arguments--
    args['do_valuation']- boolean indicating whether or not to run the valuation process
    args['p_per_kg']: Market price per kilogram of processed fish
    args['frac_p']: Fraction of market price that accounts for costs rather than profit
    args['discount']: Daily market discount rate
    '''
    
    output_dir = args['workspace_dir'] + os.sep + 'Output'
    
    #using a tuple to get data back from function, then update the shape files 
    #to reflect these new attributes
    cycle_history = calc_farm_cycles(args['g_param_a'], 
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
        
        accessor = args['farm_ID']
        feature_ID = feature.items()[accessor]
        #casting to string because it's coming out of a CSV
        num_cycles = len(cycle_history[feature_ID])
        feature.SetField('Tot_Cycles', num_cycles)
        
        layer.SetFeature(feature)
        
    #Now want to add the total processed weight of each farm as a second feature on the
    #outgoing shapefile- abstracting the calculation of this to a separate function,
    #but it will return a dictionary with a int->float mapping for 
    #farm_ID->processed weight
    proc_weight = calc_proc_weight(args['farm_op_dict'], args['frac_post_process'], 
                                   args['mort_rate_daily'], cycle_history)
    
    #Now, add the total processed weight as a shapefile feature
    hrv_field = ogr.FieldDefn('Hrvwght_kg', ogr.OFTReal)
    layer.CreateField(hrv_field)
    
    for feature in layer:
        
        feature_ID = feature.items()[args['farm_ID']]
        feature.SetField('Hrvwght_kg', proc_weight[feature_ID])
        
        layer.SetFeature(feature)
        
    print type(args['p_per_kg'])
       
    '''This will complete the valuation portion of the finfish aquaculture model, dependent on
    whether or not valuation is desired.'''
    if (bool(args['do_valuation']) == True):
        print "hELLO"

def calc_farm_cycles(a, b, water_temp_dict, farm_op_dict, dur):
    
    #One output, which will be a dictionary pointing to a list of tuples,
    #each of which contains 3 things- 
    #                (day of outplanting, day of harvest, harvest weight)
    #The dictionary will have a key of farm number, and a value of the tuple list
    
    cycle_history ={}
    tau = 0.8
    dur = int(dur)
     
    for f in range (1, len(farm_op_dict)+1):
        
        #casting f to string because farm_op_dict came from biophysical with
        #keys as strings, and then casting result back to int
        start_day = int(farm_op_dict[str(f)]['start day for growing'])
        fallow_per = int(farm_op_dict[str(f)]['Length of Fallowing period'])
        start_weight = float(farm_op_dict[str(f)]['weight of fish at start (kg)'])
        tar_weight = float(farm_op_dict[str(f)]['target weight of fish at harvest (kg)'])
        
        fallow_days_left = start_day
        farm_history = []
        fish_weight = 0
        outplant_date = None
    
        #Need to cycle through fish growth and fallowing. In order to avoid ever having
        # a day = 0 when accessing a table, I start at zero, add 1 to anything where days
        #are recorded, then do accesses as zero % 365, and add 1.
        for day in range (0, (365*dur)):
            
            #print type(water_temp_dict[str(day % 365)][str(f)])
            
            if fallow_days_left > 0:
                fallow_days_left -= 1
            
            elif fish_weight >= tar_weight:
                record = (outplant_date, day + 1, fish_weight)
                farm_history.append(record)
                fallow_days_left = fallow_per
                fish_weight = 0
            
            else:
                if fish_weight == 0:
                    fish_weight = start_weight
                    outplant_date = day + 1
                else:
             
                    #Grow 'dem fishies!
                    fish_weight = (a * (fish_weight ** b) * \
                                   float(water_temp_dict[str(day % 365 + 1)][str(f)]) \
                                   * tau) + fish_weight
            
        cycle_history[f] = farm_history
        
    #Now, want to make a tuple from the three dictionaries, and send them back 
    #to the main function
    
    return cycle_history

def calc_proc_weight(farm_op_dict, frac, mort, cycle_history):
    #This will yield one output- a dictionary which will hold a mapping from every farm
    # (as identified by farm_ID) to the total processed weight of each farm
    
    curr_cycle_totals = {}
        
    for f in range (1, len(farm_op_dict)+1):
        
        #pre-load farm specific vars, have to cast some because they come out of
        # a CSV all as strings
        curr_cycle_totals[f] = 0
        f_num_fish = int(farm_op_dict[str(f)]['number of fish in farm'])
        curr_hrv_day = int(farm_op_dict[str(f)]['start day for growing'])
        cycles_comp = len(cycle_history[f])
        farm_history = cycle_history[f]
        mort = float(mort)
        
        #We are starting this range at 0, and going to one less than the number of
        #cycles, since the list of cycles from the cycle calcs will start at index 0
        for c in range (0, cycles_comp):
            
            #this will get the tuple referring to the current cycle
            #the information will be inside the tuple as:
            # (day of outplanting, day of harvest, harvest weight)
            current_cycle_info = farm_history[c]
            outplant_date, harvest_date, harvest_weight = current_cycle_info
         
            #Now do the computation for each cycle individually, then add it to the total
            #within the dictionary
            cycle_length = harvest_date - outplant_date
            e_exponent =  -mort * cycle_length
            curr_cy_twp = harvest_weight * frac * f_num_fish * math.exp(e_exponent)
            
        curr_cycle_totals[f] += curr_cy_twp
            
    return curr_cycle_totals
