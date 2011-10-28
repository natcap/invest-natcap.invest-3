import unittest
import numpy as np
import os
from dbfpy import dbf
from osgeo import ogr, gdal
from osgeo.gdalconst import *
import carbon_biophysical

class TestCarbonBiophysical(unittest.TestCase):
    def test_carbon_biophysical_smoke(self):
        """Smoke test for carbon_biophysical function.  Shouldn't crash with
        zero length inputs"""

        args = {}
        args['workspace_dir'] = '../../carbon_output'
        args['calculate_sequestration'] = False
        args['calculate_hwp'] = False
        args['calc_uncertainty'] = False
        args['lulc_cur_uri'] = "../../test_data/lulc_samp_cur"
        args['carbon_pools_uri'] = '../../carbon_pools_float.dbf'

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonBiophysical)
    unittest.TextTestRunner(verbosity=2).run(suite)
