import unittest
import data_handler

class TestDataHandler(unittest.TestCase):
    def test_smoke(self):
        """Smoke test.  Shouldn't crash with empty map."""
        data_handler.open({})
        pass

    def test_dbf(self):
        """Test to load a dbf file."""
        data_handler.open({'uri'  : '../../carbon_pools_samp.dbf',
                           'type': 'dbf',
                           'input': True})
        pass

    def test_input_raster(self):
        """Test to load an input raster file."""
        data_handler.open({'uri'  : '../../lulc_samp_cur',
                           'type': 'gdal',
                           'input': True})
        pass
    
    def test_output_raster(self):
        """Test to load an output raster file."""
        data_handler.open({'uri'  : '../../carbon_output',
                           'type': 'gdal',
                           'input': False})
        pass
    
    def test_close(self):
        """Test to close a dataset"""
        data = data_handler.open({'uri'  : '../../lulc_samp_cur',
                           'type': 'gdal',
                           'input': True})
        data_handler.close(data)
        pass

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataHandler)
    unittest.TextTestRunner(verbosity=2).run(suite)

