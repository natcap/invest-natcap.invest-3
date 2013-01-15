"""URI level tests for the wind_energy uri handler module"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_uri_handler
import invest_test_core

class TestWindEnergyUriHandler(unittest.TestCase):
    def test_wind_energy_uri_handler_no_val(self):
        """Regression test for the uri handler given no valuation arguments"""
        #raise SkipTest
        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/uri_handler/'
        
        bathymetry_uri = os.path.join(input_dir, 'testing_dem.tif')

        land_uri = os.path.join(input_dir, 'testing_land.shp')
        
        output_dir = './data/test_out/wind_energy/uri_handler/no_val/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = bathymetry_uri
        args['land_uri'] = land_uri
        args['hub_height']  = 50 
        args['pwr_law_exponent'] = 0.11
        args['cut_in_wspd'] = 4.0
        args['rated_wspd'] = 14.0
        args['cut_out_wspd'] = 25.0
        args['turbine_rated_pwr'] = 3.6
        args['exp_out_pwr_curve'] = 2 
        args['num_days'] = 365
        args['air_density'] = 1.225 
        args['min_depth'] = 25
        args['max_depth'] = 200

        wind_energy_uri_handler.execute(args)

        shape_file_names = ['wind_points_shape.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif']

        raster_file_output_names = ['harvested_energy.tif', 'density.tif']

        for file_name in shape_file_names:
            reg_file = os.path.join(
                    regression_dir, 'global/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'global/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'global/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
   
    def test_wind_energy_uri_handler_val(self):
        """Regression test for the uri handler given valuation arguments"""
        #raise SkipTest
        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/uri_handler/'
        
        bathymetry_uri = os.path.join(input_dir, 'testing_dem.tif')

        land_uri = os.path.join(input_dir, 'testing_land.shp')
        
        output_dir = './data/test_out/wind_energy/uri_handler/no_val/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = bathymetry_uri
        args['land_uri'] = land_uri
        args['hub_height']  = 50 
        args['pwr_law_exponent'] = 0.11
        args['cut_in_wspd'] = 4.0
        args['rated_wspd'] = 14.0
        args['cut_out_wspd'] = 25.0
        args['turbine_rated_pwr'] = 3.6
        args['exp_out_pwr_curve'] = 2 
        args['num_days'] = 365
        args['air_density'] = 1.225 
        args['min_depth'] = 25
        args['max_depth'] = 200

        wind_energy_uri_handler.execute(args)

        shape_file_names = ['wind_points_shape.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif']

        raster_file_output_names = ['harvested_energy.tif', 'density.tif']

        for file_name in shape_file_names:
            reg_file = os.path.join(
                    regression_dir, 'global/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'global/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'global/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
