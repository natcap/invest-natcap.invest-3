import unittest
import invest
from osgeo import gdal

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
                             'dataType': gdal.GDT_Float32,
                             'input': False}

        arguments = {'lulc': lulc_dictionary,
                     'carbon_pools' : pool_dictionary,
                     'output' : output_dictionary}

        invest.execute('carbon_core', arguments)

        output = gdal.Open(output_dictionary['uri']).GetRasterBand(1)
        invest2 = gdal.Open('../../invest2CarbonOutput').GetRasterBand(1)

        self.assertEqual(output.XSize, invest2.XSize, "Dimensions differ: output=" + str(output.XSize) + ", i2output = " + str(invest2.XSize))
        self.assertEqual(output.YSize, invest2.YSize, "Dimensions differ: output=" + str(output.YSize) + ", i2output = " + str(invest2.YSize))

        for i in range(1, output.YSize):
           outArray = output.GetRasterBand(1)
           i2Array = invest2.GetRasterBand(1)
           for j in range(1, output.XSize):
             self.assertEqual(outArray[0][j], i2Array[0][j], "Unequal pixel values detected")
        pass


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvest)
    unittest.TextTestRunner(verbosity=2).run(suite)
