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
    def test_water_scarcity_default_inputs(self):
       

        raise SkipTest

        output_base = './invest-data/test/data/test_out/hydropower_water_scarcity_default_inputs/'
        input_dir = './invest-data/test/data/hydropower_data/test_input/'
        
        #Create the output directories
        if not os.path.isdir(output_base):
            os.mkdir(output_base)

        for folder_name in ['Output', 'Service', 'Intermediate']:
            folder_path = output_base + os.sep + folder_name
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
        
        args = {}
        args['workspace_dir'] = output_base
        args['lulc_uri'] = input_dir + 'landuse_90/w001001.adf'
        args['watersheds_uri'] = input_dir + 'watersheds.shp'
        args['sub_watersheds_uri'] = input_dir + 'subwatersheds.shp'
        args['water_yield_vol_uri'] = \
            input_dir + 'wyield_vol.tif'
        args['water_yield_mean_uri'] = \
            input_dir + 'wyield_mn.tif'
        args['watershed_yield_table_uri'] = \
            input_dir + 'water_yield_watershed.csv'
        args['subwatershed_yield_table_uri'] = \
            input_dir + 'water_yield_subwatershed.csv'
        args['hydro_calibration_table_uri'] = \
            input_dir + 'hydro_calib_table.csv'
        args['demand_table_uri'] = input_dir + 'demand_table.csv'
        args['results_suffix'] = ''
        
        water_scarcity.execute(args)
    
    def test_water_scarcity_re(self):
        
        output_base = './invest-data/test/data/test_out/hydropower_water_scarcity_uri/'
        input_dir = './invest-data/test/data/hydropower_regression_data/'
        
        #Create the output directories
        if not os.path.isdir(output_base):
            os.mkdir(output_base)

        for folder_name in ['Output', 'Service', 'Intermediate']:
            folder_path = output_base + os.sep + folder_name
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
        
        args = {}
        args['workspace_dir'] = output_base
        args['lulc_uri'] = input_dir + 'hydro_regression_byhand/lulc.tif'
        args['watersheds_uri'] = input_dir + 'hydro_regression_byhand/simple_reg_ws.shp'
        args['sub_watersheds_uri'] = input_dir + 'hydro_regression_byhand/simple_reg_subws.shp'
        args['water_yield_vol_uri'] = \
            input_dir + 'wyield_vol.tif'
        args['water_yield_mean_uri'] = \
            input_dir + 'wyield_mn.tif'
        args['watershed_yield_table_uri'] = \
            input_dir + 'water_yield_watershed.csv'
        args['subwatershed_yield_table_uri'] = \
            input_dir + 'water_yield_subwatershed.csv'
        args['hydro_calibration_table_uri'] = \
            input_dir + 'hydropower_calibration.csv'
        args['demand_table_uri'] = input_dir + 'water_demand.csv'
        args['results_suffix'] = ''
        
        water_scarcity.execute(args)
        
        regression_dir = './invest-data/test/data/hydropower_regression_data/'
        reg_consum_vol_uri = regression_dir + 'consum_vol.tif'
        reg_consum_mn_uri = regression_dir + 'consum_mn.tif'
        reg_rsup_vol_uri = regression_dir + 'rsup_vol.tif'
        reg_rsup_mn_uri = regression_dir + 'rsup_mn.tif'
        reg_cyield_vol_uri = regression_dir + 'cyield_vol.tif'
        reg_ws_table_uri = regression_dir + 'water_scarcity_watershed.csv'
        reg_sws_table_uri = regression_dir + 'water_scarcity_subwatershed.csv'
        
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
