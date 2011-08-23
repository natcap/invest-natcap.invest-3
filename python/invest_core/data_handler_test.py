import unittest
import data_handler

class TestDataHandler(unittest.TestCase):
    def test_smoke(self):
        """Smoke test.  Shouldn't crash with empty map."""
        data_handler.open({})
        pass

    def test_dbf(self):
        """Test to load a dbf file."""
        db = data_handler.open({'uri'  : '../../carbon_pools_samp.dbf',
                           'type': 'dbf',
                           'input': True})
        self.assertEqual(db.recordCount, 66)
        pass

    def test_input_raster(self):
        """Test to load an input raster file."""
        lulc = data_handler.open({'uri'  : '../../lulc_samp_cur',
                           'type': 'gdal',
                           'input': True})
        self.assertEqual(lulc.RasterXSize, 1325, "Different widths found")
        self.assertEqual(lulc.RasterYSize, 1889, "Different heights found")
        pass
    
    def test_output_raster(self):
        """Test to load an output raster file."""
        lulc = data_handler.open({'uri'  : '../../lulc_samp_cur',
                           'type': 'gdal',
                           'input': True,})
        
        output = {'uri'  : '../../carbon_output_map',
                  'type' : 'gdal',
                  'input': False,}
        
        output = data_handler.mimic(lulc, output)
        self.assertEqual(lulc.RasterXSize, output.RasterXSize, "Input and output raster widths differ")
        self.assertEqual(lulc.RasterYSize, output.RasterYSize, "Input and output raster heights differ")        
        pass
    
    def test_dataset_close(self):
        """Test to close a dataset"""
        data = data_handler.open({'uri'  : '../../lulc_samp_cur',
                           'type': 'gdal',
                           'input': True})
        data = data_handler.close(data)
        self.assertEqual(data, None) #a closed dataset == None
        pass
    
    def test_dbf_close(self):
        """Test to close a dbf file"""
        db = data_handler.open({'uri':'../../carbon_pools_samp.dbf',
                                 'type': 'dbf',
                                 'input': True})
        data_handler.close(db)
        self.assertEqual(db.closed, True)
        pass
    
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataHandler)
    unittest.TextTestRunner(verbosity=2).run(suite)

