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
    def test_parser(self):
        
#For purposes of running test independently of HRA non-core, need to
        #delete current intermediate and output folders

        uri_to_workspace = os.path.join('data','hra_preprocessor_data')
        hra_props = hra_preprocessor.parse_hra_tables(uri_to_workspace)
        LOGGER.debug(hra_props)
