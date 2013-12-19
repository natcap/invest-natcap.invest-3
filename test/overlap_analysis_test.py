'''This is the test class for overlap_analysis's outer module. This should
adequately test overlap_analysis' ability to prepare data coming in to be
passed to the core module.'''

import os
import unittest

import invest_test_core
from invest_natcap.overlap_analysis import overlap_analysis

class TestOverlapAnalysis(unittest.TestCase):
    
    def setUp(self):
    
        '''Still need to add:
                
        --Optional--
        args['import_field']- string which corresponds to a field within the
            layers being passed in within overlap analysis directory. This is
            the intra-activity importance for each activity.
        args['hum_use_hubs_loc']- URI that points to a shapefile of major hubs
            of human activity. This would allow you to degrade the weight of
            activity zones as they get farther away from these locations.
        args['decay']- float between 0 and 1, representing the decay of interest
            in areas as you get farther away from human hubs.
        '''
        args = {}

        args['workspace_dir'] = './invest-data/test/data/overlap_analysis'
        args['zone_layer_uri'] = './invest-data/test/data/overlap_analysis/AOI_WCVI.shp'
        args['grid_size'] = 500 
        args['overlap_data_dir_uri'] = './invest-data/test/data/overlap_analysis/FisheriesLayers_RI'
        args['overlap_layer_tbl'] = './invest-data/test/data/overlap_analysis/Fisheries_Inputs.csv'
        args['do_inter'] = False
        args['do_intra'] = False
        args['do_hubs'] = False
        args['intra_name'] = 'RI'

        self.args = args
        
    def test_minimal_smoke(self):

        #This just tests that OA doesn't fail.     
        overlap_analysis.execute(self.args)
        
    def test_format_over_table(self):
        
        output_table = overlap_analysis.format_over_table(self.args['overlap_layer_tbl'])
        
        reg_overlap_table = {'CommGF_Fish': 2.00, 'CommSalmonTroll_Fish': 1.50,
                             'CommShrimp_Fish': 1.50}
    
        #Dictionaries are not included in the self.assertAlmostEqual function, so writing
        #a quick function here to check them. This will use assertAlmostEqual inside of it.
        
        for element in reg_overlap_table:
            
            if output_table[element]:
                    
                #Need to pull out both elements and compare, then break down so
                #we can do an almost equal on the individual elements
                w1 = output_table[element]
                w2 = reg_overlap_table[element]

                self.assertAlmostEqual(w1, w2)
                        
            else:
                self.fail("Element %s is not a key in the test-created table.", element)

    def test_reg_default_data(self):
        
        self.args['do_inter'] = True
        self.args['do_intra'] = True

        overlap_analysis.execute(self.args)

        output_dir = os.path.join(self.args['workspace_dir'], 'Output')

        unweighted_output = os.path.join(output_dir, 'hu_freq.tif')
        weighted_output = os.path.join(output_dir, 'hu_impscore.tif')
        
        reg_unweighted = './invest-data/test/data/overlap_analysis_regression_data/hu_freq.tif'
        reg_weighted ='./invest-data/test/data/overlap_analysis_regression_data/hu_impscore.tif'

        invest_test_core.assertTwoDatasetEqualURI(self, unweighted_output, reg_unweighted)
        invest_test_core.assertTwoDatasetEqualURI(self, weighted_output, reg_weighted)
