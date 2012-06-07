"""URI level tests for the aquaculture biophysical and valuation module"""

import os, sys
import unittest

from invest_natcap.finfish_aquaculture import finfish_aquaculture
import invest_test_core

class TestFinfishAquaculture(unittest.TestCase):
    def test_finfish_aquaculture_smoke(self):
        """Smoke test for finfish_aquaculture function. """

        args = {}
        #Biophysical
        args['workspace_dir'] = './test/data/aquaculture_output'
        args['ff_farm_loc'] = './test/data/aquaculture_data/Finfish_Netpens.shp'
        args['farm_ID'] = 'FarmID'
        args['g_param_a'] = 0.038
        args['g_param_b'] = 0.6667
        args['water_temp_tbl'] = './test/data/aquaculture_data/Temp_Daily.csv'
        args['farm_op_tbl'] = './test/data/aquaculture_data/Farm_Operations.csv'
        
        #Valuation
        args['do_valuation'] = False
        args['p_per_kg']= 2.25
        args['frac_p'] = .3
        args['discount'] = 0.000192

        finfish_aquaculture.execute(args)
