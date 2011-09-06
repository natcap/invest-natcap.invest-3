import unittest
import carbon_scenario_uncertainty
import numpy as np
from dbfpy import dbf

from osgeo import ogr, gdal
from osgeo.gdalconst import *

class TestCarbonScenarioUncertainty(unittest.TestCase):
    def test_carbon_scenario_uncertainty_smoke(self):
        """Smoke test for carbon_uncertainty function.  Shouldn't crash with
        zero length inputs"""
        driver = gdal.GetDriverByName("GTIFF")
        lulc_cur = driver.Create('../../test_data/test_blank_input', 1, 1, 1, gdal.GDT_Byte)
        lulc_cur.GetRasterBand(1).SetNoDataValue(-1.0)

        output = driver.Create('../../test_data/test_blank_output', 1, 1, 4, gdal.GDT_Float32)
        for x in [1, 2, 3, 4]: output.GetRasterBand(x).SetNoDataValue(-1.0)

        args = { 'lulc_cur':lulc_cur,
                'lulc_fut':lulc_cur,
                'carbon_pools': dbf.Dbf('../../test_data/test_blank_dbf', new=True),
                'output': output}
        carbon_scenario_uncertainty.execute(args)

        #This is how GDAL closes its datasets in python
        output = None

    def test_carbon_scenario_uncertainty_with_inputs(self):
        """Test carbon_uncertainty using realistic inputs."""
        driver = gdal.GetDriverByName("GTIFF")
        lulc_cur = gdal.Open('../../test_data/lulc_samp_cur', GA_ReadOnly)
        lulc_fut = gdal.Open('../../test_data/lulc_samp_fut', GA_ReadOnly)
        output = driver.Create('../../uncertainty_sequestration_scenario.tif',
                               lulc_cur.GetRasterBand(1).XSize,
                               lulc_cur.GetRasterBand(1).YSize, 4, gdal.GDT_Float32)
        output.SetGeoTransform(lulc.GetGeoTransform())
        args = { 'lulc': lulc,
                'carbon_pools': dbf.Dbf('../../test_data/uncertain_carbon_pools_samp.dbf'),
                'output': output}
        carbon_scenario_uncertainty.execute(args)

        #This is how GDAL closes its datasets in python
        output = None

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonScenarioUncertainty)
    unittest.TextTestRunner(verbosity=2).run(suite)

