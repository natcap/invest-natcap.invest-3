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
        
        args['timber_layer_copy']   - is the layer which holds the polygon features from the copied shapefile.
        args['mdr']                 - the market discount rate.
        args['attr_table']          - the dbf file which has the polygon attribute values of each timber parcel.
        
        returns nothing"""

    #Set constant variables from arguments
    layer = args['timber_layer_copy']
    mdr = float(args['mdr'])
    attr_table = args['attr_table']
    #Set constant variables
    mdr_perc = 1 + (mdr / 100.00)
    sumTwo_lowerLimit = 0

    #Create three new fields on the shapefile's polygon layer
    for fieldname in ('TNPV', 'TBiomass', 'TVolume'):
        field_def = ogr.FieldDefn(fieldname, ogr.OFTReal)
        layer.CreateField(field_def)
        
    #Example of how to build lookup table so we don't have to loop through 
    #table linearly
    parcelIdLookup = {} # this
    for i in range(attr_table.recordCount): #this
        parcelIdLookup[attr_table[i]['Parcel_ID']] = attr_table[i] #and this
        
    #Loop through each feature (polygon) in the shapefile layer
    for feat in layer:
        #Get the correct polygon attributes to be calculated by matching the feature's polygons Parcl_ID
        #with the attribute tables polygons Parcel_ID
#        attr_row = getAttributeRow(feat, attr_table)
    
        parcl_index = feat.GetFieldIndex('Parcl_ID')
        parcl_id = feat.GetField(parcl_index)
        attr_row = parcelIdLookup[parcl_id]

        freq_Harv = attr_row['Freq_harv']
        num_Years = float(attr_row['T'])
        harv_Mass = attr_row['Harv_mass']
        harv_Cost = attr_row['Harv_cost']
        price = attr_row['Price']
        maint_Cost = attr_row['Maint_cost']
        BCEF = attr_row['BCEF']
        parcl_Area = attr_row['Parcl_area']
        perc_Harv = attr_row['Perc_harv']
        immed_Harv = attr_row['Immed_harv']

        sumTwo_upperLimit = int(num_Years - 1)
        #Variable used in npv summation one equation as a distinguisher between two immed_harv possibilities
        subtractor = 0.0
        yr_per_freq = num_Years / freq_Harv

        #Calculate the harvest value for parcel x
        harvest_value = (perc_Harv / 100.00) * ((price * harv_Mass) - harv_Cost)

        #Check to see if immediate harvest will occur
        if immed_Harv.upper() == 'N' or immed_Harv.upper() == 'NO':
            sumOne_upperLimit = int(math.floor(yr_per_freq))
            sumOne_lowerLimit = 1
            subtractor = 1.0
            summation_one = npvSummationOne(sumOne_lowerLimit, sumOne_upperLimit, harvest_value, mdr_perc, freq_Harv, subtractor)
            summation_two = npvSummationTwo(sumTwo_lowerLimit, sumTwo_upperLimit, maint_Cost, mdr_perc)
        elif immed_Harv.upper() == 'Y' or immed_Harv.upper() == 'YES':
            sumOne_upperLimit = int((math.ceil(yr_per_freq) - 1.0))
            sumOne_lowerLimit = 0
            summation_one = npvSummationOne(sumOne_lowerLimit, sumOne_upperLimit, harvest_value, mdr_perc, freq_Harv, subtractor)
            summation_two = npvSummationTwo(sumTwo_lowerLimit, sumTwo_upperLimit, maint_Cost, mdr_perc)

        #Calculate Biomass
        biomass = parcl_Area * (perc_Harv / 100.00) * harv_Mass * math.ceil(num_Years / freq_Harv)
        #Calculate Volume
        volume = biomass * (1.0 / BCEF)

        net_present_value = (summation_one - summation_two)
        total_npv = net_present_value * parcl_Area

        #For each new field set the corresponding value to the specific polygon
        for field, value in (('TNPV', total_npv), ('TBiomass', biomass), ('TVolume', volume)):
            index = feat.GetFieldIndex(field)
            feat.SetField(index, value)

        #save the field modifications to the layer.
        layer.SetFeature(feat)
        feat.Destroy()

#def getAttributeRow(feat, attr_table):
#    parcl_index = feat.GetFieldIndex('Parcl_ID')
#    parcl_id = feat.GetField(parcl_index)
#    table_index = 0
#    table_id = attr_table[table_index]['Parcel_ID']
#
#    #Make sure referring to the same polygon by comparing Parcl_ID's
#
#    #Example of how to build lookup table so we don't have to loop through 
#    #table linearly
#    parcelIdLookup = {} # this
#    while parcl_id != table_id: #this
#        parcelIdLookup[attr_table[table_index]['Parcel_ID']] = table_index #and this

#    while parcl_id != table_id:
#        table_index += 1
#        table_id = attr_table[table_index]['Parcel_ID']
#
#    return attr_table[table_index]

#Calculates the first summation for the net present value of a parcel
def npvSummationOne(lower, upper, harvest_value, mdr_perc, freq_Harv, subtractor):
    summation = 0.0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (harvest_value / (mdr_perc ** ((freq_Harv * num) - subtractor)))

    return summation

#Calculates the second summation for the net present value of a parcel
def npvSummationTwo(lower, upper, maint_Cost, mdr_perc):
    summation = 0.0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (maint_Cost / (mdr_perc ** num))

    return summation