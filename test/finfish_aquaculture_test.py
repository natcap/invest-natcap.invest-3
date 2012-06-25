"""URI level tests for the aquaculture biophysical and valuation module"""

import os, sys
import unittest
import shutil

from invest_natcap.finfish_aquaculture import finfish_aquaculture
import invest_test_core

class TestFinfishAquaculture(unittest.TestCase):
    def setUp(self):
    
        ff_aqua_args = {}
        #Biophysical
        ff_aqua_args['workspace_dir'] = './Aquaculture/Re_Testing'
        ff_aqua_args['ff_farm_loc'] = './Aquaculture/Input/Test_Data/Finfish_Netpens_Reg_Test.shp'
        ff_aqua_args['farm_ID'] = 'FarmID'
        ff_aqua_args['g_param_a'] = 0.038
        ff_aqua_args['g_param_b'] = 2.0
        ff_aqua_args['water_temp_tbl'] = './Aquaculture/Input/Test_Data/Temp_Daily_Reg_Test.csv'
        ff_aqua_args['farm_op_tbl'] = './Aquaculture/Input/Test_Data/Farm_Operations_Reg_Test.csv'
        ff_aqua_args['outplant_buffer'] = 3
        
        #Valuation
        ff_aqua_args['do_valuation'] = True
        ff_aqua_args['p_per_kg']= 2.25
        ff_aqua_args['frac_p'] = .3
        ff_aqua_args['discount'] = 0.000192
        
        ff_aqua_args['reg_cy_hist'] = {1: [(1, 3, 6266.532049655182), 
                                           (363, 365, 6266.532049655182), 
                                           (728, 730, 6266.532049655182), 
                                           (1093, 1095, 6266.532049655182), 
                                           (1458, 1460, 6266.532049655182), 
                                           (1823, 1825, 6266.532049655182)], 
                                       4: [(20, 22, 21651.134982624022), 
                                           (382, 384, 21651.134982624022), 
                                           (747, 749, 21651.134982624022), 
                                           (1112, 1114, 21651.134982624022), 
                                           (1477, 1479, 21651.134982624022)]}
        
        ff_aqua_args['tpw_totals'] =  {1: 19170334.68056063, 4: 45996057.19164784}
        ff_aqua_args['indiv_cy_tpw'] = {1: [3195055.7800934385, 3195055.7800934385, 
                                            3195055.7800934385, 3195055.7800934385, 
                                            3195055.7800934385, 3195055.7800934385], 
                                        4: [9199211.438329568, 9199211.438329568, 
                                            9199211.438329568, 9199211.438329568, 
                                            9199211.438329568]}
        #The value history contains a history of tuples that are (net revenue, npv)
        # for that particular cycle.
        ff_aqua_args['reg_value_hist'] =  {1: [(5032212.853647165, 5029315.411732361), 
                                               (5032212.853647165, 4691660.379716688), 
                                               (5032212.853647165, 4374154.623179357), 
                                               (5032212.853647165, 4078135.909026886), 
                                               (5032212.853647165, 3802150.1124727405), 
                                               (5032212.853647165, 3544841.5158939636)], 
                                           4: [(14488758.015369069, 14427692.42493477), 
                                               (14488758.015369069, 13459055.036178194), 
                                               (14488758.015369069, 12548220.25580618), 
                                               (14488758.015369069, 11699025.761093546), 
                                               (14488758.015369069, 10907300.076710137)]}
        ff_aqua_args['reg_npv'] = {1: 25520.257952021995, 4: 63041.293554722826}

        self.ff_aqua_args = ff_aqua_args
        
    def test_format_ops_table(self):
        
        reg_ops_table = {'1': {'weight of fish at start (kg)' : '0.06',
                               'target weight of fish at harvest (kg)' : '5.4',
                               'number of fish in farm' : '600000', 
                               'start day for growing' : '1',
                               'Length of Fallowing period' : '30'},
                         '4': {'weight of fish at start (kg)' : '0.08',
                               'target weight of fish at harvest (kg)' : '6',
                               'number of fish in farm' : '500000', 
                               'start day for growing' : '20',
                               'Length of Fallowing period' : '0'}}
        
        finfish_aquaculture.format_ops_table(self.ff_aqua_args['farm_op_tbl'], "Farm #:", self.ff_aqua_args)
    
        norm_ops_table = self.ff_aqua_args['farm_op_dict']
    
            
        self.assertEqual(reg_ops_table, norm_ops_table)
    
    def test_format_temp_table(self):
        
        reg_temp_table = {'0':{'1':'7', '4':'8'}, '2':{'1':'7', '4':'8'}, '3':{'1':'7', '4':'8'},
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
        
        finfish_aquaculture.format_temp_table(self.ff_aqua_args['water_temp_tbl'], self.ff_aqua_args)
        norm_temp_table = self.ff_aqua_args['water_temp_dict']
        
        self.maxDiff = None
        self.assertEqual(reg_temp_table, norm_temp_table)

    def test_finfish_aquaculture(self):
        
        #Are going to have to run the test, then index into the file locations in order 
        #to test things like the shapefile against some sort of pre-made thing.
        
        #Need to get the arguments in the proper form to pass to finfish_aquaculture
        args = {}
        args['workspace_dir'] = self.ff_aqua_args['workspace_dir']
        args['ff_farm_loc'] = self.ff_aqua_args['ff_farm_loc']
        args['farm_ID'] = self.ff_aqua_args['farm_ID']
        args['g_param_a'] = self.ff_aqua_args['g_param_a']
        args['g_param_b'] = self.ff_aqua_args['g_param_b']
        args['water_temp_tbl'] = './Aquaculture/Input/Test_Data/Temp_Daily_Reg_Test.csv'
        args['farm_op_tbl'] = './Aquaculture/Input/Test_Data/Farm_Operations_Reg_Test.csv'
        args['outplant_buffer'] = self.ff_aqua_args['outplant_buffer']
        args['do_valuation'] = self.ff_aqua_args['do_valuation']
        args['p_per_kg'] = self.ff_aqua_args['p_per_kg']
        args['frac_p'] = self.ff_aqua_args['frac_p']
        args['discount'] = self.ff_aqua_args['discount']
        
        finfish_aquaculture.execute(args)
        
        #Checking the shapefile
        completed_shp = self.ff_aqua_args['workspace_dir'] + os.sep + 'Output' + \
                    'Finfish_Harvest.shp'
        reg_shp = './Aquaculture/Input/Test_Data/Finfish_Harvest_Reg_Test_Final.shp'
        
        invest_test_core.assertTwoShapesEqualURI(self, completed_shp, reg_shp)
        
        
        #Finding the HarvestResults.html file that was created with our testing,
        #and comparing the inner text against our regression test file.
        r = re.compile("Harvest_Results_\[[0-9_-]*\]\.html")
        
        html_file = None

        for root, dirs, files in os.walk((self.ff_aqua_args['workspace_dir'] + \
                                          os.sep + 'Output')):
            html_out = [os.path.join(root, x) for x in files if r.match(x)]
            
            if html_out:
                html_file = html_out
        
        reg_html_file = './Aquaculture/Input/Test_Data/Harvest_Results_Reg_Test.html'
        
        filecmp.cmp(html_file, reg_html_file, shallow=False)
        
        #Finding the parameter log file, and checking that against our own.
        r = re.compile("Parameter_Log_\[[0-9_-]*\]\.txt")
        
        text_file = None

        for root, dirs, files in os.walk((self.ff_aqua_args['workspace_dir'] + \
                                          os.sep + 'Output')):
            text_out = [os.path.join(root, x) for x in files if r.match(x)]
            
            if text_out:
                text_file = text_out
                
        reg_text_file = './Aquaculture/Input/Test_Data/Parameter_Log_Reg_Test.txt'
        
        filecmp.cmp(text_file, reg_text_file, shallow=False)
        

    def tearDown(self):
        
        if os.path.exists(self.ff_aqua_args['workspace_dir']):
            shutil.rmtree(self.ff_aqua_args['workspace_dir'])
        