
'''This will be the test module for the non-core portion of Habitat Risk
Assessment.'''

import os
import unittest
import logging
import glob
import filecmp

import invest_test_core

from invest_natcap.hra_scratch import hra
from invest_natcap.hra_scratch import hra_core

LOGGER = logging.getLogger('hra_scratch_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRA(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/HRA/New_Test' 
        args['grid_size'] = 500
        args['max_rating'] = 3
        args['csv_uri'] = './invest-data/test/data/hra_regression_data/habitat_stressor_ratings'

        self.args = args

    def test_standard_config(self):
        '''Simplistic mock up stored in personal test_out so that we can start to debug
        pre_proc/hra/core.'''
        self.args['csv_uri'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/data/test_out/HRA/Scratch/habitat_stressor_ratings'
        self.args['workspace_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/data/test_out/HRA/Scratch'

        self.args['risk_eq'] = 'Multiplicative'
        self.args['decay_eq'] = 'Linear'

        hra.execute(self.args)
