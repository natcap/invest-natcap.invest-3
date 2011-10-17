import unittest
import invest_carbon_core
from osgeo import gdal
import os, sys
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
        outArray = outputBand.ReadAsArray(0, i, outputBand.XSize, 1)
        i2Array = invest2Band.ReadAsArray(0, i, outputBand.XSize, 1)
        for j in range(0, outputBand.XSize):
            if (i2Array[0][j] == i2bnodata):
                unit.assertEqual(outArray[0][j], obnodata, "Should have found nodata pixel (value == " + str(obnodata) + ") in output raster at row " + str(i) + " index " + str(j) + ", but found " + str(outArray[0][j]) + " instead")
            else:
                a = outArray[0][j]
                b = i2Array[0][j]
                unit.assertAlmostEqual(a, b, 4, "Unequal pixel values detected at row " +
                                  str(i) + " index " + str(j) + ":" + str(a) + " " + str(b))


def checkRasterEqualityVec(firstUri, secondUri, unit=None):
    """Check the equality of the two input rasters.
        If the unit is provided, equality can be asserted as part of an
        automated test.
        
        firstUri - the URI to a GDAL-compatible raster
        secondUri - the URI to a GDAL-compatible raster
        unit - the 'self' object from the Unittest framework. Optional.
        
        No return value."""
    output = gdal.Open(firstUri, 0)
    outputBand = output.GetRasterBand(1)
    obnodata = outputBand.GetNoDataValue()
    
    invest2 = gdal.Open(secondUri, 0)
    invest2Band = invest2.GetRasterBand(1)
    i2bnodata = invest2Band.GetNoDataValue()

    if unit != None:
        unit.assertNotEqual(obnodata, None, "Output nodata value read as None")
        unit.assertEqual(outputBand.XSize, invest2Band.XSize, "Dimensions differ: output=" + str(outputBand.XSize) + ", i2output = " + str(invest2Band.XSize))
        unit.assertEqual(outputBand.YSize, invest2Band.YSize, "Dimensions differ: output=" + str(outputBand.YSize) + ", i2output = " + str(invest2Band.YSize))
        def checkEqual(a, b):
            if b == i2bnodata:
                unit.assertEqual(a, obnodata)
            else:
                unit.assertAlmostEqual(a, b, 4)
    else:
        def checkEqual(a, b):
            if b == i2bnodata:
                if a == obnodata:
                    return
                else:
                    raise Exception( a, obnodata)
            else:
                if round(a, 4) == round(b, 4):
                    return
                else:
                    raise Exception

    for i in range(0, outputBand.YSize):
        outArray = outputBand.ReadAsArray(0, i, outputBand.XSize, 1)
        i2Array = invest2Band.ReadAsArray(0, i, outputBand.XSize, 1)
                
        fastCheck = np.vectorize(checkEqual)
        fastCheck(outArray, i2Array)
 
def removeCreatedFiles(outdir='../../carbon_output' + os.sep):
    """Remove files created with the default filenames.
    
        outdir='../../carbon_output'+os.sep - the path to the output directory
        
        no return value."""
        
    for uri in ('tot_C_cur.tif', 'tot_C_fut.tif', 'sequest.tif', 'value_seq.tif', 
                'bio_hwp_cur.tif', 'bio_hwp_fut.tif', 'vol_hwp_cur.tif',
                'vol_hwp_fut.tif'):
        filepath = outdir + uri
        if os.path.exists(filepath):
            os.remove(filepath)
        

class TestInvest(unittest.TestCase):
   
        def test_carbon_model_regression(self):
            """Regression Test to run Carbon model using sample data.  
            Results will be compared with a raster that is known to be accurate."""
    
            storage_cur = '../../carbon_output/test_carbon_output.tif'
    
            arguments = {'lulc_cur': '../../test_data/lulc_samp_cur',
                         'carbon_pools' : '../../test_data/carbon_pools_float.dbf',
                         'storage_cur' : storage_cur,
                         'output_dir' : '../../carbon_output',
                         'calc_value' : False}
    
            invest_carbon_core.execute(arguments)
    
#            assert_raster_equality(self, output_dictionary['uri'], '../../test_data/carbon_regression.tif' )
            checkRasterEqualityVec(storage_cur, '../../test_data/carbon_regression.tif', self)
            os.remove(storage_cur)
            
            removeCreatedFiles()
            pass




        def test_verify_carbon3_against_carbon21_int_pools(self):
            """Test the InVEST3 carbon model against the known output raster of InVEST2.1 carbon
                
                Uses the modified pools dbf, where all values are ints."""
                
            storage_cur = '../../carbon_output/test_carbon_output.tif'

            arguments = {'lulc_cur': '../../test_data/lulc_samp_cur',
                     'carbon_pools' : '../../test_data/carbon_pools_int.dbf',
                     'storage_cur' : storage_cur,
                     'output_dir' : '../../carbon_output',
                     'calc_value' : False}

            invest_carbon_core.execute(arguments)
            
#            assert_raster_equality(self, output_dictionary['uri'], '../../test_data/tot_c_cur_int')
            checkRasterEqualityVec(storage_cur, '../../test_data/tot_c_cur_int', self)
            os.remove(storage_cur)

            removeCreatedFiles()
            pass
        
        
        def test_carbon_valuation(self):
            """Verify that the carbon valuation model passes successfully"""
            
            storage_cur = '../../carbon_output/test_seq_cur.tif'
            storage_fut = '../../carbon_output/test_seq_fut.tif'
            seq_delta = '../../carbon_output/test_seq_delta.tif'
            seq_value = '../../carbon_output/test_carbon_value.tif'
            
            arguments = {'lulc_cur': '../../test_data/lulc_samp_cur',
                         'lulc_fut': '../../test_data/lulc_samp_fut',
                     'carbon_pools' : '../../test_data/carbon_pools_int.dbf',
                     'storage_cur' : storage_cur,
                     'storage_fut' : storage_fut,
                     'seq_delta' : seq_delta,
                     'seq_value' : seq_value,
                     'output_dir' : '../../carbon_output',
                     'calc_value' : True,
                     'lulc_cur_year' : 2000,
                     'lulc_fut_year' : 2030,
                     'c_value' : 43.0,
                     'discount' : 0.07,
                     'rate_change' : 0.0}
            
            invest_carbon_core.execute(arguments)
                            
#            assert_raster_equality(self, seq_value['uri'], '../../test_data/val_seq_int')
            checkRasterEqualityVec(seq_value, '../../test_data/val_seq_int', self)
            
            for uri in (storage_cur, storage_fut, seq_delta, seq_value):
                os.remove(uri)

            removeCreatedFiles()
            pass
        
        def test_carbon_storage_hwp_regression(self):
            """Verify the carbon storage model (with HWP) against known results"""
            
            storage_cur = '../../carbon_output/test_seq_cur.tif'
            
            arguments = {'lulc_cur': '../../test_data/lulc_samp_cur',
                     'carbon_pools' : '../../test_data/carbon_pools_int.dbf',
                     'storage_cur' : storage_cur,
                     'hwp_cur_shape' : '../../test_data/harv_samp_cur/harv_samp_cur.shp',
                     'output_dir' : '../../carbon_output',
                     'calc_value' : False,
                     'lulc_cur_year' : 2000}
            
            invest_carbon_core.execute(arguments)
                            
#            assert_raster_equality(self, seq_value['uri'], '../../test_data/carbon_hwp_cur_regression.tif')
            checkRasterEqualityVec(storage_cur, '../../test_data/carbon_hwp_cur_regression.tif', self)
            os.remove(storage_cur)
            
            #remove files created at default filepaths
            removeCreatedFiles()


        def test_carbon_storage_hwp_fut_regression(self):
            """Verify the carbon model (with cur+fut HWP) against known results"""
            
            storage_cur = '../../carbon_output/test_seq_cur.tif'
            storage_fut = '../../carbon_output/test_seq_fut.tif'
            seq_delta = '../../carbon_output/seq_delta1.tif'
            biomass_cur = '../../carbon_output/bio_cur.tif'
            biomass_fut = '../../carbon_output/bio_fut.tif'
            volume_cur = '../../carbon_output/vol_cur.tif'
            volume_fut = '../../carbon_output/vol_fut.tif'
            
            arguments = {'lulc_cur': '../../test_data/lulc_samp_cur',
                         'lulc_fut': '../../test_data/lulc_samp_fut',
                         'carbon_pools' : '../../test_data/carbon_pools_float.dbf',
                         'storage_cur' : storage_cur,
                         'storage_fut' : storage_fut,
                         'seq_delta'   : seq_delta,
                         'hwp_cur_shape' : '../../test_data/harv_samp_cur/harv_samp_cur.shp',
                         'hwp_fut_shape' : '../../test_data/harv_samp_fut/harv_samp_fut.shp',
                         'output_dir' : '../../carbon_output',
                         'calc_value' : False,
                         'lulc_cur_year' : 2000,
                         'lulc_fut_year' : 2030,
                         'biomass_cur' : biomass_cur,
                         'biomass_fut' : biomass_fut,
                         'volume_cur' : volume_cur,
                         'volume_fut' : volume_fut}
             
            invest_carbon_core.execute(arguments)
                            
            checkRasterEqualityVec(storage_fut, '../../test_data/carbon_hwp_fut_regression.tif', self)
            checkRasterEqualityVec(biomass_cur,'../../test_data/carbon_bio_cur_regression.tif', self)            
            checkRasterEqualityVec(biomass_fut,'../../test_data/carbon_bio_fut_regression.tif', self)
            checkRasterEqualityVec(volume_cur, '../../test_data/carbon_vol_cur_regression.tif', self)
            checkRasterEqualityVec(volume_fut, '../../test_data/carbon_vol_fut_regression.tif', self)
            for uri in (storage_cur, storage_fut, seq_delta, biomass_cur, 
                        biomass_fut, volume_cur, volume_fut):
                os.remove(uri)

            removeCreatedFiles()
            pass

if __name__ == '__main__':
    #If two arguments provided, assume they are rasters, check equality
    if len(sys.argv) == 3:
        try:
            checkRasterEqualityVec(sys.argv[1], sys.argv[2])
            print 'Rasters are equal.'
        except:
            print 'Rasters are not equal or an error occurred.'
    #otherwise, run the test suite.
    else:    
        suite = unittest.TestLoader().loadTestsFromTestCase(TestInvest)
        unittest.TextTestRunner(verbosity=2).run(suite)


    
 
