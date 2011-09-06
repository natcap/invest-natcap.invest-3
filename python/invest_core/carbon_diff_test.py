import unittest
import carbon_diff
import numpy as np

class TestCarbonDiff(unittest.TestCase):
    def test_carbon_diff_smoke(self):
        """Smoke test for the diff function."""
        lulc1 = np.zeros((1,0))
        lulc2 = np.zeros((1,0))
        nodata = {'cur': 0, 'fut': 0} #set a nodata value
        
        carbon_diff.execute(nodata, lulc1, lulc2)
        pass
    
    def test_1D_arrays(self):
        length = 100
        lulc1 = np.zeros((1, length))
        lulc2 = np.ones((1, length))
        nodata = {'cur': -2, 'fut': -2} #set a nodata value
        
        #run carbon_diff
        output = carbon_diff.execute(nodata, lulc1, lulc2)

        #verify the contents of output against pool and lulc data
        for x in range(lulc1.shape[1]):
            self.assertEqual(output[0][x], 1, 'Difference was not correctly calculated.')

    
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonDiff)
    unittest.TextTestRunner(verbosity=2).run(suite)