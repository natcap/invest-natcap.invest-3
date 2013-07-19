'''Test module for the hra_scratch_preprocessor module.'''


import os
import logging
import unittest
import shutil
import glob
import json

from invest_natcap.habitat_risk_assessment import hra_preprocessor
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_PREPROCESSOR_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRAPreprocessor(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/test_out/HRA' 
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
