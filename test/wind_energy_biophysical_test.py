"""URI level tests for the wind_energy biophysical module"""

import os
import sys
import pickle

from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_biophysical
import invest_test_core

class TestWindEnergyBiophysical(unittest.TestCase):
    def test_wind_energy_biophysical_read_binary_wind_data(self):
        """Regression test for turning a binary text file into a dictionary"""
        #raise SkipTest

        wind_data_uri = './invest-data/test/data/wind_energy_data/ECNA_EEZ_WEBPAR_Aug27_2012.bin'
        regression_dir = './invest-data/test/data/wind_energy_regression_data/biophysical'
        expected_uri = os.path.join(regression_dir, 'testing_binary_dict.pick')

        field_list = ['LATI', 'LONG', 'Ram-050m', 'K-010m']
        
        result_dict = wind_energy_biophysical.read_binary_wind_data(
                wind_data_uri, field_list)
    
        # Open the pickled file which is representing the expected dictionary,
        # saved in a binary format
        fp = open(expected_uri, 'rb')
        # Load the dictionary from the pickled file
        expected_dict = pickle.load(fp)
        
        self.assertEqual(expected_dict, result_dict)

        fp.close()
    
    def test_wind_energy_biophysical_read_binary_wind_data_exception(self):
        """Unit test that should raise a HubHeightException based on an invalid
            scale key"""
        #raise SkipTest

        wind_data_uri = './invest-data/test/data/wind_energy_data/ECNA_EEZ_WEBPAR_Aug27_2012.bin'
        regression_dir = './invest-data/test/data/wind_energy_regression_data/biophysical'
        expected_uri = os.path.join(regression_dir, 'testing_binary_dict.pick')

        field_list = ['LATI', 'LONG', 'Ram-250m', 'K-010m']

        self.assertRaises(
               wind_energy_biophysical.HubHeightError,
               wind_energy_biophysical.read_binary_wind_data, 
               wind_data_uri, field_list) 
    
    def test_wind_energy_biophysical_wind_data_to_point_shape(self):
        """Compare the output shapefile created from a known dictionary against
            a regression shape file that has been verified correct""" 
        #raise SkipTest
        regression_dir = './invest-data/test/data/wind_energy_regression_data/biophysical'
        shape_uri = os.path.join(regression_dir, 'wind_data_to_points.shp')

        output_dir = \
                './invest-data/test/data/test_out/wind_energy/biophysical/wind_data_to_point_shape/'
        
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
                self, shape_uri, out_uri)

    def test_wind_energy_biophysical_clip_datasource(self):
        """Regression test for clipping a shapefile from another shapefile"""
        #raise SkipTest
        
        input_dir = './invest-data/test/data/wind_energy_data/'
        regression_dir = './invest-data/test/data/wind_energy_regression_data/'
        
        original_shape_uri = os.path.join(
                input_dir, 'testing_land.shp')

        aoi_uri = os.path.join(
                regression_dir, 'biophysical/aoi_proj_to_land.shp')
        
        aoi = ogr.Open(aoi_uri)

        regression_shape_uri = os.path.join(
                regression_dir, 'biophysical/land_poly_clipped.shp')
        
        output_dir = './invest-data/test/data/test_out/wind_energy/biophysical/clip_datasource/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_uri = os.path.join(output_dir, 'clipped_shape.shp')
        
        if os.path.isfile(out_uri):
            os.remove(out_uri)

        original_shape = ogr.Open(original_shape_uri)
        
        result_shape = wind_energy_biophysical.clip_datasource(
            aoi, original_shape, out_uri)
        
        result_shape = None
        original_shape = None
        aoi = None

        invest_test_core.assertTwoShapesEqualURI(self, regression_shape_uri, out_uri)
    
    def test_wind_energy_biophysical_clip_datasource2(self):
        """Regression test for clipping a shapefile from another shapefile"""
        #raise SkipTest

        regression_dir = './invest-data/test/data/wind_energy_regression_data/biophysical'
        original_shape_uri = os.path.join(
                regression_dir, 'clip_dsource_orig.shp')

        aoi = ogr.Open(os.path.join(regression_dir, 'clip_dsource_aoi.shp'))

        regression_shape_uri = os.path.join(
                regression_dir, 'clip_dsource_result.shp')
        
        output_dir = './invest-data/test/data/test_out/wind_energy/biophysical/clip_datasource/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_uri = os.path.join(output_dir, 'clipped_shape2.shp')
        
        if os.path.isfile(out_uri):
            os.remove(out_uri)

        original_shape = ogr.Open(original_shape_uri)
        
        result_shape = wind_energy_biophysical.clip_datasource(
            aoi, original_shape, out_uri)
        
        result_shape = None
        original_shape = None
        aoi = None

        invest_test_core.assertTwoShapesEqualURI(self, regression_shape_uri, out_uri)
    
    def test_wind_energy_biophysical_clip_and_reproject_maps_dsource(self):
        """Regression test for clipping a shapefile from another shapefile and
            then projecting it to that shapefile"""
        #raise SkipTest

        regression_dir = \
              './invest-data/test/data/wind_energy_regression_data/biophysical/clip_project_map'
        input_dir = './invest-data/test/data/wind_energy_data/'

        original_shape_uri = os.path.join(
                input_dir, 'testing_land.shp')

        aoi = ogr.Open(os.path.join(input_dir, 'testing_aoi_proj.shp'))

        regression_proj_uri = os.path.join(
                regression_dir, 'land_poly_projected.shp')
        regression_clip_uri = os.path.join(
                regression_dir, 'land_poly_clipped.shp')
        regression_aoi_uri = os.path.join(
                regression_dir, 'aoi_proj_to_land.shp')
        
        reg_file_list = [
                regression_proj_uri, regression_clip_uri, regression_aoi_uri]

        output_dir = './invest-data/test/data/test_out/wind_energy/biophysical/clip_project/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_clipped_uri = os.path.join(output_dir, 'clipped.shp')
        out_projected_uri = os.path.join(output_dir, 'projected.shp')
        out_aoi_proj_uri = os.path.join(output_dir, 'aoi_to_land.shp')
       
        out_file_list = [out_projected_uri, out_clipped_uri, out_aoi_proj_uri]

        for out_uri in out_file_list:
            if os.path.isfile(out_uri):
                os.remove(out_uri)

        original_shape = ogr.Open(original_shape_uri)
        
        result_shape = wind_energy_biophysical.clip_and_reproject_maps(
            original_shape, aoi, out_clipped_uri, out_projected_uri,
            out_aoi_proj_uri)
        
        result_shape = None
        original_shape = None
        aoi = None

        for reg_uri, out_uri in zip(reg_file_list, out_file_list):
            invest_test_core.assertTwoShapesEqualURI(self, reg_uri, out_uri)

    def test_wind_energy_biophysical_clip_and_reproject_maps_dset(self):
        """Regression test for clipping a raster from another shapefile and
            then projecting it to that shapefiles projection"""
        #raise SkipTest

        regression_dir = \
              './invest-data/test/data/wind_energy_regression_data/biophysical/clip_project_map'
        input_dir = './invest-data/test/data/wind_energy_data/'

        original_raster_uri = os.path.join(
                input_dir, 'testing_bathym.tif')

        aoi = ogr.Open(os.path.join(input_dir, 'testing_aoi_proj.shp'))

        regression_proj_uri = os.path.join(
                regression_dir, 'bathymetry_projected.tif')
        regression_clip_uri = os.path.join(
                regression_dir, 'bathymetry_clipped.tif')
        regression_aoi_uri = os.path.join(
                regression_dir, 'aoi_proj_to_bath.shp')
        
        reg_file_list = [regression_proj_uri, regression_clip_uri]

        output_dir = './invest-data/test/data/test_out/wind_energy/biophysical/clip_project/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_clipped_uri = os.path.join(output_dir, 'clipped.tif')
        out_projected_uri = os.path.join(output_dir, 'projected.tif')
        out_aoi_proj_uri = os.path.join(output_dir, 'aoi_to_bath.shp')
       
        out_file_list = [out_projected_uri, out_clipped_uri]

        for out_uri in out_file_list:
            if os.path.isfile(out_uri):
                os.remove(out_uri)

        original_raster = gdal.Open(original_raster_uri)
        
        result_raster = wind_energy_biophysical.clip_and_reproject_maps(
            original_raster, aoi, out_clipped_uri, out_projected_uri,
            out_aoi_proj_uri)
        
        result_raster = None
        original_raster = None
        aoi = None

        for reg_uri, out_uri in zip(reg_file_list, out_file_list):
            invest_test_core.assertTwoDatasetEqualURI(self, reg_uri, out_uri)

        invest_test_core.assertTwoShapesEqualURI(
                self, regression_aoi_uri, out_aoi_proj_uri)
        
