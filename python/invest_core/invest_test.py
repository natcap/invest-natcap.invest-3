import unittest
import invest_core
from osgeo import gdal
import os
from numpy import *
import numpy as np

def assert_raster_equality(unit, firstUri, secondUri):
    output = gdal.Open(firstUri, 0)
    outputBand = output.GetRasterBand(1)
    obnodata = outputBand.GetNoDataValue()
    
    invest2 = gdal.Open(secondUri, 0)
    invest2Band = invest2.GetRasterBand(1)
    i2bnodata = invest2Band.GetNoDataValue()

    unit.assertNotEqual(obnodata, None, "Output nodata value read as None")
    unit.assertEqual(outputBand.XSize, invest2Band.XSize, "Dimensions differ: output=" + str(outputBand.XSize) + ", i2output = " + str(invest2Band.XSize))
    unit.assertEqual(outputBand.YSize, invest2Band.YSize, "Dimensions differ: output=" + str(outputBand.YSize) + ", i2output = " + str(invest2Band.YSize))

    for i in range(0, outputBand.YSize):
        outArray = outputBand.ReadAsArray(1, i, outputBand.XSize-1, 1)
        i2Array = invest2Band.ReadAsArray(1, i, outputBand.XSize-1, 1)
        for j in range(0, outputBand.XSize-1):
            if (i2Array[0][j] == i2bnodata):
                unit.assertEqual(outArray[0][j], obnodata, "Should have found nodata pixel (value == " + str(obnodata) + ") in output raster at row " + str(i) + " index " + str(j) + ", but found " + str(outArray[0][j]) + " instead")
            else:
                a = outArray[0][j]
                b = i2Array[0][j]
                unit.assertAlmostEqual(a, b, 4, "Unequal pixel values detected at row " +
                                  str(i) + " index " + str(j) + ":" + str(a) + " " + str(b))


def assert_raster_equality_vec(unit, firstUri, secondUri):
    output = gdal.Open(firstUri, 0)
    outputBand = output.GetRasterBand(1)
    obnodata = outputBand.GetNoDataValue()
    
    invest2 = gdal.Open(secondUri, 0)
    invest2Band = invest2.GetRasterBand(1)
    i2bnodata = invest2Band.GetNoDataValue()

    unit.assertNotEqual(obnodata, None, "Output nodata value read as None")
    unit.assertEqual(outputBand.XSize, invest2Band.XSize, "Dimensions differ: output=" + str(outputBand.XSize) + ", i2output = " + str(invest2Band.XSize))
    unit.assertEqual(outputBand.YSize, invest2Band.YSize, "Dimensions differ: output=" + str(outputBand.YSize) + ", i2output = " + str(invest2Band.YSize))

    for i in range(0, outputBand.YSize):
        outArray = outputBand.ReadAsArray(1, i, outputBand.XSize-1, 1)
        i2Array = invest2Band.ReadAsArray(1, i, outputBand.XSize-1, 1)

        def checkEqual(a, b):
            if b == i2bnodata:
                unit.assertEqual(a, obnodata)
            else:
                unit.assertAlmostEqual(a, b, 4)
                
        fastCheck = np.vectorize(checkEqual)
        fastCheck(outArray, i2Array)



class TestInvest(unittest.TestCase):
   
        def test_carbon_model_regression(self):
            """Regression Test to run Carbon model using sample data.  
            Results will be compared with a raster that is known to be accurate."""
            lulc_dictionary = {'uri'  : '../../test_data/lulc_samp_cur',
                               'type' :'gdal',
                               'input': True}
    
            pool_dictionary = {'uri'  : '../../test_data/carbon_pools_float.dbf',
                               'type' : 'dbf',
                               'input': True}
    
            output_dictionary = {'uri'  : '../../carbon_output/test_carbon_output.tif',
                                 'type' : 'gdal',
                                 'dataType': gdal.GDT_Float32,
                                 'input': False}
    
            arguments = {'lulc_cur': lulc_dictionary,
                         'carbon_pools' : pool_dictionary,
                         'storage_cur' : output_dictionary,
                         'storage_fut' : None,
                         'seq_delta': None,
                         'calc_value' : False}
    
            invest_core.execute('carbon_core', arguments)
    
#            assert_raster_equality(self, output_dictionary['uri'], '../../test_data/carbon_regression.tif' )
            assert_raster_equality_vec(self, output_dictionary['uri'], '../../test_data/carbon_regression.tif' )
            os.remove(output_dictionary['uri'])
            pass




        def test_verify_carbon3_against_carbon21_int_pools(self):
            """Test the InVEST3 carbon model against the known output raster of InVEST2.1 carbon
                
                Uses the modified pools dbf, where all values are ints."""
                
            lulc_dictionary = {'uri'  : '../../test_data/lulc_samp_cur',
                               'type' :'gdal',
                               'input': True}

            pool_dictionary = {'uri'  : '../../test_data/carbon_pools_int.dbf',
                               'type' : 'dbf',
                               'input': True}
            
            output_dictionary = {'uri'  : '../../carbon_output/test_carbon_output.tif',
                                 'type' : 'gdal',
                                 'dataType': gdal.GDT_Float32,
                                 'input': False}

            arguments = {'lulc_cur': lulc_dictionary,
                     'carbon_pools' : pool_dictionary,
                     'storage_cur' : output_dictionary,
                     'calc_value' : False}

            invest_core.execute('carbon_core', arguments)
            
#            assert_raster_equality(self, output_dictionary['uri'], '../../test_data/tot_c_cur_int')
            assert_raster_equality_vec(self, output_dictionary['uri'], '../../test_data/tot_c_cur_int')
            os.remove(output_dictionary['uri'])
            pass
        
        
        def test_carbon_valuation(self):
            """Verify that the carbon valuation model passes successfully"""
            
            lulc_cur = {'uri'  : '../../test_data/lulc_samp_cur',
                               'type' :'gdal',
                               'input': True}
            lulc_fut = {'uri'  : '../../test_data/lulc_samp_fut',
                               'type' :'gdal',
                               'input': True}

            pool_dictionary = {'uri'  : '../../test_data/carbon_pools_int.dbf',
                               'type' : 'dbf',
                               'input': True}
            
            storage_cur = {'uri'  : '../../carbon_output/test_seq_cur.tif',
                                'type' : 'gdal',
                                'dataType': gdal.GDT_Float32,
                                'input': False}
            
            storage_fut = {'uri'  : '../../carbon_output/test_seq_fut.tif',
                                 'type' : 'gdal',
                                 'dataType': gdal.GDT_Float32,
                                 'input': False}
            
            seq_delta = {'uri'  : '../../carbon_output/test_seq_delta.tif',
                                 'type' : 'gdal',
                                 'dataType': gdal.GDT_Float32,
                                 'input': False}
            
            seq_value = {'uri'  : '../../carbon_output/test_carbon_value.tif',
                                 'type' : 'gdal',
                                 'dataType': gdal.GDT_Float32,
                                 'input': False}
            
            arguments = {'lulc_cur': lulc_cur,
                         'lulc_fut': lulc_fut,
                     'carbon_pools' : pool_dictionary,
                     'storage_cur' : storage_cur,
                     'storage_fut' : storage_fut,
                     'seq_delta' : seq_delta,
                     'seq_value' : seq_value,
                     'calc_value' : True,
                     'lulc_cur_year' : 2000,
                     'lulc_fut_year' : 2030,
                     'c_value' : 43.0,
                     'discount' : 0.07,
                     'rate_change' : 0.0}
            
            invest_core.execute('carbon_core', arguments)
                            
#            assert_raster_equality(self, seq_value['uri'], '../../test_data/val_seq_int')
            assert_raster_equality_vec(self, seq_value['uri'], '../../test_data/val_seq_int')
            
            for dict in (storage_cur, storage_fut, seq_delta, seq_value):
                os.remove(dict['uri'])
            pass
        
        def test_carbon_storage_hwp_regression(self):
            """Verify the carbon storage model (with HWP) against known results"""
                        
            lulc_cur = {'uri'  : '../../test_data/lulc_samp_cur',
                               'type' :'gdal',
                               'input': True}

            pool_dictionary = {'uri'  : '../../test_data/carbon_pools_int.dbf',
                               'type' : 'dbf',
                               'input': True}
            
            storage_cur = {'uri'  : '../../carbon_output/test_seq_cur.tif',
                                'type' : 'gdal',
                                'dataType': gdal.GDT_Float32,
                                'input': False}
            
            hwp_cur = {'uri' : '../../test_data/harv_samp_cur/harv_samp_cur.shp',
                       'type' : 'ogr'}
            
            arguments = {'lulc_cur': lulc_cur,
                     'carbon_pools' : pool_dictionary,
                     'storage_cur' : storage_cur,
                     'hwp_cur_shape' : hwp_cur,
                     'calc_value' : False,
                     'lulc_cur_year' : 2000}
            
            invest_core.execute('carbon_core', arguments)
                            
#            assert_raster_equality(self, seq_value['uri'], '../../test_data/carbon_hwp_cur_regression.tif')
            assert_raster_equality_vec(self, storage_cur['uri'],
                                        '../../test_data/carbon_hwp_cur_regression.tif')
            os.remove(storage_cur['uri'])
            pass


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvest)
    unittest.TextTestRunner(verbosity=2).run(suite)



    
 
