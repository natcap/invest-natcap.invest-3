"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess
import logging

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from nose.plugins.skip import SkipTest
import numpy as np
from invest_natcap import raster_utils
import invest_test_core

LOGGER = logging.getLogger('invest_core')

class TestRasterUtils(unittest.TestCase):
    def test_vectorize_points(self):
        base_dir = 'data/test_out/raster_utils'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        shape_uri = os.path.join('data', 'marine_water_quality_data', 'TideE_WGS1984_BCAlbers.shp')
        shape = ogr.Open(shape_uri)

        output_uri = os.path.join(base_dir, 'interp_points.tif')
        out_raster = raster_utils.create_raster_from_vector_extents(30, 30, gdal.GDT_Float32, -1, output_uri, shape)
        raster_utils.vectorize_points(shape, 'kh_km2_day', out_raster)
        out_raster = None
        regression_uri = 'data/vectorize_points_regression_data/interp_points.tif'

        invest_test_core.assertTwoDatasetEqualURI(self, output_uri, regression_uri)

    def test_clip_datset(self):
        base_dir = 'data/test_out/raster_utils'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        global_clip_regression_dataset = 'data/clip_data/global_clipped.tif'
        dem_uri = '../../invest-data/Base_Data/Marine/DEMs/global_dem'
        aoi_uri = 'data/wind_energy_data/wind_energy_aoi.shp'
        dem = gdal.Open(dem_uri)
        aoi = ogr.Open(aoi_uri)
        
        global_clip_dataset = os.path.join(base_dir, 'global_clipped.tif')
        raster_utils.clip_dataset(dem, aoi, global_clip_dataset)
        invest_test_core.assertTwoDatasetEqualURI(self, global_clip_dataset, global_clip_regression_dataset)

    def test_calculate_slope(self):
        dem_points = {
            (0.0,0.0): 50,
            (0.0,1.0): 100,
            (1.0,0.0): 90,
            (1.0,1.0): 0,
            (0.5,0.5): 45}

        n = 100

        base_dir = 'data/test_out/raster_utils'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dem_uri = os.path.join(base_dir,'raster_dem.tif')
        dem_dataset = invest_test_core.make_sample_dem(n,n,dem_points, 5.0, -1, dem_uri)

        slope_uri = os.path.join(base_dir,'raster_slope.tif')
        raster_utils.calculate_slope(dem_dataset, slope_uri)

        subprocess.Popen(["qgis", dem_uri, slope_uri])

    def test_calculate_value_not_in_array(self):
        array = np.array([-1,2,5,-8,-9])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)

        array = np.array([-1,-1,-1])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)

        array = np.array([-1.1,-1.2,-1.2])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)

    def test_create_rat_with_no_rat(self):
        test_out = './data/test_out/raster_utils/create_rat/'
        out_uri = os.path.join(test_out, 'test_RAT.tif')

        if not os.path.isdir(test_out):
            os.makedirs(test_out)
        
        dr = gdal.GetDriverByName('GTiff')
 
        ds = dr.Create(out_uri, 5, 5, 1, gdal.GDT_Int32)
        
        srs = osr.SpatialReference()
        srs.SetUTM(11,1)
        srs.SetWellKnownGeogCS('NAD27')
        ds.SetProjection(srs.ExportToWkt())
        ds.SetGeoTransform([444720, 30, 0, 3751320, 0 , -30])

        matrix = np.array([[1,2,3,4,5],
                           [5,4,3,2,1],
                           [3,2,4,5,1],
                           [2,1,3,4,5],
                           [4,5,1,2,3]])

        band = ds.GetRasterBand(1)
        band.SetNoDataValue(-1)
        band.WriteArray(matrix)
        band = None

        tmp_dict = {11:'farm', 23:'swamp', 13:'marsh', 22:'forest', 3:'river'}
        field_1 = 'DESC'
       
        known_results = np.array([[3, 'river'],
                                  [11, 'farm'],
                                  [13, 'marsh'],
                                  [22, 'forest'],
                                  [23, 'swamp']])

        ds_rat = raster_utils.create_rat(ds, tmp_dict, field_1)

        band = ds_rat.GetRasterBand(1)
        rat = band.GetDefaultRAT()
        col_count = rat.GetColumnCount()
        row_count = rat.GetRowCount()

        for row in range(row_count):
            for col in range(col_count):
                self.assertEqual(str(known_results[row][col]), rat.GetValueAsString(row, col))
        
        band = None
        rat = None
        ds = None
        ds_rat = None
        
    def test_get_raster_properties(self):
        """Test get_raster_properties against a known raster saved on disk"""
        data_dir = './data/raster_utils_data'
        ds_uri = os.path.join(data_dir, 'get_raster_properties_ds.tif')

        ds = gdal.Open(ds_uri)

        result_dict = raster_utils.get_raster_properties(ds)

        expected_dict = {'width':30, 'height':-30, 'x_size':1125, 'y_size':991}

        self.assertEqual(result_dict, expected_dict)

    def test_get_raster_properties_unit_test(self):
        """Test get_raster_properties against a hand created raster with set 
            properties"""
        driver = gdal.GetDriverByName('MEM')
        ds_type = gdal.GDT_Int32
        dataset = driver.Create('', 112, 142, 1, ds_type)

        srs = osr.SpatialReference()
        srs.SetUTM(11, 1)
        srs.SetWellKnownGeogCS('NAD27')
        dataset.SetProjection(srs.ExportToWkt())
        dataset.SetGeoTransform([444720, 30, 0, 3751320, 0, -30])
        dataset.GetRasterBand(1).SetNoDataValue(-1)
        dataset.GetRasterBand(1).Fill(5)
        
        result_dict = raster_utils.get_raster_properties(dataset)

        expected_dict = {'width':30, 'height':-30, 'x_size':112, 'y_size':142}

        self.assertEqual(result_dict, expected_dict)
