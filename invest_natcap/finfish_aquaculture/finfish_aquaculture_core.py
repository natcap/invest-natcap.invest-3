'''Implementation of the aquaculture calculations, and subsequent outputs. This will
pull from data passed in by aquaculture_biophysical and aquaculture_valuation'''

import os
import math
import time
import datetime

from osgeo import ogr
from osgeo import gdal

def execute(args):
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
    cycle_history = calc_farm_cycles(args, args['g_param_a'], 
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
    sum_proc_weight, proc_weight = calc_proc_weight(args['farm_op_dict'], args['frac_post_process'], 
                                   args['mort_rate_daily'], cycle_history)
    
    #have to start at the beginning of the layer to access the attributes
    layer.ResetReading()
    
    #Now, add the total processed weight as a shapefile feature
    hrv_field = ogr.FieldDefn('Hrvwght_kg', ogr.OFTReal)
    layer.CreateField(hrv_field)
        
    for feature in layer:

        accessor = args['farm_ID']
        feature_ID = feature.items()[accessor]
        feature.SetField('Hrvwght_kg', int(sum_proc_weight[feature_ID]))
        
        layer.SetFeature(feature)

    #This will complete the valuation portion of the finfish aquaculture 
    #model, dependent on whether or not valuation is desired.
    if (bool(args['do_valuation']) == True):
        value_history, farms_npv = valuation(args['p_per_kg'], args['frac_p'], args['discount'],
                proc_weight, cycle_history)
   
        #And add it into the shape file
        layer.ResetReading()
        
        hrv_field = ogr.FieldDefn('NVP_USD_1k', ogr.OFTReal)
        layer.CreateField(hrv_field)
        
        for feature in layer:
    
            accessor = args['farm_ID']
            feature_ID = feature.items()[accessor]
            feature.SetField('NVP_USD_1k', int(farms_npv[feature_ID]))
            
            layer.SetFeature(feature)
    else:
        value_history = None
        farms_npv = None
        
    #Now, want to build the HTML table of everything we have calculated to this point
    create_HTML_table(output_dir, args['farm_ID'], args['farm_op_dict'], cycle_history, sum_proc_weight, proc_weight, args['do_valuation'],
                      farms_npv, value_history)
    
    #Last output is a text file of the parameters that the model was run with
    create_param_log(args)
   
def calc_farm_cycles(args, a, b, water_temp_dict, farm_op_dict, dur):
    
    output_dir = args['workspace_dir'] + os.sep + 'Output'
    
    filename = output_dir + os.sep + "Temporary Calcs.txt"
    file = open(filename, "w")
    
    
    #One output, which will be a dictionary pointing to a list of tuples,
    #each of which contains 3 things- 
    #                (day of outplanting, day of harvest, harvest weight)
    #The dictionary will have a key of farm number, and a value of the tuple list
    
    cycle_history ={}
    tau = 0.08
    dur = float(dur)

    for f in range (1, len(farm_op_dict)+1):
        
        #casting f to string because farm_op_dict came from biophysical with
        #keys as strings, and then casting result back to int
        #Are multiplying by 1000, because a and b are in grams, so need to do the whole
        #equation in grams
        start_day = int(farm_op_dict[str(f)]['start day for growing']) - 1
        fallow_per = int(farm_op_dict[str(f)]['Length of Fallowing period'])
        start_weight = 1000 * float(farm_op_dict[str(f)]['weight of fish at start (kg)'])
        tar_weight = 1000 * float(farm_op_dict[str(f)]['target weight of fish at harvest (kg)'])
        
        fallow_days_left = start_day
        farm_history = []
        fish_weight = 0
        outplant_date = None
    
        #Have changed the water temp table to be accessed by keys 0 to 364, so now can just
        #grab straight from the table without having to deal with change in day
        
        #However, it should be kept in mind that when doing calculations for a given day,
        #you are using YESTRDAY'S temperatures and weights to get the value for today.
        for day in range (0, int((365*dur))):
            
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
                    file.write("Fish Weight for day " + str(day) + 
                               ": " + str(fish_weight) + "\n")
                else:
             
                    #Grow 'dem fishies!
                    exponent = math.exp(float(water_temp_dict[(day-1) % 365][str(f)]) * tau)
                    file.write("temp effect is: " + str(exponent) + "\n")
                    fish_weight = (a * (fish_weight ** b) * exponent) + \
                                    fish_weight
                    
                    
                    file.write("Fish Weight for day " + str(day) + 
                               ": " + str(fish_weight) + "\n") 

        
        cycle_history[f] = farm_history
    
    return cycle_history

def calc_proc_weight(farm_op_dict, frac, mort, cycle_history):

    '''   
    Input: 
        cycle_hisory: Farm->List of Type (day of outplanting, 
                                      day of harvest, harvest weight (grams))                            
    Output:
        curr_cycle_totals_: dictionary which will hold a mapping from every farm
                (as identified by farm_ID) to the total processed weight of each farm
        indiv_tpw_totals: dictionary which will hold a farm->list mapping, where the list 
                holds the individual tpw for all cycles that the farm completed
    '''
        
    curr_cycle_totals = {}
    indiv_tpw_totals= {}
        
    for f in range (1, len(farm_op_dict)+1):
        
        #pre-load farm specific vars, have to cast some because they come out of
        # a CSV all as strings
        curr_cycle_totals[f] = 0
        f_num_fish = int(farm_op_dict[str(f)]['number of fish in farm'])
        curr_hrv_day = int(farm_op_dict[str(f)]['start day for growing'])
        cycles_comp = len(cycle_history[f])
        farm_history = cycle_history[f]
        mort = float(mort)
        indiv_tpw_totals[f] = []
        
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
            #Note that we divide by 1000 to make sure the output in in kg
            cycle_length = harvest_date - outplant_date
            e_exponent =  -mort * cycle_length
            curr_cy_tpw = (harvest_weight / 1000) * frac * f_num_fish * \
                            math.exp(e_exponent)
            
            indiv_tpw_totals[f].append(curr_cy_tpw)
            curr_cycle_totals[f] += curr_cy_tpw
            
    return (curr_cycle_totals, indiv_tpw_totals)

def valuation (price_per_kg, frac_mrkt_price, discount, proc_weight, cycle_history):
    
    '''This performs the valuation calculations, and returns a dictionary with a
    farm-> float mapping, where each float is the net processed value of the fish
    processed on that farm, in $1000s of dollars.
    
    Inputs:
        cycle_hisory: Farm->List of Type (day of outplanting, 
                                          day of harvest, harvest weight (grams))
        proc_weight: Farm->List of TPW for each cycle (kilograms)
        
    Outputs:
        val_history: dictionary which will hold a farm->list mapping, where the 
                list holds tuples containing (Net Revenue, Net Present Value) for
                each cycle completed by that farm
        valuations: dictionary with a farm-> float mapping, where each float is the 
                net processed value of the fish processed on that farm
        '''
    val_history = {}
    valuations = {}
    
    for f in range (1, len(cycle_history) + 1):
        
        val_history[f] = []
        valuations[f] = 0
        
        #running from 0 to 1 less than the number of cycles that farm completed,
        #since the list that each farm ID is mapped to starts at index 0
        for c in range (0, len(cycle_history[f])):
            
            tpw = proc_weight[f][c]
            #the 2 refers to the placement of day of harvest in the tuple for each cycle
            t = cycle_history[f][c][1]
            
            net_rev = tpw * (price_per_kg *(1 - frac_mrkt_price))
            npv = net_rev * (1 / (1 + discount) ** t)
            
            val_history[f].append((net_rev, npv))
            
            #divide by 1000, because the number we want to return is in thousands of dollars
            valuations[f] += npv /1000
    
    return val_history, valuations

def create_HTML_table (output_dir, FID, farm_op_dict, cycle_history, sum_proc_weight, 
                       proc_weight, do_valuation, farms_npv, value_history):
    '''Inputs:
        cycle_history: dictionary mapping farm ID->list of tuples, each of which 
                contains 3 things- (day of outplanting, day of harvest, harvest weight of 
                a single fish in grams)
        sum_proc_weight: dictionary which holds a mapping from farm ID->total processed 
                weight of each farm 
        proc_weight: dictionary which holds a farm->list mapping, where the list holds 
                the individual tpw for all cycles that the farm completed
        do_valuation: boolean variable that says whether or not valuation is desired
        farms_npv: dictionary with a farm-> float mapping, where each float is the 
                net processed value of the fish processed on that farm, in $1000s 
                of dollars.
        value_history: dictionary which holds a farm->list mapping, where the 
                list holds tuples containing (Net Revenue, Net Present Value) for
                each cycle completed by that farm
    
       Output:
        HTML file: contains 3 tables that summarize inputs and outputs for the duration
            of the model. If valuation is not desired, then those cells designated for
            valuation will be highlighted in red.
            - Input Table: Farm Operations provided data, including Farm ID #, Cycle
                    Number, weight of fish at start, weight of fish at harvest, number 
                    of fish in farm, start day for growing, and length of fallowing period
            - Output Table 1: Farm Harvesting data, including a summary table for each 
                    harvest cycle of each farm. Will show Farm ID, cycle number, days
                    since outplanting date, harvested weight, net revenue, outplant day,
                    and year.
            - Output Table 2: Model outputs for each farm, including Farm ID, net present
                    value, number of completed harvest cycles, and total volume harvested.
    '''
    filename = output_dir + os.sep + "HarvestResults_[" + \
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "].html"
    file = open(filename, "w")
    
    file.write("<html>")
    file.write("<title>" + "Marine InVEST" + "</title>")
    file.write("<CENTER><H1>" + "Aquaculture Model (Finfish Harvest)" + "</H1></CENTER>")
    file.write("<br>")
    file.write("This page contains results from running the Marine InVEST Finfish \
    Aquaculture model." + "<p>" + "Cells highlighted in yellow are values that were \
    also populated in the attribute table of the netpens feature class.  Cells \
    highlighted in red should be interpreted as null values since valuation was not \
    selected.")
    file.write("<br><br>")
    file.write("<HR>")
    
    #Here starts the information being put into the first table
    file.write("<H2>" + "Farm Operations (input)" + "</H2>")
    file.write("<table border=\"1\", cellpadding=\"5\">")
    
    #We are getting the keywords for the farm options off of an arbitrary element in
    #in farm_op_dict. However, we had to create a copy in order to simulate a peek method
    #and not remove that item from the original dictionary
    cp_dict = farm_op_dict.copy()
    str_headers = cp_dict.popitem()[1].keys()

    inner_strings = []
    
    for id in farm_op_dict.keys():
        single_str = "<td>" + id + "</td>"
        
        for info in str_headers:
            
            single_str += "<td>" + farm_op_dict[id][str(info)] + "</td>"
            
        inner_strings.append(single_str)
    
    str_headers.insert(0, "Farm #:")
    
    for element in str_headers:
        file.write("<td><b>")
        file.write(element)
        file.write("</b></td>")
    file.write("</tr>")
    
    for element in inner_strings:
        file.write("<tr>")
        file.write(element)
        file.write("</tr>")
            
    file.write("</table>")
    
    #Here starts the second table
    #For ease, am preloading a list with the headers for this table, since they aren't
    #necessarily already input
    str_headers = ['Farm ID Number', 'Cycle Number', 'Days Since Outplanting Date', 
                   'Harvested Weight', 'Net Revenue', 'Net Present Value', 'Outplant Day',
                   'Outplant Year']
    
    inner_strings = []
    
    for id in cycle_history.keys():
        
        #Explicitly getting the number of fish that the farm has, because we will need
        #it later when we write to the table
        num_fishies = int(farm_op_dict[str(id)]['number of fish in farm'])
        
        vars = []
        for cycle in range(0, len(cycle_history[id])):
        
            #pre-load all values
            cycle_num = cycle + 1
            
            curr_cycle = cycle_history[id][cycle]
            outplant_date, harvest_date, harvest_weight = curr_cycle
            
            #harvest weight is the weight in grams on an individual fish at harvest. 
            #Need to multiply by the number of fish, then divide by 1000 to get kg
            #of fish total
            total_harvest_weight = round(num_fishies*harvest_weight/1000)
            
            out_day = outplant_date % 365
            out_year = outplant_date // 365 + 1
            
            str_line = ""
            #Need to make it so if we don't have valuation, those cells just show up red
            if (do_valuation == True):
                indiv_rev, indiv_npv = value_history[id][cycle]
    
                #revenue and net present value should be in thousands of dollars
                vars = [id, cycle_num, harvest_date, total_harvest_weight, 
                        round(indiv_rev / 1000), round(indiv_npv/1000), out_day, out_year]
            else:
                
                indiv_rev = ""
                indiv_npv = ""
                
                vars = [id, cycle_num, harvest_date, total_harvest_weight, 
                        indiv_rev, indiv_npv, out_day, out_year]
            
            for element in vars:
                if element == indiv_rev or element == indiv_npv:
                    str_line += "<td bgcolor= \"#FF0000\">"
                else :
                    str_line += "<td>"
                str_line += str(element)
                str_line += "</td>"
        
            inner_strings.append(str_line)
    
    #Write the second table itself
    file.write("<br><HR><H2>Farm Harvesting (output)</H2>")
    file.write("<table border=\"1\", cellpadding=\"5\">")
    file.write("<tr>")
    for element in str_headers:
        file.write("<td><b>")
        file.write(element)
        file.write("</b></td>")
    file.write("</tr>")
    
    for element in inner_strings:
        file.write("<tr>")
        file.write(element)
        file.write("</tr>")
    file.write("</table>")
    
    #Here starts the creation of the third table. Like the last one, I am pre-loading
    #the headers, since they aren't actually input anywhere
    str_headers = ['Farm ID Number', 'Net Present Value', 
                   'Number of Completed Harvest Cycles', 'Total Volume Harvested']
    
    inner_strings = []

    for id in cycle_history.keys():
        
        #pre-load variables
        if (do_valuation == True): 
            npv = round(farms_npv[id])
        else:
            npv = ""
            
        num_cy_complete = len(cycle_history[id])
        total_harvested = round(sum_proc_weight[id])
        
        vars = [npv, num_cy_complete, total_harvested]
        
        str_line = ""
        str_line += "<td>" + str(id) + "</td>"
        
        for element in vars:
            if element == npv:
                str_line += "<td BGCOLOR=\"#ff0000\">"
            else:
                str_line += "<td BGCOLOR=\"#ffff00\">"
            str_line += str(element)
            str_line += "</td>"
                
   
        inner_strings.append(str_line)

        
    #Write the third table itself
    file.write("<br><HR><H2>Farm Result Totals (output)</H2>")
    file.write("<table border=\"1\", cellpadding=\"5\">")
    file.write("<tr>")
    for element in str_headers:
        file.write("<td><b>")
        file.write(element)
        file.write("</b></td>")
    file.write("</tr>")
    
    for element in inner_strings:

        file.write("<tr>")
        file.write(element)
        file.write("</tr>")
    file.write("</table>")
    
    #end page
    file.write("</html>")
    file.close()   

def create_param_log(args):
    
    '''Input: A dictionary of all input parameters for this run of the finfish
            aquaculture model.
            
        Output: A .txt file that contains the run parameters for this run of the
            model. Named by date and time.
    '''
    output_dir = args['workspace_dir'] + os.sep + 'Output'
    
    filename = output_dir + os.sep + "Parameter_Log_[" + \
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "].txt"
    file = open(filename, "w")
    
    str_list = []
    
    str_list.append("BIOPHYSICAL ARGUMENTS \n")
    str_list.append("Workspace: " + args['workspace_dir'])
    str_list.append("Output Directory: " +  output_dir)
    str_list.append("Farm Identifier: " + args['farm_ID'])
    str_list.append("Growth Parameter A: " + str(args['g_param_a']))
    str_list.append("Growth Parameter B: " + str(args['g_param_b']))
    str_list.append("Mortality Rate (Daily): " + str(args['mort_rate_daily']))
    str_list.append("Duration of Model: " + str(args['duration']))
    
    str_list.append("\nVALUATION ARGUMENTS \n")
    str_list.append("Valuation: " + str(args['do_valuation']))
    if (args['do_valuation'] == True):
        str_list.append("Price Per Kilogram of Fish: " + str(args['p_per_kg']))
        str_list.append("Fraction of Price Attributable to Costs: " + 
                        str(args['frac_p']))
        str_list.append("Daily Market Discount Rate: " + str(args['discount']))
    
    for element in str_list:
        file.write(element)
        file.write("\n")
    
    file.close()