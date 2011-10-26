import unittest
import imp, sys, os
import timber
import math
import numpy as np
from dbfpy import dbf

from osgeo import ogr, gdal
from osgeo.gdalconst import *

class TestTimber(unittest.TestCase):
#    def test_timber_smoke(self):
#        """Smoke test for carbon_uncertainty function.  Shouldn't crash with
#        zero length inputs"""
#        driver = gdal.GetDriverByName("GTIFF")
#        lulc_cur = driver.Create('../../test_data/test_blank_input', 1, 1, 1, gdal.GDT_Byte)
#        lulc_cur.GetRasterBand(1).SetNoDataValue(255)
#
#        output_seq = driver.Create('../../test_data/test_output/test_blank_output', 1, 1, 1, gdal.GDT_Float32)
#        output_map = driver.Create('../../test_data/test_output/test_blank_output_map', 1, 1, 1, gdal.GDT_Byte)
#        output_seq.GetRasterBand(1).SetNoDataValue(0)
#        output_map.GetRasterBand(1).SetNoDataValue(255)
#
#        args = { 'lulc_cur':lulc_cur,
#                'lulc_fut':lulc_cur,
#                'carbon_pools': dbf.Dbf('../../test_data/test_output/test_blank_dbf', new=True),
#                'output_seq': output_seq,
#                'output_map': output_map,
#                'percentile': 0.1}
#        carbon_scenario_uncertainty.execute(args)
#
#        #This is how GDAL closes its datasets in python
#        output = None

#    def test_timber_with_inputs(self):
#        """Test carbon_uncertainty using realistic inputs."""

    def test_timber_getBiomass(self):
        plant_dict = dbf.Dbf('../../test_data/timber/input/plant_table.dbf')
        TBiomass = timber.getBiomass(plant_dict[0]['Parcl_area'], plant_dict[0]['Perc_harv'],
                                     plant_dict[0]['Harv_mass'], plant_dict[0]['T'], plant_dict[0]['Freq_harv'])
        calculatedBiomass = 90000
        self.assertEqual(calculatedBiomass, TBiomass)
        
    def test_timber_getVolume(self):
        plant_dict = dbf.Dbf('../../test_data/timber/input/plant_table.dbf')
        TVolume = timber.getVolume(90000, plant_dict[0]['BCEF'])
        calculatedVolume = 90000
        self.assertEqual(calculatedVolume, TVolume)
        
    def test_timber_harvestValue(self):
        plant_dict = dbf.Dbf('../../test_data/timber/input/plant_table.dbf')
        harvest_value = timber.harvestValue(plant_dict[0]['Perc_harv'], plant_dict[0]['Price'], 
                                            plant_dict[0]['Harv_mass'], plant_dict[0]['Harv_cost'])
        harvest_value_calculated = 9215.00
        self.assertEqual(harvest_value, harvest_value_calculated)
        
    def test_timber_summationOne(self):
        plant_dict = dbf.Dbf('../../test_data/timber/input/plant_table.dbf')
        harvest_value = timber.harvestValue(plant_dict[0]['Perc_harv'], plant_dict[0]['Price'], 
                                            plant_dict[0]['Harv_mass'], plant_dict[0]['Harv_cost'])
        
        upper_limit = int(math.floor(plant_dict[0]['T']/plant_dict[0]['Freq_harv']))
        
        summation = timber.summationOneAlt(1, upper_limit, harvest_value, 7, plant_dict[0]['Freq_harv'])
        summation_calculated = 0.0
        for num in range(1, 6):
            summation_calculated = summation_calculated + (9215/((1.07)**((10*num)-1)))
        self.assertAlmostEqual(summation_calculated, summation, 15)
        
    def test_timber_summationTwo(self):
        plant_dict = dbf.Dbf('../../test_data/timber/input/plant_table.dbf')
        
        upper_limit = int(plant_dict[0]['T']-1)
        
        summation = timber.summationTwo(0, upper_limit, plant_dict[0]['Maint_cost'], 7)
        summation_calculated = 0.0
        for num in range(0, 50):
            summation_calculated = summation_calculated + (100/((1.07)**num))
            
        self.assertAlmostEqual(summation_calculated, summation, 15)
        
    def test_timber_totalNetPresentValue(self):
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        plant_file = dbf.Dbf('../../test_data/timber/input/plant_table.dbf')
        plant_shape = ogr.Open('../../test_data/timber/input/plantation.shp', 1)
        
        ogr.GetDriverByName('ESRI Shapefile').\
            CopyDataSource(plant_shape, '../../test_data/timber/output' + os.sep)
        timber_shp_copy = ogr.Open('../../test_data/timber/output/plantation.shp', 1)
       
        timber_layer = timber_shp_copy.GetLayerByName('plantation')
        plant_dict = {'plant_prod':plant_file, 'mdr':7, 'timber_layer': timber_layer, 'timber_shp_copy': timber_shp_copy}
        total_dict = timber.execute(plant_dict)
        
        summation_calculatedOne = 0.0
        summation_calculatedTwo = 0.0
        for num in range(1, 6):
            summation_calculatedOne = summation_calculatedOne + (9215/((1.07)**((10*num)-1)))
        
        for num in range(0, 50):
            summation_calculatedTwo = summation_calculatedTwo + (100/((1.07)**num))
        
        npv = summation_calculatedOne - summation_calculatedTwo
        tnpv = npv * 1200
        real_dict = (tnpv, 9579556.619, 30340425.432, 33555128.142, 520724.18, -5885248.892)
        
        for index, value in enumerate(total_dict):
            self.assertAlmostEqual(real_dict[index], value, 3)
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTimber)
    unittest.TextTestRunner(verbosity=2).run(suite)

