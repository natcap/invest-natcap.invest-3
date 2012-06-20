"""URI level tests for the aquaculture core module"""

import os, sys
import unittest
import ogr

from invest_natcap.finfish_aquaculture import finfish_aquaculture_core
import invest_test_core

class TestFinfishAquacultureCore(unittest.TestCase):
   
    
    def setUp(self):
    
        ff_farm_loc = './test/data/aquaculture_data/Test_Data/Finfish_Netpens_Jodie_Data.shp'
        ff_aqua_args = {}
        
        #Biophysical
        ff_aqua_args['workspace_dir'] = './test/data/aquaculture_output/Test'
        ff_aqua_args['farm_ID'] = 'FarmID'
        ff_aqua_args['ff_farm_file'] = ogr.Open(ff_farm_loc)
        ff_aqua_args['g_param_a'] = 0.1
        ff_aqua_args['g_param_b'] = 0.9
        ff_aqua_args['water_temp_tbl'] = {'0':{'1':'7', '4':'8'}, '2':{'1':'7', '4':'8'}, '3':{'1':'7', '4':'8'},
                           '4':{'1':'7', '4':'8'}, '5':{'1':'7', '4':'8'}, '6':{'1':'7', '4':'8'},
                           '7':{'1':'7', '4':'8'}, '8':{'1':'7', '4':'8'}, '9':{'1':'7', '4':'8'},
                           '10':{'1':'7', '4':'8'}, '11':{'1':'7', '4':'8'}, '12':{'1':'7', '4':'8'},
                           '13':{'1':'7', '4':'8'}, '14':{'1':'7', '4':'8'}, '15':{'1':'7', '4':'8'},
                           '16':{'1':'7', '4':'8'}, '17':{'1':'7', '4':'8'}, '18':{'1':'7', '4':'8'},
                           '19':{'1':'7', '4':'8'}, '20':{'1':'7', '4':'8'}, '21':{'1':'7', '4':'8'},
                           '22':{'1':'7', '4':'8'}, '23':{'1':'7', '4':'8'}, '24':{'1':'7', '4':'8'},
                           '25':{'1':'7', '4':'8'}, '26':{'1':'7', '4':'8'}, '27':{'1':'7', '4':'8'},
                           '28':{'1':'7', '4':'8'}, '29':{'1':'7', '4':'8'}, '30':{'1':'7', '4':'8'},
                           '31':{'1':'7', '4':'8'}, '32':{'1':'7', '4':'8'}, '33':{'1':'7', '4':'8'},
                           '34':{'1':'7', '4':'8'}, '35':{'1':'7', '4':'8'}, '36':{'1':'7', '4':'8'},
                           '37':{'1':'7', '4':'8'}, '38':{'1':'7', '4':'8'}, '39':{'1':'7', '4':'8'},
                           '1':{'1':'7', '4':'8'}}
        ff_aqua_args['farm_op_tbl'] = {'1': {'weight of fish at start (kg)' : '0.06',
                               'target weight of fish at harvest (kg)' : '5.4',
                               'number of fish in farm' : '600000', 
                               'start day for growing' : '1',
                               'Length of Fallowing period' : '30'},
                         '4': {'weight of fish at start (kg)' : '0.08',
                               'target weight of fish at harvest (kg)' : '6',
                               'number of fish in farm' : '500000', 
                               'start day for growing' : '20',
                               'Length of Fallowing period' : '0'}}
        ff_aqua_args['duration'] = .1
        
        #Valuation
        ff_aqua_args['do_valuation'] = False
        ff_aqua_args['p_per_kg']= 2.25
        ff_aqua_args['frac_p'] = .3
        ff_aqua_args['discount'] = 0.000192
        
        self.ff_aqua_args = ff_aqua_args
    
    '''For these, we will basically have to run each test, get the values and compare
    against expected values. THEN, add everything to their corresponding shapefiles
    and compare the two shapefiles(?)'''
        
    def test_calc_cycle_history(self):
        
        #reg_cy_hist = 
    
        cycle_history = finfish_aquaculture_core.calc_farm_cycles(
                                self.ff_aqua_args, self.ff_aqua_args['g_param_a'],
                                self.ff_aqua_args['g_param_b'], self.ff_aqua_args['water_temp_tbl'],
                                self.ff_aqua_args['farm_op_tbl'], self.ff_aqua_args['duration'])