import unittest
import invest_core
from osgeo import gdal

def assert_raster_equality(unit, firstUri, secondUri):
    output = gdal.Open(firstUri, 0)
    outputBand = output.GetRasterBand(1)
    obnodata = outputBand.GetNoDataValue()
    print obnodata
    
    invest2 = gdal.Open(secondUri, 0)
    invest2Band = invest2.GetRasterBand(1)
    i2bnodata = invest2Band.GetNoDataValue()
    print i2bnodata

    unit.assertIsNot(obnodata, None, "Output nodata value read as None")
    unit.assertEqual(outputBand.XSize, invest2Band.XSize, "Dimensions differ: output=" + str(outputBand.XSize) + ", i2output = " + str(invest2Band.XSize))
    unit.assertEqual(outputBand.YSize, invest2Band.YSize, "Dimensions differ: output=" + str(outputBand.YSize) + ", i2output = " + str(invest2Band.YSize))

    for i in range(0, outputBand.YSize):
        outArray = outputBand.ReadAsArray(1, i, outputBand.XSize-1, 1)
        i2Array = invest2Band.ReadAsArray(1, i, outputBand.XSize-1, 1)
        for j in range(0, outputBand.XSize-1):
            if (i2Array[0][j] == i2bnodata):
                unit.assertEqual(outArray[0][j], obnodata, "Should have found nodata pixel (value == " + str(obnodata) + ") in output raster at row " + str(i) + " index " + str(j) + ", but found " + str(outArray[0][j]) + " instead")
            else:
                unit.assertEqual(outArray[0][j], i2Array[0][j], "Unequal pixel values detected at row " + str(i) + " index " + str(j) + ":" + str(outArray[0][j]) + " " + str(i2Array[0][j]))





class TestInvest(unittest.TestCase):
   
        def test_carbon_model_regression(self):
            """Test to run Carbon model on sample data"""
            lulc_dictionary = {'uri'  : '../../lulc_samp_cur',
                               'type' :'gdal',
                               'input': True}
    
            pool_dictionary = {'uri'  : '../../test_data/carbon_pools_float.dbf',
                               'type' : 'dbf',
                               'input': True}
    
            output_dictionary = {'uri'  : '../../carbon_output/out1.png',
                                 'type' : 'gdal',
                                 'dataType': gdal.GDT_Float32,
                                 'input': False}
    
            arguments = {'lulc': lulc_dictionary,
                         'carbon_pools' : pool_dictionary,
                         'output' : output_dictionary}
    
#            invest_core.execute('carbon_core', arguments)
    
            assert_raster_equality(self, output_dictionary['uri'], '../../test_data/carbon_regression.tif' )
            pass




        def test_verify_carbon3_against_carbon21_int_pools(self):
            """Test the InVEST3 carbon model against the known output raster of InVEST2.1 carbon
                
                Uses the modified pools dbf, where all values are ints."""
                
            lulc_dictionary = {'uri'  : '../../lulc_samp_cur',
                               'type' :'gdal',
                               'input': True}

            pool_dictionary = {'uri'  : '../../test_data/carbon_pools_int.dbf',
                               'type' : 'dbf',
                               'input': True}
            
            output_dictionary = {'uri'  : '../../carbon_output/out.tif',
                                 'type' : 'gdal',
                                 'dataType': gdal.GDT_Float32,
                                 'input': False}

            arguments = {'lulc': lulc_dictionary,
                     'carbon_pools' : pool_dictionary,
                     'output' : output_dictionary}

            invest_core.execute('carbon_core', arguments)
            
            assert_raster_equality(self, output_dictionary['uri'], '../../test_data/tot_c_cur_int')
            pass
        
        
            


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvest)
    unittest.TextTestRunner(verbosity=2).run(suite)



    
 