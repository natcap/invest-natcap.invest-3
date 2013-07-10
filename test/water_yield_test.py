"""URI level tests for the water yield module"""

import unittest
import logging
import os

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.hydropower import water_yield
import invest_test_core

LOGGER = logging.getLogger('water_yield_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaterYield(unittest.TestCase):
    """Main testing class for the water yield tests"""
    def test_bonnie_water_yield(self):
        """This is a test that runs the water yield model with the default
           data given as input."""

        output_base = './invest-data/test/data/test_out/bonnie_water_yield_test/'
        input_dir = '../../InVEST_BLK/'
        
        args = {}
        args['workspace_dir'] = output_base
        args['lulc_uri'] = input_dir + 'smc_c_15n'
        args['soil_depth_uri'] = input_dir + 'soildepth_smn1.tif'
        args['precipitation_uri'] = input_dir + 'precip_663'
        args['pawc_uri'] = input_dir + 'AWC_SMN.tif'
        args['eto_uri'] = input_dir + 'pet_1011_4'
        args['watersheds_uri'] = input_dir + 'Watershed.shp'
        args['sub_watersheds_uri'] = input_dir + 'SubWatersheds.shp'
        args['biophysical_table_uri'] = \
            input_dir + 'biophys_2-22.csv'
        args['seasonality_constant'] = 79.0
        args['results_suffix'] = 'aa'
        
        water_yield.execute(args)

    def test_water_yield_default_inputs(self):
        """This is a test that runs the water yield model with the default
           data given as input."""

        raise SkipTest

        output_base = './invest-data/test/data/test_out/hydropower_water_yield_default_inputs/'
        input_dir = './invest-data/test/data/hydropower_data/test_input/'
        
        args = {}
        args['workspace_dir'] = output_base
        args['lulc_uri'] = input_dir + 'landuse_90/w001001.adf'
        args['soil_depth_uri'] = input_dir + 'soil_depth/w001001.adf'
        args['precipitation_uri'] = input_dir + 'precip/w001001.adf'
        args['pawc_uri'] = input_dir + 'pawc/w001001.adf'
        args['eto_uri'] = input_dir + 'eto/w001001.adf'
        args['watersheds_uri'] = input_dir + 'watersheds.shp'
        args['sub_watersheds_uri'] = input_dir + 'subwatersheds.shp'
        args['biophysical_table_uri'] = \
            input_dir + 'Biophysical_Models.csv'
        args['seasonality_constant'] = 5.0
        args['results_suffix'] = ''
        
        water_yield.execute(args)

    def test_water_yield_re(self):
        """This is a regression test for the water yield model that takes
           hand calculated input rasters and checks them against hand verified
           regression files."""

        raise SkipTest
        
        output_base = './invest-data/test/data/test_out/hydropower_water_yield_uri/'
        input_dir = './invest-data/test/data/hydropower_regression_data/hydro_regression_byhand/'
        
#        if not os.path.isdir(output_base):
#            os.makedirs(output_base)
        
        args = {}
        args['workspace_dir'] = output_base
        args['lulc_uri'] = input_dir + 'lulc.tif'
        args['soil_depth_uri'] = input_dir + 'soil_depth.tif'
        args['precipitation_uri'] = input_dir + 'precipitation.tif'
        args['pawc_uri'] = input_dir + 'pawc.tif'
        args['eto_uri'] = input_dir + 'eto.tif'
        args['watersheds_uri'] = input_dir + 'simple_reg_ws.shp'
        args['sub_watersheds_uri'] = input_dir + 'simple_reg_subws.shp'
        args['biophysical_table_uri'] = \
            input_dir + 'Biophysical_Models.csv'
        args['seasonality_constant'] = 5.0
        args['results_suffix'] = ''
        
        water_yield.execute(args)
        
        regression_dir = './invest-data/test/data/hydropower_regression_data/'
        reg_pixel_aet_uri = regression_dir + 'aet_pixel.tif'
        reg_pixel_fractp_uri = regression_dir + 'fractp_pixel.tif'
        reg_pixel_wyield_uri = regression_dir + 'wyield_pixel.tif'
        reg_fractp_mn_uri = regression_dir + 'fractp_mn.tif'
        reg_wyield_ha_uri = regression_dir + 'wyield_ha.tif'
        reg_wyield_vol_uri = regression_dir + 'wyield_vol.tif'
        reg_wyield_mn_uri = regression_dir + 'wyield_mn.tif'
        reg_aet_mn_uri = regression_dir + 'aet_mn.tif'
        reg_ws_table_uri = regression_dir + 'water_yield_watershed.csv'
        reg_sws_table_uri = regression_dir + 'water_yield_subwatershed.csv'
        
        pixel_aet_uri = output_base + 'Output/Pixel/aet.tif'
        pixel_fractp_uri = output_base + 'Output/Pixel/fractp.tif'
        pixel_wyield_uri = output_base + 'Output/Pixel/wyield.tif'
        fractp_mn_uri = output_base + 'Output/fractp_mn.tif'
        wyield_ha_uri = output_base + 'Service/wyield_ha.tif'
        wyield_vol_uri = output_base + 'Service/wyield_vol.tif'
        wyield_mn_uri = output_base + 'Service/wyield_mn.tif'
        aet_mn_uri = output_base + 'Output/aet_mn.tif'
        ws_table_uri = output_base + 'Output/water_yield_watershed.csv'
        sws_table_uri = output_base + 'Output/water_yield_subwatershed.csv'
        
        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_aet_uri, 
                                                  pixel_aet_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_fractp_uri, 
                                                  pixel_fractp_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_wyield_uri, 
                                                  pixel_wyield_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_fractp_mn_uri, 
                                                  fractp_mn_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_ha_uri, 
                                                  wyield_ha_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_vol_uri, 
                                                  wyield_vol_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_mn_uri, 
                                                  wyield_mn_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_aet_mn_uri, 
                                                  aet_mn_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_ws_table_uri, 
                                              ws_table_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_sws_table_uri, 
                                              sws_table_uri)
