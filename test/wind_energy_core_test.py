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
        #raise SkipTest
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
