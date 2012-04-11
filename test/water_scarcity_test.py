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
        
        output_base = './data/test_out/hydropower_water_scarcity_uri/'
        input_dir = './data/hydropower_data/'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
        
        args = {}
        args['workspace_dir'] = input_dir
        args['lulc_uri'] = input_dir + 'test_input/landuse_90'
        args['watersheds_uri'] = input_dir + 'test_input/watersheds.shp'
        args['sub_watersheds_uri'] = input_dir + 'test_input/subwatersheds.shp'
        args['water_yield_vol_uri'] = \
            input_dir + 'water_scarcity/test_input/wyield_vol'
        args['water_yield_mean_uri'] = \
            input_dir + 'water_scarcity/test_input/wyield_mn'
        args['watershed_yield_table_uri'] = \
            input_dir + 'test_input/water_yield_watershed_input.csv'
        args['subwatershed_yield_table_uri'] = \
            input_dir + 'test_input/water_yield_subwatershed_input.csv'
        args['hydro_calibration_table_uri'] = \
            input_dir + 'test_input/hydro_calib_table.csv'
        args['demand_table_uri'] = input_dir + 'test_input/demand_table.csv'
        args['results_suffix'] = ''
        
        water_scarcity.execute(args)
        
        regression_dir = './data/hydropower_regression_data/'
        reg_consum_vol_uri = regression_dir + 'consum_vol_regression.tif'
        reg_consum_mn_uri = regression_dir + 'consum_mn_regression.tif'
        reg_rsup_vol_uri = regression_dir + 'rsup_vol_regression.tif'
        reg_rsup_mn_uri = regression_dir + 'rsup_mn_regression.tif'
        reg_cyield_vol_uri = regression_dir + 'cyield_vol_regression.tif'
        reg_ws_table_uri = regression_dir + 'ws_scarcity_table_regression.csv'
        reg_sws_table_uri = regression_dir + 'sws_scarcity_table_regression.csv'
        
        consum_vol_uri = output_base + 'Output/consum_vol.tif'
        consum_mn_uri = output_base + 'Output/consum_mn.tif'
        rsup_vol_uri = output_base + 'Output/rsup_vol.tif'
        rsup_mn_uri = output_base + 'Output/rsup_mn.tif'
        cyield_vol_uri = output_base + 'Output/cyield_vol.tif'
        ws_table_uri = output_base + 'Output/water_scarcity_watershed.csv'
        sws_table_uri = output_base + 'Output/water_scarcity_subwatershed.csv'
        
        invest_test_core.assertTwoDatasetEqualURI(self, reg_consum_vol_uri, 
                                                  consum_vol_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_consum_mn_uri, 
                                                  consum_mn_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_rsup_vol_uri, 
                                                  rsup_vol_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_rsup_mn_uri, 
                                                  rsup_mn_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_cyield_vol_uri, 
                                                  cyield_vol_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_ws_table_uri, 
                                              ws_table_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_sws_table_uri, 
                                              sws_table_uri)