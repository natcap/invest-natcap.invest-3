'''This will be the test module for the non-core portion of Fisheries.'''

import os
import logging
import glob
import filecmp

import invest_natcap.testing

from invest_natcap.fisheries import fisheries

LOGGER = logging.getLogger('fisheries_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRA(invest_natcap.testing.GISTest):

    def test_main_csv_parse(self):
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
        fisheries.parse_main_csv(shrimp_correct, shrimp_area_count)
        dictionary = fisheries.parse_main_csv(lobster_multi_area, lobster_area_count)

        #Check that exceptions are properly raised when expected.
        self.assertRaises(fisheries.ImproperStageParameter,
                        fisheries.parse_main_csv, shrimp_bad_stage, shrimp_area_count)

        self.assertRaises(fisheries.ImproperAreaParameter,
                        fisheries.parse_main_csv, shrimp_bad_area, shrimp_area_count)
    
    def test_recruitment_errors(self):
        '''One of the first things we want to check is whether the necessary
        parameters for recruitment (based on the user-selected recruitment
        equation) exist within args. Test that it's throwing errors when
        expected for args sets that don't contain what we want.
        '''
        
        args = {}
        args['workspace_uri'] = './invest-data/test/data/test_out/fisheries'

        args['beta'] = 1
        args['alpha'] = 1
        args['fix_param'] = 100
        #Eventually, we will have an actual fecundity CSV. For now, it just needs
        #to exist in args.
        args['fec_params_uri'] = \
            './invest-data/test/data/fisheries/CSVs/shrimp_correct.csv'  
        #Test B-H, Ricker
        for equation in ['Beverton-Holt', 'Ricker']:
            args['rec_eq'] = equation
            del args['alpha']

            self.assertRaises(fisheries.MissingRecruitmentParameter,
                            fisheries.execute, args)

        #Test Fecundity
        args['rec_eq'] = 'Fecundity'
        del args['fec_params_uri']

        self.assertRaises(fisheries.MissingRecruitmentParameter,
                        fisheries.execute, args)

        #Test Fixed Recruitment
        args['rec_eq'] = 'Fixed'
        del args['fix_param']

        self.assertRaises(fisheries.MissingRecruitmentParameter,
                        fisheries.execute, args)
