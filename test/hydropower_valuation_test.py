"""URI level tests for the hydrowpower valuation module"""

import unittest
import logging
import os

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.hydropower import hydropower_valuation
import invest_cython_core
import invest_test_core

LOGGER = logging.getLogger('hydropower_valuation_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHydropowerValuation(unittest.TestCase):
    """Main testing class for the hydropower valuation tests"""
    def test_water_scarcity_re(self):
        base = './data/hydropower_data/'
        args = {}
        args['workspace_dir'] = base
        args['cal_water_yield'] = base + 'samp_input/cyield_vol.tif'
        args['watersheds_uri'] = base + 'test_input/watersheds.shp'
        args['sub_watersheds_uri'] = base + 'test_input/subwatersheds.shp'
        args['water_consump'] = base + 'samp_input/consum_vol.tif'
        args['watershed_scarcity_table_uri'] = \
            base + 'test_input/water_scarcity_watershed.csv'
        args['subwatershed_scarcity_table_uri'] = \
            base + 'test_input/water_scarcity_subwatershed.csv'
        args['valuation_table_uri'] = \
            base + 'test_input/hydro_valuation_table.csv'
        args['results_suffix'] = ''
        
        hydropower_valuation.execute(args)