import unittest
import invest_carbon_core

class TestInvestCarbonCore(unittest.TestCase):
    def test_carbon_uncertainty_model(self):
        args = {'carbon_pools': '../../test_data/uncertain_carbon_pools_samp.dbf',
                'lulc_fut': '../../test_data/lulc_samp_fut',
                'percentile': 0.2,
                'output_dir': '../../',
                'lulc_cur': '../../test_data/lulc_samp_cur',
                'calc_uncertainty' : False,
                'calc_value': False}

        invest_carbon_core.execute(args)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCarbonCore)
    unittest.TextTestRunner(verbosity=2).run(suite)





