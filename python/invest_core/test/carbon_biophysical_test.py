import os, sys
import unittest

#Add current directory and parent path for import tests
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')

import carbon_biophysical

class TestCarbonBiophysical(unittest.TestCase):
#    def test_carbon_biophysical_smoke(self):
#        """Smoke test for carbon_biophysical function.  Shouldn't crash with \
#zero length inputs"""
#
#        args = {}
#        args['workspace_dir'] = '../../carbon_output'
#        args['calculate_sequestration'] = False
#        args['calculate_hwp'] = False
#        args['calc_uncertainty'] = False
#        args['lulc_cur_uri'] = "../../test_data/lulc_samp_cur"
#        args['carbon_pools_uri'] = '../../test_data/carbon_pools_float.dbf'
#
#        carbon_biophysical.execute(args)
#
#    def test_carbon_biophysical_sequestration(self):
#        """Test for carbon_biophysical function running with sample input to do \
#sequestration on lulc maps."""
#
#        args = {}
#        args['workspace_dir'] = '../../carbon_output'
#        args['calculate_sequestration'] = True
#        args['calculate_hwp'] = False
#        args['calc_uncertainty'] = False
#        args['lulc_cur_uri'] = "../../test_data/lulc_samp_cur"
#        args['lulc_fut_uri'] = "../../test_data/lulc_samp_fut"
#        args['carbon_pools_uri'] = '../../test_data/carbon_pools_float.dbf'
#
#        carbon_biophysical.execute(args)

    def test_carbon_biophysical_sequestration_hwp(self):
        """Test for carbon_biophysical function running with sample input to do \
sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = '../../carbon_output'
        args['calculate_sequestration'] = True
        args['calculate_hwp'] = True
        args['calc_uncertainty'] = False
        args['lulc_cur_uri'] = "../../test_data/lulc_samp_cur"
        args['lulc_fut_uri'] = "../../test_data/lulc_samp_fut"
        args['carbon_pools_uri'] = '../../test_data/carbon_pools_float.dbf'
        args['lulc_cur_year'] = 2000
        args['lulc_fut_year'] = 2030
        args['hwp_cur_shape_uri'] = "../../test_data/harv_samp_cur"
        args['hwp_fut_shape_uri'] = "../../test_data/harv_samp_fut"

        carbon_biophysical.execute(args)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonBiophysical)
    unittest.TextTestRunner(verbosity=2).run(suite)
