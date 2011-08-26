import unittest

def suite():
    tests = ['carbon_seq_test',
             'carbon_core_test',
             'data_handler_test']
    suite = unittest.TestLoader().loadTestsFromNames(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    suite()
