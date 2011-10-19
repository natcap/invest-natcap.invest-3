import numpy as np
import imp, sys, os
from osgeo import ogr
from osgeo.gdalconst import *
from dbfpy import dbf
from osgeo import gdal
import math

def execute(args):
    """Executes the basic timber management model that calculates the Total Net Present Value and maps
        it to an outputted shapefile.
    
        args - is a dictionary with at least the following entries:
        args['timber_shape']     - is a OGR shapefile.
        args['timber_layer']     - is the layer which holds the polygon features.
        args['timber_shp_copy']  - is a copy of the original OGR shapefile and will be used as the output with
                                    with the new fields attached to the features.
        args['output_dir']       - the directory where the output files should be saved.
        args['mdr']              - the market discount rate.
        args['plant_prod']       - the dbf file which has the attribute values of each timber parcel.
        
        returns nothing"""
        
    
    field_def = ogr.FieldDefn('TNPV', ogr.OFTReal)
    #output_shape = args['timber_shape']
    ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(args['timber_shape'], '../../test_data/timber/timber_output' + os.sep)
    output_shape = ogr.Open('../../test_data/timber/timber_output/plantation.shp')
    layer = output_shape.GetLayerByName('plantation')
    
    layer.CreateField(field_def)
    
    ###################
    
    
    
#    driverName = 'ESRI Shapefile'
#    drv = org. GetDriverByName(driverName)
#    ds = drv.CreateDataSource('point_out.shp')
#    lyr = ds.CreateLayer('plantation', None, ogr.wkbPolygon)
    
    
    
    ##############
    plant_dict = args['plant_prod']
    plant_total = []
    for i in range(plant_dict.recordCount):
        net_present_value = 0
        summation_one = 0.0
        summation_two = 0.0
        lower_limit2 = 0
        upper_limit2 = plant_dict[i]['T'] - 1
        harvest_value = harvestValue(plant_dict[i]['Perc_harv'],plant_dict[i]['Price'],
                                     plant_dict[i]['Harv_mass'],plant_dict[i]['Harv_cost'],)
        
        if plant_dict[i]['Immed_harv']=='N':
            upper_limit = int(math.floor(plant_dict[i]['T']/plant_dict[i]['Freq_harv']))
            lower_limit = 1
            summation_one = summationOneAlt(lower_limit, upper_limit, harvest_value, args['mdr'], plant_dict[i]['Freq_harv'])
            summation_two = summationTwo(lower_limit2, upper_limit2, plant_dict[i]['Maint_cost'], args['mdr'])

            
        else:
            upper_limit = int((math.ceil(float(plant_dict[i]['T'])/float(plant_dict[i]['Freq_harv'])))-1)
            lower_limit = 0
            summation_one = summationOne(lower_limit, upper_limit, harvest_value, args['mdr'], plant_dict[i]['Freq_harv'])
            summation_two = summationTwo(lower_limit2, upper_limit2, plant_dict[i]['Maint_cost'], args['mdr'])
            
        net_present_value = (summation_one - summation_two)
        total_npv = net_present_value * plant_dict[i]['Parcl_area']


        feature = layer.GetFeature(0)
        index = feature.GetFieldIndex('TNPV')
        #feature.SetField(index, total_npv)       
        
        plant_total.append(total_npv)
        #layer.SetFeature(feature)
        
        #feature.Destroy()
    #save the field modifications to the layer.
    
    return plant_total
        
def harvestValue(perc_Harv, price, harv_Mass, harv_Cost):
    harvest_value = (perc_Harv/100.00)*((price*harv_Mass)-harv_Cost)
    return harvest_value

def summationOne(lower, upper, harvest_value, mdr, freq_Harv):
    summation = 0.0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (harvest_value/((1.0+(mdr/100.00))**(freq_Harv*num)))
            
    return summation

def summationOneAlt(lower, upper, harvest_value, mdr, freq_Harv):
    summation = 0.0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (harvest_value/((1.0+(mdr/100.00))**((freq_Harv*num)-1)))
            
    return summation

def summationTwo(lower, upper, maint_Cost, mdr):
    summation = 0.0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (maint_Cost/((1.0+(mdr/100.00))**num))
            
    return summation



#def build_plant_prod_dict(dbf, index):
#    plant_dict = []
#    for key in range(dbf.recordCount):
        