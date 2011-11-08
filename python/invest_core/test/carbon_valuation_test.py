"URI level tests for the carbon valuation module"

import os, sys
import unittest
import invest_test_core

#Add current directory and parent path for import tests
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')

import carbon_valuation

class TestCarbonBiophysical(unittest.TestCase):
    def test_carbon_valuation_regression(self):
        """Regression test for carbon_valuation function.  A few pixels have 
            been tested by hand against the following python snippet:
            
        >>> def f(V,sequest,yr_fut,yr_cur,r,c):
        ...     sum = 0
        ...     for t in range(yr_fut-yr_cur):
        ...             sum += 1/((1+(r/100.0))**t*(1+c/100.0)**t)
        ...     return sum*V*sequest/(yr_fut-yr_cur)
        ... 
        >>> V=43.0
        >>> yr_cur=2000
        >>> yr_fut=2030
        >>> sequest=1.0
        >>> sequest=-57.8494
        >>> f(V,sequest,yr_fut,yr_cur,r,c)
        -1100.9511853253725
            """

        args = {}
        args['workspace_dir'] = '../../carbon_valuation_output'
        args['sequest_uri'] = '../../test_data/sequest_regression.tif'
        args['V'] = 43.0
        args['r'] = 7.0
        args['c'] = 0.0
        args['yr_cur'] = 2000
        args['yr_fut'] = 2030

        carbon_valuation.execute(args)

        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Output/value_seq.tif",
            '../../test_data/value_seq_regression.tif')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonBiophysical)
    unittest.TextTestRunner(verbosity=2).run(suite)
