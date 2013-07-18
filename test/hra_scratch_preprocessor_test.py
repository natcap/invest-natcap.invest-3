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

