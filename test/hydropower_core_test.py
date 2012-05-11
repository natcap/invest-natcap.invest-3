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
    def test_hydropower_core_water_yield_re(self):
        """Regression test for the water_yield function in hydropower_core"""
        
        base = './data/hydropower_regression_data/hydro_regression_byhand/'
        output_base = './data/test_out/hydro_regression_byhand/'
        
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
        
        args = {}
        args['workspace_dir'] = output_base
        args['lulc'] = gdal.Open(base + 'lulc.tif')
        args['soil_depth'] = gdal.Open(base + 'soil_depth.tif')
        args['precipitation'] = gdal.Open(base + 'precipitation.tif')
        args['pawc'] = gdal.Open(base + 'pawc.tif')
        args['eto'] = gdal.Open(base + 'eto.tif')
        args['watersheds'] = ogr.Open(base + 'simple_reg_ws.shp')
        args['sub_watersheds'] = ogr.Open(base + 'simple_reg_subws.shp')
        args['seasonality_constant'] = 5
        args['results_suffix'] = ''
        
        #Open/read in the csv files into a dictionary and add to arguments
        biophysical_table_uri = base + 'Biophysical_Models.csv'
        biophysical_table_map = {}
        biophysical_table_file = open(biophysical_table_uri)
        reader = csv.DictReader(biophysical_table_file)
        for row in reader:
            biophysical_table_map[int(row['lucode'])] = \
                {'etk':float(row['etk']), 'root_depth':float(row['root_depth'])}

        args['biophysical_dictionary'] = biophysical_table_map
        
        hydropower_core.water_yield(args)
#        
#        regression_dir = './data/hydropower_regression_data/'
#        reg_pixel_aet_uri = regression_dir + 'aet_regression.tif'
#        reg_pixel_fractp_uri = regression_dir + 'fractp_regression.tif'
#        reg_pixel_wyield_uri = regression_dir + 'wyield_regression.tif'
#        reg_fractp_mn_uri = regression_dir + 'fractp_mn_regression.tif'
#        reg_wyield_ha_uri = regression_dir + 'wyield_ha_regression.tif'
#        reg_wyield_vol_uri = regression_dir + 'wyield_vol_regression.tif'
#        reg_wyield_mn_uri = regression_dir + 'wyield_mn_regression.tif'
#        reg_aet_mn_uri = regression_dir + 'aet_mn_regression.tif'
#        reg_ws_table_uri = regression_dir + 'ws_wyield_table_regression.csv'
#        reg_sws_table_uri = regression_dir + 'sws_wyield_table_regression.csv'
#        
#        pixel_aet_uri = output_base + 'Output/Pixel/aet.tif'
#        pixel_fractp_uri = output_base + 'Output/Pixel/fractp.tif'
#        pixel_wyield_uri = output_base + 'Output/Pixel/wyield.tif'
#        fractp_mn_uri = output_base + 'Output/fractp_mn.tif'
#        wyield_ha_uri = output_base + 'Service/wyield_ha.tif'
#        wyield_vol_uri = output_base + 'Service/wyield_vol.tif'
#        wyield_mn_uri = output_base + 'Service/wyield_mn.tif'
#        aet_mn_uri = output_base + 'Output/aet_mn.tif'
#        ws_table_uri = output_base + 'Output/water_yield_watershed.csv'
#        sws_table_uri = output_base + 'Output/water_yield_subwatershed.csv'
#        
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_aet_uri, 
#                                                  pixel_aet_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_fractp_uri, 
#                                                  pixel_fractp_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_wyield_uri, 
#                                                  pixel_wyield_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_fractp_mn_uri, 
#                                                  fractp_mn_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_ha_uri, 
#                                                  wyield_ha_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_vol_uri, 
#                                                  wyield_vol_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_mn_uri, 
#                                                  wyield_mn_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_aet_mn_uri, 
#                                                  aet_mn_uri)
#        invest_test_core.assertTwoCSVEqualURI(self, reg_ws_table_uri, 
#                                              ws_table_uri)
#        invest_test_core.assertTwoCSVEqualURI(self, reg_sws_table_uri, 
#                                              sws_table_uri)
#    def test_hydropower_core_water_yield_re(self):
#        """Regression test for the water_yield function in hydropower_core"""
#        
#        base = './data/hydropower_data'
#        output_base = './data/test_out/water_yield_out/'
#        args = {}
#        args['workspace_dir'] = output_base
#        args['lulc'] = gdal.Open(base + '/test_input/landuse_90')
#        args['soil_depth'] = gdal.Open(base + '/test_input/soil_depth')
#        args['precipitation'] = gdal.Open(base + '/test_input/precip')
#        args['pawc'] = gdal.Open(base + '/test_input/pawc')
#        args['eto'] = gdal.Open(base + '/test_input/eto')
#        args['watersheds'] = ogr.Open(base + '/test_input/watersheds.shp')
#        args['sub_watersheds'] = ogr.Open(base + '/test_input/subwatersheds.shp')
#        args['seasonality_constant'] = 5
#        args['results_suffix'] = ''
#        
#        biophysical_table_uri = base + '/test_input/Biophysical_Models.csv'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        
#        #Create the output directories
#        for folder_name in ['Output', 'Service', 'Intermediate']:
#            folder_path = output_base + os.sep + folder_name
#            if not os.path.isdir(folder_path):
#                os.mkdir(folder_path)
#                
#        pixel_dir = output_base + os.sep + 'Output/Pixel'
#        
#        if not os.path.isdir(pixel_dir):
#            os.mkdir(pixel_dir)
#        
#        #Open/read in the csv files into a dictionary and add to arguments
#        biophysical_table_map = {}
#        biophysical_table_file = open(biophysical_table_uri)
#        reader = csv.DictReader(biophysical_table_file)
#        for row in reader:
#            biophysical_table_map[row['lucode']] = row
#        
#        args['biophysical_dictionary'] = biophysical_table_map
#        
#        hydropower_core.water_yield(args)
#        
#        regression_dir = './data/hydropower_regression_data/'
#        reg_pixel_aet_uri = regression_dir + 'aet_regression.tif'
#        reg_pixel_fractp_uri = regression_dir + 'fractp_regression.tif'
#        reg_pixel_wyield_uri = regression_dir + 'wyield_regression.tif'
#        reg_fractp_mn_uri = regression_dir + 'fractp_mn_regression.tif'
#        reg_wyield_ha_uri = regression_dir + 'wyield_ha_regression.tif'
#        reg_wyield_vol_uri = regression_dir + 'wyield_vol_regression.tif'
#        reg_wyield_mn_uri = regression_dir + 'wyield_mn_regression.tif'
#        reg_aet_mn_uri = regression_dir + 'aet_mn_regression.tif'
#        reg_ws_table_uri = regression_dir + 'ws_wyield_table_regression.csv'
#        reg_sws_table_uri = regression_dir + 'sws_wyield_table_regression.csv'
#        
#        pixel_aet_uri = output_base + 'Output/Pixel/aet.tif'
#        pixel_fractp_uri = output_base + 'Output/Pixel/fractp.tif'
#        pixel_wyield_uri = output_base + 'Output/Pixel/wyield.tif'
#        fractp_mn_uri = output_base + 'Output/fractp_mn.tif'
#        wyield_ha_uri = output_base + 'Service/wyield_ha.tif'
#        wyield_vol_uri = output_base + 'Service/wyield_vol.tif'
#        wyield_mn_uri = output_base + 'Service/wyield_mn.tif'
#        aet_mn_uri = output_base + 'Output/aet_mn.tif'
#        ws_table_uri = output_base + 'Output/water_yield_watershed.csv'
#        sws_table_uri = output_base + 'Output/water_yield_subwatershed.csv'
#        
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_aet_uri, 
#                                                  pixel_aet_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_fractp_uri, 
#                                                  pixel_fractp_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_pixel_wyield_uri, 
#                                                  pixel_wyield_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_fractp_mn_uri, 
#                                                  fractp_mn_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_ha_uri, 
#                                                  wyield_ha_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_vol_uri, 
#                                                  wyield_vol_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_wyield_mn_uri, 
#                                                  wyield_mn_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_aet_mn_uri, 
#                                                  aet_mn_uri)
#        invest_test_core.assertTwoCSVEqualURI(self, reg_ws_table_uri, 
#                                              ws_table_uri)
#        invest_test_core.assertTwoCSVEqualURI(self, reg_sws_table_uri, 
#                                              sws_table_uri)
#        
#    def test_hydropower_core_raster_from_table_values_hand(self):
#        """Hand calculated test to make sure that rasters are being
#           created from table values correctly
#        """
#        #TEST create_etk_root function to see how it handles if a LULC Code
#        #in the table does not exist on the lulc raster
#        
#        output_base = './data/test_out/hydropower_raster_from_table/'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        
#        dict = {1 : {'etk': 25.0}, 2: {'etk': 1000.0}, 
#                3 : {'etk': 250.0}, 4: {'etk': 500.0}}
#        
#        driver = gdal.GetDriverByName("GTIFF")
#        #Create a blank xDim x yDim raster
#        lulc = driver.Create(output_base + 'test_10x10_lulc.tif', 10,
#                             10, 1, gdal.GDT_Int32)
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
#                          [4, 4, 2, 2, 1, 255, 255, 255, 255, 8]])
#        
#        lulc.GetRasterBand(1).WriteArray(array, 0, 0)
#        new_path = output_base + 'test_10x10_etk_root.tif'
#        new_raster = \
#            hydropower_core.raster_from_table_values(lulc, new_path,dict, 'etk')
#
#        result_array = \
#            np.array([[255, 25, 1000, 255, 255, 250, 500, 500, 25, 1000],
#                      [255, 25, 1000, 1000, 250, 250, 500, 500, 25, 1000],
#                      [255, 25, 1000, 1000, 250, 250, 500, 500, 25, 1000],
#                      [25, 25, 1000, 1000, 250, 250, 500, 500, 255, 255],
#                      [25, 25, 1000, 1000, 250, 250, 500, 500, 255, 255],
#                      [255, 25, 1000, 1000, 1000, 1000, 250, 250, 250, 250],
#                      [255, 500, 500, 1000, 1000, 25, 25, 25, 25, 250],
#                      [25, 250, 250, 1000, 1000, 25, 25, 1000, 250, 500],
#                      [25, 1000, 250, 500, 25, 1000, 250, 500, 25, 1000],
#                      [500, 500, 1000, 1000, 25, 255, 255, 255, 255, 255]])
#        
#        array_result = new_raster.GetRasterBand(1).ReadAsArray()
#
#        self.assertTrue((array_result==result_array).all())
#
#    def test_hydropower_core_raster_from_table_values_re(self):
#        """ A regression test to make sure that rasters created from table
#            values are correct
#        """
#        #TEST create_etk_root function to see how it handles if a LULC Code
#        #in the table does not exist on the lulc raster
#        
#        input_dir = './data/hydropower_data/test_input/'
#        output_base = './data/test_out/hydropower_raster_from_table/'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        
#        lulc = gdal.Open(input_dir + 'landuse_90')
#        
#        #Open/read in the csv files into a dictionary and add to arguments
#        bio_dict = {}
#        biophysical_table_file = open(input_dir + 'Biophysical_Models.csv')
#        reader = csv.DictReader(biophysical_table_file)
#        for row in reader:
#            bio_dict[int(row['lucode'])] = \
#                {'etk':float(row['etk']), 'root_depth':float(row['root_depth'])}
#            
#        new_path = output_base + 'test_etk_reg.tif'
#        
#        new_raster = \
#            hydropower_core.raster_from_table_values(lulc, new_path, bio_dict, 
#                                                     'etk')
#        new_raster = None
#        
#        reg_raster_uri = \
#            './data/hydropower_regression_data/test_etk_regression.tif'
#        
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_raster_uri, 
#                                                  new_path)
#        
#    def test_hydropower_core_create_writer_table_watershed(self):
#        """A hand calculated test case to make sure that the water yield
#           tables are getting created correctly
#        """
#        
#        output_base = './data/test_out/hydropower_water_yield_tables/'
#        table_path = output_base + 'test_wyield_watershed.csv'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
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
#            row = np.array(row)
#            try:
#                self.assertTrue((expected_rows[i]==row).all())
#                i = i+1
#            except:
#                self.fail('The CSV files are not the same')
#        
#    def test_hydropower_core_create_writer_table_subwatershed(self):
#        """Similar test to the one above for checking the water yield table
#           function, but this time using subwatershed properties
#        """
#        output_base = './data/test_out/hydropower_water_yield_tables/'
#        table_path = output_base + 'test_wyield_subwatershed.csv'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
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
#            row = np.array(row)
#            try:
#                self.assertTrue((expected_rows[i]==row).all())
#                i = i+1
#            except:
#                self.fail('The CSV files are not the same')
#                
#    def test_hydropower_core_sheds_map_subsheds(self):
#        """A hand calculated test to make sure that sub watersheds can be
#           identified with watersheds
#        """
#        
#        input_dir = './data/hydropower_data/test_input/'
#        output_base = './data/test_out/hydropower_sheds_map_subsheds/'
#
#        sub_sheds_path = input_dir + 'subwatersheds.shp'
#        sheds_path = input_dir + 'watersheds.shp'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
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
#    def test_hydropower_core_sheds_map_subsheds_calc(self):
#        """A test to see if the function sheds_map_subsheds can correctly 
#           match polygons from two different shapefiles that overlap each other.
#           Here, I created two polygon shapefiles by hand and test them
#        """
#        
#        input_dir = './data/hydropower_data/test_input/'
#        output_base = './data/test_out/hydropower_sheds_map_subsheds/'
#
#        sub_sheds_path = input_dir + 'test_hydro_sheds.shp'
#        sheds_path = input_dir + 'test_hydro_subsheds.shp'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#            
#        sub_sheds = ogr.Open(sub_sheds_path)
#        sheds = ogr.Open(sheds_path)
#        
#        shed_relationship = \
#            hydropower_core.sheds_map_subsheds(sheds, sub_sheds)
#        
#        expected_dict = {}
#        expected_dict[1] = 3
#        expected_dict[2] = 3
#        expected_dict[3] = 2
#        expected_dict[4] = 1
#        expected_dict[5] = 1
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
#    def test_hydropower_core_create_operation_raster_re(self):
#        """A regression test to ensure that the proper mean raster is
#           being created
#        """
#        
#        output_base = './data/test_out/hydropower_create_mean_raster'
#        output_path = output_base + 'test_mean_aet.tif'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        input_dir = './data/hydropower_data/test_input/'
#        regression_dir = './data/hydropower_regression_data/'
#        
#        aet_path = input_dir + 'test_aet_mn.tif'
#        mask_path = regression_dir + 'sub_shed_mask_regression.tif'
#        reg_mean_path = regression_dir + 'aet_mn_regression.tif'
#        
#        aet_raster = gdal.Open(aet_path)
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
#        new_raster = None
#        mask_raster = None
#
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_mean_path, 
#                                                  output_path)
#        
#    def test_hydropower_core_create_operation_raster_re2(self):
#        """A regression test to ensure that the proper sum raster is
#           being created
#        """
#        
#        output_base = './data/test_out/hydropower_create_mean_raster'
#        output_path = output_base + 'test_sum_consum_vol.tif'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        input_dir = './data/hydropower_data/test_input/'
#        regression_dir = './data/hydropower_regression_data/'
#        
#        base_raster_path = regression_dir + 'clipped_consum_regression.tif'
#        mask_path = regression_dir + 'sub_shed_mask2_regression.tif'
#        reg_sum_path = regression_dir + 'consum_vol_regression.tif'
#        
#        base_raster = gdal.Open(base_raster_path)
#        
#        mask_raster = gdal.Open(mask_path)
#        mask_band = mask_raster.GetRasterBand(1)
#        mask = mask_band.ReadAsArray()
#
#        id_list = [1,2,3,4,5,6,7,8,9]        
#        dict = {}
#        
#        new_raster = \
#            hydropower_core.create_operation_raster(base_raster, output_path, 
#                                                    id_list, 'sum', mask, dict)
#       
#        new_raster = None
#        mask_raster = None
#
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_sum_path, 
#                                                  output_path)
#        
#    def test_hydropower_core_create_operation_raster_byhand(self):
#        """A test to make sure that the mean raster output is correct
#           by passing in a hand calculated raster
#        """
#        input_dir = './data/hydropower_data/test_input/'
#        output_base = './data/test_out/hydropower_create_mean_raster/'
#        output_path = output_base + 'test_mean_byhand.tif'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        field_name = 'subws_id'
#        id_list = [1,2,3,4,5,6,7,8,9]
#        
#        #Create two 4x4 rasters in memory
#        base = gdal.Open(input_dir + 'test_aet_mn.tif', gdal.GA_ReadOnly)
#        cols = 4
#        rows = 4
#        projection = base.GetProjection()
#        geotransform = base.GetGeoTransform()
#        value_raster = \
#            invest_cython_core.newRaster(cols, rows, projection, geotransform, \
#                                         'GTiff', -1, gdal.GDT_Float32, 1, \
#                                          output_path)
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
#    def test_hydropower_core_create_area_raster_regression(self):
#        """A regression test to make sure that the area rasters are being
#           created properly
#        """
#        output_base = './data/test_out/hydropower_create_area_raster/'
#        output_path = output_base + 'test_area_wyield.tif'
#        
#        input_dir = './data/hydropower_data/test_input/'
#        regression_dir = './data/hydropower_regression_data/'
#        
#        sub_sheds_path = input_dir + 'subwatersheds.shp'
#        wyield_path = input_dir + 'test_wyield.tif'
#        mask_path = regression_dir + 'sub_shed_mask_regression.tif'
#        reg_area_path = regression_dir + 'wyield_area_regression.tif'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
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
#        new_raster = \
#            hydropower_core.create_area_raster(wyield_raster, output_path, 
#                                               sub_sheds, field_name, mask)
#        
#        invest_test_core.assertTwoDatasetsEqual(self, wyield_regression_raster, 
#                                                new_raster)
#
#    def test_hydropower_core_create_area_raster_byhand(self):
#        """A test to make sure the area rasters are being created properly
#           by making hand calculated input data
#        """
#        input_dir = './data/hydropower_data/test_input/'
#        output_base = './data/test_out/hydropower_create_area_raster/'
#        output_path = output_base + 'test_area_byhand.tif'
#        sub_sheds_path = input_dir + 'subwatersheds.shp'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#        
#        sub_sheds = ogr.Open(sub_sheds_path)
#        
#        field_name = 'subws_id'
#        
#        #Create two 4x4 rasters in memory
#        base = gdal.Open(input_dir + 'test_aet_mn.tif', gdal.GA_ReadOnly)
#        cols = 4
#        rows = 4
#        projection = base.GetProjection()
#        geotransform = base.GetGeoTransform()
#        value_raster = invest_cython_core.newRaster(cols, rows, projection,
#            geotransform, 'GTiff', -1, gdal.GDT_Float32, 1, output_path)
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
#        new_raster = \
#            hydropower_core.create_area_raster(value_raster, output_path, 
#                                               sub_sheds, field_name, mask)
#
#        new_array = new_raster.GetRasterBand(1).ReadAsArray()
#        
#        self.assertTrue(area_calc.shape == new_array.shape)
#        
#        for i, j in zip(area_calc, new_array):
#            for m, n in zip(i,j):
#                self.assertAlmostEqual(m, n, 4)
#        
#    def test_hydropower_core_get_mask(self):
#        """A regression test that makes sure the proper mask is being
#           generated given a watershed shapefile
#        """
#        input_dir = './data/hydropower_data/test_input/'
#        regression_dir = './data/hydropower_regression_data/'
#        output_base = './data/test_out/hydropower_get_mask/'
#        output_path = output_base + 'test_new_mask.tif'
#        sub_sheds_path = input_dir + 'subwatersheds.shp'
#        wyield_path = input_dir + 'test_wyield.tif'
#        regression_mask_path = regression_dir + 'sub_shed_mask_regression.tif'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
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
#    def test_hydropower_core_get_operation_value(self):
#        """Test the get_operation_value function with the mean operation"""
#        
#        input_dir = './data/hydropower_data/test_input/'
#        output_base = './data/test_out/hydropower_get_mask/'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#            
#        #place code here
#        mask_raster = gdal.Open(input_dir + 'sub_shed_mask.tif')
#        raster = gdal.Open(input_dir + 'test_wyield.tif')
#        
#        shed_mask = mask_raster.GetRasterBand(1).ReadAsArray()
#
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
#            self.assertAlmostEqual(val, result_dict[key], 1)
#
#    def test_hydropower_core_get_operation_value2(self):
#        """Test the get_operation_value function with the sum operation"""
#        
#        input_dir = './data/hydropower_data/test_input/'
#        regression_dir = './data/hydropower_regression_data/'
#        output_base = './data/test_out/hydropower_get_mask/'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#            
#        #place code here
#        mask_raster = gdal.Open(input_dir + 'sub_shed_mask.tif')
#        raster = gdal.Open(regression_dir + 'wyield_tmp_regression.tif')
#        
#        shed_mask = mask_raster.GetRasterBand(1).ReadAsArray()
#
#        id_list = [1,2,3,4,5,6,7,8,9]
#        operation = 'sum'
#        
#        result_dict = hydropower_core.get_operation_value(raster, id_list,
#                                                          shed_mask, operation)
#        LOGGER.debug('get_operation_sum : %s', result_dict)
#        calc_dict = {1:20091785.33746, 2:5940049.32458, 3:25528521.86999, 
#                     4:56315504.13885, 5:37722788.59826,
#                     6:11983232.36431, 7:11512050.67187, 8:9076579.09057, 
#                     9:1001744.45562}
#
#        for key, val in calc_dict.iteritems():
#            self.assertAlmostEqual(val, result_dict[key], 1)
#        
#        
#    def test_hydropower_core_get_shed_ids(self):
#        """A by hand test for get_shed_ids function
#        
#        """
#        
#        #place code here
#        nodata = -1
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
##    def test_hydropower_core_create_operation_raster_hand(self):
##        """A by hand test for the create_operation_raster function
##        
##        """
##        
##        #place code here
##        
##        
##    def test_hydropower_core_create_operation_raster_regression(self):
##        """A regression test for create_operation_raster function
##        
##        """
##        
##        #place code here
##        
##        
##        
##    def test_hydropower_core_clip_raster_from_polygon(self):
##        """A test case for this function.  I should already have some test
##        cases for this function from wave energy model
##        
##        """
##        
##        #place code here
##        
##    def test_hydropower_core_clip_raster_from_polygon_re(self):
##        """A regression test for clip_raster_from_polygon function."""
##        test_dir = './data/hydropower_data'
##        output_dir = './data/test_out/hydropower_core_clip_raster_from_poly'
##        regression_dir = './data/hydropower_regression_data'
##        raster_input_path = \
##            test_dir + os.sep + 'test_input/fractp_tmp.tif'
##        copy_raster_input_path = \
##            output_dir + os.sep + 'clip_raster_from_poly_output.tif'
##        regression_raster_path = \
##            regression_dir + os.sep + 'clip_raster_from_poly_regression.tif'
##        clip_shape_path = \
##            test_dir + os.sep + 'test_input/subwatershed.shp'
##        
##        clip_shape = ogr.Open(clip_shape_path)
##        raster_input = gdal.Open(raster_input_path)
##
##        #Add the Output directory onto the given workspace
##        if not os.path.isdir(output_dir):
##            os.mkdir(output_dir)
##        
##        copy_raster = \
##            hydropower_core.clip_raster_from_polygon(clip_shape, raster_input, 
##                                                     copy_raster_input_path)
##        copy_raster.FlushCache()
##        #Check that resulting rasters are correct
##        invest_test_core.assertTwoDatasetEqualURI(self,
##            regression_raster_path, copy_raster_input_path)
##                
##        copy_raster = None
##        raster_input = None
##        clip_shape.Destroy()
##        
##        
##        
##        
#
#    def test_hydropower_core_water_scarcity_regression(self):
#        """A regression test for the core water scarcity functionality
#        
#        """
#        
#        #place code here
#        base = './data/hydropower_data'
#        output_base = './data/test_out/hydropower_water_scarcity/'
#        args = {}
#        args['workspace_dir'] = output_base
#        args['water_yield_vol_uri'] = \
#            gdal.Open(base + '/test_input/wyield_vol.tif')
#        args['water_yield_mean_uri'] = \
#            gdal.Open(base + '/test_input/wyield_mn.tif')
#        args['lulc_uri'] = gdal.Open(base + '/test_input/landuse_90')
#        args['watersheds'] = ogr.Open(base + '/test_input/watersheds.shp')
#        args['sub_watersheds'] = \
#            ogr.Open(base + '/test_input/subwatersheds.shp')
#        args['results_suffix'] = ''
#        
#        watershed_yield_table_uri = \
#            base + '/test_input/water_yield_watershed.csv'
#        subwatershed_yield_table_uri = \
#            base + '/test_input/water_yield_subwatershed.csv'
#        demand_table_uri = base + '/test_input/demand_table.csv'
#        hydro_calibration_table_uri = \
#            base + '/test_input/hydro_calibration_table.csv'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        
#        #Create the output directories
#        for folder_name in ['Output', 'Service', 'Intermediate']:
#            folder_path = output_base + os.sep + folder_name
#            if not os.path.isdir(folder_path):
#                os.mkdir(folder_path)
#
#        #Open/read in the csv files into a dictionary and add to arguments
#        watershed_yield_table_map = {}
#        watershed_yield_table_file = open(watershed_yield_table_uri)
#        reader = csv.DictReader(watershed_yield_table_file)
#        for row in reader:
#            watershed_yield_table_map[row['ws_id']] = row
#        
#        args['watershed_yield_table'] = watershed_yield_table_map
#        watershed_yield_table_file.close()
#        
#        subwatershed_yield_table_map = {}
#        subwatershed_yield_table_file = open(subwatershed_yield_table_uri)
#        reader = csv.DictReader(subwatershed_yield_table_file)
#        for row in reader:
#            subwatershed_yield_table_map[row['subws_id']] = row
#        
#        water_scarcity_args['subwatershed_yield_table'] = \
#            subwatershed_yield_table_map
#        subwatershed_yield_table_file.close()
#        
#        demand_table_map = {}
#        demand_table_file = open(args['demand_table_uri'])
#        reader = csv.DictReader(demand_table_file)
#        for row in reader:
#            demand_table_map[int(row['lucode'])] = int(row['demand'])
#        
#        args['demand_table'] = demand_table_map
#        demand_table_file.close()
#        
#        hydro_cal_table_map = {}
#        hydro_cal_table_file = open(hydro_calibration_table_uri)
#        reader = csv.DictReader(hydro_cal_table_file)
#        for row in reader:
#            hydro_cal_table_map[int(row['ws_id'])] = int(row['calib'])
#            
#        args['hydro_calibration_table'] = hydro_cal_table_map
#        hydro_cal_table_file.close()
#        
#        hydropower_core.valuation(args)
#        
#        regression_dir = './data/hydropower_regression_data/'
#        reg_consum_vol_uri = regression_dir + 'Output/consum_vol_regression.tif'
#        reg_consum_mn_uri = regression_dir + 'Output/consum_mn_regression.tif'
#        reg_rsup_vol_uri = regression_dir + 'Output/rsup_vol_regression.tif'
#        reg_rsup_mn_uri = regression_dir + 'Output/rsup_mn_regression.tif'
#        reg_cyield_vol_uri = regression_dir + 'Output/cyield_vol_regression.tif'
#        reg_ws_table_uri = \
#            regression_dir + 'Output/water_scarcity_watershed_regression.csv'
#        reg_sws_table_uri = \
#            regression_dir + 'Output/water_scarcity_subwatershed_regression.csv'
#        
#        consum_vol_uri = output_base + 'Output/consum_vol.tif'
#        consum_mn_uri = output_base + 'Output/consum_mn.tif'
#        rsup_vol_uri = output_base + 'Output/rsup_vol.tif'
#        rsup_mn_uri = output_base + 'Output/rsup_mn.tif'
#        cyield_vol_uri = output_base + 'Output/cyield_vol.tif'
#        
#        ws_table_uri = output_base + 'Output/water_scarcity_watershed.csv'
#        sws_table_uri = \
#            output_base + 'Output/water_scarcity_subwatershed.csv'
#        
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_consum_vol_uri, 
#                                                  consum_vol_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_consum_mn_uri, 
#                                                  consum_mn_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_rsup_vol_uri, 
#                                                  rsup_vol_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_rsup_mn_uri, 
#                                                  rsup_mn_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_cyield_vol_uri, 
#                                                  cyield_vol_uri)
#        invest_test_core.assertTwoCSVEqualURI(self, reg_ws_table_uri, 
#                                              ws_table_uri)
#        invest_test_core.assertTwoCSVEqualURI(self, reg_sws_table_uri, 
#                                              sws_table_uri)
#
#    def test_hydropower_core_write_scarcity_table(self):
#        """A by hand test for the write_scarcity_table function
#        
#        """
#        
#        #place code here
#        output_base = './data/test_out/write_scarcity_table/'
#        output_path = output_base + 'test_scarcity_table.csv'
#        regression_dir = './data/hydropower_regression_data/'
#        reg_table_path = regression_dir + 'scarcity_reg_table.csv'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        if os.path.isfile(output_path):
#            os.remove(output_path)
#            
#        field_list = 'ws_id, area, volume, avg_weight'
#        shed_table = {0: {'ws_id':0, 'area':32, 'volume': 54, 'avg_weight':5},
#                      1: {'ws_id':1, 'area':28, 'volume': 48, 'avg_weight':8},
#                      2: {'ws_id':2, 'area':16, 'volume': 78, 'avg_weight':10}}
#        
#        hydropower_core.write_scarcity_table(shed_table, field_list, 
#                                             output_path)
#        
#        invest_test_core.assertTwoCSVEqualURI(self, reg_table_path, output_path)
#        
#    def test_hydropower_core_sum_mean_dict_sum(self):
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
#    def test_hydropower_core_sum_mean_dict_mean(self):
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
#    def test_hydropower_core_valuation_regression(self):
#        """A regression test for the core valuation functionality
#        
#        """
#        
#        #place code here
#        base = './data/hydropower_data'
#        output_base = './data/test_out/hydropower_valuation/'
#        args = {}
#        args['workspace_dir'] = output_base
#        args['cal_water_yield_uri'] = gdal.Open(base + '/test_input/cyield_vol.tif')
#        args['water_consump_uri'] = gdal.Open(base + '/test_input/consum_vol.tif')
#        args['watersheds'] = ogr.Open(base + '/test_input/watersheds.shp')
#        args['sub_watersheds'] = ogr.Open(base + '/test_input/subwatersheds.shp')
#        args['results_suffix'] = ''
#        
#        watershed_scarcity_table_uri = base + '/test_input/water_scarcity_watershed.csv'
#        subwatershed_scarcity_table_uri = base + '/test_input/water_scarcity_subwatershed.csv'
#        valuation_table_uri = base + '/test_input/valuation_table.csv'
#        
#        if not os.path.isdir(output_base):
#            os.mkdir(output_base)
#        
#        #Create the output directories
#        for folder_name in ['Output', 'Service', 'Intermediate']:
#            folder_path = output_base + os.sep + folder_name
#            if not os.path.isdir(folder_path):
#                os.mkdir(folder_path)
#
#        #Open csv tables and add to the arguments
#        valuation_table_map = {}
#        valuation_table_file = open(valuation_table_uri)
#        reader = csv.DictReader(valuation_table_file)
#        for row in reader:
#            valuation_table_map[row['ws_id']] = row
#        
#        args['valuation_table'] = valuation_table_map
#        valuation_table_file.close()
#        
#        water_scarcity_map = {}
#        water_scarcity_table_file = open(watershed_scarcity_table_uri)
#        reader = csv.DictReader(water_scarcity_table_file)
#        for row in reader:
#            water_scarcity_map[row['ws_id']] = row
#        
#        val_args['watershed_scarcity_table'] = water_scarcity_map
#        water_scarcity_table_file.close()
#    
#        subwater_scarcity_map = {}
#        subwater_scarcity_table_file = open(subwatershed_scarcity_table_uri)
#        reader = csv.DictReader(subwater_scarcity_table_file)
#        for row in reader:
#            subwater_scarcity_map[row['subws_id']] = row
#        
#        val_args['subwatershed_scarcity_table'] = subwater_scarcity_map
#        subwater_scarcity_table_file.close()    
#        
#        hydropower_core.valuation(args)
#        
#        regression_dir = './data/hydropower_regression_data/'
#        reg_hp_energy_uri = regression_dir + 'Service/hp_energy_regression.tif'
#        reg_hp_val_uri = regression_dir + 'Service/hp_val_regression.tif'
#        reg_hp_val_ws_uri = \
#            regression_dir + 'Service/hydropower_value_watershed_regression.csv'
#        reg_hp_val_sws_uri = \
#            regression_dir + 'Service/hydropower_value_subwatershed_regression.csv'
#        
#        hp_energy_uri = output_base + 'Service/hp_energy.tif'
#        hp_val_uri = output_base + 'Service/hp_val.tif'
#        hp_val_ws_uri = output_base + 'Service/hydropower_value_watershed.csv'
#        hp_val_sws_uri = \
#            output_base + 'Service/hydropower_value_subwatershed.csv'
#        
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_hp_energy_uri, 
#                                                  hp_energy_uri)
#        invest_test_core.assertTwoDatasetEqualURI(self, reg_hp_val_uri, 
#                                                  hp_val_uri)
#        invest_test_core.assertTwoCSVEqualURI(self, reg_hp_val_ws_uri, 
#                                              hp_val_ws_uri)
#        invest_test_core.assertTwoCSVEqualURI(self, reg_hp_val_sws_uri, 
#                                              hp_val_sws_uri)
#                
##    def test_hydropower_core_make_raster(self):
##        
##        out_dir = './data/test_out/hydropower_get_mask'
##        output_path = out_dir + os.sep + 'new_mask.tif'
##        
##        if not os.path.isdir(out_dir):
##            os.mkdir(out_dir)
##        if os.path.isfile(output_path):
##            os.remove(output_path)
##        
##        wrk_dir = './data/hydropower_data/test_input'
##        regression_dir = './data/hydropower_regression_data'
##        
##        sub_sheds_path = wrk_dir + os.sep + 'subwatersheds.shp'
##        wyield_path = wrk_dir + os.sep + 'test_wyield.tif'
##        regression_mask_path = regression_dir + os.sep + 'sub_shed_mask_regression.tif'
##        new_raster_path = 
##        sub_sheds = ogr.Open(sub_sheds_path)
##        wyield = gdal.Open(wyield_path)
##        reg_mask_raster = gdal.Open(regression_mask_path)
##        
##        reg_mask = reg_mask_raster.GetRasterBand(1).ReadAsArray()
##        field_name = 'subws_id'