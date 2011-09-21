import unittest
import carbon_core
import numpy as np
import random

def suite():
    tests = ['carbon_add_test',
             'carbon_diff_test',
             'carbon_value_test',
             'carbon_core_test',
             'data_handler_test',
             'carbon_uncertainty_test',
             'carbon_scenario_uncertainty_test']
    suite = unittest.TestLoader().loadTestsFromNames(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

class CarbonTestSuite(unittest.TestCase):
    def test_carbon_seq_smoke(self):
        """Smoke test for carbon_seq function.  Shouldn't crash with
        zero length inputs"""
        lulc = np.zeros((1, 0))
        pools = {}
        carbon_core.carbon_seq(lulc, pools)

    def test_carbon_seq_1D_array(self):
        """Test of carbon_seq against a 1D input/output array"""
        #setup the three args to carbon_seq
        length = 100
        lulc = np.zeros((1, length))
        for x in range(length):
            lulc[0][x] = random.randint(0, 2)

        pools = {0: 3.3,
                 1: 4.4,
                 2: 5.5}

        #run carbon_seq
        output = carbon_core.carbon_seq(lulc, pools)

        #verify the contents of output against pool and lulc data
        for x in range(lulc.shape[1]):
            self.assertEqual(output[0][x],
                            pools[lulc[0][x]],
                            'Pool data was not correctly transcribed')


    def test_carbon_diff_smoke(self):
        """Smoke test for the diff function."""
        lulc1 = np.zeros((1,0))
        lulc2 = np.zeros((1,0))
        nodata = {'input': 0, 'output': 0} #set a nodata value
        
        carbon_core.carbon_diff(nodata, lulc1, lulc2)
        pass
    
    def test_carbon_diff_1D_arrays(self):
        length = 100
        lulc1 = np.zeros((1, length))
        lulc2 = np.ones((1, length))
        nodata = {'input': -2, 'output': -2} #set a nodata value
        
        #run carbon_diff
        output = carbon_core.carbon_diff(nodata, lulc1, lulc2)

        #verify the contents of output against pool and lulc data
        for x in range(lulc1.shape[1]):
            self.assertEqual(output[0][x], 1, 'Difference was not correctly calculated.')



    def test_carbon_add_smoke(self):
        """Smoke test for the diff function."""
        lulc1 = np.zeros((1,0))
        lulc2 = np.zeros((1,0))
        nodata = {'cur': 0, 'fut': 0} #set a nodata value
        
        carbon_core.carbon_add(nodata, lulc1, lulc2)
        pass
    
    def test_carbon_add_1D_arrays(self):
        length = 100
        lulc1 = np.zeros((1, length))
        lulc2 = np.zeros((1, length))
        for x in range(length):
            lulc1[0][x] = 15.0*random.random()
            lulc2[0][x] = 10.0*random.random()
            
        nodata = {'input': -2, 'output': -2} #set a nodata value
        
        #run carbon_add
        output = carbon_core.carbon_add(nodata, lulc1, lulc2)

        #verify the contents of output against pool and lulc data
        for x in range(lulc1.shape[1]):
            self.assertEqual(output[0][x], lulc1[0][x] + lulc2[0][x], 'Sum was not correctly calculated.')


    def test_carbon_value_1D_array(self):
        """Test of carbon_value against a 1D input/output array"""
        #setup the three args to carbon_seq
        length = 100
        lulc = np.ones((1, length))
        nodata = {'input': -1, 'output': -1}

        #run carbon_value
        output = carbon_core.carbon_value(nodata, lulc, 3, 2.0, 4.0)

        #verify the output data was calculated and mapped correctly
        #Each value should equal 2.66666666666
        for x in range(lulc.shape[1]):
            self.assertAlmostEqual(output[0][x],2.6666666666, 8)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(CarbonTestSuite)
    unittest.TextTestRunner(verbosity=2).run(suite)