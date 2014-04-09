"Wind Energy Unit and Regression tests for functions"
import math
import os
import sys
import unittest
import random
import logging
import csv
import pickle

from osgeo import ogr
from osgeo import gdal
from osgeo import osr
import numpy as np
from nose.plugins.skip import SkipTest

from invest_natcap import raster_utils
from invest_natcap.wind_energy import wind_energy
import invest_natcap.testing as testing

LOGGER = logging.getLogger('wind_energy_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

TEST_DIR = './invest-data/test/data/test_out'
REGRESSION_DIR = './invest-data/test/data/wind_energy_regression_data'
INPUT_DIR = './invest-data/test/data/wind_energy_data'

class TestWindEnergyFunctionUnit(testing.GISTest):
    def test_wind_energy_distance_transform_dataset_unit(self):
        """A unit test for the distance_transform_dataset function"""
        #raise SkipTest        
       
        output_dir = os.path.join(
                TEST_DIR, 'wind_energy/biophysical/distance_transform_dataset')

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        min_dist = 40
        max_dist = 80
        out_nodata = -1.0
        # Where the created test file will be written to
        out_uri = os.path.join(output_dir, 'transformed_ds_by_hand.tif')
        dataset_uri = os.path.join(output_dir, 'dist_by_hand.tif')
        # Create a new dataset by hand in memory
        driver = gdal.GetDriverByName('GTiff')
        dataset_type = gdal.GDT_Float32
        # Create a 5x5 dataset
        dataset = driver.Create(dataset_uri, 5, 5, 1, dataset_type)
        # Set spatial reference and projection such that it is in meters
        srs = osr.SpatialReference()
        srs.SetUTM( 11, 1 )
        srs.SetWellKnownGeogCS( 'NAD27' )
        dataset.SetProjection( srs.ExportToWkt() )
        # Set GeoTransform
        dataset.SetGeoTransform( [444720, 30, 0, 3751320, 0, -30 ] )
        # Create rows and columns of the dataset such that 0.0 is where land is
        # and 1.0 is where land is.
        raster = np.array([[-1.0, 0.0, 0.0, 0.0, 0.0],
                           [-1.0, 0.0, 0.0, 1.0, 1.0],
                           [0.0, 0.0, 1.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0, -1.0, -1.0]])

        dataset.GetRasterBand(1).WriteArray(raster)
        dataset.GetRasterBand(1).SetNoDataValue(out_nodata)
        dataset = None
        
        # Hand calculated results
        expected_results = np.array([[-1.0, -1.0, -1.0, -1.0, -1.0],
                                     [-1.0, -1.0, -1.0, -1.0, -1.0],
                                     [-1.0, -1.0, -1.0, 42.4264068, 60.0],
                                     [-1.0, -1.0, 42.4264068, 67.0820394, -1.0],
                                     [-1.0, -1.0, 60.0, -1.0, -1.0]])

        wind_energy.distance_transform_dataset(
                dataset_uri, min_dist, max_dist, out_nodata, out_uri)

        result_ds = gdal.Open(out_uri)

        result_array = result_ds.GetRasterBand(1).ReadAsArray()
        # Check that the two matrices are the same
        for expected, recieved in zip(expected_results, result_array):
            for val_exp, val_rec in zip(expected, recieved):
                self.assertAlmostEqual(val_exp, val_rec, 3)

        result_ds = None

    def test_wind_energy_point_to_polygon_distance(self):
        """A unit test for getting the shortest distance from a point geometry
            to a polygon geometry"""
        #raise SkipTest

        polygon_ds_uri = os.path.join(REGRESSION_DIR, 
                'uri_handler/val_dist_land_options/intermediate/'
                'val_land_poly_projected.shp')
        point_ds_uri = os.path.join(REGRESSION_DIR,
                'wind_energy_core/testing_distance_points.shp')

        expected_list = [6.09064, 6.68105, 21.1257]

        result = wind_energy.point_to_polygon_distance(
                polygon_ds_uri, point_ds_uri)

        LOGGER.debug('result: %s', result)

        for exp, res in zip(expected_list, result):
            self.assertAlmostEqual(exp, res, 4)

    def test_wind_energy_point_to_polygon_distance2(self):
        """A unit test for getting the shortest distance from a point geometry
            to another point geometry"""
        #raise SkipTest

        point_1_ds_uri = os.path.join(REGRESSION_DIR,
                'wind_energy_core/testing_distance_points.shp')
        point_2_ds_uri = os.path.join(REGRESSION_DIR,
                'wind_energy_core/testing_distance_grid_points.shp')

        expected_list = [19.47249, 16.03225, 26.7911] 

        result = wind_energy.point_to_polygon_distance(
                point_2_ds_uri, point_1_ds_uri)

        LOGGER.debug('result: %s', result)

        for exp, res in zip(expected_list, result):
            self.assertAlmostEqual(exp, res, 4)
    
    def test_wind_energy_get_points_geometries(self):
        """A unit test for properly reading coordinates into a list from a
            point shapefile """
        #raise SkipTest
        regression_dir = os.path.join(REGRESSION_DIR, 'wind_energy_core')
        datasource_uri = os.path.join(regression_dir, 'dict_to_shape.shp')

        expected_list = np.array([
            [-70.096,42.689], [-69.796,42.689],
            [-69.796,42.496], [-70.096,42.496]])
        
        result = wind_energy.get_points_geometries(datasource_uri)

        LOGGER.debug('geometry list : %s', result)

        self.assertTrue((expected_list == result).all())

    def test_wind_energy_get_dictionary_from_shape(self):
        """A unit test for building a dictionary from a shapefile"""
        #raise SkipTest
        regression_dir = os.path.join(REGRESSION_DIR, 'wind_energy_core')
        datasource_uri = os.path.join(regression_dir, 'dict_to_shape.shp')
      
        expected_dict = {
                (-69.796,42.689) : {'lati':42.689, 'long':-69.796, 'height':10,
                                    'K_shape':2.567},
                (-69.796,42.496) : {'lati':42.496, 'long':-69.796, 'height':10,
                                    'K_shape':2.567},
                (-70.096,42.496) : {'lati':42.496, 'long':-70.096, 'height':10,
                                    'K_shape':2.567},
                (-70.096,42.689) : {'lati':42.689, 'long':-70.096, 'height':10,
                                    'K_shape':2.567}}
        
        result = wind_energy.get_dictionary_from_shape(datasource_uri)

        LOGGER.debug('dictionary : %s', result)

        self.assertEqual(expected_dict, result)
    
    def test_wind_energy_read_binary_wind_data(self):
        """Regression test for turning a binary text file into a dictionary"""
        #raise SkipTest

        wind_data_uri = os.path.join(
                INPUT_DIR, 'ECNA_EEZ_WEBPAR_Aug27_2012.bin')
        regression_dir = os.path.join(REGRESSION_DIR, 'biophysical')
        expected_uri = os.path.join(regression_dir, 'testing_binary_dict.pick')

        field_list = ['LATI', 'LONG', 'Ram-050m', 'K-010m']
        
        result_dict = wind_energy.read_binary_wind_data(
                wind_data_uri, field_list)
    
        # Open the pickled file which is representing the expected dictionary,
        # saved in a binary format
        fp = open(expected_uri, 'rb')
        # Load the dictionary from the pickled file
        expected_dict = pickle.load(fp)
        
        self.assertEqual(expected_dict, result_dict)

        fp.close()

    def test_wind_energy_read_binary_wind_data_exception(self):
        """Unit test that should raise a HubHeightException based on an invalid
            scale key"""
        #raise SkipTest

        wind_data_uri = os.path.join(
                INPUT_DIR, 'ECNA_EEZ_WEBPAR_Aug27_2012.bin')
        regression_dir = os.path.join(REGRESSION_DIR, 'biophysical')
        expected_uri = os.path.join(regression_dir, 'testing_binary_dict.pick')

        field_list = ['LATI', 'LONG', 'Ram-250m', 'K-010m']

        self.assertRaises(
               wind_energy.HubHeightError, wind_energy.read_binary_wind_data, 
               wind_data_uri, field_list) 
   

class TestWindEnergyFunctionRegression(testing.GISTest):
    def test_wind_energy_add_field_to_shape_given_list(self):
        """A regression test for adding a field to a shapefile given a list of
            data entries"""
        #raise SkipTest
        points_ds_uri = os.path.join(REGRESSION_DIR,
                'wind_energy_core/testing_distance_points.shp')
        expected_ds_uri = os.path.join(REGRESSION_DIR,
                'wind_energy_core/testing_point_fields.shp')

        out_dir = os.path.join(
                TEST_DIR, 'wind_energy/valuation/add_field_to_shape')
        copy_uri = os.path.join(out_dir, 'wind_points_new_field.shp')

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        if os.path.isfile(copy_uri):
            os.remove(copy_uri)

        points_ds = ogr.Open(points_ds_uri)

        copy_drv = ogr.GetDriverByName('ESRI Shapefile')
        copy_ds = copy_drv.CopyDataSource(points_ds, copy_uri)

        copy_ds = None
        point_ds = None

        distances = [25.5, 12.4, 9.2] 

        wind_energy.add_field_to_shape_given_list(
                copy_uri, distances, 'O2L')

        self.assertVectorsEqual(copy_uri, expected_ds_uri)

    def test_wind_energy_create_wind_farm_box(self):
        """A regression test for create_wind_farm_box function"""
        #raise SkipTest

        # Datasource from regression directory is used for its projection and to
        # locate the linestring to a known point
        regression_dir = os.path.join(
                REGRESSION_DIR, 'uri_handler/val_dist_land_options/output')
        datasource_uri = os.path.join(regression_dir, 'wind_energy_points.shp')
        # Directory and path to save the created rectangular polygon
        test_dir = os.path.join(
                TEST_DIR, 'wind_energy/valuation/create_wind_farm_box')
        out_uri = os.path.join(test_dir, 'wind_farm_box.shp')
        # The regression file to test against
        reg_uri = os.path.join(
                regression_dir,
                'example_size_and_orientation_of_a_possible_wind_farm.shp')

        # If the output directory for the polygon does not exist, create it
        if not os.path.isdir(test_dir):
            os.makedirs(test_dir)
        # If the file path for the output shape already exists, delete it
        # because we cannot create a new polygon using the same name as an
        # existing one
        if os.path.isfile(out_uri):
            os.remove(out_uri)

        # Open the wind energy points datasource to use its spatial reference
        # and to get a starting location for the wind farm
        datasource = ogr.Open(datasource_uri)
        wind_energy_layer = datasource.GetLayer()
        # Get the feature count to know how many points we have
        feature_count = int(wind_energy_layer.GetFeatureCount())
        # Select a feature to get the starting location from. This is done by
        # grabbing the feature whos index is half the feature count. For some
        # reason OGR requires the type for the index to be a LONG
        feature = wind_energy_layer.GetFeature(
                    long(math.ceil(feature_count / 2)))
        pt_geometry = feature.GetGeometryRef()
        center_x = pt_geometry.GetX()
        center_y = pt_geometry.GetY()
        start_point = (center_x, center_y)
        spat_ref = wind_energy_layer.GetSpatialRef()
        
        LOGGER.debug('Starting Point : %s', start_point)
        
        # A default length and width to test against
        x_len = 5243 
        y_len = 5243

        wind_energy.create_wind_farm_box(
                spat_ref, start_point, x_len, y_len, out_uri)

        datasource = None

        # Do a general check that the shapefiles are the same
        self.assertVectorsEqual(out_uri, reg_uri)

    def test_wind_energy_distance_transform_dataset(self):
        """A regression test for the distance_transform_dataset function"""
        #raise SkipTest        
        regres_dir = os.path.join(
                REGRESSION_DIR, 'uri_handler/dist_options/intermediate')

        output_dir = os.path.join(TEST_DIR, 
                'wind_energy/biophysical/distance_transform_dataset')
        
        # Where the created test file will be written to
        out_uri = os.path.join(output_dir, 'transformed_ds.tif')
        # The path of the regression file to test against
        reg_transformed_dataset_uri = os.path.join(
                regres_dir, 'distance_mask.tif')
        # A regression file for passing into the function
        reg_dataset_uri = os.path.join(
                regres_dir, 'aoi_raster.tif')

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        min_dist = 1000 
        max_dist = 20000
        out_nodata = -32768.0

        wind_energy.distance_transform_dataset(
                reg_dataset_uri, min_dist, max_dist, out_nodata, out_uri)

        self.assertRastersEqual(reg_transformed_dataset_uri, out_uri)

    def test_wind_energy_wind_data_to_point_shape(self):
        """Compare the output shapefile created from a known dictionary against
            a regression shape file that has been verified correct""" 
        #raise SkipTest
        regression_dir = os.path.join(REGRESSION_DIR, 'biophysical')
        shape_uri = os.path.join(regression_dir, 'wind_data_to_points.shp')

        output_dir = os.path.join(
                TEST_DIR,'wind_energy/biophysical/wind_data_to_point_shape')
        
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

        points = wind_energy.wind_data_to_point_shape(
                expected_dict, 'wind_data', out_uri)        

        points = None

        self.assertVectorsEqual(shape_uri, out_uri)

    def test_wind_energy_clip_datasource(self):
        """Regression test for clipping a shapefile from another shapefile"""
        #raise SkipTest
        
        original_shape_uri = os.path.join(INPUT_DIR, 'testing_land.shp')

        aoi_uri = os.path.join(
                REGRESSION_DIR, 'biophysical/aoi_proj_to_land.shp')

        regression_shape_uri = os.path.join(
                REGRESSION_DIR, 'biophysical/land_poly_clipped.shp')
        
        output_dir = os.path.join(
                TEST_DIR, 'wind_energy/biophysical/clip_datasource')

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_uri = os.path.join(output_dir, 'clipped_shape.shp')
        
        if os.path.isfile(out_uri):
            os.remove(out_uri)

        original_shape = ogr.Open(original_shape_uri)
        
        wind_energy.clip_datasource(aoi_uri, original_shape_uri, out_uri)

        self.assertVectorsEqual(regression_shape_uri, out_uri)
    
    def test_wind_energy_clip_datasource2(self):
        """Regression test for clipping a shapefile from another shapefile"""
        #raise SkipTest

        regression_dir = os.path.join(REGRESSION_DIR, 'biophysical')
        original_shape_uri = os.path.join(
                regression_dir, 'clip_dsource_orig.shp')

        aoi_uri = os.path.join(regression_dir, 'clip_dsource_aoi.shp')

        regression_shape_uri = os.path.join(
                regression_dir, 'clip_dsource_result.shp')
        
        output_dir = os.path.join(
            TEST_DIR, 'wind_energy/biophysical/clip_datasource')

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_uri = os.path.join(output_dir, 'clipped_shape2.shp')
        
        if os.path.isfile(out_uri):
            os.remove(out_uri)

        wind_energy.clip_datasource(aoi_uri, original_shape_uri, out_uri)

        self.assertVectorsEqual(regression_shape_uri, out_uri)
    
    def test_wind_energy_clip_and_reproject_shapefile(self):
        """Regression test for clipping a shapefile from another shapefile and
            then projecting it to that shapefile"""
        #raise SkipTest

        regression_dir = os.path.join(
                REGRESSION_DIR, 'biophysical/clip_project_map')

        original_shape_uri = os.path.join(
                INPUT_DIR, 'testing_land.shp')

        aoi_uri = os.path.join(INPUT_DIR, 'testing_aoi_proj.shp')

        regression_proj_uri = os.path.join(
                regression_dir, 'land_poly_projected.shp')

        output_dir = os.path.join(
                TEST_DIR, 'wind_energy/biophysical/clip_project')

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_projected_uri = os.path.join(output_dir, 'projected.shp')

        if os.path.isfile(out_projected_uri):
            os.remove(out_projected_uri)
        
        wind_energy.clip_and_reproject_shapefile(
            original_shape_uri, aoi_uri, out_projected_uri)

        self.assertVectorsEqual(regression_proj_uri, out_projected_uri)

    def test_wind_energy_clip_and_reproject_maps_dset(self):
        """Regression test for clipping a raster from another shapefile and
            then projecting it to that shapefiles projection"""
        #raise SkipTest

        regression_dir = os.path.join(
                REGRESSION_DIR, 'biophysical/clip_project_map')

        original_raster_uri = os.path.join(
                INPUT_DIR, 'testing_bathym.tif')

        aoi_uri = os.path.join(INPUT_DIR, 'testing_aoi_proj.shp')

        regression_proj_uri = os.path.join(
                regression_dir, 'bathymetry_projected.tif')

        output_dir = os.path.join(
            TEST_DIR, 'wind_energy/biophysical/clip_project')

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_projected_uri = os.path.join(output_dir, 'projected.tif')

        if os.path.isfile(out_projected_uri):
            os.remove(out_projected_uri)
        
        wind_energy.clip_and_reproject_raster(
            original_raster_uri, aoi_uri, out_projected_uri)
        
        self.assertRastersEqual(regression_proj_uri, out_projected_uri)

    def test_wind_energy_clip_and_project_shapefile(self):
        """Regression test for clipping a shapefile from another shapefile and
            then projecting it to that shapefile"""
        #raise SkipTest

        regression_dir = os.path.join(REGRESSION_DIR, 'valuation')

        original_shape_uri = os.path.join(
                INPUT_DIR, 'testing_land.shp')

        aoi_uri = os.path.join(INPUT_DIR, 'testing_aoi_proj.shp')

        regression_proj_uri = os.path.join(
                regression_dir, 'val_land_poly_projected.shp')

        output_dir = os.path.join(
                TEST_DIR, 'wind_energy/valuation/clip_project')

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        out_projected_uri = os.path.join(output_dir, 'projected.shp')

        if os.path.isfile(out_projected_uri):
            os.remove(out_projected_uri)
        
        wind_energy.clip_and_reproject_shapefile(
            original_shape_uri, aoi_uri, out_projected_uri)

        self.assertVectorsEqual(regression_proj_uri, out_projected_uri)
