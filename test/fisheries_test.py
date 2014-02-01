'''This will be the test module for the non-core portion of Fisheries.'''

import os
import logging
import glob
import filecmp
from nose.plugins.skip import SkipTest

import invest_natcap.testing

from invest_natcap.fisheries import fisheries

LOGGER = logging.getLogger('fisheries_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRA(invest_natcap.testing.GISTest):

    def test_main_csv_parse(self):
        raise SkipTest
        '''Want to make sure that the main CSV parsing function is working as
        expected. Should run through fine on the sample CSV, but throw errors
        for both types of incorrect parameter names.'''

        shrimp_correct = './invest-data/test/data/fisheries/CSVs/shrimp_correct.csv'  
        shrimp_bad_area = './invest-data/test/data/fisheries/CSVs/shrimp_bad_area.csv'  
        shrimp_bad_stage = './invest-data/test/data/fisheries/CSVs/shrimp_bad_stage.csv'  
        
        lobster_multi_area = './invest-data/test/data/fisheries/CSVs/lobster_multi_area.csv'

        shrimp_area_count = 1
        lobster_area_count = 9
        
        #Smoke test the single area and multi area files.
        fisheries.parse_main_csv(shrimp_correct, shrimp_area_count, 'Fixed')
        dictionary = fisheries.parse_main_csv(lobster_multi_area, lobster_area_count, 'Beverton-Holt')

        #Check that exceptions are properly raised when expected.
        self.assertRaises(fisheries.ImproperStageParameter,
                        fisheries.parse_main_csv, shrimp_bad_stage, shrimp_area_count, 'Fixed')

        self.assertRaises(fisheries.ImproperAreaParameter,
                        fisheries.parse_main_csv, shrimp_bad_area, shrimp_area_count, 'Fixed')
    
    def test_recruitment_errors(self):
        '''One of the first things we want to check is whether the necessary
        parameters for recruitment (based on the user-selected recruitment
        equation) exist within args. Test that it's throwing errors when
        expected for args sets that don't contain what we want.
        '''
        
        args = {}
        args['workspace_uri'] = './invest-data/test/data/test_out/fisheries'

        #Test B-H, Ricker
        for equation in ['Beverton-Holt', 'Ricker']:
            args['rec_eq'] = equation

            self.assertRaises(fisheries.MissingRecruitmentParameter,
                            fisheries.execute, args)

        #Test Fecundity
        args['rec_eq'] = 'Fecundity'

        self.assertRaises(fisheries.MissingRecruitmentParameter,
                        fisheries.execute, args)

        #Test Fixed Recruitment
        args['rec_eq'] = 'Fixed'

        self.assertRaises(fisheries.MissingRecruitmentParameter,
                        fisheries.execute, args)

    def test_age_no_gender_smoke(self):

        #Going to use Blue Crab for testing.
        args = {}
        args['workspace_uri'] = './invest-data/test/data/test_out/fisheries'
        args['aoi_uri'] = './invest-data/test/data/fisheries/BC_temp_aoi.shp'
        args['class_params_uri'] = './invest-data/Fisheries/Input/blue_crab_main_params.csv'
        args['maturity_type'] = "Age Specific"
        args['num_classes'] = 4
        args['is_gendered'] = False
        args['rec_eq'] = "Ricker"
        args['alpha'] = 6050000
        args['beta'] = 0.00000004140
        args['init_recruits'] = 200000
        args['duration'] = 100

        fisheries.execute(args)

    def test_age_gendered_smoke(self):

        args = {}
        args['workspace_uri'] = './invest-data/test/data/test_out/fisheries'
        args['aoi_uri'] = './invest-data/Fisheries/Input/DC_HoodCanal_Subregions.shp'
        args['class_params_uri'] = './invest-data/Fisheries/Input/dungeness_crab_main_params.csv'
        args['maturity_type'] = "Age Specific"
        #Are counting each gender/age combo as an age class?
        args['num_classes'] = 10
        args['is_gendered'] = True
        args['rec_eq'] = "Ricker"
        args['alpha'] = 2000000
        args['beta'] = 0.00000030912
        args['init_recruits'] = 2249339326901.15
        args['duration'] = 100

        fisheries.execute(args)
    
    def test_stage_no_gender_smoke(self):
       
        args = {}
        args['workspace_uri'] = './invest-data/test/data/test_out/fisheries'
        args['aoi_uri'] = './invest-data/test/data/fisheries/BC_temp_aoi.shp'
        args['class_params_uri'] = './invest-data/Fisheries/Input/white_shrimp_main_params.csv'
        args['maturity_type'] = "Stage Specific"
        #Are counting each gender/age combo as an age class?
        args['num_classes'] = 5
        args['is_gendered'] = False
        args['rec_eq'] = "Fixed"
        args['fix_param'] = 216000000000
        args['init_recruits'] = 100000
        args['duration'] = 300

        fisheries.execute(args)
        
