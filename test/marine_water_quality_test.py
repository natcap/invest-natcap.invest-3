"""URI level tests for the marine water quality module"""

import unittest
import logging
import os

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.marine_water_quality import marine_water_quality_biophysical
import invest_test_core

LOGGER = logging.getLogger('marine_water_quality_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestMWQBiophysical(unittest.TestCase):
    """Main testing class for the MWQ biophysical tests"""
    def test_marine_water_quality_biophysical(self):
        output_base = './data/test_out/marine_water_quality_test/'
        input_dir = './data/marine_water_quality_data/'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
        
        args = {}
        args['workspace_dir'] = output_base
        
        
        marine_water_quality_biophysical.execute(args)
