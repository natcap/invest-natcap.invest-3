'''Testing framework for the management zone OA core. This will run an
overarching test of the core module, then compare it against a pre-edited
version.'''

import unittest
import os
import logging
import invest_test_core

from osgeo import ogr

from invest_natcap.overlap_analysis import overlap_analysis_mz_core
from invest_natcap.overlap_analysis import overlap_core

LOGGER = logging.getLogger('overlap_analysis_mz_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestMZCore(unittest.TestCase):

    def setUp(self):
        
        args = {}

        args['workspace_dir'] = './invest-data/test/data/test_out/Overlap'
        args['zone_layer_file'] = ogr.Open('./invest-data/test/data/test_out/Overlap/Input/test_mz.shp')
        
        files_loc = './invest-data/test/data/test_out/Overlap/Input/Test_Activity'
        files_dict = overlap_core.get_files_dict(files_loc)
        args['over_layer_dict'] = files_dict

        self.args = args
    
    def test_reg_overall(self):
        
        #Redefining args to check against what we already have
        self.args['workspace_dir'] = '.data/overlap_analysis'
        self.args['zone_layer_file'] = './invest-data/test/data/overlap_analysis/ManagementZones_WCVI.shp'
        
        
        files_loc = './invest-data/test/data/overlap_analysis/FisheriesLayers_RI'
        files_dict = overlap_core.get_files_dict(files_loc)
        self.args['over_layer_dict'] = files_dict
        
        overlap_analysis_mz_core.execute(self.args)
        
        out_file = os.path.join(self.args['workspace_dir'], 'Output', 'mz_frequency.shp')

        reg_mz_out = './invest-data/test/data/overlap_analysis_regression_data/mz_frequency.shp'

        invest_test_core.assertTwoShapesEqualURI(self, out_file, reg_mz_out)
