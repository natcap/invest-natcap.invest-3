"""URI level tests for the wind_energy biophysical module"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_biophysical
import invest_test_core

class TestWindEnergyBiophysical(unittest.TestCase):
    def test_wind_energy_biophysical_global(self):
        """Regression test for the main biophsyical outputs"""

        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/global/'
        
        bathymetry_uri = os.path.join(regression_dir, 'global_dem_clip.tif')

        global_land_uri = os.path.join(regression_dir, 'global_poly_clip.shp')
        
        output_dir = './data/test_out/wind_energy/biophysical/global/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(
                input_dir, 'ECNA_EEZ_WEBPAR_Aug27_2012.txt')
        args['bathymetry_uri'] = bathymetry_uri
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

        wind_energy_biophysical.execute(args)

        shape_file_names = ['wind_points_shape.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif']

        raster_file_output_names = ['harvested_energy.tif', 'density.tif']

        for file_name in shape_file_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

    def test_wind_energy_biophysical_aoi_no_dist(self):
        """Regression test for the main biophsyical outputs"""

        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/aoi_no_dist/'
        
        bathymetry_uri = os.path.join(regression_dir, 'global_dem_clip.tif')

        global_land_uri = os.path.join(regression_dir, 'global_poly_clip.shp')
        
        output_dir = './data/test_out/wind_energy/biophysical/aoi_no_dist/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(
                input_dir, 'ECNA_EEZ_WEBPAR_Aug27_2012.txt')
        args['aoi_uri'] = os.path.join(input_dir, 'reprojected_distance_aoi.shp')
        args['bathymetry_uri'] = bathymetry_uri
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

        wind_energy_biophysical.execute(args)

        shape_file_names = [
                'wind_points_shape.shp', 'aoi_prj_to_bathymetry.shp', 
                'aoi_prj_to_wind_points.shp', 'wind_points_clipped.shp', 
                'wind_points_reprojected.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_reprojected.tif']

        raster_file_output_names = ['harvested_energy.tif', 'density.tif']

        for file_name in shape_file_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
        
    def test_wind_energy_biophysical_aoi_dist(self):
        """Regression test for the main biophsyical outputs"""

        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/aoi_dist/'
        
        bathymetry_uri = os.path.join(regression_dir, 'global_dem_clip.tif')

        global_land_uri = os.path.join(regression_dir, 'global_poly_clip.shp')
        
        output_dir = './data/test_out/wind_energy/biophysical/aoi_dist/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_uri'] = os.path.join(
                input_dir, 'ECNA_EEZ_WEBPAR_Aug27_2012.txt')
        args['aoi_uri'] = os.path.join(input_dir, 'reprojected_distance_aoi.shp')
        args['bathymetry_uri'] = bathymetry_uri
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
        args['min_distance'] = 7000
        args['max_distance'] = 80000
        args['land_polygon_uri'] = global_land_uri

        wind_energy_biophysical.execute(args)

        shape_file_names = [
                'wind_points_shape.shp', 'aoi_prj_to_bathymetry.shp', 
                'aoi_prj_to_wind_points.shp', 'wind_points_clipped.shp', 
                'wind_points_reprojected.shp', 'aoi_prj_to_land_poly.shp',
                'land_poly_clipped.shp', 'land_poly_reprojected.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'bathymetry_clipped.tif', 'bathymetry_reprojected.tif',
                'aoi_raster.tif', 'distance_mask.tif']

        raster_file_output_names = ['harvested_energy.tif', 'density.tif']

        for file_name in shape_file_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
    
    def test_wind_energy_biophysical_check_datasource_projections(self):
        """Load a properly projected datasource and check that it passes"""
        
        datasource_uri = './data/wind_energy_data/reprojected_distance_aoi.shp'
        
        datasource = ogr.Open(datasource_uri)

        result = \
            wind_energy_biophysical.check_datasource_projections([datasource])

        self.assertTrue(result)
    
    def test_wind_energy_biophysical_check_datasource_projections_mult(self):
        """Load multiple properly projected datasource and check that they
            pass"""
        
        datasource_uri = './data/wind_energy_data/reprojected_distance_aoi.shp'
        datasource_uri_2 = \
            './data/wind_energy_regression_data/wind_points_reprojected.shp'
        datasource_uri_3 = \
            './data/wind_energy_regression_data/projected_land_poly.shp'
        
        datasource_list = []
        for uri in [datasource_uri, datasource_uri_2, datasource_uri_3]:
            datasource_list.append(ogr.Open(uri))

        result = wind_energy_biophysical.check_datasource_projections(
                datasource_list)

        self.assertTrue(result)

    def test_wind_energy_biophysical_check_datasource_projections_fail(self):
        """Load a couple datasources and check that one fails"""
        
        ds_one_uri = './data/wind_energy_data/reprojected_distance_aoi.shp'
        ds_two_uri = './data/wind_energy_data/wind_energy_distance_aoi.shp'
       
        ds_one = ogr.Open(ds_one_uri)
        ds_two = ogr.Open(ds_two_uri)

        result = wind_energy_biophysical.check_datasource_projections(
                [ds_one, ds_two])

        self.assertTrue(not result)

    def test_wind_energy_biophysical_read_wind_data(self):
        """Unit test for turning a text file into a dictionary"""

        wind_data_uri = './data/wind_energy_data/small_wind_data_sample.txt'

        expected_dict = {}

        expected_dict[1.0] = {'LONG': -97.33333, 'LATI':26.80006,
                              'Ram-020m':6.80006, 'Ram-030m':7.196512,
                              'Ram-040m':7.427887, 'Ram-050m':7.612466, 
                              'K-010m':2.73309}
        expected_dict[2.0] = {'LONG': -97.33333, 'LATI':26.86673,
                              'Ram-020m':6.910594, 'Ram-030m':7.225791,
                              'Ram-040m':7.458108, 'Ram-050m':7.643438, 
                              'K-010m':2.732726}

        results = wind_energy_biophysical.read_wind_data(wind_data_uri)

        self.assertEqual(expected_dict, results)

    def test_wind_energy_biophysical_wind_data_to_point_shape(self):
        """Compare the output shapefile created from a known dictionary agaisnt
            a regression shape file that has been verified correct"""        
        regression_shape_uri = \
            './data/wind_energy_regression_data/wind_data_to_points.shp'

        output_dir = './data/test_out/wind_energy/wind_data_to_point_shape/'
        
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_uri = os.path.join(output_dir, 'wind_data_shape.shp')

        expected_dict = {}

        expected_dict['1.0'] = {'LONG': -97.333330, 'LATI':26.800060,
                              'Ram-020m':6.800060, 'Ram-030m':7.196512,
                              'Ram-040m':7.427887, 'Ram-050m':7.612466, 
                              'K-010m':2.733090}
        expected_dict['2.0'] = {'LONG': -97.333330, 'LATI':26.866730,
                              'Ram-020m':6.910594, 'Ram-030m':7.225791,
                              'Ram-040m':7.458108, 'Ram-050m':7.643438, 
                              'K-010m':2.732726}

        points = wind_energy_biophysical.wind_data_to_point_shape(
                expected_dict, 'wind_data', out_uri)        

        points = None

        invest_test_core.assertTwoShapesEqualURI(self, regression_shape_uri, out_uri)

    def test_wind_energy_biophysical_clip_datasource(self):
        """Regression test for clipping a shapefile from another shapefile"""

        original_shape_uri = \
            './data/wind_energy_regression_data/wind_points_shape.shp'

        aoi = ogr.Open('./data/wind_energy_regression_data/aoi_prj_to_land.shp')

        regression_shape_uri = \
            './data/wind_energy_regression_data/wind_points_clipped.shp'
        
        output_dir = './data/test_out/wind_energy/clip_datasource/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_uri = os.path.join(output_dir, 'clipped_shape.shp')
        
        if os.path.isfile(out_uri):
            os.remove(out_uri)

        original_shape = ogr.Open(original_shape_uri)
        
        result_shape = wind_energy_biophysical.clip_datasource(
            aoi, original_shape, out_uri)
        
        result_shape = None

        invest_test_core.assertTwoShapesEqualURI(self, regression_shape_uri, out_uri)

        original_shape = None
        aoi = None
    
    def test_wind_energy_biophysical_clip_datasource2(self):
        """Regression test for clipping a shapefile from another shapefile"""

        original_shape_uri = \
            './data/wind_energy_regression_data/clip_dsource_orig.shp'

        aoi = ogr.Open('./data/wind_energy_regression_data/clip_dsource_aoi.shp')

        regression_shape_uri = \
            './data/wind_energy_regression_data/clip_dsource_result.shp'
        
        output_dir = './data/test_out/wind_energy/clip_datasource/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_uri = os.path.join(output_dir, 'clipped_shape2.shp')
        
        if os.path.isfile(out_uri):
            os.remove(out_uri)

        original_shape = ogr.Open(original_shape_uri)
        
        result_shape = wind_energy_biophysical.clip_datasource(
            aoi, original_shape, out_uri)
        
        result_shape = None

        invest_test_core.assertTwoShapesEqualURI(self, regression_shape_uri, out_uri)
