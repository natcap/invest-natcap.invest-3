"""URI level tests for the water scarcity module"""

import unittest
import logging
import os

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.hydropower import water_scarcity
import invest_cython_core
import invest_test_core

LOGGER = logging.getLogger('water_scarcity_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaterScarcity(unittest.TestCase):
    """Main testing class for the water scarcity tests"""
    def test_water_scarcity_re(self):
        base = './data/hydropower_data/water_scarcity'
        args = {}
        args['workspace_dir'] = base
        args['lulc_uri'] = base + 'test_input/landuse_90'
        args['watersheds_uri'] = base + 'test_input/watersheds.shp'
        args['sub_watersheds_uri'] = base + 'test_input/subwatersheds.shp'
        args['water_yield_vol_uri'] = base + 'test_input/'
        args['water_yield_mean_uri'] = base + 'test_input/'
        args['watershed_yield_table_uri'] = base + 'test_input/'
        args['subwatershed_yield_table_uri'] = base + 'test_input/'
        args['hydro_calibration_table_uri'] = base + 'test_input/'
        args['demand_table_uri'] = base + 'test_input/'
         
        water_scarcity.execute(args)