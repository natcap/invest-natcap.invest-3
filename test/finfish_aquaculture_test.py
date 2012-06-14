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
        args['ff_farm_loc'] = './test/data/aquaculture_data/Finfish_Netpens_Jodie_Data.shp'
        args['farm_ID'] = 'FarmID'
        args['g_param_a'] = 0.038
        args['g_param_b'] = 0.6667
        args['water_temp_tbl'] = './test/data/aquaculture_data/Temp_Daily_Jodie_Test.csv'
        args['farm_op_tbl'] = './test/data/aquaculture_data/Farm_Operations_Jodie_Test.csv'
        
        #Valuation
        args['do_valuation'] = False
        args['p_per_kg']= 2.25
        args['frac_p'] = .3
        args['discount'] = 0.000192
        
        self.args = args        
    
    def test_finfish_aquaculture_smoke(self):
        """Smoke test for finfish_aquaculture function. """

        finfish_aquaculture.execute(self.args)
    
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
        
        norm_ops_table = finfish_aquaculture.format_ops_table(self.args['farm_op_tbl'], "Farm# :")
    
        self.assertEqual(reg_ops_table, norm_ops_table)
    
    def test_format_temp_table(self):
        
        reg_temp_table = {}
    
    def tearDown(self):
        
        if os.path.exists(self.args['workspace_dir']):
            shutil.rmtree(self.args['workspace_dir'])
            
        
            