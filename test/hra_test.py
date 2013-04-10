'''This will be the test module for the non-core portion of Habitat Risk
Assessment.'''

import os
import unittest
import logging

import invest_test_core

from invest_natcap.habitat_risk_assessment import hra
from invest_natcap.habitat_risk_assessment import hra_core

LOGGER = logging.getLogger('hra_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRA(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = './data/test_out/HRA/New_Test' 
        args['grid_size'] = 500
        args['max_rating'] = 3
        args['csv_uri'] = './data/hra_regression_data/habitat_stressor_ratings'

        self.args = args
    
    def test_euc_nodecay_noplots_smoke(self):
        '''Most simplistic version of the model run. Will use euclidean
        risk, since that was the original desired eqauation, as well as
        no decay on the stressors.'''


        self.args['risk_eq'] = 'Euclidean'
        self.args['decay_eq'] = 'None'

        hra.execute(self.args)

    def test_euc_withAOI_smoke(self):
        '''Want to make sure that we can run from non-core when including an AOI
        overlay as a final output. That shoudl produce an HTML folder, containining
        a table.'''

        self.args['aoi_tables'] = './data/hra_regression_data/Input/subregions.shp'

        self.execute(self.args)

    def test_ImproperAOIAttrib_exception(self):
        '''Want to check that if this model run contains an AOI, that we have a
        'name' attribute in each of the AOI features. If this is not true, it
        should raise an ImproperAOIAttributeName exception. We will use a
        seperate improperly named AOI file for these purposes.
        '''

        self.args['aoi_tables'] = './data/hra_regression_data/Input/subregions_incorrect.shp'

        self.assertRaises(hra.ImproperAOIAttributeName,
                        hra.execute, self.args)

    def test_ImproperCritAttrib_exception(self):
        '''Want to check that if this model uses shapefile criteria, that each 
        of them contains an attribute of 'name'. Currently, this is case
        sensitive. After the fact, it can be changed. If this is not existant, it
        should raise an ImproperCriteriaAttributeName exception. We will use a
        seperate improperly named shape criteria file for these purposes.
        '''

        self.args['csv_uri'] = './data/hra_regression_data/Input/habitat_stressor_ratings_bad_attrib'

        self.assertRaises(hra.ImproperCriteriaAttributeName,
                        hra.execute, self.args)


