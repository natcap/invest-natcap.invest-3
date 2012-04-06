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
        base = './data/hydropower_data/'
        args = {}
        args['workspace_dir'] = base
        args['lulc_uri'] = base + 'test_input/landuse_90'
        args['watersheds_uri'] = base + 'test_input/watersheds.shp'
        args['sub_watersheds_uri'] = base + 'test_input/subwatersheds.shp'
        args['water_yield_vol_uri'] = base + 'water_scarcity/test_input/wyield_vol'
        args['water_yield_mean_uri'] = base + 'water_scarcity/test_input/wyield_mn'
        args['watershed_yield_table_uri'] = base + 'test_input/water_yield_watershed_input.csv'
        args['subwatershed_yield_table_uri'] = base + 'test_input/water_yield_subwatershed_input.csv'
        args['hydro_calibration_table_uri'] = base + 'test_input/hydro_calib_table.csv'
        args['demand_table_uri'] = base + 'test_input/demand_table.csv'
        args['results_suffix'] = ''
        
        water_scarcity.execute(args)