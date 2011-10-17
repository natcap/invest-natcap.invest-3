import numpy as np
from osgeo import gdal
import math

def execute(args):
    """Runs a scenario based uncertainty model for two LULC maps.  Output
        is a 4 output_seq raster for 3 bands indicating carbon sequestration
        change for low, average, and high measurements.  Fourth output_seq is
        the minimum percentage ranking of each pixel in each of the
        three scenarios.
    
        args - is a dictionary with at least the following entries:
        args['timber_shape'] - is an open ogr shape file
        args['timber_lyr'] - layer
        args['plant_prod'] - is a dictionary of the shapefiles attributes
        args['output_seq']: timber_shp_copy,
        args['output_dir']: args['output_dir'],
        args['mdr']
        
        returns nothing"""
        
    plant_dict = args['plant_prod']
    plant_total = []
    for i in range(plant_dict.recordCount):
        harvest_value = harvestValue(plant_dict[i]['Perc_harv'],plant_dict[i]['Price'],
                                     plant_dict[i]['Harv_mass'],plant_dict[i]['Harv_cost'],)
        summation_one = 0.0
        summation_two = 0.0
        upper_limit = int(math.ceil(plant_dict[i]['T']/plant_dict[i]['Freq_harv'])-1)
        lower_limit = 0.0
        lower_limit2 = 0.0
        upper_limit2 = plant_dict[i]['T'] - 1
        summation_one = summationOne(lower_limit, upper_limit, harvest_value, args['mdr'], plant_dict[i]['Freq_harv'])
        summation_two = summationTwo(lower_limit2, upper_limit2, plant_dict[i]['Maint_cost'], args['mdr'])
        net_present_value = summation_one - summation_two
        
        plant_total.append(net_present_value)
        
def harvestValue(perc_Harv, price, harv_Mass, harv_Cost):
    harvest_value = (perc_Harv/100.00)*((price*harv_Mass)-harv_Cost)
    return harvest_value

def summationOne(lower, upper, harvest_value, mdr, freq_Harv):
    summation = 0
    upper = upper + 1
    for num in range(lower, upper):
            summation = summation + (harvest_value/((1.0+(mdr/100.00))**(freq_Harv*num)))
            
    return summation

def summationTwo(lower, upper, maint_Cost, mdr):
    summation = 0
    for num in range(lower, upper):
            summation = summation + (maint_Cost/(1.0+((mdr/100.00)**num2)))
            
    return summation



#def build_plant_prod_dict(dbf, index):
#    plant_dict = []
#    for key in range(dbf.recordCount):
        