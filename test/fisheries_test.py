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

class TestFisheries(invest_natcap.testing.GISTest):

    def test_main_csv_parse(self):
        '''Want to make sure that the main CSV parsing function is working as
        expected. Should run through fine on the sample CSV, but throw errors
        for both types of incorrect parameter names.'''

        shrimp_correct = './invest-data/test/data/fisheries/CSVs/shrimp_correct.csv'  
        shrimp_bad_area = './invest-data/test/data/fisheries/CSVs/shrimp_bad_area.csv'  
        shrimp_bad_stage = './invest-data/test/data/fisheries/CSVs/shrimp_bad_stage.csv'  
        
        lobster_multi_area = './invest-data/test/data/fisheries/CSVs/lobster_multi_area.csv'

        #All the files missing area or stage parameters
        shrimp_no_dur = './invest-data/test/data/fisheries/CSVs/shrimp_missing_duration.csv'
        bc_no_mat = './invest-data/test/data/fisheries/CSVs/blue_crab_missing_mat.csv'
        shrimp_no_weight = './invest-data/test/data/fisheries/CSVs/shrimp_missing_weight.csv'
        bc_no_vuln = './invest-data/test/data/fisheries/CSVs/blue_crab_missing_vuln.csv'
        bc_no_exploit = './invest-data/test/data/fisheries/CSVs/blue_crab_missing_vuln.csv'

        bc_area_count = 1
        shrimp_area_count = 1
        lobster_area_count = 9
        
        #Smoke test the single area and multi area files.
        fisheries.parse_main_csv(shrimp_correct, shrimp_area_count, 'Fixed', True, 'Stage Specific')
        dictionary = fisheries.parse_main_csv(lobster_multi_area, 
                            lobster_area_count, 'Beverton-Holt', True, 'Age Specific')

        #Check that exceptions are properly raised when expected.
        self.assertRaises(fisheries.ImproperStageParameter,
                        fisheries.parse_main_csv, shrimp_bad_stage, 
                            shrimp_area_count, 'Fixed', True, 'Stage Specific')

        self.assertRaises(fisheries.ImproperAreaParameter,
                        fisheries.parse_main_csv, shrimp_bad_area, 
                        shrimp_area_count, 'Fixed', True, 'Age Specific')
  
        #Exception raises for all the missing stage/area columns. 
        self.assertRaises(fisheries.MissingParameter,
                        fisheries.parse_main_csv, shrimp_no_dur, 
                        shrimp_area_count, 'Fixed', True, 'Stage Specific')
        self.assertRaises(fisheries.MissingParameter,
                        fisheries.parse_main_csv, shrimp_no_weight, 
                        shrimp_area_count, 'Fixed', True, 'Stage Specific')
        self.assertRaises(fisheries.MissingParameter,
                        fisheries.parse_main_csv, bc_no_mat, 
                        bc_area_count, 'Ricker', True, 'Age Specific')
        self.assertRaises(fisheries.MissingParameter,
                        fisheries.parse_main_csv, bc_no_vuln, 
                        bc_area_count, 'Ricker', True, 'Age Specific')
        self.assertRaises(fisheries.MissingParameter,
                        fisheries.parse_main_csv, bc_no_exploit, 
                        bc_area_count, 'Ricker', True, 'Age Specific')

    def test_fecundity_csv_parse(self):
       '''Since none of the models currently use fecundity for their
       recruitment, need to test to make sure that it actually parses the way I
       think it should.'''

       csv_uri = './invest-data/test/data/fisheries/CSVs/shrimp_fecundity_test.csv'

       dictionary = fisheries.parse_fec_csv(csv_uri)

       LOGGER.debug(dictionary)

    def test_recruitment_errors(self):
        '''One of the first things we want to check is whether the necessary
        parameters for recruitment (based on the user-selected recruitment
        equation) exist within args. Test that it's throwing errors when
        expected for args sets that don't contain what we want.
        '''
        
        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/fisheries'

        #Test B-H, Ricker
        for equation in ['Beverton-Holt', 'Ricker']:
            args['rec_eq'] = equation

            self.assertRaises(fisheries.MissingParameter,
                            fisheries.execute, args)

        #Test Fecundity
        args['rec_eq'] = 'Fecundity'

        self.assertRaises(fisheries.MissingParameter,
                        fisheries.execute, args)

        #Test Fixed Recruitment
        args['rec_eq'] = 'Fixed'

        self.assertRaises(fisheries.MissingParameter,
                        fisheries.execute, args)

    def test_age_no_gender_smoke(self):
        #Going to use Blue Crab for testing.
        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/fisheries'
        args['aoi_uri'] = './invest-data/Fisheries/Input/Galveston_Subregion.shp'
        args['class_params_uri'] = './invest-data/Fisheries/Input/blue_crab_main_params.csv'
        args['maturity_type'] = "Age Specific"
        args['hrv_type'] = 'Numbers'
        args['num_classes'] = 4
        args['is_gendered'] = False
        args['rec_eq'] = "Ricker"
        args['alpha'] = 6050000
        args['beta'] = 0.00000004140
        args['init_recruits'] = 200000
        args['duration'] = 100

        fisheries.execute(args)

    def test_age_gendered_smoke(self):
        #Using DC for gendered testing.
        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/fisheries'
        args['aoi_uri'] = './invest-data/Fisheries/Input/DC_HoodCanal_Subregions.shp'
        args['class_params_uri'] = './invest-data/Fisheries/Input/dungeness_crab_main_params.csv'
        args['maturity_type'] = "Age Specific"
        args['hrv_type'] = 'Numbers'
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
        #Using white shrimp for stage testing.
        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/fisheries'
        args['aoi_uri'] = './invest-data/Fisheries/Input/Galveston_Subregion.shp'
        args['class_params_uri'] = './invest-data/Fisheries/Input/white_shrimp_main_params.csv'
        args['maturity_type'] = "Stage Specific"
        args['hrv_type'] = 'Weight'
        #Are counting each gender/age combo as an age class?
        args['num_classes'] = 5
        args['is_gendered'] = False
        args['rec_eq'] = "Fixed"
        args['fix_param'] = 216000000000
        args['init_recruits'] = 100000
        args['duration'] = 300

        fisheries.execute(args)

    def test_age_no_gender_migration(self):
        #Using lobster to test a model which uses migration.
        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/fisheries'
        args['aoi_uri'] = './invest-data/Fisheries/Input/Lob_Belize_Subregions.shp'
        args['class_params_uri'] = './invest-data/Fisheries/Input/caribbean_spiny_lobster_main_params.csv'
        args['maturity_type'] = "Age Specific"
        args['hrv_type'] = 'Weight'
        args['num_classes'] = 8
        args['is_gendered'] = False
        args['rec_eq'] = "Beverton-Holt"
        args['alpha'] = 5770000
        args['beta'] = 2885000
        args['init_recruits'] = 4686959.42894736
        args['mig_params_uri'] = './invest-data/Fisheries/Input/Caribbean_Spiny_Lobster_migration'
        args['frac_post_process'] = 0.286332579995172
        args['unit_price'] = 29.9320213844594
        args['duration'] = 100

        fisheries.execute(args)

