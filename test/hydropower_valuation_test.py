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
    def test_hydropower_valuation_default_inputs(self):
        base = './invest-data/test/data/hydropower_data/test_input/'
        output_base = './invest-data/test/data/test_out/hydropower_valuation_default_inputs/'
        raise SkipTest        
        #Create the output directories
        if not os.path.isdir(output_base):
            os.mkdir(output_base)

        for folder_name in ['Output', 'Service', 'Intermediate']:
            folder_path = output_base + os.sep + folder_name
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
	
        args = {}
        args['workspace_dir'] = output_base 
        args['cyield_uri'] = base + 'cyield_vol.tif'
        args['watersheds_uri'] = base + 'watersheds.shp'
        args['sub_watersheds_uri'] = base + 'subwatersheds.shp'
        args['consump_uri'] = base + 'consum_vol.tif'
        args['watershed_scarcity_table_uri'] = \
            base + 'water_scarcity_watershed.csv'
        args['subwatershed_scarcity_table_uri'] = \
            base + 'water_scarcity_subwatershed.csv'
        args['valuation_table_uri'] = \
            base + 'hydro_valuation_table.csv'
        args['results_suffix'] = ''
        
        hydropower_valuation.execute(args)

    def test_hydropower_valuation_re(self):
        base = './invest-data/test/data/hydropower_regression_data/'
        output_base = './invest-data/test/data/test_out/hydropower_valuation_uri/'
        
        #Create the output directories
        if not os.path.isdir(output_base):
            os.mkdir(output_base)

        for folder_name in ['Output', 'Service', 'Intermediate']:
            folder_path = output_base + os.sep + folder_name
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
	
        args = {}
        args['workspace_dir'] = output_base 
        args['cyield_uri'] = base + 'cyield_vol.tif'
        args['watersheds_uri'] = base + 'hydro_regression_byhand/simple_reg_ws.shp'
        args['sub_watersheds_uri'] = base + 'hydro_regression_byhand/simple_reg_subws.shp'
        args['consump_uri'] = base + 'consum_vol.tif'
        args['watershed_scarcity_table_uri'] = \
            base + 'water_scarcity_watershed.csv'
        args['subwatershed_scarcity_table_uri'] = \
            base + 'water_scarcity_subwatershed.csv'
        args['valuation_table_uri'] = \
            base + 'hydropower_valuation.csv'
        args['results_suffix'] = ''
        
        hydropower_valuation.execute(args)
        
        regression_dir = './invest-data/test/data/hydropower_regression_data/'
        reg_hp_energy_uri = regression_dir + 'hp_energy.tif'
        reg_hp_val_uri = regression_dir + 'hp_val.tif'
        reg_hp_val_ws_uri = \
            regression_dir + 'hydropower_value_watershed.csv'
        reg_hp_val_sws_uri = \
            regression_dir + 'hydropower_value_subwatershed.csv'
        
        hp_energy_uri = output_base + 'Service/hp_energy.tif'
        hp_val_uri = output_base + 'Service/hp_val.tif'
        hp_val_ws_uri = output_base + 'Service/hydropower_value_watershed.csv'
        hp_val_sws_uri = \
            output_base + 'Service/hydropower_value_subwatershed.csv'
        
        invest_test_core.assertTwoDatasetEqualURI(self, reg_hp_energy_uri, 
                                                  hp_energy_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_hp_val_uri, 
                                                  hp_val_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_hp_val_ws_uri, 
                                              hp_val_ws_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_hp_val_sws_uri, 
                                              hp_val_sws_uri)

