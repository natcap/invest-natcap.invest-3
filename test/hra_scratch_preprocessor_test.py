'''Test module for the hra_scratch_preprocessor module.'''


import os
import logging
import unittest
import shutil
import glob
import json

from invest_natcap.hra_scratch import hra_preprocessor
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_PREPROCESSOR_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRAPreprocessor(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA_Scratch' 
        args['stressors_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/StressorLayers'
        args['exposure_crits'] = ['management effectiveness', 'intensity_rating']
        args['sensitivity_crits'] = ['temporal overlap', \
                    'frequency of disturbance']
        args['resilience_crits'] = ['recruitment rate', 'natural mortality']
    
        self.args = args

    def test_HabsOnly_NoShapes_smoke(self):
        '''This will use only the habitats directory as an input to overlap
        stressors, and won't attempt to pull in shapefile criteria.'''

        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers'

        hra_preprocessor.execute(self.args)
    
    def test_HabsOnlyShape_smoke(self):
        '''This will use only the habitats directory as an input to overlap
        stressors, and will atempt to use a single shapefile criteria with
        eelgrass and recruitment rate.'''

        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers'
        self.args['criteria_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria'

        hra_preprocessor.execute(self.args)

    @unittest.skip("For later testing.")
    def test_HabsSpecies_NoShapes_smoke(self):

        self.args['species_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA/Input/SpeciesLayers'
        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers'

        hra_preprocessor.execute(self.args)

    def test_Missing_HabsSpecies_exception(self):
        '''Want to make sure that if neither a habitat or species is selected for
        use in overlap, that it throws an error. Should raise a 
        MissingHabitatOrSpecies exception.'''

        self.assertRaises(hra_preprocessor.MissingHabitatsOrSpecies,
                        hra_preprocessor.execute, self.args)
    
    def test_NotEnoughCriteria_exception(self):
        '''Want to make sure that if we have at least 4 or more criteria passed
        within our 3 criteria type lists. Should raise a NotEnoughCriteria 
        exception.'''

        self.args['habitats_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Input/HabitatLayers'

        #Since we had 6 crits to begin with, remove one from each should leave
        #us with 3, want to make sure this causes to error.
        for c_list in (self.args['resilience_crits'], 
                    self.args['sensitivity_crits'],
                    self.args['exposure_crits']):

            c_list.remove(c_list[0])

        self.assertRaises(hra_preprocessor.NotEnoughCriteria,
                        hra_preprocessor.execute, self.args)
    
    def test_Improper_Crit_FileStruct(self):
        '''Since the folder structure for the criteria shapefiles must be in an
        explicit form, want to check that it will error if given an incorrect
        folder setup.'''

        crit_uri = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria_Bad_Struct'

        self.assertRaises(IOError, hra_preprocessor.make_crit_shape_dict,
                    crit_uri)
    
    def test_make_crit_dict_regression(self):
        '''This should specifically test the make_crit_shape_dict function in
        hra_preprocessor. This will get called by both preprocessor and
        non-core. Want to check against the dictionary of what we think it
        should be.'''

        shp_crit_dir = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria'

        expected_dict = \
            {'h_s_e': {},
             'h': {'kelp':
                    {'recruitment rate': 
                        '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/Shape_Criteria/Resilience/kelp_recruitment_rate.shp'
                    }
                  },
             'h_s_c': {}
            }

        produced_dict = hra_preprocessor.make_crit_shape_dict(shp_crit_dir)

        self.maxDiff = None
        self.assertEqual(expected_dict, produced_dict)

    def test_UnexpectedString_exception(self):
        '''Want to make sure that preproc will throw an exception if a CSV is
        passed which contains strings or null values where there should be
        floats for use in calculation'''

        test_CSV = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/hra_regression_data/habitat_stressor_ratings_null_vals/kelp_ratings.csv'
        empty_dict = {}

        self.assertRaises(hra_preprocessor.UnexpectedString,
                        hra_preprocessor.parse_overlaps, test_CSV, empty_dict, 
                                                                    empty_dict, empty_dict)