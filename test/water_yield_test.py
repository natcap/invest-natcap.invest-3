"""URI level tests for the water yield module"""

import unittest
import logging
import os

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.hydropower import water_yield
import invest_cython_core
import invest_test_core

LOGGER = logging.getLogger('water_yield_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaterYield(unittest.TestCase):
    """Main testing class for the water yield tests"""
    def test_water_yield_re(self):
        base = './data/hydropower_data/'
        args = {}
        args['workspace_dir'] = base
        args['lulc_uri'] = base + 'test_input/landuse_90'
        args['soil_depth_uri'] = base + 'test_input/soil_depth'
        args['precipitation_uri'] = base + 'test_input/precip'
        args['pawc_uri'] = base + 'test_input/pawc'
        args['ape_uri'] = base + 'test_input/eto'
        args['watersheds_uri'] = base + 'test_input/watersheds.shp'
        args['sub_watersheds_uri'] = base + 'test_input/subwatersheds.shp'
        args['biophysical_table_uri'] = \
            base + 'test_input/Biophysical_Models.csv'
        args['zhang'] = 7.0
        
        water_yield.execute(args)