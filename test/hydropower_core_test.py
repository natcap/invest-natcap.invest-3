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
    def test_hydropower_core_water_yield_reg_byhand(self):
        """Regression test for the water_yield function in hydropower_core"""
        
        base = './invest-data/test/data/hydropower_regression_data/hydro_regression_byhand/'
        output_base = './invest-data/test/data/test_out/hydro_regression_byhand/'
        
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
        
        regression_dir = './invest-data/test/data/hydropower_regression_data/'
        reg_pixel_aet_uri = regression_dir + 'aet_pixel.tif'
        reg_pixel_fractp_uri = regression_dir + 'fractp_pixel.tif'
        reg_pixel_wyield_uri = regression_dir + 'wyield_pixel.tif'
        reg_fractp_mn_uri = regression_dir + 'fractp_mn.tif'
        reg_wyield_ha_uri = regression_dir + 'wyield_ha.tif'
        reg_wyield_vol_uri = regression_dir + 'wyield_vol.tif'
        reg_wyield_mn_uri = regression_dir + 'wyield_mn.tif'
        reg_aet_mn_uri = regression_dir + 'aet_mn.tif'
        reg_ws_table_uri = regression_dir + 'water_yield_subwatershed.csv'
        reg_sws_table_uri = regression_dir + 'water_yield_watershed.csv'
        
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
                
    def test_hydropower_core_sheds_map_subsheds(self):
        """A hand calculated test to make sure that sub watersheds can be
           identified with watersheds
        """
        
        input_dir = './invest-data/test/data/hydropower_data/test_input/'
        output_base = './invest-data/test/data/test_out/hydropower_sheds_map_subsheds/'

        sub_sheds_path = input_dir + 'subwatersheds.shp'
        sheds_path = input_dir + 'watersheds.shp'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
            
        sub_sheds = ogr.Open(sub_sheds_path)
        sheds = ogr.Open(sheds_path)
        
        shed_relationship = \
            hydropower_core.sheds_map_subsheds(sheds, sub_sheds)
        
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
        
    def test_hydropower_core_sheds_map_subsheds_calc(self):
        """A test to see if the function sheds_map_subsheds can correctly 
           match polygons from two different shapefiles that overlap each other.
           Here, I created two polygon shapefiles by hand and test them
        """
        
        input_dir = './invest-data/test/data/hydropower_data/test_input/'
        output_base = './invest-data/test/data/test_out/hydropower_sheds_map_subsheds/'

        sub_sheds_path = input_dir + 'test_hydro_sheds.shp'
        sheds_path = input_dir + 'test_hydro_subsheds.shp'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
            
        sub_sheds = ogr.Open(sub_sheds_path)
        sheds = ogr.Open(sheds_path)
        
        shed_relationship = \
            hydropower_core.sheds_map_subsheds(sheds, sub_sheds)
        
        expected_dict = {}
        expected_dict[1] = 3
        expected_dict[2] = 3
        expected_dict[3] = 2
        expected_dict[4] = 1
        expected_dict[5] = 1
        
        for key, val in shed_relationship.iteritems():
            if key in expected_dict:
                self.assertEqual(val, expected_dict[key])
            else:
                self.fail('Keys do not match')
                
        sub_sheds.Destroy()
        sheds.Destroy()
        
    def test_hydropower_core_sheds_map_subsheds_calc2(self):
        """A test to see if the function sheds_map_subsheds can correctly 
           match polygons from two different shapefiles that overlap each other.
           Here, I created two polygon shapefiles by hand and test them
        """
        
        input_dir = './invest-data/test/data/hydropower_regression_data/hydro_regression_byhand/'
        output_base = './invest-data/test/data/test_out/hydropower_sheds_map_subsheds/'

        sub_sheds_path = input_dir + 'simple_reg_subws.shp'
        sheds_path = input_dir + 'simple_reg_ws.shp'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
            
        sub_sheds = ogr.Open(sub_sheds_path)
        sheds = ogr.Open(sheds_path)
        
        shed_relationship = \
            hydropower_core.sheds_map_subsheds(sheds, sub_sheds)
        
        expected_dict = {}
        expected_dict[1] = 0
        expected_dict[2] = 1
        expected_dict[3] = 1
        
        for key, val in shed_relationship.iteritems():
            if key in expected_dict:
                self.assertEqual(val, expected_dict[key])
            else:
                self.fail('Keys do not match')
                
        sub_sheds.Destroy()
        sheds.Destroy()
        
    def test_hydropower_core_get_area_of_polygons_byhand(self):
        """A test to make sure the area rasters are being created properly
           by making hand calculated input data
        """
        input_dir = './invest-data/test/data/hydropower_regression_data/hydro_regression_byhand/' 
        
        shapefile = ogr.Open(input_dir + 'simple_reg_subws.shp')
        
        field_name = 'subws_id'
        
        result_dict = \
                hydropower_core.get_area_of_polygons(shapefile, field_name)

        byhand_dict = {1:3556.8 ,2:1789.7 ,3:3502.5}

        for result, byhand in zip(result_dict, byhand_dict):
            self.assertAlmostEqual(result, byhand, 0)

        shapefile = None

    def test_hydropower_core_water_scarcity_regression(self):
        """A regression test for the core water scarcity functionality
        
        """
        base = './invest-data/test/data/hydropower_regression_data/'
        output_base = './invest-data/test/data/test_out/hydro_regression_byhand/'
        #place code here
        args = {}
        args['workspace_dir'] = output_base
        args['water_yield_vol'] = \
            gdal.Open(base + 'wyield_vol.tif')
        args['water_yield_mn'] = \
            gdal.Open(base + 'wyield_mn.tif')
        args['lulc'] = gdal.Open(base + 'hydro_regression_byhand/lulc.tif')
        args['watersheds'] = ogr.Open(base + 'hydro_regression_byhand/simple_reg_ws.shp')
        args['sub_watersheds'] = \
            ogr.Open(base + 'hydro_regression_byhand/simple_reg_subws.shp')
        args['results_suffix'] = ''
        
        watershed_yield_table_uri = \
            base + 'water_yield_watershed.csv'
        subwatershed_yield_table_uri = \
            base + 'water_yield_subwatershed.csv'
        demand_table_uri = base + 'water_demand.csv'
        hydro_calibration_table_uri = \
            base + 'hydropower_calibration.csv'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
        
        #Create the output directories
        for folder_name in ['Output', 'Service', 'Intermediate']:
            folder_path = output_base + os.sep + folder_name
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)

        #Open/read in the csv files into a dictionary and add to arguments
        watershed_yield_table_map = {}
        watershed_yield_table_file = open(watershed_yield_table_uri)
        reader = csv.DictReader(watershed_yield_table_file)
        for row in reader:
            watershed_yield_table_map[int(row['ws_id'])] = row
        
        args['watershed_yield_table'] = watershed_yield_table_map
        watershed_yield_table_file.close()
        
        subwatershed_yield_table_map = {}
        subwatershed_yield_table_file = open(subwatershed_yield_table_uri)
        reader = csv.DictReader(subwatershed_yield_table_file)
        for row in reader:
            subwatershed_yield_table_map[int(row['subws_id'])] = row
        
        args['subwatershed_yield_table'] = \
            subwatershed_yield_table_map
        subwatershed_yield_table_file.close()
        
        demand_table_map = {}
        demand_table_file = open(demand_table_uri)
        reader = csv.DictReader(demand_table_file)
        for row in reader:
            demand_table_map[int(row['lucode'])] = int(row['demand'])
        
        args['demand_table'] = demand_table_map
        demand_table_file.close()
        
        hydro_cal_table_map = {}
        hydro_cal_table_file = open(hydro_calibration_table_uri)
        reader = csv.DictReader(hydro_cal_table_file)
        for row in reader:
            hydro_cal_table_map[int(row['ws_id'])] = float(row['calib'])
            
        args['hydro_calibration_table'] = hydro_cal_table_map
        hydro_cal_table_file.close()
        
        hydropower_core.water_scarcity(args)
        
        regression_dir = './invest-data/test/data/hydropower_regression_data/'
        reg_consum_vol_uri = regression_dir + 'consum_vol.tif'
        reg_consum_mn_uri = regression_dir + 'consum_mn.tif'
        reg_rsup_vol_uri = regression_dir + 'rsup_vol.tif'
        reg_rsup_mn_uri = regression_dir + 'rsup_mn.tif'
        reg_cyield_vol_uri = regression_dir + 'cyield_vol.tif'
        reg_ws_table_uri = \
            regression_dir + 'water_scarcity_watershed.csv'
        reg_sws_table_uri = \
            regression_dir + 'water_scarcity_subwatershed.csv'
        
        consum_vol_uri = output_base + 'Output/consum_vol.tif'
        consum_mn_uri = output_base + 'Output/consum_mn.tif'
        rsup_vol_uri = output_base + 'Output/rsup_vol.tif'
        rsup_mn_uri = output_base + 'Output/rsup_mn.tif'
        cyield_vol_uri = output_base + 'Output/cyield_vol.tif'
        
        ws_table_uri = output_base + 'Output/water_scarcity_watershed.csv'
        sws_table_uri = \
            output_base + 'Output/water_scarcity_subwatershed.csv'
        
        invest_test_core.assertTwoDatasetEqualURI(self, reg_consum_vol_uri, 
                                                  consum_vol_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_consum_mn_uri, 
                                                  consum_mn_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_rsup_vol_uri, 
                                                  rsup_vol_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_rsup_mn_uri, 
                                                  rsup_mn_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_cyield_vol_uri, 
                                                  cyield_vol_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_ws_table_uri, 
                                              ws_table_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_sws_table_uri, 
                                              sws_table_uri)

    def test_hydropower_core_write_csv_table_ws(self):
        """A by hand test for the write_csv_table function
           at the watershed level
        """
        
        #place code here
        output_base = './invest-data/test/data/test_out/write_csv_table/'
        output_path = output_base + 'test_csv_table_ws.csv'
        regression_dir = './invest-data/test/data/hydropower_regression_data/'
        reg_table_path = regression_dir + 'hand_calc_table_ws.csv'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
        if os.path.isfile(output_path):
            os.remove(output_path)
            
        field_list = ['ws_id','wyield', 'wyield_mn', 'cyield']
        shed_table = {0: {'ws_id':0, 'wyield':32, 
                          'wyield_mn': 54.05, 'cyield':5},
                      1: {'ws_id':1, 'wyield':28, 
                          'wyield_mn': 48.34, 'cyield':8},
                      2: {'ws_id':2, 'wyield':16, 
                          'wyield_mn': 78.73, 'cyield':10}}
        
        hydropower_core.write_csv_table(shed_table, field_list, 
                                             output_path)
        
        invest_test_core.assertTwoCSVEqualURI(self, reg_table_path, output_path)
        
    def test_hydropower_core_write_csv_table_sws(self):
        """A by hand test for the write_csv_table function
           at the subwatershed level
        """
        
        #place code here
        output_base = './invest-data/test/data/test_out/write_csv_table/'
        output_path = output_base + 'test_csv_table_sws.csv'
        regression_dir = './invest-data/test/data/hydropower_regression_data/'
        reg_table_path = regression_dir + 'hand_calc_table_sws.csv'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
        if os.path.isfile(output_path):
            os.remove(output_path)
            
        field_list = ['ws_id', 'subws_id', 'wyield', 'wyield_mn', 'cyield']
        shed_table = {1: {'ws_id':0, 'subws_id':1, 'wyield':32, 
                          'wyield_mn': 54.05, 'cyield':5},
                      2: {'ws_id':1, 'subws_id':2, 'wyield':28, 
                          'wyield_mn': 48.34, 'cyield':8},
                      3: {'ws_id':2, 'subws_id':3, 'wyield':16, 
                          'wyield_mn': 78.73, 'cyield':10},
                      4: {'ws_id':2, 'subws_id':4, 'wyield':116, 
                          'wyield_mn': 178.173, 'cyield':110}}

        hydropower_core.write_csv_table(shed_table, field_list, 
                                             output_path)
        
        invest_test_core.assertTwoCSVEqualURI(self, reg_table_path, output_path)
        
    def test_hydropower_core_sum_mean_dict_sum(self):
        """A by hand test for the sum_mean_dict function
        
        """
        
        #place code here
        dict1 = {0:[1,2,3], 1:[4,5,6], 2:[7,8,9]}
        dict2 = {1:5, 2:7, 3:3, 4:21, 5:17, 6:13, 7:37, 8:83, 9:59}
        expected_dict = {0:15, 1:51, 2:179}
        
        new_dict = hydropower_core.sum_mean_dict(dict1, dict2, 'sum')
        
        for key, val in expected_dict.iteritems():
            if key in new_dict:
                self.assertEqual(val, new_dict[key])
            else:
                self.fail('keys do not match')
    
    def test_hydropower_core_sum_mean_dict_mean(self):
        """A by hand test for the sum_mean_dict function
        
        """
        
        #place code here
        dict1 = {0:[1,2,3], 1:[4,5,6], 2:[7,8,9]}
        dict2 = {1:5, 2:7, 3:3, 4:21, 5:17, 6:13, 7:37, 8:83, 9:60}
        expected_dict = {0:5, 1:17, 2:60}
        
        new_dict = hydropower_core.sum_mean_dict(dict1, dict2, 'mean')
        
        for key, val in expected_dict.iteritems():
            if key in new_dict:
                self.assertEqual(val, new_dict[key])
            else:
                self.fail('keys do not match')

    def test_hydropower_core_valuation_regression(self):
        """A regression test for the core valuation functionality
        
        """
        
        #place code here
        base = './invest-data/test/data/hydropower_regression_data/'
        output_base = './invest-data/test/data/test_out/hydro_regression_byhand/'
        
        args = {}
        args['workspace_dir'] = output_base
        args['cyield_vol'] = gdal.Open(base + 'cyield_vol.tif')
        args['consump_vol'] = gdal.Open(base + 'consum_vol.tif')
        args['watersheds'] = ogr.Open(base + 'hydro_regression_byhand/simple_reg_ws.shp')
        args['sub_watersheds'] = ogr.Open(base + 'hydro_regression_byhand/simple_reg_subws.shp')
        args['results_suffix'] = ''
        
        watershed_scarcity_table_uri = base + 'water_scarcity_watershed.csv'
        subwatershed_scarcity_table_uri = base + 'water_scarcity_subwatershed.csv'
        valuation_table_uri = base + 'hydropower_valuation.csv'
        
        if not os.path.isdir(output_base):
            os.mkdir(output_base)
        
        #Create the output directories
        for folder_name in ['Output', 'Service', 'Intermediate']:
            folder_path = output_base + os.sep + folder_name
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)

        #Open csv tables and add to the arguments
        valuation_table_map = {}
        valuation_table_file = open(valuation_table_uri)
        reader = csv.DictReader(valuation_table_file)
        for row in reader:
            valuation_table_map[int(row['ws_id'])] = row
        
        args['valuation_table'] = valuation_table_map
        valuation_table_file.close()
        
        water_scarcity_map = {}
        water_scarcity_table_file = open(watershed_scarcity_table_uri)
        reader = csv.DictReader(water_scarcity_table_file)
        for row in reader:
            water_scarcity_map[int(row['ws_id'])] = row
        
        args['watershed_scarcity_table'] = water_scarcity_map
        water_scarcity_table_file.close()
    
        subwater_scarcity_map = {}
        subwater_scarcity_table_file = open(subwatershed_scarcity_table_uri)
        reader = csv.DictReader(subwater_scarcity_table_file)
        for row in reader:
            subwater_scarcity_map[int(row['subws_id'])] = row
        
        args['subwatershed_scarcity_table'] = subwater_scarcity_map
        subwater_scarcity_table_file.close()    
        
        hydropower_core.valuation(args)
        
        regression_dir = './invest-data/test/data/hydropower_regression_data/'
        reg_hp_energy_uri = regression_dir + 'hp_energy.tif'
        reg_hp_val_uri = regression_dir + 'hp_val.tif'
        reg_hp_val_ws_uri = \
            regression_dir + 'hydropower_value_watershed.csv'
        reg_hp_val_sws_uri = \
            regression_dir + 'hydropower_value_subwatershed.csv'
        
        hp_energy_uri = output_base + 'Service/hp_energy.tif'
        hp_val_uri = output_base + 'Service/hp_val.tif'
        hp_val_ws_uri = output_base + 'Service/hydropower_value_watershed.csv'
        hp_val_sws_uri = \
            output_base + 'Service/hydropower_value_subwatershed.csv'
        
        invest_test_core.assertTwoDatasetEqualURI(self, reg_hp_energy_uri, 
                                                  hp_energy_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_hp_val_uri, 
                                                  hp_val_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_hp_val_ws_uri, 
                                              hp_val_ws_uri)
        invest_test_core.assertTwoCSVEqualURI(self, reg_hp_val_sws_uri, 
                                              hp_val_sws_uri)

