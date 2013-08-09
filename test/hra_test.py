
'''This will be the test module for the non-core portion of Habitat Risk
Assessment.'''

import os
import unittest
import logging
import glob
import filecmp

import invest_natcap.testing

from invest_natcap.habitat_risk_assessment import hra
from invest_natcap.habitat_risk_assessment import hra_core

LOGGER = logging.getLogger('hra_scratch_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRA(invest_natcap.testing.GISTest):

    def setUp(self):

        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/HRA/New_Test' 
        args['grid_size'] = 500
        args['max_rating'] = 3
        args['csv_uri'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/habitat_stressor_ratings'

        self.args = args

    def test_standard_config_smoke(self):
        '''Simplistic mock up stored in personal test_out so that we can start to debug
        pre_proc/hra/core.'''

        self.args['risk_eq'] = 'Multiplicative'
        self.args['decay_eq'] = 'Linear'

        hra.execute(self.args)

    def test_euc_nodecay_noplots_smoke(self):
        '''Most simplistic version of the model run. Will use euclidean
        risk, since that was the original desired eqauation, as well as
        no decay on the stressors.'''


        self.args['risk_eq'] = 'Euclidean'
        self.args['decay_eq'] = 'None'

        hra.execute(self.args)

    def test_euc_withAOI_smoke(self):
        '''Want to make sure that we can run from non-core when including an AOI
        overlay as a final output. That should produce an HTML folder, containining
        a table.'''
    
        #Standard params
        self.args['risk_eq'] = 'Euclidean'
        self.args['decay_eq'] = 'None'
        self.args['aoi_tables'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/subregions.shp'

        hra.execute(self.args)

    def test_euc_full_regression(self):
        '''Alright. Let's do this shit.'''

        exp_workspace = './invest-data/test/data/hra_regression_data/'

        self.args['workspace_dir'] = './invest-data/test/data/test_out/HRA/Reg_Folder'
        self.args['risk_eq'] = 'Euclidean'
        self.args['decay_eq'] = 'Linear'
        self.args['aoi_tables'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/subregions.shp'

        hra.execute(self.args)
        
        res_inter = os.path.join(self.args['workspace_dir'], 'Intermediate')
        res_output = os.path.join(self.args['workspace_dir'], 'Output')

