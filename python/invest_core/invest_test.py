import unittest
import invest

class TestInvest(unittest.TestCase):
    def test_carbon_model(self):
        """Test to run Carbon model on sample data"""
        lulc_dictionary = {'uri'  : '../../lulc_samp_cur',
                           'type' :'gdal',
                           'input': True}

        pool_dictionary = {'uri'  : '../../carbon_pools_samp.dbf',
                           'type' : 'dbf',
                           'input': True}

        output_dictionary = {'uri'  : '../../carbon_output_map.tif',
                             'type' : 'gdal',
                             'input': False}

        arguments = {'lulc': lulc_dictionary,
                     'carbon_pools' : pool_dictionary,
                     'output' : output_dictionary}

        invest.execute('carbon_core', arguments)
        pass


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvest)
    unittest.TextTestRunner(verbosity=2).run(suite)
