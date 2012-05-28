"""URI level tests for the aquaculture biophysical module"""

import os, sys
import unittest

from invest_natcap.finfish_aquaculture import finfish_aquaculture_biophysical
import invest_test_core

class TestFinfishAquacultureBiophysical(unittest.TestCase):
    def test_finfish_aquaculture_biophysical_smoke(self):
        """Smoke test for finfish_aquaculture_biophysical function. """

        args = {}
        args['workspace_dir'] = './data/aquaculture_output'
        args['ff_farm_loc'] = './test/data/aquaculture_data/Finfish_Netpens.shp'
        args['farm_ID'] = 'FarmID'
        args['g_param_a'] = 0.038
        args['g_param_b'] = 0.6667
        args['water_temp_tbl'] = './test/data/aquaculture_data/Temp_Daily.csv'
        args['farm_op_tbl'] = './test/data/aquaculture_data/Farm_Operations.csv'

        finfish_aquaculture_biophysical.execute(args)
