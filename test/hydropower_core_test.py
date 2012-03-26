"""URI level tests for the hydropower core module"""

import unittest
import logging
import os
import csv

from osgeo import gdal
from osgeo import ogr
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.hydropower import hydropower_core
import invest_cython_core
import invest_test_core

LOGGER = logging.getLogger('water_yield_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHydropowerCore(unittest.TestCase):
    """Main testing class for the water yield tests"""
#    def test_water_yield_re(self):
#        base = './data/hydropower_data/'
#        args = {}
#        args['workspace_dir'] = base
#        args['lulc_uri'] = base + 'test_input/landuse_90'
#        args['soil_depth_uri'] = base + 'test_input/soil_depth'
#        args['precipitation_uri'] = base + 'test_input/precip'
#        args['pawc_uri'] = base + 'test_input/pawc'
#        args['ape_uri'] = base + 'test_input/eto'
#        args['watersheds_uri'] = base + 'test_input/watersheds.shp'
#        args['sub_watersheds_uri'] = base + 'test_input/subwatersheds.shp'
#        args['biophysical_table_uri'] = \
#            base + 'test_input/Biophysical_Models.csv'
#        args['zhang'] = 5.0
#        
#        water_yield.execute(args)

#    def test_create_raster(self):
#        
#        dict = {1 : {'etk': '25'}, 2: {'etk': '1000'}, 
#                3 : {'etk': '250'}, 4: {'etk': '500'}}
#        driver = gdal.GetDriverByName("GTIFF")
#        #Create a blank xDim x yDim raster
#        lulc = driver.Create('./data/hydropower_data/test_blank_input.tif', 10,
#                             10, 1, gdal.GDT_Float32)
#        lulc.GetRasterBand(1).SetNoDataValue(255)
#        #Fill raster with nodata 
#        lulc.GetRasterBand(1).Fill(lulc.GetRasterBand(1).GetNoDataValue())
#        
#        array = np.array([[255, 1, 2, 255, 255, 3, 4, 4, 1, 2],
#                          [255, 1, 2, 2, 3, 3, 4, 4, 1, 2],
#                          [255, 1, 2, 2, 3, 3, 4, 4, 1, 2],
#                          [1, 1, 2, 2, 3, 3, 4, 4, 255, 255],
#                          [1, 1, 2, 2, 3, 3, 4, 4, 255, 255],
#                          [255, 1, 2, 2, 2, 2, 3, 3, 3, 3],
#                          [255, 4, 4, 2, 2, 1, 1, 1, 1, 3],
#                          [1, 3, 3, 2, 2, 1, 1, 2, 3, 4],
#                          [1, 2, 3, 4, 1, 2, 3, 4, 1, 2],
#                          [4, 4, 2, 2, 1, 255, 255, 255, 255, 2]])
#        
#        lulc.GetRasterBand(1).WriteArray(array, 0, 0)
#        new_path = './data/hydropower_data/test_blank_output.tif'
#        new_raster = \
#            hydropower_core.create_etk_root_rasters(lulc, new_path, \
#                                                    255, dict, 'etk')
#        new_array = np.array([[255, 25, 1000, 255, 255, 250, 500, 500, 25, 1000],
#                              [255, 25, 1000, 1000, 250, 250, 500, 500, 25, 1000],
#                              [255, 25, 1000, 1000, 250, 250, 500, 500, 25, 1000],
#                              [25, 25, 1000, 1000, 250, 250, 500, 500, 255, 255],
#                              [25, 25, 1000, 1000, 250, 250, 500, 500, 255, 255],
#                              [255, 25, 1000, 1000, 1000, 1000, 250, 250, 250, 250],
#                              [255, 500, 500, 1000, 1000, 25, 25, 25, 25, 250],
#                              [25, 250, 250, 1000, 1000, 25, 25, 1000, 250, 500],
#                              [25, 1000, 250, 500, 25, 1000, 250, 500, 25, 1000],
#                              [500, 500, 1000, 1000, 25, 255, 255, 255, 255, 1000]])
#        
#        array_result = new_raster.GetRasterBand(1).ReadAsArray()
#        
#        self.assertTrue((array_result==new_array).all)
        
    def test_create_writer_table_watershed(self):
        
        wrk_dir = './data/test_out/hydropower_water_yield_tables/'
        table_path = wrk_dir + os.sep + 'water_yield_watershed.csv'
        if not os.path.isdir(wrk_dir):
            os.mkdir(wrk_dir)
        if os.path.isfile(table_path):
            os.remove(table_path)
        
        field_list = ['ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 
                      'wyield_sum']
        
        water_dict = {}
        water_dict['precip_mn'] = {1:1654.32, 2:1432, 3:1948.593}
        water_dict['PET_mn'] = {1:432.65, 2:123.43, 3:342.34}
        water_dict['AET_mn'] = {1:88.88, 2:99.99, 3:111.11}
        water_dict['wyield_mn'] = {1:2222.22, 2:4444.44, 3:3333}
        water_dict['wyield_sum'] = {1:555.55, 2:666.66, 3:777}
        
        new_table = hydropower_core.create_writer_table(table_path, field_list, 
                                                        water_dict)
        
        new_table.close()
        
        expected_rows = \
            np.array([['ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 'wyield_sum'],
             [1, 1654.32, 432.65, 88.88, 2222.22, 555.55],
             [2, 1432, 123.43, 99.99, 4444.44, 666.66],
             [3, 1948.593, 342.34, 111.11, 3333, 777]])
        
        new_table = open(table_path, 'rb')
        reader = csv.reader(new_table)
        i = 0
        for row in reader:
            try:
                self.assertTrue((expected_rows[i]==row).all())
                i = i+1
            except:
                self.fail('The CSV files are not the same')
                
    def test_create_writer_table_subwatershed(self):
        
        wrk_dir = './data/test_out/hydropower_water_yield_tables/'
        table_path = wrk_dir + os.sep + 'water_yield_subwatershed.csv'
        if not os.path.isdir(wrk_dir):
            os.mkdir(wrk_dir)
        if os.path.isfile(table_path):
            os.remove(table_path)
        
        field_list = ['ws_id', 'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 
                      'wyield_mn','wyield_sum']
        wsr = {1:1, 2:2, 3:2, 4:1}
        water_dict = {}
        water_dict['precip_mn'] = {1:1654.32, 2:1432, 3:1948.593, 4:1212.12}
        water_dict['PET_mn'] = {1:432.65, 2:123.43, 3:342.34, 4:2323.23}
        water_dict['AET_mn'] = {1:88.88, 2:99.99, 3:111.11, 4:343.43}
        water_dict['wyield_mn'] = {1:2222.22, 2:4444.44, 3:3333, 4:5656}
        water_dict['wyield_sum'] = {1:555.55, 2:666.66, 3:777, 4:6767}
        
        new_table = hydropower_core.create_writer_table(table_path, field_list, 
                                                        water_dict, wsr)
        
        new_table.close()
        
        expected_rows = \
            np.array([['ws_id', 'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 'wyield_sum'],
             [1, 1, 1654.32, 432.65, 88.88, 2222.22, 555.55],
             [2, 2, 1432, 123.43, 99.99, 4444.44, 666.66],
             [2, 3, 1948.593, 342.34, 111.11, 3333, 777],
             [1, 4, 1212.12, 2323.23, 343.43, 5656, 6767]])
        
        new_table = open(table_path, 'rb')
        reader = csv.reader(new_table)
        i = 0
        for row in reader:
            try:
                self.assertTrue((expected_rows[i]==row).all())
                i = i+1
            except:
                self.fail('The CSV files are not the same')
                
                
    def test_polygons_in_polygons(self):
        
        wrk_dir = './data/hydropower_data/test_input'
        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
        sheds_path = wrk_dir + os.sep + 'watersheds.shp'
        
        sub_sheds = ogr.Open(sub_sheds_path)
        sheds = ogr.Open(sheds_path)
        
        shed_relationship = \
            hydropower_core.polygon_contains_polygons(sheds, sub_sheds)
        
        expected_dict = {}
        expected_dict[1] = 0
        expected_dict[2] = 0
        expected_dict[3] = 0
        expected_dict[4] = 1
        expected_dict[5] = 1
        expected_dict[6] = 1
        expected_dict[7] = 2
        expected_dict[8] = 2
        expected_dict[9] = 2
        
        for key, val in shed_relationship.iteritems():
            if key in expected_dict:
                self.assertEqual(val, expected_dict[key])
            else:
                self.fail('Keys do not match')
                
        sub_sheds.Destroy()
        sheds.Destroy()
        
    def test_create_mean_raster_regression(self):
        
        out_dir = './data/test_out/hydropower_create_mean_raster'
        output_path = out_dir + os.sep + 'mean_aet.tif'
        
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        if os.path.isfile(output_path):
            os.remove(output_path)
        
        wrk_dir = './data/hydropower_data/test_input'
        regression_dir = './data/hydropower_regression_data'
        
        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
        aet_path = wrk_dir + os.sep + 'test_aet_mn.tif'
        mask_path = regression_dir + os.sep + 'sub_shed_mask_regression.tif'
        reg_mean_path = regression_dir + os.sep + 'aet_mn_regression.tif'
        
        sub_sheds = ogr.Open(sub_sheds_path)
        aet_raster = gdal.Open(aet_path)
        aet_regression_raster = gdal.Open(reg_mean_path)
        
        mask_raster = gdal.Open(mask_path)
        mask_band = mask_raster.GetRasterBand(1)
        mask = mask_band.ReadAsArray()
        
        field_name = 'subws_id'
        
        new_raster = hydropower_core.create_mean_raster(aet_raster, output_path, 
                                                        sub_sheds, field_name, 
                                                        mask)
        
        invest_test_core.assertTwoDatasetsEqual(self, aet_regression_raster, 
                                                new_raster)

    def test_create_mean_raster_byhand(self):
        
        out_dir = './data/test_out/hydropower_create_mean_raster'
        output_path = out_dir + os.sep + 'mean_byhand.tif'
        
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        if os.path.isfile(output_path):
            os.remove(output_path)
        
        wrk_dir = './data/hydropower_data/test_input'
        
        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
        
        sub_sheds = ogr.Open(sub_sheds_path)
        
        field_name = 'subws_id'
        
        #Create two 3x3 rasters in memory
        base = gdal.Open('./data/hydropower_data/test_input/test_aet_mn.tif', 
                         gdal.GA_ReadOnly)
        cols = 4
        rows = 4
        projection = base.GetProjection()
        geotransform = base.GetGeoTransform()
        value_raster = invest_cython_core.newRaster(cols, rows, projection,
            geotransform, 'GTiff', -1, gdal.GDT_Float32, 1,
            './data/test_out/hydropower_create_mean_raster/mean_byhand.tif')

        #This is a test case that was calculated by hand
        array = np.array([[111, 115, 999, 1],
                          [108, 109, 999, 1],
                          [105, 102, 999, 1],
                          [100, 124, 888, 1]])

        value_raster.GetRasterBand(1).WriteArray(array, 0, 0)

        mask = np.array([[9, 8, 7, 7],
                         [6, 6, 5, 5],
                         [4, 4, 3, 3],
                         [2, 2, 1, 1]])
        
        mean_calc = np.array([[111, 115, 500, 500],
                              [108.5, 108.5, 500, 500],
                              [103.5, 103.5, 500, 500],
                              [112, 112, 444.5, 444.5]])
        
        new_raster = hydropower_core.create_mean_raster(value_raster, output_path, 
                                                        sub_sheds, field_name, 
                                                        mask)

        new_array = new_raster.GetRasterBand(1).ReadAsArray()
        
        self.assertTrue(mean_calc.shape == new_array.shape)
        
        for i, j in zip(mean_calc, new_array):
            for m, n in zip(i,j):
                self.assertAlmostEqual(m, n, 4)
        
        
    def test_create_area_raster_regression(self):
        
        out_dir = './data/test_out/hydropower_create_area_raster'
        output_path = out_dir + os.sep + 'area_wyield.tif'
        
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        if os.path.isfile(output_path):
            os.remove(output_path)
        
        wrk_dir = './data/hydropower_data/test_input'
        regression_dir = './data/hydropower_regression_data'
        
        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
        wyield_path = wrk_dir + os.sep + 'test_wyield.tif'
        mask_path = regression_dir + os.sep + 'sub_shed_mask_regression.tif'
        reg_area_path = regression_dir + os.sep + 'wyield_area_regression.tif'
        
        sub_sheds = ogr.Open(sub_sheds_path)
        wyield_raster = gdal.Open(wyield_path)
        wyield_regression_raster = gdal.Open(reg_area_path)
        
        mask_raster = gdal.Open(mask_path)
        mask_band = mask_raster.GetRasterBand(1)
        mask = mask_band.ReadAsArray()
        
        field_name = 'subws_id'
        
        new_raster = hydropower_core.create_area_raster(wyield_raster, output_path, 
                                                        sub_sheds, field_name, 
                                                        mask)
        
        invest_test_core.assertTwoDatasetsEqual(self, wyield_regression_raster, 
                                                new_raster)

    def test_create_area_raster_byhand(self):
        
        out_dir = './data/test_out/hydropower_create_area_raster'
        output_path = out_dir + os.sep + 'area_byhand.tif'
        
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        if os.path.isfile(output_path):
            os.remove(output_path)
        
        wrk_dir = './data/hydropower_data/test_input'
        
        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
        
        sub_sheds = ogr.Open(sub_sheds_path)
        
        field_name = 'subws_id'
        
        #Create two 3x3 rasters in memory
        base = gdal.Open('./data/hydropower_data/test_input/test_aet_mn.tif', 
                         gdal.GA_ReadOnly)
        cols = 4
        rows = 4
        projection = base.GetProjection()
        geotransform = base.GetGeoTransform()
        value_raster = invest_cython_core.newRaster(cols, rows, projection,
            geotransform, 'GTiff', -1, gdal.GDT_Float32, 1,
            './data/test_out/hydropower_create_area_raster/area_byhand.tif')

        #This is a test case that was calculated by hand
        area_calc = np.array([[964800, 7857000, 10057500, 10057500],
                          [11385900, 11385900, 32837400, 32837400],
                          [39781800, 39781800, 19117800, 19117800],
                          [5412600, 5412600, 17784900, 17784900]])

        mask = np.array([[9, 8, 7, 7],
                         [6, 6, 5, 5],
                         [4, 4, 3, 3],
                         [2, 2, 1, 1]])

        new_raster = hydropower_core.create_area_raster(value_raster, output_path, 
                                                        sub_sheds, field_name, 
                                                        mask)

        new_array = new_raster.GetRasterBand(1).ReadAsArray()
        
        self.assertTrue(area_calc.shape == new_array.shape)
        
        for i, j in zip(area_calc, new_array):
            for m, n in zip(i,j):
                self.assertAlmostEqual(m, n, 4)
        
        
