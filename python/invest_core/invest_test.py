import unittest
import invest_core
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

        output_dictionary = {'uri'  : '../../carbon_output/out.png',
                             'type' : 'gdal',
                             'dataType': gdal.GDT_Float32,
                             'input': False}

        arguments = {'lulc': lulc_dictionary,
                     'carbon_pools' : pool_dictionary,
                     'output' : output_dictionary}

#        invest_core.execute('carbon_core', arguments)

        output = gdal.Open(output_dictionary['uri'], 0)
        outputBand = output.GetRasterBand(1)
        obnodata = output.GetRasterBand(1).GetNoDataValue()
        print obnodata
        
        invest2 = gdal.Open('../../tot_c_cur', 0)
        invest2Band = invest2.GetRasterBand(1)
        i2bnodata = invest2Band.GetNoDataValue()
        print i2bnodata

        self.assertEqual(outputBand.XSize, invest2Band.XSize, "Dimensions differ: output=" + str(outputBand.XSize) + ", i2output = " + str(invest2Band.XSize))
        self.assertEqual(outputBand.YSize, invest2Band.YSize, "Dimensions differ: output=" + str(outputBand.YSize) + ", i2output = " + str(invest2Band.YSize))

        for i in range(0, outputBand.YSize):
            outArray = outputBand.ReadAsArray(1, i, outputBand.XSize-1, 1)
            i2Array = invest2Band.ReadAsArray(1, i, outputBand.XSize-1, 1)
            for j in range(0, outputBand.XSize-1):
                if (i2Array[0][j] == i2bnodata):
                    self.assertEqual(outArray[0][j], obnodata, "Should have found nodata pixel (value == " + str(obnodata) + ") in output raster at row " + str(i) + " index " + str(j) + ", but found " + str(outArray[0][j]) + " instead")
                else:
                    self.assertEqual(outArray[0][j], i2Array[0][j], "Unequal pixel values detected at row " + str(i) + " index " + str(j) + ":" + str(outArray[0][j]) + " " + str(i2Array[0][j]))
        pass


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvest)
    unittest.TextTestRunner(verbosity=2).run(suite)
