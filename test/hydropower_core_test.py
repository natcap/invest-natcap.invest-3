"""URI level tests for the hydropower core module"""

import unittest
import logging
import os
import csv

from osgeo import gdal
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