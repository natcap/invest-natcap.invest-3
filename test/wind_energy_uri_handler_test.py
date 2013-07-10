"""URI level tests for the wind_energy uri handler module"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_uri_handler
import invest_test_core

class TestWindEnergyUriHandler(unittest.TestCase):
    def test_wind_energy_uri_handler_no_options(self):
        """Regression test for the uri handler given no optional arguments"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/no_options/'
        output_dir = './invest-data/test/data/test_out/wind_energy/uri_handler/no_options/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['number_of_machines'] = 60
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = False
        #args['land_polygon_uri'] = os.path.join(input_dir, 'testing_land.shp')
        #args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        #args['min_distance'] = 1000
        #args['max_distance'] = 50000
        #args['grid_points_uri'] = 
        #args['foundation_cost'] = 2
        #args['dollar_per_kWh'] = .187
        #args['discount_rate'] = .116
        #args['avg_grid_distance'] = 4
        #args['suffix'] = ''

        wind_energy_uri_handler.execute(args)

        shape_file_output_names = ['wind_energy_points.shp',
                'example_size_and_orientation_of_a_possible_wind_farm.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif']

        raster_file_output_names = ['harvested_energy_MWhr_per_yr.tif', 'density_W_per_m2.tif']

        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
   
    def test_wind_energy_uri_handler_aoi(self):
        """Regression test for the uri handler given aoi as the only optional
            argument"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/aoi_option/'
        output_dir = './invest-data/test/data/test_out/wind_energy/uri_handler/aoi_option/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['number_of_machines'] = 60
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = False
        #args['suffix'] = ''

        wind_energy_uri_handler.execute(args)

        shape_file_intermediate_names = [
                'aoi_proj_to_bath.shp', 'aoi_proj_to_wind_points.shp', 
                'wind_energy_points_from_dat.shp', 'wind_points_clipped.shp']
        
        shape_file_output_names = ['wind_energy_points.shp',
                'example_size_and_orientation_of_a_possible_wind_farm.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_projected.tif']

        raster_file_output_names = ['harvested_energy_MWhr_per_yr.tif', 'density_W_per_m2.tif']

        for file_name in shape_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

    def test_wind_energy_uri_handler_aoi_land_options(self):
        """Regression test for the uri handler given the aoi and land polygon
            optional arguments"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/aoi_land_options/'
        output_dir = './invest-data/test/data/test_out/wind_energy/uri_handler/aoi_land_options/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['land_polygon_uri'] = os.path.join(input_dir, 'testing_land.shp')
        args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['number_of_machines'] = 60
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = False
        #args['grid_points_uri'] = 
        #args['foundation_cost'] = 2
        #args['dollar_per_kWh'] = .187
        #args['discount_rate'] = .116
        #args['avg_grid_distance'] = 4
        #args['suffix'] = ''
        #args['min_distance'] = 
        #args['max_distance'] = 

        wind_energy_uri_handler.execute(args)

        shape_file_intermediate_names = [
                'aoi_proj_to_bath.shp', 'aoi_proj_to_wind_points.shp', 
                'wind_energy_points_from_dat.shp', 'wind_points_clipped.shp']
        
        shape_file_output_names = ['wind_energy_points.shp',
                'example_size_and_orientation_of_a_possible_wind_farm.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_projected.tif']

        raster_file_output_names = ['harvested_energy_MWhr_per_yr.tif', 'density_W_per_m2.tif']

        for file_name in shape_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

    def test_wind_energy_uri_handler_dist_options(self):
        """Regression test for the uri handler given the aoi, land polygon,
            and distance optional arguments"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/dist_options/'
        output_dir = './invest-data/test/data/test_out/wind_energy/uri_handler/dist_options/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['land_polygon_uri'] = os.path.join(input_dir, 'testing_land.shp')
        args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['number_of_machines'] = 60
        args['min_distance'] = 1000
        args['max_distance'] = 20000
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = False
        #args['grid_points_uri'] = 
        #args['foundation_cost'] = 2
        #args['dollar_per_kWh'] = .187
        #args['discount_rate'] = .116
        #args['avg_grid_distance'] = 4
        #args['suffix'] = ''

        wind_energy_uri_handler.execute(args)

        shape_file_intermediate_names = [
                'aoi_proj_to_bath.shp', 'aoi_proj_to_wind_points.shp', 
                'wind_energy_points_from_dat.shp', 'wind_points_clipped.shp',
                'aoi_proj_to_land.shp', 'land_poly_clipped.shp',
                'land_poly_projected.shp']
        
        shape_file_output_names = ['wind_energy_points.shp',
                'example_size_and_orientation_of_a_possible_wind_farm.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_projected.tif',
                'aoi_raster.tif']

        raster_file_output_names = ['harvested_energy_MWhr_per_yr.tif', 'density_W_per_m2.tif']

        for file_name in shape_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

    def test_wind_energy_uri_handler_val_land_options(self):
        """Regression test for the uri handler given the aoi, land polygon,
            optional arguments"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/val_land_options/'
        output_dir = './invest-data/test/data/test_out/wind_energy/uri_handler/val_land_options/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['land_polygon_uri'] = os.path.join(input_dir, 'testing_land.shp')
        args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = True
        args['foundation_cost'] = 2
        args['number_of_machines'] = 60
        args['dollar_per_kWh'] = .187
        args['discount_rate'] = .116
        args['avg_grid_distance'] = 4
        #args['suffix'] = ''
        #args['grid_points_uri'] = 
        #args['min_distance'] = 1000
        #args['max_distance'] = 20000

        wind_energy_uri_handler.execute(args)

        shape_file_intermediate_names = [
                'aoi_proj_to_bath.shp', 'aoi_proj_to_wind_points.shp', 
                'wind_energy_points_from_dat.shp', 'wind_points_clipped.shp',
                'val_aoi_proj_to_land_poly.shp', 'val_land_poly_clipped.shp',
                'val_land_poly_projected.shp']
        
        shape_file_output_names = [
                'wind_energy_points.shp', 
                'example_size_and_orientation_of_a_possible_wind_farm.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_projected.tif']

        raster_file_output_names = [
                'harvested_energy_MWhr_per_yr.tif', 'density_W_per_m2.tif', 'levelized_cost_price_per_kWh.tif',
                'npv_US_millions.tif', 'carbon_emissions_tons.tif']

        for file_name in shape_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

    def test_wind_energy_uri_handler_val_grid_options(self):
        """Regression test for the uri handler given the aoi and grid point
            optional arguments"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/val_grid_options/'
        output_dir = './invest-data/test/data/test_out/wind_energy/uri_handler/val_grid_options/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = True
        args['foundation_cost'] = 2
        args['number_of_machines'] = 60
        args['dollar_per_kWh'] = .187
        args['discount_rate'] = .116
        args['avg_grid_distance'] = 4
        args['grid_points_uri'] = os.path.join(
                input_dir, 'testing_grid_points.csv') 
        #args['land_polygon_uri'] = os.path.join(input_dir, 'testing_land.shp')
        #args['suffix'] = ''
        #args['min_distance'] = 1000
        #args['max_distance'] = 20000

        wind_energy_uri_handler.execute(args)

        shape_file_intermediate_names = [
                'aoi_proj_to_bath.shp', 'aoi_proj_to_wind_points.shp', 
                'wind_energy_points_from_dat.shp', 'wind_points_clipped.shp',
                'aoi_proj_to_grid_points.shp', 'grid_point_clipped.shp',
                'aoi_proj_to_land_points.shp','grid_point_projected.shp',
                'land_point_clipped.shp', 'land_point_projected.shp',
                'val_land_points.shp', 'val_grid_points.shp']
        
        shape_file_output_names = [
                'wind_energy_points.shp', 
                'example_size_and_orientation_of_a_possible_wind_farm.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_projected.tif']

        raster_file_output_names = [
                'harvested_energy_MWhr_per_yr.tif', 'density_W_per_m2.tif', 'levelized_cost_price_per_kWh.tif',
                'npv_US_millions.tif', 'carbon_emissions_tons.tif']

        for file_name in shape_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
    
    def test_wind_energy_uri_handler_val_dist_land_options(self):
        """Regression test for the uri handler given the aoi, land polygon,
            and distance optional arguments"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/val_dist_land_options/'
        output_dir = './invest-data/test/data/test_out/wind_energy/uri_handler/val_dist_land_options/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = True
        args['foundation_cost'] = 2
        args['number_of_machines'] = 60
        args['dollar_per_kWh'] = .187
        args['discount_rate'] = .116
        args['avg_grid_distance'] = 4
        args['land_polygon_uri'] = os.path.join(input_dir, 'testing_land.shp')
        args['min_distance'] = 1000
        args['max_distance'] = 20000
        #args['suffix'] = ''
        #args['grid_points_uri'] = os.path.join(
        #        input_dir, 'testing_grid_points.csv') 

        wind_energy_uri_handler.execute(args)

        shape_file_intermediate_names = [
                'aoi_proj_to_bath.shp', 'aoi_proj_to_land.shp', 
                'aoi_proj_to_wind_points.shp', 'land_poly_clipped.shp',
                'land_poly_projected.shp', 'wind_energy_points_from_dat.shp',
                'wind_points_clipped.shp', 'val_land_poly_projected.shp',
                'val_land_poly_clipped.shp', 'val_aoi_proj_to_land_poly.shp']
        
        shape_file_output_names = [
                'wind_energy_points.shp', 
                'example_size_and_orientation_of_a_possible_wind_farm.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_projected.tif',
                'aoi_raster.tif', 'distance_mask.tif']

        raster_file_output_names = [
                'harvested_energy_MWhr_per_yr.tif', 'density_W_per_m2.tif', 'levelized_cost_price_per_kWh.tif',
                'npv_US_millions.tif', 'carbon_emissions_tons.tif']

        for file_name in shape_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
    
    def test_wind_energy_uri_handler_val_dist_land_grid_options(self):
        """Regression test for the uri handler given all optional arguments"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/val_dist_land_grid_options/'
        output_dir = \
            './invest-data/test/data/test_out/wind_energy/uri_handler/val_dist_land_grid_options/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = True
        args['foundation_cost'] = 2
        args['number_of_machines'] = 60
        args['dollar_per_kWh'] = .187
        args['discount_rate'] = .116
        args['avg_grid_distance'] = 4
        args['land_polygon_uri'] = os.path.join(input_dir, 'testing_land.shp')
        args['min_distance'] = 1000
        args['max_distance'] = 20000
        args['grid_points_uri'] = os.path.join(
                input_dir, 'testing_grid_points.csv') 
        #args['suffix'] = ''

        wind_energy_uri_handler.execute(args)

        shape_file_intermediate_names = [
                'aoi_proj_to_bath.shp', 'aoi_proj_to_land.shp', 
                'aoi_proj_to_wind_points.shp', 'land_poly_clipped.shp',
                'land_poly_projected.shp', 'aoi_proj_to_grid_points.shp',
                'aoi_proj_to_land_points.shp', 'grid_point_clipped.shp',
                'land_point_clipped.shp', 'val_grid_points.shp',
                'val_land_points.shp', 'grid_point_projected.shp',
                'land_point_projected.shp', 'wind_energy_points_from_dat.shp',
                'wind_points_clipped.shp']
        
        shape_file_output_names = [
                'wind_energy_points.shp', 
                'example_size_and_orientation_of_a_possible_wind_farm.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_projected.tif',
                'aoi_raster.tif', 'distance_mask.tif']

        raster_file_output_names = [
                'harvested_energy_MWhr_per_yr.tif', 'density_W_per_m2.tif', 'levelized_cost_price_per_kWh.tif',
                'npv_US_millions.tif', 'carbon_emissions_tons.tif']

        for file_name in shape_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
    
    def test_wind_energy_uri_handler_suffix_options(self):
        """Regression test for the uri handler given all optional arguments and
            the suffix"""
        #raise SkipTest
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = \
            './invest-data/test/data/wind_energy_regression_data/uri_handler/val_suffix_options/'
        output_dir = \
            './invest-data/test/data/test_out/wind_energy/uri_handler/val_suffix_options/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(input_dir, 'testing_points.bin')
        args['bathymetry_uri'] = os.path.join(input_dir, 'testing_bathym.tif') 
        args['aoi_uri'] = os.path.join(input_dir, 'testing_aoi_proj.shp') 
        args['turbine_parameters_uri'] = os.path.join(
                input_dir, '3_6_turbine.csv') 
        args['global_wind_parameters_uri'] = os.path.join(
                input_dir, 'global_wind_energy_parameters.csv') 
        args['min_depth'] = 3
        args['max_depth'] = 100
        args['valuation_container'] = True
        args['foundation_cost'] = 2
        args['number_of_machines'] = 60
        args['dollar_per_kWh'] = .187
        args['discount_rate'] = .116
        args['avg_grid_distance'] = 4
        args['land_polygon_uri'] = os.path.join(input_dir, 'testing_land.shp')
        args['min_distance'] = 1000
        args['max_distance'] = 20000
        args['grid_points_uri'] = os.path.join(
                input_dir, 'testing_grid_points.csv') 
        args['suffix'] = 'test'

        wind_energy_uri_handler.execute(args)

        shape_file_intermediate_names = [
                'aoi_proj_to_bath_test.shp', 'aoi_proj_to_grid_points_test.shp',
                'aoi_proj_to_land_points_test.shp', 'aoi_proj_to_land_test.shp',
                'aoi_proj_to_wind_points_test.shp',
                'grid_point_clipped_test.shp', 'grid_point_projected_test.shp',
                'land_point_clipped_test.shp', 'land_point_projected_test.shp',
                'land_poly_clipped_test.shp', 'land_poly_projected_test.shp',
                'val_grid_points_test.shp', 'val_land_points_test.shp',
                'wind_energy_points_from_dat_test.shp',
                'wind_points_clipped_test.shp']
        
        shape_file_output_names = [
                'wind_energy_points_test.shp', 
                'example_size_and_orientation_of_a_possible_wind_farm_test.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp_test.tif', 'density_temp_test.tif', 'depth_mask_test.tif',
                'bathymetry_clipped_test.tif', 'bathymetry_projected_test.tif',
                'aoi_raster_test.tif', 'distance_mask_test.tif']

        raster_file_output_names = [
                'harvested_energy_MWhr_per_yr_test.tif', 
                'density_W_per_m2_test.tif', 'levelized_cost_price_per_kWh_test.tif',
                'npv_US_millions_test.tif', 'carbon_emissions_tons_test.tif']

        for file_name in shape_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in shape_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, 'intermediate/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'output/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
