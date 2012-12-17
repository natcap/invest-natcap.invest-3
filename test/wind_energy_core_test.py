import os, sys
import unittest
import random
import logging
import csv

from osgeo import ogr
from osgeo import gdal
from osgeo import osr
from osgeo.gdalconst import *
import numpy as np
from nose.plugins.skip import SkipTest

from invest_natcap import raster_utils
from invest_natcap.wind_energy import wind_energy_core
import invest_test_core

LOGGER = logging.getLogger('wind_energy_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestWindEnergyCore(unittest.TestCase):
    def test_wind_energy_core_distance_transform_dataset(self):
        """A regression test for the distance_transform_dataset function"""
        raise SkipTest        
        regression_dir = './data/wind_energy_regression_data/biophysical_core_tests/'

        reg_transformed_dataset_uri = os.path.join(
                regression_dir, 'distance_mask.tif')

        reg_dataset_uri = os.path.join(regression_dir, 'aoi_raster.tif')
        reg_dataset = gdal.Open(reg_dataset_uri)

        output_dir = './data/test_out/wind_energy_biophysical/distance_transform_dataset/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        min_dist = 7000 
        max_dist = 80000
        out_nodata = -32768.0
        out_uri = os.path.join(output_dir, 'transformed_ds.tif')


        result = wind_energy_core.distance_transform_dataset(
                reg_dataset, min_dist, max_dist, out_nodata, out_uri)

        reg_dataset = None
        result = None

        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_transformed_dataset_uri, out_uri)

    def test_wind_energy_core_distance_transform_dataset_unit(self):
        """A unit test for the distance_transform_dataset function"""
        raise SkipTest        
        
        output_dir = './data/test_out/wind_energy_biophysical/distance_transform_dataset/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        min_dist = 40 
        max_dist = 80
        out_nodata = -1.0
        out_uri = os.path.join(output_dir, 'transformed_ds_by_hand.tif')

        driver = gdal.GetDriverByName('MEM')
        dataset_type = gdal.GDT_Float32

        dataset = driver.Create('', 5, 5, 1, dataset_type)

        srs = osr.SpatialReference()
        srs.SetUTM( 11, 1 )
        srs.SetWellKnownGeogCS( 'NAD27' )
        dataset.SetProjection( srs.ExportToWkt() )

        dataset.SetGeoTransform( [444720, 30, 0, 3751320, 0, -30 ] )

        raster = np.array([[-1.0,0.0,0.0,0.0,0.0],
                           [-1.0,0.0,0.0,1.0,1.0],
                           [0.0,0.0,1.0,1.0,1.0],
                           [0.0,1.0,1.0,1.0,1.0],
                           [0.0,1.0,1.0,-1.0,-1.0]])

        dataset.GetRasterBand(1).WriteArray(raster)
        dataset.GetRasterBand(1).SetNoDataValue(out_nodata)
   
        expected_results = np.array([[-1.0,-1.0,-1.0,-1.0,-1.0],
                                     [-1.0,-1.0,-1.0,-1.0,-1.0],
                                     [-1.0,-1.0,-1.0,42.4264068, 60.0],
                                     [-1.0,-1.0,42.4264068,67.0820394,-1.0],
                                     [-1.0,-1.0,60.0,-1.0,-1.0]])

        result_ds = wind_energy_core.distance_transform_dataset(
                dataset, min_dist, max_dist, out_nodata, out_uri)

        result_array = result_ds.GetRasterBand(1).ReadAsArray()

        for expected, recieved in zip(expected_results, result_array):
            for val_exp, val_rec in zip(expected, recieved):
                self.assertAlmostEqual(val_exp, val_rec, 3)

        dataset = None
    
    def test_wind_energy_core_biophysical(self):
        """Test the main biophysical function assuming we were provided with an
            AOI and Land Polygon"""
        raise SkipTest
        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/wind_energy_core/'
        regression_results_dir = './data/wind_energy_regression_data/' 
        bathymetry_uri = os.path.join(
                regression_dir, 'bathymetry_reprojected.tif')

        land_uri = os.path.join(regression_dir, 'land_poly_reprojected.shp')
        
        wind_data_points_uri = os.path.join(
                regression_dir, 'wind_points_reprojected.shp')

        aoi_uri = os.path.join(input_dir, 'reprojected_distance_aoi.shp')

        output_dir = './data/test_out/wind_energy/biophysical/wind_energy_core/'
        inter_dir = os.path.join(output_dir, 'intermediate/')        
        out_dir = os.path.join(output_dir, 'output/')        
        
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        for dir_path in [inter_dir, out_dir]:
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

        wind_pts_copy_uri = os.path.join(
                inter_dir, 'wind_points_reprojected.shp')

        if os.path.isfile(wind_pts_copy_uri):
            os.remove(wind_pts_copy_uri)

        wind_pts_copy = ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(
                ogr.Open(wind_data_points_uri), wind_pts_copy_uri)

        args = {}
        args['workspace_dir'] = output_dir
        args['wind_data_points'] = wind_pts_copy
        args['aoi'] = ogr.Open(aoi_uri) 
        args['bathymetry'] = gdal.Open(bathymetry_uri)
        args['hub_height']  = 50 
        args['pwr_law_exponent'] = 0.11
        args['cut_in_wspd'] = 4.0
        args['rated_wspd'] = 14.0
        args['cut_out_wspd'] = 25.0
        args['turbine_rated_pwr'] = 3.6
        args['exp_out_pwr_curve'] = 2 
        args['num_days'] = 365
        args['air_density'] = 1.225 
        args['min_depth'] = -25.0
        args['max_depth'] = -200.0
        args['min_distance'] = 7000
        args['max_distance'] = 80000
        args['land_polygon'] = ogr.Open(land_uri)
        args['suffix'] = ''

        wind_energy_core.biophysical(args)

        shape_file_names = [
                'wind_points_reprojected.shp']
        
        raster_file_intermediate_names = [
                'harvested_temp.tif', 'density_temp.tif', 'depth_mask.tif',
                'aoi_raster.tif', 'distance_mask.tif']

        raster_file_output_names = ['harvested_energy.tif', 'density.tif']

        for file_name in shape_file_names:
            reg_file = os.path.join(
                    regression_results_dir, 'aoi_dist/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_file, out_file)
        
        for file_name in raster_file_intermediate_names:
            reg_file = os.path.join(
                    regression_results_dir, 'aoi_dist/' + file_name)
            out_file = os.path.join(
                    output_dir, 'intermediate/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

        for file_name in raster_file_output_names:
            reg_file = os.path.join(
                    regression_results_dir, 'aoi_dist/' + file_name)
            out_file = os.path.join(
                    output_dir, 'output/' + file_name)
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_file, out_file)

    def test_wind_energy_core_valuation_point_to_polygon_distance(self):
        """A unit test for getting the shortest distance from a point geometry
            to a polygon geometry"""
        raise SkipTest

        regression_dir = './data/wind_energy_regression_data/'
        polygon_ds_uri = os.path.join(regression_dir, 'projected_land_poly.shp')
        point_ds_uri = os.path.join(regression_dir, 'test_points_projected.shp')
       
        polygon_ds = ogr.Open(polygon_ds_uri)
        point_ds = ogr.Open(point_ds_uri)

        expected_list = [6.78634, 21.84987, 12.75408, 46.35042]

        result = wind_energy_core.point_to_polygon_distance(
                polygon_ds, point_ds)

        LOGGER.debug('result: %s', result)

        for exp, res in zip(expected_list, result):
            self.assertAlmostEqual(exp, res, 4)

    def test_wind_energy_core_valuation_point_to_polygon_distance2(self):
        """A unit test for getting the shortest distance from a point geometry
            to another point geometry"""
        raise SkipTest

        regression_dir = './data/wind_energy_regression_data/val_grid'
        point_1_ds_uri = os.path.join(regression_dir, 'val_grid_point_projected.shp')
        point_2_ds_uri = os.path.join(regression_dir, 'val_land_point_projected.shp')
       
        point_1_ds = ogr.Open(point_1_ds_uri)
        point_2_ds = ogr.Open(point_2_ds_uri)

        expected_list = [21.33411, 32.91942] 

        result = wind_energy_core.point_to_polygon_distance(
                point_1_ds, point_2_ds)

        LOGGER.debug('result: %s', result)

        for exp, res in zip(expected_list, result):
            self.assertAlmostEqual(exp, res, 4)
    
    def test_wind_energy_core_valuation_add_field_to_shape_given_list(self):
        """A regression test for adding a field to a shapefile given a list of
            data entries"""
        raise SkipTest
        regression_dir = './data/wind_energy_regression_data/'
        polygon_ds_uri = os.path.join(regression_dir, 'projected_land_poly.shp')
        point_ds_uri = os.path.join(
                regression_dir, 'wind_points_reprojected.shp')
      

        out_dir = './data/test_out/wind_energy/valuation/add_field_to_shape/'
        copy_uri = os.path.join(out_dir, 'wind_points_new_field.shp')

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        if os.path.isfile(copy_uri):
            os.remove(copy_uri)

        polygon_ds = ogr.Open(polygon_ds_uri)
        point_ds = ogr.Open(point_ds_uri)

        copy_drv = ogr.GetDriverByName('ESRI Shapefile')
        copy_ds = copy_drv.CopyDataSource(point_ds, copy_uri)

        distances = wind_energy_core.point_to_polygon_distance(
                polygon_ds, copy_ds)

        _ = wind_energy_core.add_field_to_shape_given_list(
                copy_ds, distances, 'O2L')

    def test_wind_energy_core_valuation_build_subset_dictionary(self):
        """A unit test for building a dictionary from another dictionary"""
        raise SkipTest

        main_dict = {0 : {'lati':42.689, 'long':-70.096, 'height':10,
                          'K_shape':2.567},
                     1 : {'lati':42.689, 'long':-69.796, 'height':10,
                          'K_shape':3.102},
                     2 : {'lati':42.496, 'long':-69.796, 'height':10,
                          'K_shape':2.798},
                     3 : {'lati':42.496, 'long':-70.096, 'height':10,
                          'K_shape':1.989}}

        expected_dict = {0:2.567, 1:3.102, 2:2.798, 3:1.989}

        result = wind_energy_core.build_subset_dictionary(main_dict)

        self.assertEqual(expected_list, result)

    def test_wind_energy_core_valuation_build_list_points_from_dict(self):
        """A unit test for building a list of points from a dictionary"""
        raise SkipTest

        main_dict = {0 : {'lati':42.689, 'long':-70.096, 'height':10,
                          'K_shape':2.567},
                     1 : {'lati':42.689, 'long':-69.796, 'height':10,
                          'K_shape':2.567},
                     2 : {'lati':42.496, 'long':-69.796, 'height':10,
                          'K_shape':2.567},
                     3 : {'lati':42.496, 'long':-70.096, 'height':10,
                          'K_shape':2.567}}

        expected_list = [[-70.096, 42.689],[-69.796, 42.689],
                         [-69.796, 42.496],[-70.096, 42.496]]

        result = wind_energy_core.build_list_points_from_dict(main_dict)

        self.assertEqual(expected_list, result)

    def test_wind_energy_core_valuation_distance_kd(self):
        """A unit test for getting the shortest distances between geometries
            (two shapefiles) """
        raise SkipTest

        array_one = np.array([[1,1], [2,4], [13,8], [11, 6]])
        array_two = np.array([[0,0], [20,14], [9,8], [7, 16]])

        expected_distances = np.array([1.4142, 9.2195, 2.8284, 10])
        expected_indexes = np.array([0, 2, 3, 2])

        result = wind_energy_core.distance_kd(array_one, array_two)

        LOGGER.debug('kd distances : %s', result)

        for exp, res in zip(expected_distances, result[0]):
            self.assertAlmostEqual(exp, res, 4)

        self.assertTrue((expected_indexes == result[1]).all()) 

    def test_wind_energy_core_valuation_get_points_geometries(self):
        """A unit test for properly reading coordinates into a list from a
            point shapefile """
        raise SkipTest
        regression_dir = './data/wind_energy_regression_data/'
        datasource_uri = os.path.join(regression_dir, 'dict_to_shape.shp')

        datasource = ogr.Open(datasource_uri)

        expected_list = np.array([[-70.096,42.689],[-69.796,42.689],[-69.796,42.496],[-70.096,42.496]])
        
        result = wind_energy_core.get_points_geometries(datasource)

        LOGGER.debug('geometry list : %s', result)

        self.assertTrue((expected_list == result).all())

    def test_wind_energy_core_valuation_get_dictionary_from_shape(self):
        """A unit test for building a dictionary from a shapefile"""
        raise SkipTest
        regression_dir = './data/wind_energy_regression_data/'
        datasource_uri = os.path.join(regression_dir, 'dict_to_shape.shp')
      
        datasource = ogr.Open(datasource_uri)

        expected_dict = {(-69.796,42.689) : {'lati':42.689, 'long':-69.796, 'height':10,
                                             'K_shape':2.567},
                         (-69.796,42.496) : {'lati':42.496, 'long':-69.796, 'height':10,
                                             'K_shape':2.567},
                         (-70.096,42.496) : {'lati':42.496, 'long':-70.096, 'height':10,
                                             'K_shape':2.567},
                         (-70.096,42.689) : {'lati':42.689, 'long':-70.096, 'height':10,
                                             'K_shape':2.567}}
        
        result = wind_energy_core.get_dictionary_from_shape(datasource)

        LOGGER.debug('dictionary : %s', result)

        self.assertEqual(expected_dict, result)

    def test_wind_energy_core_create_rectangular_polygon(self):
        """A regression test for create_rectangular_polygon"""
        #raise SkipTest

        # Dataset from regression directory is used for its projection and to
        # locate the polygon to a known point
        regression_dir = './data/wind_energy_regression_data/'
        dataset_uri = os.path.join(regression_dir, 'aoi_dist/density.tif')
        # Directory and path to save the created rectangular polygon
        test_dir = './data/test_out/wind_energy/valuation/create_rectangular_polygon'
        out_uri = os.path.join(test_dir, 'wind_farm_poly.shp')
        # The regression file to test against
        reg_uri = os.path.join(regression_dir, 'wind_farm_poly.shp')
        reg_ds = ogr.Open(reg_uri)

        # If the output directory for the polygon does not exist, create it
        if not os.path.isdir(test_dir):
            os.makedirs(test_dir)
        # If the file path for the output shape already exists, delete it
        # because we cannot create a new polygon using the same name as an
        # existing one
        if os.path.isfile(out_uri):
            os.remove(out_uri)

        # Open the dataset and gets its projection as well known text, then make
        # that into a spatial reference
        dataset = gdal.Open(dataset_uri)
        dataset_wkt = dataset.GetProjection()
        spat_ref = osr.SpatialReference()
        spat_ref.ImportFromWkt(dataset_wkt)

        # To make sure we stay within the same projection scope, get the center
        # point of the raster to be our starting point. This should also ensure
        # the two shapefiles being tested are in the same location
        band = dataset.GetRasterBand(1)
        gt = dataset.GetGeoTransform()
        xsize = band.XSize
        ysize = band.YSize
        point_x = (xsize / 2 ) * gt[1] + gt[0]
        point_y = (ysize / 2 ) * gt[5] + gt[3]

        start_point = (point_x, point_y)
        
        LOGGER.debug('Starting Point : %s', start_point)
        
        # A default length and width to test against
        x_len = 2333
        y_len = 5327

        # What the area should be
        expected_area = 12427891

        wind_farm = wind_energy_core.create_rectangular_polygon(
                        spat_ref, start_point, x_len, y_len, out_uri)

        layer = wind_farm.GetLayer()
        feat = layer.GetFeature(0)
        geom = feat.GetGeometryRef()

        # Check that the areas are the same
        self.assertEqual(geom.Area(), expected_area)
        # Do a general check that the shapefiles are the same
        invest_test_core.assertTwoShapesEqual(self, wind_farm, reg_ds)

        geom = None
        feat = None
        layer = None
        wind_farm = None
        reg_ds = None
        dataset = None


