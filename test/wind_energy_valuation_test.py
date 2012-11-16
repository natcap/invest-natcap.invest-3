"""URI level tests for the wind_energy valuation module"""

import os.path
import sys
from osgeo import gdal
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_valuation
import invest_test_core

class TestWindEnergyValuation(unittest.TestCase):
    def test_wind_energy_valuation_land(self):
        """A test for the valuation module using land polygon to get
            distances"""
        #raise SkipTest

        out_dir = './data/test_out/wind_energy/valuation/full_land_poly/'
        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        args = {}
        args['workspace_dir'] = out_dir
        args['aoi_uri'] = os.path.join(
                input_dir, 'reprojected_distance_aoi.shp')
        args['biophysical_data_uri'] = os.path.join(
                regression_dir, 'wind_points_reprojected.shp')
        args['turbine_info_uri'] = os.path.join(
                input_dir, 'turbine_parameters.csv')
        args['land_polygon_uri'] = os.path.join(
                regression_dir, 'global_poly_clip.shp')
        args['number_of_machines'] = 30
        args['dollar_per_kWh'] = 1.81
        args['suffix'] = ''
        
        wind_energy_valuation.execute(args)

        shape_file_names = [
                'val_aoi_proj_to_bio_points.shp', 'val_bio_points_clipped.shp', 
                'val_bio_points_projected.shp', 'val_aoi_proj_to_land_poly.shp',
                'val_land_poly_clipped.shp', 'val_land_poly_projected.shp']

        raster_file_output_names = [
                'carbon_emissions.tif', 'levelized.tif', 'npv.tif']

        for file_name in shape_file_names:
            reg_file = os.path.join(
                    regression_dir, 'val_land_poly/' + file_name)
            out_file = os.path.join(
                    out_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'val_land_poly/' + file_name)
            out_file = os.path.join(
                    out_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
    
    def test_wind_energy_valuation_grid(self):
        """A test for valuation module using land and grid points to compute
            distances"""
        raise SkipTest
        out_dir = './data/test_out/wind_energy/valuation/full_grid/'
        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        args = {}
        args['workspace_dir'] = out_dir
        args['aoi_uri'] = os.path.join(
                input_dir, 'reprojected_distance_aoi.shp')
        args['biophysical_data_uri'] = os.path.join(
                regression_dir, 'wind_points_reprojected.shp')
        args['turbine_info_uri'] = os.path.join(
                input_dir, 'turbine_parameters.csv')
        args['grid_points_uri'] = os.path.join(
                input_dir, 'land_grid_points.csv')
        args['number_of_machines'] = 30
        args['dollar_per_kWh'] = 1.81
        args['suffix'] = ''
        
        wind_energy_valuation.execute(args)

        shape_file_names = [
                'val_aoi_proj_to_bio_points.shp', 
                'val_aoi_proj_to_grid_point.shp', 
                'val_aoi_proj_to_land_point.shp',
                'val_bio_points_clipped.shp', 'val_grid_points.shp',
                'val_land_points.shp', 'val_grid_point_clipped.shp',
                'val_grid_point_projected.shp', 'val_land_point_clipped.shp',
                'val_land_point_projected.shp', 
                'val_bio_points_projected.shp']

        raster_file_output_names = [
                'carbon_emissions.tif', 'levelized.tif', 'npv.tif']

        for file_name in shape_file_names:
            reg_file = os.path.join(
                    regression_dir, 'val_grid/' + file_name)
            out_file = os.path.join(
                    out_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_dir, 'val_grid/' + file_name)
            out_file = os.path.join(
                    out_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)
    
    def test_wind_energy_valuation_clip_and_reproject_datasource(self):
        """A regression test for clipping and reprojecting a datasource"""

        raise SkipTest
        out_dir = './data/test_out/wind_energy/valuation/clip_and_reproject/'
        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        aoi = ogr.Open(os.path.join(input_dir, 'reprojected_distance_aoi.shp'))
        dsource = ogr.Open(os.path.join(regression_dir, 'global_poly_clip.shp'))
        regression_file_uri = os.path.join(
                regression_dir, 'projected_land_poly.shp')
        out_uri = os.path.join(out_dir, 'dsource')

        result = wind_energy_valuation.clip_and_reproject_datasource(
                dsource, aoi, out_uri)

        result = None

        test_uri = os.path.join(out_dir, 'val_dsource_projected.shp')

        invest_test_core.assertTwoShapesEqualURI(
                self, regression_file_uri, test_uri)

