import unittest
import carbon_seq
import numpy as np

class TestCarbonSeq(unittest.TestCase):
    def test_carbon_seq_smoke(self):
        """Smoke test for carbon_seq function.  Shouldn't crash with
        zero length inputs"""
        lulc = np.array([])
        pools = {}
        output = np.empty(lulc.size)
        carbon_seq.carbon_seq(lulc, pools, output)
        pass

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonSeq)
    unittest.TextTestRunner(verbosity=2).run(suite)

