import unittest
import carbon_add
import numpy as np
import random

class TestCarbonAdd(unittest.TestCase):
    def test_carbon_add_smoke(self):
        """Smoke test for the diff function."""
        lulc1 = np.zeros((1,0))
        lulc2 = np.zeros((1,0))
        nodata = {'cur': 0, 'fut': 0} #set a nodata value
        
        carbon_add.execute(nodata, lulc1, lulc2)
        pass
    
    def test_1D_arrays(self):
        length = 100
        lulc1 = np.zeros((1, length))
        lulc2 = np.zeros((1, length))
        for x in range(length):
            lulc1[0][x] = 15.0*random.random()
            lulc2[0][x] = 10.0*random.random()
            
        nodata = {'cur': -2, 'fut': -2} #set a nodata value
        
        #run carbon_add
        output = carbon_add.execute(nodata, lulc1, lulc2)

        #verify the contents of output against pool and lulc data
        for x in range(lulc1.shape[1]):
            self.assertEqual(output[0][x], lulc1[0][x] + lulc2[0][x], 'Sum was not correctly calculated.')

    
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonAdd)
    unittest.TextTestRunner(verbosity=2).run(suite)