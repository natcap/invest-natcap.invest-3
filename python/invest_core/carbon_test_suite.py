import unittest

def suite():
    tests = ['carbon_seq_test',
             'carbon_diff_test',
             'carbon_value_test',
             'carbon_core_test',
             'data_handler_test',
             'carbon_uncertainty_test',
             'carbon_scenario_uncertainty_test']
    suite = unittest.TestLoader().loadTestsFromNames(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    suite()
