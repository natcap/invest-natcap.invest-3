'''This will be the test module for the hra_core module.'''

import os
import logging
import unittest
import shutil

from invest_natcap.habitat_risk_assessment import hra_preprocessor
from osgeo import gdal, ogr

LOGGER = logging.getLogger('HRA_CORE_TEST')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRAPreprocessor(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = './data/test_out/HRA' 
        args['stressors_dir'] = './data/test_out/HRA/Input/StressorLayers'
        args['exposure_crits' = ['intensity rating', 'management effectiveness']
        args['sensitivity_crits'] = 'temporal overlap rating', \
                    'frequency of disturbance']
        args['resiliance_crits'] = ['natural mortality', 'recruitment rate']
    
        self.args = args

    def test_HabsOnly_NoShapes_smoke(self):
    '''This will use only the habitats directory as an input to overlap
    stressors, and won't attempt to pull in shapefile criteria.'''

        self.args['do_species'] = False
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'
        self.args['do_shapes'] = False

        hra_preprocessor.execute(self.args)

    def test_HabsSpecies_NoShapes_smoke(self):

        self.args['do_species'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/SpeciesLayers'
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'
        self.args['do_shapes'] = False

        hra_preprocessor.execute(self.args)

    def test_Missing_HabsSpecies_exception(self):
    '''Want to make sure that if neither a habitat or species is selected for
    use in overlap, that it throws an error. Should raise a 
    MissingHabitatOrSpecies exception.'''

        self.args['do_species'] = False
        self.args['do_habitats'] = False

        self.assertRaises(hra_preprocessor.MissingHabitatOrSpecies,
                        hra_preprocessor.execute, self.args)

    def test_NotEnoughCriteria_exception(self):
    '''Want to make sure that if we have at least 4 or more criteria passed
    within our 3 criteria type lists. Should raise a NotEnoughCriteria 
    exception.'''

        self.args['do_species'] = False
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'

        #Since we had 6 crits to begin with, remove one from each should leave
        #us with 3, want to make sure this causes to error.
        for c_list in (self.args['resiliance_crits'], 
                    self.args['sensitivity_crits'],
                    self.args['exposure_crits']):

            c_list.remove(c_list[0])


        self.assertRaises(hra_preprocessor.NotEngoughCriteria,
                        hra_preprocessor.execute, self.args)

    def test_ImproperCriteraSpread_exception(self):

        self.args['do_species'] = False
        self.args['do_habitats'] = True
        self.args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'

        self.args['resiliance_crits'] = []

        self.assertRaises(hra_preprocessor.ImproperCriteriaSpread,
                        hra_preprocessor.execute, self.args)

