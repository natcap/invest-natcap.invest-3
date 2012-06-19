"""URI level tests for the aquaculture biophysical and valuation module"""

import os, sys
import unittest
import shutil

from invest_natcap.finfish_aquaculture import finfish_aquaculture
import invest_test_core

class TestFinfishAquaculture(unittest.TestCase):
    def setUp(self):
    
        args = {}
        #Biophysical
        args['workspace_dir'] = './test/data/aquaculture_output/Test'
        args['ff_farm_loc'] = './test/data/aquaculture_data/Test_Data/Finfish_Netpens_Jodie_Data.shp'
        args['farm_ID'] = 'FarmID'
        args['g_param_a'] = 0.038
        args['g_param_b'] = 0.6667
        args['water_temp_tbl'] = './test/data/aquaculture_data/Test_Data/Temp_Daily_Reg_Test.csv'
        args['farm_op_tbl'] = './test/data/aquaculture_data/Test_Data/Farm_Operations_Reg_Test.csv'
        
        #Valuation
        args['do_valuation'] = False
        args['p_per_kg']= 2.25
        args['frac_p'] = .3
        args['discount'] = 0.000192
        
        self.args = args
        
        ff_aqua_args = {}
        self.ff_aqua_args = ff_aqua_args
        
    def test_format_ops_table(self):
        
        reg_ops_table = {'1': {'Fraction of fish remaining after processing' : '.85', 
                               'Natural mortality rate on the farm (daily)' : '0.000137',
                               'Duration of simulation (years)' : '.1', 
                               'weight of fish at start (kg)' : '0.06',
                               'target weight of fish at harvest (kg)' : '5.4',
                               'number of fish in farm' : '600000', 
                               'start day for growing' : '1',
                               'Length of Fallowing period' : '30'},
                         '4': {'Fraction of fish remaining after processing' : '.85', 
                               'Natural mortality rate on the farm (daily)' : '0.000137',
                               'Duration of simulation (years)' : '.1', 
                               'weight of fish at start (kg)' : '0.08',
                               'target weight of fish at harvest (kg)' : '6.0',
                               'number of fish in farm' : '500000', 
                               'start day for growing' : '20',
                               'Length of Fallowing period' : '0'}}
    
        print reg_ops_table
        print "\n"
        
        finfish_aquaculture.format_ops_table(self.args['farm_op_tbl'], "Farm #:", self.ff_aqua_args)
    
        norm_ops_table = self.ff_aqua_args['farm_op_dict']
    
            
        self.assertEqual(reg_ops_table, norm_ops_table)
    
    def test_format_temp_table(self):
        
        reg_temp_table = {'1':{'1':'7', '4':'8'}, '2':{'1':'7', '4':'8'}, '3':{'1':'7', '4':'8'},
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
                          '40':{'1':'7', '4':'8'}}
    
        norm_temp_table = finfish_aquaculture.format_temp_table(self.args['water_temp_tbl'])
        
        self.assertEqual(reg_temp_table, norm_temp_table)
        
    def tearDown(self):
        
        if os.path.exists(self.args['workspace_dir']):
            shutil.rmtree(self.args['workspace_dir'])
            
        
            