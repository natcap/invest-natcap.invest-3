import carbon_core
import carbon_uncertainty
import math
import carbon_seq
import numpy as np
from osgeo import gdal

def execute(args):
    """Runs a scenario based uncertainty model for two LULC maps.  Output
        is a 4 output_seq raster for 3 bands indicating carbon sequestration
        change for low, average, and high measurements.  Fourth output_seq is
        the minimum percentage ranking of each pixel in each of the
        three scenarios.
    
        args - is a dictionary with at least the following entries:
        args['lulc_cur'] - is an open ogr shape file
        args['layer'] - layer
        args['plant_prod'] - is a dictionary of the shapefiles attributes
        args['mdr'] - the market discount rate
        args['output_seq'] - an ogr shape file location
        
        returns nothing"""

        
    #Determine what values should have been stored per layer
    featureDict = {}
    avg = math.floor((yrFut + yrCur)/2.0)
    for feature in args['layer']:
        #first, initialize layer fields by index
        fieldArgs = {'Perc_harv' : feature.GetFieldIndex('Perc_harv'),
                     'Harv_mass' : feature.GetFieldIndex('Harv_mass'),
                     'Freq_harv' : feature.GetFieldIndex('Freq_harv'),
                     'Price' : feature.GetFieldIndex('Price'),
                     'Maint_cost' : feature.GetFieldIndex('Maint_cost'),
                     'Harv_cost' : feature.GetFieldIndex('Harv_cost'),
                     'T' : feature.GetFieldIndex('T'),      
                     'Immed_harv' : feature.GetFieldIndex('Immed_harv'),
                     'BCEF' : feature.GetFieldIndex('BCEF')}
        
        #then, replace the indices with actual items
        for key,index in fieldArgs.iteritems():
            fieldArgs[key] = feature.GetField(index)
        
        harvest_value = (fieldArgs['Perc_harv']/100)*((fieldArgs['Price']*fieldArgs['Harv_mass'])-fieldArgs['Harv_cost'])
        net_present_value = 0
        upper_limit = math.ceil(fieldArgs['T']/fieldArgs['Freq_harv'])-1
        lower_limit = 0
        for lower_limit in upper_limit:
            net_present_value = net_present_value + harvest_value/((1+(args['lulc_cur'].mdr/100))**(fieldArgs['Freq_harv']*lower_limit))
            
        
        #set the HWP carbon pool for this feature.
        featureDict[feature.GetFID()] = fieldArgs['Cut_fut']*sum
        
    #reopen the shapefile that contains calculated HWP values
    hwp_shape = ogr.Open('./testShapeFut')
    hwp_layer = hwp_shape.GetLayerByName('harv_samp_fut')

    #Assert that HWP values stored in the shapefile match our dict entries
    for fid in featureDict:
        feature = hwp_layer.GetFeature(fid)   
        index = feature.GetFieldIndex('hwp_pool')
        self.assertAlmostEqual(feature.GetField(index), featureDict[fid], 8)