import numpy as np
import imp, sys, os
from osgeo import ogr
from osgeo.gdalconst import *
from dbfpy import dbf
from osgeo import gdal
import math
import datetime
from datetime import date
from datetime import datetime
import time

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
        
    plant_total = []
    layer = args['timber_layer_copy']
    mdr = float(args['mdr'])
    plant_prod_loc = args['plant_prod_loc']
    plant_dict = args['plant_prod']
    timber_shape_loc = args['timber_shape_loc']
    output_dir = args['output_dir']
    
    mdr_perc = 1+(mdr/100.00)
    
    for fieldname in ('TNPV', 'TBiomass', 'TVolume'):
        field_def = ogr.FieldDefn(fieldname, ogr.OFTReal)
        layer.CreateField(field_def)
    
    for i in range(plant_dict.recordCount):
        
        freq_Harv  = plant_dict[i]['Freq_harv']
        num_Years  = float(plant_dict[i]['T'])
        harv_Mass  = plant_dict[i]['Harv_mass']
        harv_Cost  = plant_dict[i]['Harv_cost']
        price      = plant_dict[i]['Price']
        maint_Cost = plant_dict[i]['Maint_cost']
        BCEF       = plant_dict[i]['BCEF']
        parcl_Area = plant_dict[i]['Parcl_area']
        perc_Harv  = plant_dict[i]['Perc_harv']
        immed_Harv = plant_dict[i]['Immed_harv']
           
        net_present_value = 0
        summation_one = 0.0
        summation_two = 0.0
        lower_limit = 0
        upper_limit = 0
        lower_limit2 = 0
        upper_limit2 = num_Years - 1
        subtractor = 0.0
        yr_per_freq = num_Years/freq_Harv
        
        #Calculate the harvest value for parcel x
        harvest_value = harvestValue(perc_Harv, price, harv_Mass, harv_Cost)
        
        #Frequency Harvest cannot be greater than the time period
        if freq_Harv > num_Years :
           freq_Harv = num_Years 
        
        #Check to see if immediate harvest will occur
        if immed_Harv == 'N':
            upper_limit = int(math.floor(yr_per_freq))
            lower_limit = 1
            subtractor = 1.0
            summation_one = summationOne(lower_limit, upper_limit, harvest_value, mdr_perc, freq_Harv, subtractor)
            summation_two = summationTwo(lower_limit2, upper_limit2, maint_Cost, mdr_perc)            
        else:
            upper_limit = int((math.ceil(yr_per_freq)-1.0))
            lower_limit = 0
            summation_one = summationOne(lower_limit, upper_limit, harvest_value, mdr_perc, freq_Harv, subtractor)
            summation_two = summationTwo(lower_limit2, upper_limit2, maint_Cost, mdr_perc)
        
        #Calculate Biomass
        biomass = getBiomass(parcl_Area, perc_Harv, harv_Mass, num_Years, freq_Harv)
        
        volume = getVolume(biomass, BCEF)
        net_present_value = (summation_one - summation_two)
        total_npv = net_present_value * parcl_Area

        feature = layer.GetFeature(i)
        
        for field, value in (('TNPV', total_npv), ('TBiomass', biomass), ('TVolume', volume)):
            index = feature.GetFieldIndex(field)
            feature.SetField(index, value)       

#        plant_total.append(total_npv)
        #save the field modifications to the layer.
        layer.SetFeature(feature)
        
        feature.Destroy()
        
    #Create the output file with the attributes used    
    textFileOut(timber_shape_loc, output_dir, mdr, plant_prod_loc)

#    return plant_total

#Calculates harvest value for parcel
def harvestValue(perc_Harv, price, harv_Mass, harv_Cost):
    harvest_value = (perc_Harv/100.00)*((price*harv_Mass)-harv_Cost)
    return harvest_value

#Calculates the first summation for the net present value of a parcel
def summationOne(lower, upper, harvest_value, mdr_perc, freq_Harv, subtractor):
    summation = 0.0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (harvest_value/(mdr_perc**((freq_Harv*num)-subtractor)))
                        
    return summation

#Calculates the second summation for the net present value of a parcel
def summationTwo(lower, upper, maint_Cost, mdr_perc):
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

        