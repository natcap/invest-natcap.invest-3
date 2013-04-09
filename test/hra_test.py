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

#    def test_run_zero_buffer(self):

 #       self.args['buffer_dict'] = {'FinfishAquacultureComm': 0}

  #      hra.execute(self.args)

'''    def test_dict(self):

        #Need to make a copy so that we have something to pass when we check
        #out the raster dictionary creation by itself. However, we have to run
        #the whole thing first so that the rasterized versions of the shapefiles
        #exist in the first place.
        dict_orig = copy.deepcopy(self.args['ratings'])

        #This is just checking whether or not it is erroring anywhere in HRA
        hra.execute(self.args)
        
        #This should pull out the ratings dictionary, and check it against our
        #pre-populated one with the open raster datasets. Need to do a 
        #dictionary check and a raster compare.
        inter_dir = os.path.join(self.args['workspace_dir'], 'Intermediate')
        h_dir = os.path.join(inter_dir, 'Habitat_Rasters')
        s_dir = os.path.join(inter_dir, 'Stressor_Rasters')
        
        model_raster_dict = hra.combine_hs_rasters(inter_dir, h_dir, s_dir, dict_orig)

        #test_raster_dict = INSERT PRE-CREATED DICTIONARY HERE '''

    def test_ImproperAOIAttrib_exception(self):
        '''Want to check that if this model run contains an AOI, that we have a
        'name' attribute in each of the AOI features. If this is not true, it
        should raise an ImproperAOIAttributeName exception. We will use a
        seperate improperly named AOI file for these purposes.
        '''

        self.args['aoi_tables'] = './data/hra_regression_data/Input/subregions_incorrect.shp'

        self.assertRaises(hra_core.ImproperAOIAttributeName,
                        hra_core.execute, self.args)

    def test_ImproperCritAttrib_exception(self):
        '''Want to check that if this model uses shapefile criteria, that each 
        of them contains an attribute of 'name'. Currently, this is case
        sensitive. After the fact, it can be changed. If this is not existant, it
        should raise an ImproperCriteriaAttributeName exception. We will use a
        seperate improperly named shape criteria file for these purposes.
        '''

        self.args['aoi_tables'] = './data/hra_regression_data/Input/subregions_incorrect.shp'

        self.assertRaises(hra_core.ImproperAOIAttributeName,
                        hra_core.execute, self.args)


