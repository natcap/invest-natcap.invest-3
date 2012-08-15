'''Testing framework for the management zone OA core. This will run an
overarching test of the core module, then compare it against a pre-edited
version.'''

import unittest
import os
import logging
import invest_test_core

from osgeo import ogr
from invest_natcap.overlap_analysis import overlap_analysis_mz_core
from invest_natcap.overlap_analysis import overlap_analysis_mz

LOGGER = logging.getLogger('overlap_analysis_mz_core_test')

logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestMZCore(unittest.TestCase):

    def setUp(self):
        
        args = {}

        args['workspace_dir'] = './data/test_out/Overlap'
        args['zone_layer_file'] = ogr.Open('./data/test_out/Overlap/Input/test_mz.shp')
        
        files_loc = './data/test_out/Overlap/Input/Test_Activity'

        files_dict = overlap_analysis_mz.get_files_dict(files_loc)

        args['over_layer_dict'] = files_dict

        self.args = args
    
    def test_reg_overall(self):

        overlap_analysis_mz_core.execute(self.args)
