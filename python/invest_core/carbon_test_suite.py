import unittest
import carbon, carbon_core
import numpy as np
import random
import os
import math
from dbfpy import dbf
import osgeo.osr as osr
try:
    from osgeo import ogr, gdal
    from osgeo.gdalconst import *
    import numpy
    use_numeric = False
except ImportError:
    import ogr, gdal
    from gdalconst import *
    import Numeric

def suite():
    tests = ['carbon_add_test',
             'carbon_diff_test',
             'carbon_value_test',
             'carbon_core_test',
             'carbon_uncertainty_test',
             'carbon_scenario_uncertainty_test']
    suite = unittest.TestLoader().loadTestsFromNames(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

def makeRandomRaster(cols, rows, uri='test.tif', format='GTiff'):
    """Create a new raster with random int values.
        
        cols - an int, the number of columns in the output raster
        rows - an int, the number of rows in the output raster
        uri - a string for the path to the file
        format - a string representing the GDAL format code such as 
            'GTiff' or 'MEM'.  See http://gdal.org/formats_list.html for a
            complete list of formats.
            
        returns a new dataset with random values."""
        
    driver = gdal.GetDriverByName(format)
    dataset = driver.Create(uri, cols, rows, 1, gdal.GDT_Float32)
    band = dataset.GetRasterBand(1)
    
    for i in range(0, band.YSize):
        array = band.ReadAsArray(0, i, band.XSize, 1)
        for j in range(0, band.XSize):
            array[0][j] = random.randint(1,10)
        dataset.GetRasterBand(1).WriteArray(array, 0, i)

    return dataset

def vectorize_dataset_equality_pools(unit, firstDS, secondDS, dict):
    """Assert that the pixel values of secondDS match those of firstDS when
        the input dict is mapped.
        
        unit - the 'self' object from the unittesting framework
        firstDS - an open GDAL raster dataset
        secondDS - an open GDAL raster dataset
        dict - a dictionary mapping values of firstDS to what they should have
            been recorded as in secondDS.
            
        no return value"""
        
    firstDSBand = firstDS.GetRasterBand(1)
    secondDSBand = secondDS.GetRasterBand(1)
    unit.assertEqual(firstDSBand.XSize, secondDSBand.XSize,
                      "Dimensions differ: first=" + str(firstDSBand.XSize) +
                       ", second = " + str(secondDSBand.XSize))
    unit.assertEqual(firstDSBand.YSize, secondDSBand.YSize,
                      "Dimensions differ: first=" + str(firstDSBand.YSize) + 
                      ", second = " + str(secondDSBand.YSize))

    for i in range(0, firstDSBand.YSize):
        firstArray = firstDSBand.ReadAsArray(0, i, firstDSBand.XSize, 1)
        secondArray = secondDSBand.ReadAsArray(0, i, firstDSBand.XSize, 1)

        def checkEqual(a, b):
            """Assert that dict[a] == b"""
            unit.assertAlmostEqual(dict[a], b, 6)
                
        fastCheck = np.vectorize(checkEqual)
        fastCheck(firstArray, secondArray)


class CarbonTestSuite(unittest.TestCase):
    def test_carbon_seq_smoke(self):
        """Smoke test for carbon_seq function.  Shouldn't crash with
        zero length inputs"""
        lulc = np.zeros((1, 0))
        pools = {}
        carbon_core.carbon_seq(lulc, pools)

    def test_carbon_seq_1D_array(self):
        """Test of carbon_seq against a 1D input/output array"""
        #setup the three args to carbon_seq
        length = 100
        lulc = np.zeros((1, length))
        for x in range(length):
            lulc[0][x] = random.randint(0, 2)

        pools = {0: 3.3,
                 1: 4.4,
                 2: 5.5}

        #run carbon_seq
        output = carbon_core.carbon_seq(lulc, pools)

        #verify the contents of output against pool and lulc data
        for x in range(lulc.shape[1]):
            self.assertEqual(output[0][x],
                            pools[lulc[0][x]],
                            'Pool data was not correctly transcribed')


    def test_carbon_diff_smoke(self):
        """Smoke test for the diff function."""
        lulc1 = np.zeros((1,0))
        lulc2 = np.zeros((1,0))
        nodata = {'input': 0, 'output': 0} #set a nodata value
        
        carbon_core.carbon_diff(nodata, lulc1, lulc2)
        pass
    
    def test_carbon_diff_1D_arrays(self):
        length = 100
        lulc1 = np.zeros((1, length))
        lulc2 = np.ones((1, length))
        nodata = {'input': -2, 'output': -2} #set a nodata value
        
        #run carbon_diff
        output = carbon_core.carbon_diff(nodata, lulc1, lulc2)

        #verify the contents of output against pool and lulc data
        for x in range(lulc1.shape[1]):
            self.assertEqual(output[0][x], 1, 'Difference was not correctly calculated.')



    def test_carbon_add_smoke(self):
        """Smoke test for the diff function."""
        lulc1 = np.zeros((1,0))
        lulc2 = np.zeros((1,0))
        nodata = {'cur': 0, 'fut': 0} #set a nodata value
        
        carbon_core.carbon_add(nodata, lulc1, lulc2)
        pass
    
    def test_carbon_add_1D_arrays(self):
        length = 100
        lulc1 = np.zeros((1, length))
        lulc2 = np.zeros((1, length))
        for x in range(length):
            lulc1[0][x] = 15.0*random.random()
            lulc2[0][x] = 10.0*random.random()
            
        nodata = {'input': -2, 'output': -2} #set a nodata value
        
        #run carbon_add
        output = carbon_core.carbon_add(nodata, lulc1, lulc2)

        #verify the contents of output against pool and lulc data
        for x in range(lulc1.shape[1]):
            self.assertEqual(output[0][x], lulc1[0][x] + lulc2[0][x], 'Sum was not correctly calculated.')


    def test_carbon_value_1D_array(self):
        """Test of carbon_value against a 1D input/output array"""
        #setup the three args to carbon_seq
        length = 100
        lulc = np.ones((1, length))
        nodata = {'input': -1, 'output': -1}

        #run carbon_value
        output = carbon_core.carbon_value(nodata, lulc, 3, 2.0, 4.0)

        #verify the output data was calculated and mapped correctly
        #Each value should equal 2.66666666666
        for x in range(lulc.shape[1]):
            self.assertAlmostEqual(output[0][x],2.6666666666, 8)


    def test_carbon_core_smoke(self):
        """Smoke test for carbon_core function.  Shouldn't crash with
        zero length inputs"""
        driver = gdal.GetDriverByName("GTIFF")
        lulc_path = '../../test_data/test_blank_input'
        lulc = driver.Create(lulc_path, 1, 1, 1, gdal.GDT_Byte)
        lulc.GetRasterBand(1).SetNoDataValue(-1.0)

        output_path = '../../test_data/test_blank_output'
        output = driver.Create(output_path, 1, 1, 1, gdal.GDT_Byte)
        output.GetRasterBand(1).SetNoDataValue(-1.0)

        args = { 'lulc_cur':lulc,
                'carbon_pools': dbf.Dbf('../../test_data/test_blank_dbf', new=True),
                'storage_cur': output,
                'calc_value' : False}

        carbon_core.execute(args)

        #close the two created datasets and DBF file.
        lulc = None
        output = None
        args['carbon_pools'].close()

        os.remove(output_path)
        os.remove('../../test_data/test_blank_dbf')
        os.remove(lulc_path)
        pass

    def test_carbon_core_with_inputs(self):
        """Test carbon_core using realistic inputs."""
        driver = gdal.GetDriverByName("GTIFF")
        lulc = gdal.Open('../../test_data/lulc_samp_cur', GA_ReadOnly)
        out_dict = {'uri':'../../test_real_output.tif',
                    'input':False,
                    'type': 'gdal',
                    'dataType': 6}
        output = carbon.mimic(lulc, out_dict['uri'])
        args = { 'lulc_cur': lulc,
                'carbon_pools': dbf.Dbf('../../test_data/carbon_pools_int.dbf'),
                'storage_cur': output,
                'calc_value' : False}

        carbon_core.execute(args)
        output = None
        os.remove(out_dict['uri'])
        pass

    def test_carbon_core_with_HWP_inputs(self):
        """Test carbon using realistic inputs.  Includes HWP"""
        driver = gdal.GetDriverByName("GTIFF")
        lulc = gdal.Open('../../test_data/lulc_samp_cur', GA_ReadOnly)
        out_dict = {'uri':'../../carbon_output/test_real_output_hwp.tif',
                    'input':False,
                    'type': 'gdal',
                    'dataType': 6}
        output = carbon.mimic(lulc, out_dict['uri'])
        args = { 'lulc_cur': lulc,
                'carbon_pools': dbf.Dbf('../../test_data/carbon_pools_int.dbf'),
                'storage_cur': output,
                'calc_value' : False,
                'hwp_cur_shape': ogr.Open('../../test_data/harv_samp_cur/harv_samp_cur.shp'),
                'lulc_cur_year' : 2000}



        carbon_core.execute(args)
        output = None
        #os.remove(out_dict['uri'])
        pass

    def test_carbon_core_HWP_cur_fut(self):
        """Test carbon_core with cur and fut HWP"""
        driver = gdal.GetDriverByName("GTIFF")
        lulc = gdal.Open('../../test_data/lulc_samp_cur', GA_ReadOnly)
        out_dict = {'uri':'../../carbon_output/test_real_output_hwp.tif',
                    'input':False,
                    'type': 'gdal',
                    'dataType': 6}
        output = carbon.mimic(lulc, out_dict['uri'])
        args = { 'lulc_cur': lulc,
                'carbon_pools': dbf.Dbf('../../test_data/carbon_pools_int.dbf'),
                'storage_cur': output,
                'calc_value' : False,
                'hwp_cur_shape': ogr.Open('../../test_data/harv_samp_cur/harv_samp_cur.shp'),
                'hwp_fut_shape': ogr.Open('../../test_data/harv_samp_fut/harv_samp_fut.shp'),
                'lulc_cur_year' : 2000,
                'lulc_fut_year' : 2030}

        carbon_core.execute(args)
        output = None
        #os.remove(out_dict['uri'])
        pass


    def test_carbon_core_build_pools(self):
        """Verify the correct construction of the pools dict based on input
            datasets.  Since carbon_core.build_pools calls 
            carbon_core.build_pools_dict, this test will only verify that the
            process works and that the correct number of records have been 
            retained.  See test_carbon_core_build_pools_dict for per-record
            testing of the correct dict construction."""
            
        db = dbf.Dbf('../../test_data/carbon_pools_float.dbf', readOnly=1)
        raster1 = gdal.Open('../../test_data/lulc_samp_cur', gdal.GA_ReadOnly)
        raster2 = gdal.Open('../../test_data/lulc_samp_fut', gdal.GA_ReadOnly)
        
        pools = carbon_core.build_pools(db, raster1, raster2)
        numRecords = db.recordCount
        poolsLen = len(pools)

        #adding one extra value to the expected length of the pools dict
        #Extra entry represents the nodata value.
        self.assertEqual(numRecords + 1, poolsLen, 'Expected ' + str(numRecords) +
            ' records in the pools dict, but found ' + str(poolsLen) + ' instead')

        

    def test_carbon_core_build_pools_dict(self):
        """Verify the correct construction of the pools dict, including the 
            provided nodata values.  This is done on a per-entry basis."""
            
        db = dbf.Dbf('../../test_data/carbon_pools_float.dbf', readOnly=1)
        area = 1
        inNoData = -1
        outNoData = 255
        pools = carbon_core.build_pools_dict(db, area, inNoData, outNoData)

        #loop through dbf entries and verify the correct sum has been returned.
        for i in range(db.recordCount):
            sum = 0
            for field in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD'):
                sum += db[i][field]
            sum = sum * area
            lulc_id = db[i]['LULC']
            self.assertEqual(pools[lulc_id], sum)
        
        #assert the nodata value entry
        self.assertEqual(pools[inNoData], outNoData)
        
        #close the DBF file.
        db.close()
        pass

    
    def test_carbon_core_pixel_area(self):
        """Verify the correct output of carbon_core.pixelArea()"""
        
        dataset = gdal.Open('../../test_data/carbon_regression.tif', gdal.GA_ReadOnly)
        
        srs = osr.SpatialReference()
        srs.SetProjection(dataset.GetProjection())
        linearUnits = srs.GetLinearUnits()
        geotransform = dataset.GetGeoTransform()
        #take absolute value since sometimes negative widths/heights
        areaMeters = abs(geotransform[1] * geotransform[5] * (linearUnits ** 2))
        result = areaMeters / (10 ** 4) #convert m^2 to Ha
        
        #run pixelArea()
        area = carbon_core.pixelArea(dataset)
        
        #assert the output of pixelArea against our calculation
        self.assertEqual(result, area)
        pass

    def test_carbon_core_build_nodata_dict(self):
        """Assert that the nodata dict is being constructed properly
            based on its two input rasters, which have potentially different
            nodata values"""
            
        inputRaster = gdal.Open('../../test_data/lulc_samp_cur')
        outputRaster = gdal.Open('../../test_data/carbon_regression.tif')

        nodata_dict = carbon_core.build_nodata_dict(inputRaster, outputRaster)
        
        inNoData = inputRaster.GetRasterBand(1).GetNoDataValue()
        outNoData = outputRaster.GetRasterBand(1).GetNoDataValue()
        
        self.assertEqual(nodata_dict['input'], inNoData)
        self.assertEqual(nodata_dict['output'], outNoData)
        pass
    
    def test_carbon_core_calc_feature_hwp(self):
        """Verify the correct output of calcFeatureHWP() against our own
            calculation using the same numbers."""
            
        limit = 4
        decay = 0.74
        endDate = 2030
        startDate = 2000
        freq = 4
        
        #run calcFeatureHWP
        result = carbon_core.calcFeatureHWP(limit, decay, endDate, startDate, freq)   
                
        #Calculate the result on our own
        sum = 0
        for t in range(int(limit)):
            w = math.log(2)/decay
            m =  endDate - startDate - (t*freq)
            sum += ((1-(math.e**(-w)))/(w*math.e**(m*w)))
    
        #verify our output
        self.assertEqual(result, sum)

    def test_carbon_core_valuate(self):
        """Verify the correct output of carbon_core.valuate()
        
            This test uses a small sample dataset with only ints as possible
            input values.  This greatly limits the number of possible values
            written to the MEM raster and allows us to check its values with
            a constructed dict."""
            
        #create the memory-based output raster
        driver = gdal.GetDriverByName('MEM')
        seq_value = driver.Create('temp.tif', 100, 100, 1, gdal.GDT_Float32)
        
        #set up our args dict for carbon_core.valuate()
        args = {'lulc_cur': gdal.Open('../../test_data/lulc_samp_cur',
                                       gdal.GA_ReadOnly),
                'storage_cur': gdal.Open('../../test_data/carbon_regression.tif',
                                          gdal.GA_ReadOnly),
                'seq_delta' : gdal.Open('../../test_data/randomInts100x100.tif'),
                'seq_value' : seq_value,
                'carbon_pools': dbf.Dbf('../../test_data/carbon_pools_float.dbf'),
                'lulc_fut_year': 2030,
                'lulc_cur_year': 2000,
                'c_value': 7.54,
                'discount': 0.7,
                'rate_change':0.8}
        
        #run the valuate function
        carbon_core.valuate(args)

        #calculate the number of years for use in the valuation equation
        numYears = args['lulc_fut_year'] - args['lulc_cur_year']

        #calculate the multiplier.
        #This is based on the summation portion of equation 10.14
        multiplier = 0.
#        for n in range(numYears-1): #Subtract 1 per the user's manual
        for n in range(numYears):    #This is wrong; allows us to match invest2
            multiplier += 1./(((1.+args['rate_change'])**n)
                              *(1.+args['discount'])**n)
        
        #build up a dictionary for the expected output of valuate()
        valueDict = {}
        for i in range(1,11):
            carbon_stored = float(i)/numYears
            valueDict[i] = args['c_value']*carbon_stored*multiplier
        
        #Assert that valuate() wrote the correct values to seq_value
        vectorize_dataset_equality_pools(self, args['seq_delta'], seq_value, valueDict)        
        pass

    def test_carbon_core_rasterValue(self):
        """Verify the correct output of carbon_core.rasterValue()"""
        
        #assemble arguments
        driver = gdal.GetDriverByName('MEM')
        outputRaster = driver.Create('temp.tif', 100, 100, 1, gdal.GDT_Float32)
        inputRaster = gdal.Open('../../test_data/randomInts100x100.tif')
        carbonValue = 7.54
        discount = 0.7
        rateOfChange = 0.7
        numYears = 30
        
        #run carbon_core.rasterValue()
        carbon_core.rasterValue(inputRaster, outputRaster, carbonValue, 
                                discount, rateOfChange, numYears)
        
        #calculate the multiplier.
        #This is based on the summation portion of equation 10.14
        multiplier = 0.
#        for n in range(numYears-1): #Subtract 1 per the user's manual
        for n in range(numYears):    #This is wrong; allows us to match invest2
            multiplier += 1./(((1.+rateOfChange)**n)*(1.+discount)**n)
        
        #build up a dictionary for the expected output of valuate()
        valueDict = {}
        for i in range(1,11):
            carbon_stored = float(i)/numYears
            valueDict[i] =carbonValue*carbon_stored*multiplier
        
        #Assert that rasterValue() wrote the correct values to outputRaster
        vectorize_dataset_equality_pools(self, inputRaster, outputRaster, valueDict)
        pass

    def test_carbon_core_rasterDiff(self):
        """Verify the correct output of carbon_core.rasterDiff()"""

        #set up arguments        
        driver = gdal.GetDriverByName('MEM')
        outputRaster = driver.Create('temp.tif', 100, 100, 1, gdal.GDT_Float32)
        raster1 = gdal.Open('../../test_data/randomInts100x100.tif', gdal.GA_ReadOnly)
        raster2 = gdal.Open('../../test_data/constant4.67_100x100.tif', gdal.GA_ReadOnly)
        
        #run carbon_core.rasterDiff
        carbon_core.rasterDiff(raster1, raster2, outputRaster)
        
        #set up our dict of rasterDiff's expected output
        valueDict = {}
        for i in range(1,11):
            valueDict[i] = 4.67-i #4.67 is the value of every pixel in raster2

        #Verify that rasterDiff() wrote the correct values to the outputRaster
        vectorize_dataset_equality_pools(self, raster1, outputRaster, valueDict)
        pass
    


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(CarbonTestSuite)
    unittest.TextTestRunner(verbosity=2).run(suite)