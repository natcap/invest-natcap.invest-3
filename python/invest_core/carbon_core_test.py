import unittest
import carbon_core
import numpy as np
import os
from dbfpy import dbf

try:
    from osgeo import ogr, gdal
    from osgeo.gdalconst import *
    import numpy
    use_numeric = False
except ImportError:
    import ogr, gdal
    from gdalconst import *
    import Numeric

class TestCarbonCore(unittest.TestCase):
    def test_carbon_core_smoke(self):
        """Smoke test for carbon_core function.  Shouldn't crash with
        zero length inputs"""
        driver = gdal.GetDriverByName("GTIFF")
        args = { 'lulc': driver.Create('../../test_blank_input', 1, 1, 1, gdal.GDT_Byte),
                'carbon_pool': dbf.Dbf('../../test_blank_dbf', new=True),
                'output': driver.Create('../../test_blank_output', 1, 1, 1, gdal.GDT_Byte)}
        carbon_core.execute(args)
        pass

    def test_carbon_core_with_inputs(self):
        driver = gdal.GetDriverByName("GTIFF")
        lulc = gdal.Open('../../lulc_samp_cur', GA_ReadOnly)
        args = { 'lulc': lulc,
                'carbon_pool': dbf.Dbf('../../carbon_pools_samp.dbf'),
                'output': driver.Create('../../test_real_output', lulc.RasterXSize, lulc.RasterYSize, 1, gdal.GDT_Byte)}
        carbon_core.execute(args)
        pass

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonCore)
    unittest.TextTestRunner(verbosity=2).run(suite)

