import unittest
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


    def test_timber_harvestValue(self):
        plant_dict = dbf.Dbf('../../test_data/timber/plant_table.dbf')
        harvest_value = timber.harvestValue(plant_dict[0]['Perc_harv'], plant_dict[0]['Price'], 
                                            plant_dict[0]['Harv_mass'], plant_dict[0]['Harv_cost'])
        harvest_value_calculated = 9215.00
        self.assertEqual(harvest_value, harvest_value_calculated)
        
    def test_timber_summationOne(self):
        plant_dict = dbf.Dbf('../../test_data/timber/plant_table.dbf')
        harvest_value = timber.harvestValue(plant_dict[0]['Perc_harv'], plant_dict[0]['Price'], 
                                            plant_dict[0]['Harv_mass'], plant_dict[0]['Harv_cost'])
        upper_limit = int(math.ceil(plant_dict[0]['T']/plant_dict[0]['Freq_harv'])-1)
        
        summation = timber.summationOne(0, upper_limit, harvest_value, 7, plant_dict[0]['Freq_harv'])
        summation_calculated = 18106.69902
        self.assertAlmostEqual(summation_calculated, summation, 3)
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTimber)
    unittest.TextTestRunner(verbosity=2).run(suite)

