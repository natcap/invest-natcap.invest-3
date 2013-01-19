"""URI level tests for the wind_energy biophysical module"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_biophysical
import invest_test_core

class TestWindEnergyBiophysical(unittest.TestCase):
    def test_wind_energy_biophysical_read_binary_wind_data(self):
        """Unit test for turning a text file into a dictionary"""
        #raise SkipTest

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
        #raise SkipTest
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

        invest_test_core.assertTwoShapesEqualURI(
                self, regression_shape_uri, out_uri)

    def test_wind_energy_biophysical_clip_datasource(self):
        """Regression test for clipping a shapefile from another shapefile"""
        #raise SkipTest

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
        #raise SkipTest

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
