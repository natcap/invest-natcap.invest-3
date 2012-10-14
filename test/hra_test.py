'''This will be the test module for the non-core portion of Habitat Risk
Assessment.'''

import os
import unittest
import logging

import invest_test_core

from invest_natcap.habitat_risk_assessment import hra_core
from invest_natcap.habitat_risk_assessment import hra

LOGGER = logging.getLogger('hra_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRACore(unittest.TestCase):

    def setUp(self):

        args = {}
        args['workspace_dir'] = './data/test_out/HRA' 
        args['habitat_dir'] = '../../HabitatRiskAssess/Input/HabitatLayers'
        args['stressors_dir'] = '../../HabitatRiskAssess/Input'
