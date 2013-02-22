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
        args['habitat_dir'] = './data/test_out/HRA/Input/HabitatLayers'
        args['stressors_dir'] = './data/test_out/HRA/Input/StressorLayers'
        args['exposure_crits' = ['intensity rating', 'management effectiveness']
        args['sensitivity_crits'] = 'temporal overlap rating', \
                    'frequency of disturbance']
        args['resiliance_crits'] = ['natural mortality', 'recruitment rate']
