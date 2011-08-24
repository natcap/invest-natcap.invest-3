import unittest
import carbon_seq
import numpy as np
import random

class TestCarbonSeq(unittest.TestCase):
    def test_carbon_seq_smoke(self):
        """Smoke test for carbon_seq function.  Shouldn't crash with
        zero length inputs"""
        lulc = np.zeros((1, 0))
        pools = {}
        output = np.empty(lulc.size)
        carbon_seq.execute(lulc, pools, output)
        pass
    
    def test_1D_array(self):
        """Test of carbon_seq against a 1D input/output array"""
        #setup the three args to carbon_seq
        length = 100
        lulc = np.zeros((1, length))
        for x in range(length):
            lulc[0][x] = random.randint(0,2)
            
        pools = {0: 3.3,
                 1: 4.4,
                 2: 5.5}
        
        output = np.zeros((1, length))
        
        #run carbon_seq
        output = carbon_seq.execute(lulc, pools, output)
        
        #verify the contents of output against pool and lulc data
        for x in range(lulc.shape[1]):
            self.assertEqual(output[0][x],
                            pools[lulc[0][x]],
                            'Pool data was not correctly transcribed')
        pass
    
    

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonSeq)
    unittest.TextTestRunner(verbosity=2).run(suite)

