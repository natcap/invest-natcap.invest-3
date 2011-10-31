import numpy as np
import imp, sys, os
from osgeo import ogr
import math
import datetime
from datetime import date
from datetime import datetime

def execute(args):
    """Executes the basic timber management model that calculates the Total Net Present Value and maps
        it to an outputted shapefile.
    
        args - is a dictionary with at least the following entries:
        
        args['timber_shape_loc']    - the location of the input shapefile
        args['output_dir']          - the workspace where the outputs will be saved.
        args['timber_layer_copy']   - is the layer which holds the polygon features from the copied shapefile.
        args['timber_shp_copy']     - is a copy of the original OGR shapefile and will be used as the output with
                                        with the new fields attached to the features.
        args['mdr']                 - the market discount rate.
        args['plant_prod']          - the dbf file which has the attribute values of each timber parcel.
        args['plant_prod_loc']      - the location of the production table file.
        
        returns nothing"""

    #Set constant variables from arguments
    layer = args['timber_layer_copy']
    mdr = float(args['mdr'])
    plant_prod_loc = args['plant_prod_loc']
    plant_dict = args['plant_prod']
    timber_shape_loc = args['timber_shape_loc']
    output_dir = args['output_dir']
    #Set constant variables
    mdr_perc = 1+(mdr/100.00)
    lower_limit2 = 0
    
    #Create three new fields on the shapefile's polygon layer
    for fieldname in ('TNPV', 'TBiomass', 'TVolume'):
        field_def = ogr.FieldDefn(fieldname, ogr.OFTReal)
        layer.CreateField(field_def)
    #Loop through each feature (polygon) in the shapefile layer
    for feat in layer:
        #Get the correct polygon attributes to be calculated by matching the feature's polygons Parcl_ID
        #with the attribute tables polygons Parcel_ID
        plant_row = getAttributeRow(feat, plant_dict)
        
        freq_Harv  = plant_row['Freq_harv']
        num_Years  = float(plant_row['T'])
        harv_Mass  = plant_row['Harv_mass']
        harv_Cost  = plant_row['Harv_cost']
        price      = plant_row['Price']
        maint_Cost = plant_row['Maint_cost']
        BCEF       = plant_row['BCEF']
        parcl_Area = plant_row['Parcl_area']
        perc_Harv  = plant_row['Perc_harv']
        immed_Harv = plant_row['Immed_harv']

        upper_limit2 = int(num_Years - 1)
        subtractor = 0.0
        yr_per_freq = num_Years/freq_Harv
        
        #Calculate the harvest value for parcel x
        harvest_value = harvestValue(perc_Harv, price, harv_Mass, harv_Cost)
        
        #Frequency Harvest cannot be greater than the time period
        if freq_Harv > num_Years :
           freq_Harv = num_Years 
        
        #Check to see if immediate harvest will occur
        if immed_Harv.upper() == 'N' or 'NO':
            upper_limit = int(math.floor(yr_per_freq))
            lower_limit = 1
            subtractor = 1.0
            summation_one = npvSummationOne(lower_limit, upper_limit, harvest_value, mdr_perc, freq_Harv, subtractor)
            summation_two = npvSummationTwo(lower_limit2, upper_limit2, maint_Cost, mdr_perc)            
        elif immed_Harv.upper() == 'Y' or 'YES':
            upper_limit = int((math.ceil(yr_per_freq)-1.0))
            lower_limit = 0
            summation_one = npvSummationOne(lower_limit, upper_limit, harvest_value, mdr_perc, freq_Harv, subtractor)
            summation_two = npvSummationTwo(lower_limit2, upper_limit2, maint_Cost, mdr_perc)
        
        #Calculate Biomass
        biomass = getBiomass(parcl_Area, perc_Harv, harv_Mass, num_Years, freq_Harv)
        #Calculate Volume
        volume = getVolume(biomass, BCEF)
        
        net_present_value = (summation_one - summation_two)        
        total_npv = net_present_value * parcl_Area

        #For each new field set the corresponding value to the specific polygon
        for field, value in (('TNPV', total_npv), ('TBiomass', biomass), ('TVolume', volume)):
            index = feat.GetFieldIndex(field)
            feat.SetField(index, value)       

        #save the field modifications to the layer.
        layer.SetFeature(feat)        
        feat.Destroy()
        
    #Create the output file with the attributes used    
    textFileOut(timber_shape_loc, output_dir, mdr, plant_prod_loc)

def getAttributeRow(feat, plant_dict):
    parcl_index = feat.GetFieldIndex('Parcl_ID')
    parcl_id = feat.GetField(parcl_index)
    table_index = 0
    table_id = plant_dict[table_index]['Parcel_ID']
        
    #Make sure referring to the same polygon by comparing Parcl_ID's
    while parcl_id != table_id:
        table_index += 1
        table_id = plant_dict[table_index]['Parcel_ID']
                    
    return plant_dict[table_index]

#Calculates harvest value for parcel
def harvestValue(perc_Harv, price, harv_Mass, harv_Cost):
    harvest_value = (perc_Harv/100.00)*((price*harv_Mass)-harv_Cost)
    return harvest_value

#Calculates the first summation for the net present value of a parcel
def npvSummationOne(lower, upper, harvest_value, mdr_perc, freq_Harv, subtractor):
    summation = 0.0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (harvest_value/(mdr_perc**((freq_Harv*num)-subtractor)))
                        
    return summation

#Calculates the second summation for the net present value of a parcel
def npvSummationTwo(lower, upper, maint_Cost, mdr_perc):
    summation = 0.0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (maint_Cost/(mdr_perc**num))
            
    return summation

#Calculates the Biomass for a parcel
def getBiomass(parcl_Area, perc_Harv, harv_Mass, T, freq_Harv):
    TBiomass = parcl_Area * (perc_Harv/100.00) * harv_Mass * math.ceil(T/freq_Harv)
    return TBiomass

#Calculates the Volume for a parcel
def getVolume(biomass, BCEF):
    TVolume = biomass * (1.0/BCEF)
    return TVolume

#Creates a text file which saves the attributes to the Output folder
def textFileOut(timber_shape, output_dir, mdr, plant_prod):    
    now = datetime.now()
    date = now.strftime('%Y-%m-%d-%H-%M')
    
    text_array =["TIMBER MODEL PARAMETERS",
                 "_______________________\n",
                 "Date and Time: " + date,
                 "Output Folder: " + output_dir,
                 "Managed timber forest parcels: " + timber_shape,
                 "Production table: " + plant_prod,
                 "Market discount rate: " + str(mdr),
                 "Script Location: " + os.path.dirname(sys.argv[0])+"\\"+os.path.basename(sys.argv[0])]
      
    filename = output_dir+os.sep+"Timber_"+date+".txt"
    file = open(filename, 'w')
    
    for value in text_array:
        file.write(value + '\n')
        file.write('\n')
    
    file.close()


    #Run through each timber parcel in the table, calculating it's TNPV
#    for i in range(plant_dict.recordCount):
#        
#        freq_Harv  = plant_dict[i]['Freq_harv']
#        num_Years  = float(plant_dict[i]['T'])
#        harv_Mass  = plant_dict[i]['Harv_mass']
#        harv_Cost  = plant_dict[i]['Harv_cost']
#        price      = plant_dict[i]['Price']
#        maint_Cost = plant_dict[i]['Maint_cost']
#        BCEF       = plant_dict[i]['BCEF']
#        parcl_Area = plant_dict[i]['Parcl_area']
#        perc_Harv  = plant_dict[i]['Perc_harv']
#        immed_Harv = plant_dict[i]['Immed_harv']      

#        feature = layer.GetFeature(parcl_index)