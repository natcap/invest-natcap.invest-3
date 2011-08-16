import unittest
import carbon_core
import numpy as np

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
    def test_carbon_cpre_smoke(self):
        """Smoke test for carbon_core function.  Shouldn't crash with
        zero length inputs"""
        args = { 'lulc': driver.Create(None, 0, 0, 1, gdal.GDT_Byte),
                'carbon_pool': {},
                'carbon_map_output': driver.Create(None, 0, 0, 1, gdal.GDT_Byte)}
        carbon_core.carbon_core(args)
        pass

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonCore)
    unittest.TextTestRunner(verbosity=2).run(suite)

