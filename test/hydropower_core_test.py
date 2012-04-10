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
    def test_water_yield_re(self):
        """Regression test for the water_yield function"""
        base = './data/hydropower_data'
        output_base = './data/test_out/water_yield_out/'
        args = {}
        args['workspace_dir'] = output_base
        args['lulc'] = gdal.Open(base + '/test_input/landuse_90')
        args['soil_depth'] = gdal.Open(base + '/test_input/soil_depth')
        args['precipitation'] = gdal.Open(base + '/test_input/precip')
        args['pawc'] = gdal.Open(base + '/test_input/pawc')
        args['eto'] = gdal.Open(base + '/test_input/eto')
        args['watersheds'] = ogr.Open(base + '/test_input/watersheds.shp')
        args['sub_watersheds'] = ogr.Open(base + '/test_input/subwatersheds.shp')
        args['seasonality_constant'] = 5
        args['results_suffix'] = ''
        
        biophysical_table_uri = base + '/test_input/Biophysical_Models.csv'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
        
        #Create the output directories
        for folder_name in ['Output', 'Service', 'Intermediate']:
            folder_path = output_base + os.sep + folder_name
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
                
        pixel_dir = output_base + os.sep + 'Output/Pixel'
        
        if not os.path.isdir(pixel_dir):
            os.mkdir(pixel_dir)
        
        #Open/read in the csv files into a dictionary and add to arguments
        biophysical_table_map = {}
        biophysical_table_file = open(biophysical_table_uri)
        reader = csv.DictReader(biophysical_table_file)
        for row in reader:
            biophysical_table_map[row['lucode']] = row
        
        args['biophysical_dictionary'] = biophysical_table_map
        
        hydropower_core.water_yield(args)
        
        regression_dir = './data/hydropower_regression_data/'
        reg_pixel_aet_uri = regression_dir + 'aet_regression.tif'
        reg_pixel_fractp_uri = regression_dir + 'fractp_regression.tif'
        reg_pixel_wyield_uri = regression_dir + 'wyield_regression.tif'
        reg_fractp_mn_uri = regression_dir + 'fractp_mn_regression.tif'
        reg_wyield_ha_uri = regression_dir + 'wyield_ha_regression.tif'
        reg_wyield_vol_uri = regression_dir + 'wyield_vol_regression.tif'
        reg_wyield_mn_uri = regression_dir + 'wyield_mn_regression.tif'
        reg_aet_mn_uri = regression_dir + 'aet_mn_regression.tif'
        reg_ws_table_uri = regression_dir + 'ws_wyield_table_regression.csv'
        reg_sws_table_uri = regression_dir + 'sws_wyield_table_regression.csv'
        
        pixel_aet_uri = output_base + 'Output/Pixel/aet.tif'
        pixel_fractp_uri = output_base + 'Output/Pixel/fractp.tif'
        pixel_wyield_uri = output_base + 'Output/Pixel/wyield.tif'
        fractp_mn_uri = output_base + 'Output/fractp_mn.tif'
        wyield_ha_uri = output_base + 'Service/wyield_ha.tif'
        wyield_vol_uri = output_base + 'Service/wyield_vol.tif'
        wyield_mn_uri = output_base + 'Service/wyield_mn.tif'
        aet_mn_uri = output_base + 'Output/aet_mn.tif'
        ws_table_uri = output_base + 'Output/water_yield_watershed.csv'
        sws_table_uri = output_base + 'Output/water_yield_subwatershed.csv'
        
        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_aet_uri, 
                                                  pixel_aet_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_fractp_uri, 
                                                  pixel_fractp_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_wyield_uri, 
                                                  pixel_wyield_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_fractp_mn_uri, 
                                                  fractp_mn_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_ha_uri, 
                                                  wyield_ha_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_vol_uri, 
                                                  wyield_vol_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_mn_uri, 
                                                  wyield_mn_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_aet_mn_uri, 
                                                  aet_mn_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_ws_table_uri, 
                                              ws_table_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_sws_table_uri, 
                                              sws_table_uri)
#        
#    def test_raster_from_table_values_hand(self):
#        #TEST create_etk_root function to see how it handles if a LULC Code
#        #in the table does not exist on the lulc raster
#
#        dict = {1 : {'etk': '25'}, 2: {'etk': '1000'}, 
#                3 : {'etk': '250'}, 4: {'etk': '500'}}
#        
#        driver = gdal.GetDriverByName("GTIFF")
#        #Create a blank xDim x yDim raster
#        lulc = driver.Create('./data/test_out/test_blank_input.tif', 10,
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
#            hydropower_core.raster_from_table_values(lulc, new_path,dict, 'etk')
#
#        new_array = \
#            np.array([[255, 25, 1000, 255, 255, 250, 500, 500, 25, 1000],
#                      [255, 25, 1000, 1000, 250, 250, 500, 500, 25, 1000],
#                      [255, 25, 1000, 1000, 250, 250, 500, 500, 25, 1000],
#                      [25, 25, 1000, 1000, 250, 250, 500, 500, 255, 255],
#                      [25, 25, 1000, 1000, 250, 250, 500, 500, 255, 255],
#                      [255, 25, 1000, 1000, 1000, 1000, 250, 250, 250, 250],
#                      [255, 500, 500, 1000, 1000, 25, 25, 25, 25, 250],
#                      [25, 250, 250, 1000, 1000, 25, 25, 1000, 250, 500],
#                      [25, 1000, 250, 500, 25, 1000, 250, 500, 25, 1000],
#                      [500, 500, 1000, 1000, 25, 255, 255, 255, 255, 1000]])
#        
#        array_result = new_raster.GetRasterBand(1).ReadAsArray()
#        
#        self.assertTrue((array_result==new_array).all())
#
#    def test_raster_from_table_values_re(self):
#        #TEST create_etk_root function to see how it handles if a LULC Code
#        #in the table does not exist on the lulc raster
#        
#        lucl = gdal.Open('./data/hydropower/test_input/landuse_90')
#        
#        #Open/read in the csv files into a dictionary and add to arguments
#        bio_dict = {}
#        biophysical_table_file = \
#            open('./data/hydropower_data/test_input/Biophysical_Models.csv')
#        reader = csv.DictReader(biophysical_table_file)
#        for row in reader:
#            bio_dict[row['lucode']] = row
#    
#        new_path = './data/test_out/lulc_bio_out.tif'
#        
#        new_raster = \
#            hydropower_core.raster_from_table_values(lulc, new_path, bio_dict, 
#                                                     'etk')
#            
#        reg_raster_uri = './data/hydropower_regression_data/lulc_bio_reg.tif'
#        
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_raster_uri, 
#                                                  new_path)
#        
#    def test_create_writer_table_watershed(self):
#        
#        wrk_dir = './data/test_out/hydropower_water_yield_tables/'
#        table_path = wrk_dir + os.sep + 'water_yield_watershed.csv'
#        
#        if not os.path.isdir(wrk_dir):
#            os.mkdir(wrk_dir)
#        if os.path.isfile(table_path):
#            os.remove(table_path)
#        
#        field_list = ['ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 'wyield_mn', 
#                      'wyield_sum']
#        
#        water_dict = {}
#        water_dict['precip_mn'] = {1:1654.32, 2:1432, 3:1948.593}
#        water_dict['PET_mn'] = {1:432.65, 2:123.43, 3:342.34}
#        water_dict['AET_mn'] = {1:88.88, 2:99.99, 3:111.11}
#        water_dict['wyield_mn'] = {1:2222.22, 2:4444.44, 3:3333}
#        water_dict['wyield_sum'] = {1:555.55, 2:666.66, 3:777}
#        
#        new_table = hydropower_core.create_writer_table(table_path, field_list, 
#                                                        water_dict)
#        
#        new_table.close()
#        
#        expected_rows = np.array([['ws_id', 'precip_mn', 'PET_mn', 'AET_mn', 
#                                   'wyield_mn', 'wyield_sum'],
#                                  [1, 1654.32, 432.65, 88.88, 2222.22, 555.55],
#                                  [2, 1432, 123.43, 99.99, 4444.44, 666.66],
#                                  [3, 1948.593, 342.34, 111.11, 3333, 777]])
#        
#        new_table = open(table_path, 'rb')
#        reader = csv.reader(new_table)
#        i = 0
#        for row in reader:
#            try:
#                self.assertTrue((expected_rows[i]==row).all())
#                i = i+1
#            except:
#                self.fail('The CSV files are not the same')
#                
#    def test_create_writer_table_subwatershed(self):
#        
#        wrk_dir = './data/test_out/hydropower_water_yield_tables/'
#        table_path = wrk_dir + os.sep + 'water_yield_subwatershed.csv'
#        
#        if not os.path.isdir(wrk_dir):
#            os.mkdir(wrk_dir)
#        if os.path.isfile(table_path):
#            os.remove(table_path)
#        
#        field_list = ['ws_id', 'subws_id', 'precip_mn', 'PET_mn', 'AET_mn', 
#                      'wyield_mn','wyield_sum']
#        wsr = {1:1, 2:2, 3:2, 4:1}
#        water_dict = {}
#        water_dict['precip_mn'] = {1:1654.32, 2:1432, 3:1948.593, 4:1212.12}
#        water_dict['PET_mn'] = {1:432.65, 2:123.43, 3:342.34, 4:2323.23}
#        water_dict['AET_mn'] = {1:88.88, 2:99.99, 3:111.11, 4:343.43}
#        water_dict['wyield_mn'] = {1:2222.22, 2:4444.44, 3:3333, 4:5656}
#        water_dict['wyield_sum'] = {1:555.55, 2:666.66, 3:777, 4:6767}
#        
#        new_table = hydropower_core.create_writer_table(table_path, field_list, 
#                                                        water_dict, wsr)
#        
#        new_table.close()
#        
#        expected_rows = np.array([['ws_id', 'subws_id', 'precip_mn', 'PET_mn', 
#                                   'AET_mn', 'wyield_mn', 'wyield_sum'],
#                                [1, 1, 1654.32, 432.65, 88.88, 2222.22, 555.55],
#                                [2, 2, 1432, 123.43, 99.99, 4444.44, 666.66],
#                                [2, 3, 1948.593, 342.34, 111.11, 3333, 777],
#                                [1, 4, 1212.12, 2323.23, 343.43, 5656, 6767]])
#        
#        new_table = open(table_path, 'rb')
#        reader = csv.reader(new_table)
#        i = 0
#        for row in reader:
#            try:
#                self.assertTrue((expected_rows[i]==row).all())
#                i = i+1
#            except:
#                self.fail('The CSV files are not the same')
#                
#                
#    def test_sheds_map_subsheds(self):
#
#        wrk_dir = './data/hydropower_data/test_input'
#        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
#        sheds_path = wrk_dir + os.sep + 'watersheds.shp'
#        
#        sub_sheds = ogr.Open(sub_sheds_path)
#        sheds = ogr.Open(sheds_path)
#        
#        shed_relationship = \
#            hydropower_core.sheds_map_subsheds(sheds, sub_sheds)
#        
#        expected_dict = {}
#        expected_dict[1] = 0
#        expected_dict[2] = 0
#        expected_dict[3] = 0
#        expected_dict[4] = 1
#        expected_dict[5] = 1
#        expected_dict[6] = 1
#        expected_dict[7] = 2
#        expected_dict[8] = 2
#        expected_dict[9] = 2
#        
#        for key, val in shed_relationship.iteritems():
#            if key in expected_dict:
#                self.assertEqual(val, expected_dict[key])
#            else:
#                self.fail('Keys do not match')
#                
#        sub_sheds.Destroy()
#        sheds.Destroy()
#        
#    def test_create_operation_raster_re(self):
#
#        out_dir = './data/test_out/hydropower_create_mean_raster'
#        output_path = out_dir + os.sep + 'mean_aet.tif'
#        
#        if not os.path.isdir(out_dir):
#            os.mkdir(out_dir)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        wrk_dir = './data/hydropower_data/test_input'
#        regression_dir = './data/hydropower_regression_data'
#        
#        aet_path = wrk_dir + os.sep + 'test_aet_mn.tif'
#        mask_path = regression_dir + os.sep + 'sub_shed_mask_regression.tif'
#        reg_mean_path = regression_dir + os.sep + 'aet_mn_regression.tif'
#        
#        sub_sheds = ogr.Open(sub_sheds_path)
#        aet_raster = gdal.Open(aet_path)
#        aet_regression_raster = gdal.Open(reg_mean_path)
#        
#        mask_raster = gdal.Open(mask_path)
#        mask_band = mask_raster.GetRasterBand(1)
#        mask = mask_band.ReadAsArray()
#
#        id_list = [1,2,3,4,5,6,7,8,9]        
#        dict = {}
#        
#        new_raster = \
#            hydropower_core.create_operation_raster(aet_raster, output_path, 
#                                                    id_list, 'mean', mask, dict)
#       
#        invest_test_core.assertTwoDatasetsEqual(self, aet_regression_raster, 
#                                                new_raster)
#
#    def test_create_operation_raster_byhand(self):
#        
#        out_dir = './data/test_out/hydropower_create_mean_raster'
#        output_path = out_dir + os.sep + 'mean_byhand.tif'
#        
#        if not os.path.isdir(out_dir):
#            os.mkdir(out_dir)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        wrk_dir = './data/hydropower_data/test_input'
#        
#        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
#        
#        sub_sheds = ogr.Open(sub_sheds_path)
#        
#        field_name = 'subws_id'
#        
#        #Create two 3x3 rasters in memory
#        base = gdal.Open('./data/hydropower_data/test_input/test_aet_mn.tif', 
#                         gdal.GA_ReadOnly)
#        cols = 4
#        rows = 4
#        projection = base.GetProjection()
#        geotransform = base.GetGeoTransform()
#        value_raster = \
#            invest_cython_core.newRaster(cols, rows, projection, geotransform, \
#                                         'GTiff', -1, gdal.GDT_Float32, 1, \
#            './data/test_out/hydropower_create_mean_raster/mean_byhand.tif')
#
#        #This is a test case that was calculated by hand
#        array = np.array([[111, 115, 999, 1],
#                          [108, 109, 999, 1],
#                          [105, 102, 999, 1],
#                          [100, 124, 888, 1]])
#
#        value_raster.GetRasterBand(1).WriteArray(array, 0, 0)
#
#        mask = np.array([[9, 8, 7, 7],
#                         [6, 6, 5, 5],
#                         [4, 4, 3, 3],
#                         [2, 2, 1, 1]])
#        
#        mean_calc = np.array([[111, 115, 500, 500],
#                              [108.5, 108.5, 500, 500],
#                              [103.5, 103.5, 500, 500],
#                              [112, 112, 444.5, 444.5]])
#        
#        dict = {}
#        
#        new_raster = \
#            hydropower_core.create_operation_raster(value_raster, output_path, 
#                                                    id_list, 'mean', mask, dict)
#
#        new_array = new_raster.GetRasterBand(1).ReadAsArray()
#        
#        self.assertTrue(mean_calc.shape == new_array.shape)
#        
#        for i, j in zip(mean_calc, new_array):
#            for m, n in zip(i,j):
#                self.assertAlmostEqual(m, n, 4)
#        
#        
#    def test_create_area_raster_regression(self):
#        
#        out_dir = './data/test_out/hydropower_create_area_raster'
#        output_path = out_dir + os.sep + 'area_wyield.tif'
#        
#        if not os.path.isdir(out_dir):
#            os.mkdir(out_dir)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        wrk_dir = './data/hydropower_data/test_input'
#        regression_dir = './data/hydropower_regression_data'
#        
#        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
#        wyield_path = wrk_dir + os.sep + 'test_wyield.tif'
#        mask_path = regression_dir + os.sep + 'sub_shed_mask_regression.tif'
#        reg_area_path = regression_dir + os.sep + 'wyield_area_regression.tif'
#        
#        sub_sheds = ogr.Open(sub_sheds_path)
#        wyield_raster = gdal.Open(wyield_path)
#        wyield_regression_raster = gdal.Open(reg_area_path)
#        
#        mask_raster = gdal.Open(mask_path)
#        mask_band = mask_raster.GetRasterBand(1)
#        mask = mask_band.ReadAsArray()
#        
#        field_name = 'subws_id'
#        
#        new_raster = hydropower_core.create_area_raster(wyield_raster, output_path, 
#                                                        sub_sheds, field_name, 
#                                                        mask)
#        
#        invest_test_core.assertTwoDatasetsEqual(self, wyield_regression_raster, 
#                                                new_raster)
#
#    def test_create_area_raster_byhand(self):
#        
#        out_dir = './data/test_out/hydropower_create_area_raster'
#        output_path = out_dir + os.sep + 'area_byhand.tif'
#        
#        if not os.path.isdir(out_dir):
#            os.mkdir(out_dir)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        wrk_dir = './data/hydropower_data/test_input'
#        
#        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
#        
#        sub_sheds = ogr.Open(sub_sheds_path)
#        
#        field_name = 'subws_id'
#        
#        #Create two 3x3 rasters in memory
#        base = gdal.Open('./data/hydropower_data/test_input/test_aet_mn.tif', 
#                         gdal.GA_ReadOnly)
#        cols = 4
#        rows = 4
#        projection = base.GetProjection()
#        geotransform = base.GetGeoTransform()
#        value_raster = invest_cython_core.newRaster(cols, rows, projection,
#            geotransform, 'GTiff', -1, gdal.GDT_Float32, 1,
#            './data/test_out/hydropower_create_area_raster/area_byhand.tif')
#
#        #This is a test case that was calculated by hand
#        area_calc = np.array([[964800, 7857000, 10057500, 10057500],
#                          [11385900, 11385900, 32837400, 32837400],
#                          [39781800, 39781800, 19117800, 19117800],
#                          [5412600, 5412600, 17784900, 17784900]])
#
#        mask = np.array([[9, 8, 7, 7],
#                         [6, 6, 5, 5],
#                         [4, 4, 3, 3],
#                         [2, 2, 1, 1]])
#
#        new_raster = hydropower_core.create_area_raster(value_raster, output_path, 
#                                                        sub_sheds, field_name, 
#                                                        mask)
#
#        new_array = new_raster.GetRasterBand(1).ReadAsArray()
#        
#        self.assertTrue(area_calc.shape == new_array.shape)
#        
#        for i, j in zip(area_calc, new_array):
#            for m, n in zip(i,j):
#                self.assertAlmostEqual(m, n, 4)
#        
#    def test_get_mask(self):
#        
#        out_dir = './data/test_out/hydropower_get_mask'
#        output_path = out_dir + os.sep + 'new_mask.tif'
#        
#        if not os.path.isdir(out_dir):
#            os.mkdir(out_dir)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        wrk_dir = './data/hydropower_data/test_input'
#        regression_dir = './data/hydropower_regression_data'
#        
#        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
#        wyield_path = wrk_dir + os.sep + 'test_wyield.tif'
#        regression_mask_path = \
#            regression_dir + os.sep + 'sub_shed_mask_regression.tif'
#        
#        sub_sheds = ogr.Open(sub_sheds_path)
#        wyield = gdal.Open(wyield_path)
#        reg_mask_raster = gdal.Open(regression_mask_path)
#        
#        reg_mask = reg_mask_raster.GetRasterBand(1).ReadAsArray()
#        field_name = 'subws_id'
#        
#        new_mask = \
#            hydropower_core.get_mask(wyield, output_path, sub_sheds, field_name)
#        
#        self.assertTrue(new_mask.shape == reg_mask.shape)
#        
#        for i, j in zip(reg_mask, new_mask):
#            for m, n in zip(i,j):
#                self.assertAlmostEqual(m, n, 4)
#        
#    def test_get_operation_value(self):
#        """A by hand test for the get_operation_value function
#        
#        """
#        
#        #place code here
#        wrk_dir = './data/hydropower_data/test_input'
#        mask_raster = wrk_dir + os.sep + 'sub_shed_mask.tif'
#        shed_mask = mask_raster.GetRasterBand(1).ReadAsArray()
#        raster = gdal.Open(wrk_dir + os.sep + 'wyield_clipped.tif')
#        id_list = [1,2,3,4,5,6,7,8,9]
#        operation = 'mean'
#        
#        result_dict = hydropower_core.get_operation_value(raster, id_list,
#                                                          shed_mask, operation)
#
#        calc_dict = {1:1016.74, 2:987.704, 3:1201.79, 4:1274.05, 5:1033.9,
#                     6:947.216, 7:1030.16, 8:1039.7, 9:934.463}
#
#        for key, val in calc_dict.iteritems():
#            self.assertAlmostEqual(val, result_dict[val], 1)
#        
#    def test_get_shed_ids(self):
#        """A by hand test for get_shed_ids function
#        
#        """
#        
#        #place code here
#        
#        value_array = np.array([[0,0,0,1,1,-1],
#                                [0,0,0,1,1,1],
#                                [-1,2,2,2,2,-1],
#                                [3,3,3,4,4,-1]])
#        
#        result_list = hydropower_core.get_shed_ids(value_array, nodata)
#        
#        calc_list = np.array([0,1,2,3,4])
#        
#        self.assertTrue((result_list==calc_list).all())
#        
#    def test_create_operation_raster_hand(self):
#        """A by hand test for the create_operation_raster function
#        
#        """
#        
#        #place code here
#        
#        
#    def test_create_operation_raster_regression(self):
#        """A regression test for create_operation_raster function
#        
#        """
#        
#        #place code here
#        
#        
#        
#    def test_clip_raster_from_polygon(self):
#        """A test case for this function.  I should already have some test
#        cases for this function from wave energy model
#        
#        """
#        
#        #place code here
#        
#    def test_clip_raster_from_polygon_re(self):
#        """A regression test for clip_raster_from_polygon function."""
#        test_dir = './data/hydropower_data'
#        output_dir = './data/test_out/hydropower_core_clip_raster_from_poly'
#        regression_dir = './data/hydropower_regression_data'
#        raster_input_path = \
#            test_dir + os.sep + 'test_input/fractp_tmp.tif'
#        copy_raster_input_path = \
#            output_dir + os.sep + 'clip_raster_from_poly_output.tif'
#        regression_raster_path = \
#            regression_dir + os.sep + 'clip_raster_from_poly_regression.tif'
#        clip_shape_path = \
#            test_dir + os.sep + 'test_input/subwatershed.shp'
#        
#        clip_shape = ogr.Open(clip_shape_path)
#        raster_input = gdal.Open(raster_input_path)
#
#        #Add the Output directory onto the given workspace
#        if not os.path.isdir(output_dir):
#            os.mkdir(output_dir)
#        
#        copy_raster = \
#            hydropower_core.clip_raster_from_polygon(clip_shape, raster_input, 
#                                                     copy_raster_input_path)
#        copy_raster.FlushCache()
#        #Check that resulting rasters are correct
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            regression_raster_path, copy_raster_input_path)
#                
#        copy_raster = None
#        raster_input = None
#        clip_shape.Destroy()
#        
#        
#        
#        
#        
#    def test_water_scarcity_regression(self):
#        """A regression test for the core water scarcity functionality
#        
#        """
#        
#        #place code here
#        
#
#    def test_write_scarcity_table(self):
#        """A by hand test for the write_scarcity_table function
#        
#        """
#        
#        #place code here
#        file_path = './data/test_out/write_scarcity_table.csv'
#        regression_path = \
#            './data/hydropower_regression_data/scarcity_reg_table.csv'
#        field_list = 'ws_id, area, volume, avg_weight'
#        shed_table = {0: {'ws_id':0, 'area':32, 'volume': 54, 'avg_weight':5},
#                      1: {'ws_id':1, 'area':28, 'volume': 48, 'avg_weight':8},
#                      2: {'ws_id':2, 'area':16, 'volume': 78, 'avg_weight':10}}
#        
#        hydropower_core.write_scarcity_table(shed_table, field_list, file_path)
#        
##        invest_test_core.assertTwoCSVEqualURI(self, regression_path, file_path)
#        
#    def test_sum_mean_dict_sum(self):
#        """A by hand test for the sum_mean_dict function
#        
#        """
#        
#        #place code here
#        dict1 = {0:[1,2,3], 1:[4,5,6], 2:[7,8,9]}
#        dict2 = {1:5, 2:7, 3:3, 4:21, 5:17, 6:13, 7:37, 8:83, 9:59}
#        expected_dict = {0:15, 1:51, 2:179}
#        
#        new_dict = hydropower_core.sum_mean_dict(dict1, dict2, 'sum')
#        
#        for key, val in expected_dict.iteritems():
#            if key in new_dict:
#                self.assertEqual(val, new_dict[key])
#            else:
#                self.fail('keys do not match')
#    
#    def test_sum_mean_dict_mean(self):
#        """A by hand test for the sum_mean_dict function
#        
#        """
#        
#        #place code here
#        dict1 = {0:[1,2,3], 1:[4,5,6], 2:[7,8,9]}
#        dict2 = {1:5, 2:7, 3:3, 4:21, 5:17, 6:13, 7:37, 8:83, 9:60}
#        expected_dict = {0:5, 1:17, 2:60}
#        
#        new_dict = hydropower_core.sum_mean_dict(dict1, dict2, 'mean')
#        
#        for key, val in expected_dict.iteritems():
#            if key in new_dict:
#                self.assertEqual(val, new_dict[key])
#            else:
#                self.fail('keys do not match')
#                
#    
#    def test_valuation_regression(self):
#        """A regression test for the core valuation functionality
#        
#        """
#        
#        #place code here
#        
#                
#    def test_make_raster(self):
#        
#        out_dir = './data/test_out/hydropower_get_mask'
#        output_path = out_dir + os.sep + 'new_mask.tif'
#        
#        if not os.path.isdir(out_dir):
#            os.mkdir(out_dir)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        wrk_dir = './data/hydropower_data/test_input'
#        regression_dir = './data/hydropower_regression_data'
#        
#        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
#        wyield_path = wrk_dir + os.sep + 'test_wyield.tif'
#        regression_mask_path = regression_dir + os.sep + 'sub_shed_mask_regression.tif'
#        new_raster_path = 
#        sub_sheds = ogr.Open(sub_sheds_path)
#        wyield = gdal.Open(wyield_path)
#        reg_mask_raster = gdal.Open(regression_mask_path)
#        
#        reg_mask = reg_mask_raster.GetRasterBand(1).ReadAsArray()
#        field_name = 'subws_id'