import os, sys
import unittest
import invest_test_core

#Add current directory and parent path for import tests
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')

import carbon_valuation

class TestCarbonBiophysical(unittest.TestCase):
    def test_carbon_biophysical_smoke(self):
        """Smoke test for carbon_biophysical function.  Shouldn't crash with \
#zero length inputs"""

        args = {}
        args['workspace_dir'] = '../../carbon_valuation_output'
        args['sequest_uri'] = '../../test_data/sequest_regression.tif'
        args['V'] = 43.0
        args['r'] = 7.0
        args['c'] = 0.0
        args['yr_cur'] = 2000
        args['yr_fut'] = 2030

        carbon_valuation.execute(args)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonBiophysical)
    unittest.TextTestRunner(verbosity=2).run(suite)
