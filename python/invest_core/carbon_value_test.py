import unittest
import carbon_value
import numpy as np

class TestCarbonValue(unittest.TestCase):
    def test_1D_array(self):
        """Test of carbon_seq against a 1D input/output array"""
        #setup the three args to carbon_seq
        length = 100
        lulc = np.ones((1, length))
        nodata = {'cur': -1, 'fut': -1}

        #run carbon_value
        output = carbon_value.execute(nodata, lulc, 3, 2.0, 4.0)

        #verify the output data was calculated and mapped correctly
        #Each value should equal 2.66666666666
        for x in range(lulc.shape[1]):
            self.assertAlmostEqual(output[0][x],2.6666666666, 8)
            
            
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonValue)
    unittest.TextTestRunner(verbosity=2).run(suite)