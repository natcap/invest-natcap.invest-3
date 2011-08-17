import unittest
import invest_core

def suite():
    tests = ['invest_core.carbon_seq_test',
             'invest_core.carbon_core_test',
             'invest_core.data_handler_test']
    suite = unittest.TestLoader().loadTestsFromNames(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    suite()
