'''This is the test class for overlap_analysis's outer module. This should
adequately test overlap_analysis' ability to prepare data coming in to be
passed to the core module.'''

import os
import unittest

import invest_test_core
from invest_natcap.overlap_analysis import overlap_analysis

class TestOverlapAnalysis(unittest.TestCase):
    
    def setUp(self):
        
        args = {}
        '''
            Still need to add:
                
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
        args['workspace'] = './data/overlap_analysis'
        args['zone_layer_loc'] = './data/overlap_analysis/AOI_WCVI.shp'
        args['do_grid'] = True
        args['grid_size'] = 1000
        args['overlap_data_dir_loc'] = './data/overlap_analysis/FisheriesLayer_RI'
        args['overlap_layer_tbl'] = './data/overlap_analysis/Fisheries_Inputs.csv'
        
        self.args = args
        
    def test_execute(self):
        #DO WE WANT TO TEST FINAL OUTPUTS OR INTERMEDIATE CREATED FILES
        pass
        
    def test_format_over_table(self):
        
        output_table = overlap_analysis.format_over_table(self.args['overlap_layer_tbl'])
        
        reg_overlap_table = {'CommGf_Fish': (2.00, 0), 'CommSalmonTroll_Fish': (1.50, 0),
                             'CommShrimp_Fish': (1.50, 0)}
    
        invest_test_core.assertAlmostEqual(output_table, reg_overlap_table)