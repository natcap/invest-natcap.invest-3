import unittest
import carbon, invest_carbon_core
import invest_test
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




class CarbonTestSuite(unittest.TestCase):

    def test_carbon_build_pools(self):
        """Verify the correct construction of the pools dict based on input
            datasets.  Since carbon.build_pools calls 
            carbon.build_pools_dict, this test will only verify that the
            process works and that the correct number of records have been 
            retained.  See test_carbon_build_pools_dict for per-record
            testing of the correct dict construction."""

        db = dbf.Dbf('../../test_data/carbon_pools_float.dbf', readOnly=1)
        raster1 = gdal.Open('../../test_data/lulc_samp_cur', gdal.GA_ReadOnly)
        raster2 = gdal.Open('../../test_data/lulc_samp_fut', gdal.GA_ReadOnly)

        pools = carbon.build_pools(db, raster1, raster2)
        numRecords = db.recordCount
        poolsLen = len(pools)

        #adding one extra value to the expected length of the pools dict
        #Extra entry represents the nodata value.
        self.assertEqual(numRecords + 1, poolsLen, 'Expected ' + str(numRecords) +
            ' records in the pools dict, but found ' + str(poolsLen) + ' instead')

    def test_carbon_build_pools_dict(self):
        """Verify the correct construction of the pools dict, including the 
            provided nodata values.  This is done on a per-entry basis."""

        db = dbf.Dbf('../../test_data/carbon_pools_float.dbf', readOnly=1)
        area = 1
        inNoData = -1
        outNoData = 255
        pools = carbon.build_pools_dict(db, area, inNoData, outNoData)

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

    def test_carbon_build_nodata_dict(self):
        """Assert that the nodata dict is being constructed properly
            based on its two input rasters, which have potentially different
            nodata values"""

        inputRaster = gdal.Open('../../test_data/lulc_samp_cur')
        outputRaster = gdal.Open('../../test_data/carbon_regression.tif')

        nodata_dict = carbon.build_nodata_dict(inputRaster, outputRaster)

        inNoData = inputRaster.GetRasterBand(1).GetNoDataValue()
        outNoData = outputRaster.GetRasterBand(1).GetNoDataValue()

        self.assertEqual(nodata_dict['input'], inNoData)
        self.assertEqual(nodata_dict['output'], outNoData)
        pass

    def test_carbon_valuate(self):
        """Verify the correct output of carbon.valuate()
        
            This test uses a small sample dataset with only ints as possible
            input values.  This greatly limits the number of possible values
            written to the MEM raster and allows us to check its values with
            a constructed dict."""

        #create the memory-based output raster
        driver = gdal.GetDriverByName('MEM')
        seq_value = driver.Create('temp.tif', 100, 100, 1, gdal.GDT_Float32)

        #set up our args dict for carbon.valuate()
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
        carbon.valuate(args)

        #calculate the number of years for use in the valuation equation
        numYears = args['lulc_fut_year'] - args['lulc_cur_year']

        #calculate the multiplier.
        #This is based on the summation portion of equation 10.14
        multiplier = 0.
#        for n in range(numYears-1): #Subtract 1 per the user's manual
        for n in range(numYears):    #This is wrong; allows us to match invest2
            multiplier += 1. / (((1. + args['rate_change']) ** n)
                              * (1. + args['discount']) ** n)

        #build up a dictionary for the expected output of valuate()
        valueDict = {}
        for i in range(1, 11):
            carbon_stored = float(i) / numYears
            valueDict[i] = args['c_value'] * carbon_stored * multiplier

        #Assert that valuate() wrote the correct values to seq_value
        vectorize_dataset_equality_pools(self, args['seq_delta'], seq_value, valueDict)
        pass

    def test_carbon_rasterValue(self):
        """Verify the correct output of carbon.rasterValue()"""

        #assemble arguments
        driver = gdal.GetDriverByName('MEM')
        outputRaster = driver.Create('temp.tif', 100, 100, 1, gdal.GDT_Float32)
        inputRaster = gdal.Open('../../test_data/randomInts100x100.tif')
        carbonValue = 7.54
        discount = 0.7
        rateOfChange = 0.7
        numYears = 30

        #run carbon.rasterValue()
        carbon.rasterValue(inputRaster, outputRaster, carbonValue,
                                discount, rateOfChange, numYears)

        #calculate the multiplier.
        #This is based on the summation portion of equation 10.14
        multiplier = 0.
#        for n in range(numYears-1): #Subtract 1 per the user's manual
        for n in range(numYears):    #This is wrong; allows us to match invest2
            multiplier += 1. / (((1. + rateOfChange) ** n) * (1. + discount) ** n)

        #build up a dictionary for the expected output of valuate()
        valueDict = {}
        for i in range(1, 11):
            carbon_stored = float(i) / numYears
            valueDict[i] = carbonValue * carbon_stored * multiplier

        #Assert that rasterValue() wrote the correct values to outputRaster
        vectorize_dataset_equality_pools(self, inputRaster, outputRaster, valueDict)

    def test_harvestProductInfo_cur_fut(self):
        """Verify that harvestProductInfo produces the correct results
            This is verified by a regression test."""

        #Create a working copy of the existing storage (regression) raster
        storage_orig = gdal.Open('../../test_data/carbon_regression.tif', gdal.GA_ReadOnly)
        driver = gdal.GetDriverByName('MEM')
        storage_mod_cur = driver.CreateCopy('temp0.tif', storage_orig, 0)
        storage_mod_fut = driver.CreateCopy('temp1.tif', storage_orig, 0)

        lulc = gdal.Open('../../test_data/lulc_samp_cur', gdal.GA_ReadOnly)

        #set up arguments
        args = {'lulc_cur' : lulc,
                'storage_cur' : storage_mod_cur,
                'carbon_pools' : dbf.Dbf('../../test_data/carbon_pools_float.dbf'),
                'lulc_fut' : gdal.Open('../../test_data/lulc_samp_fut', gdal.GA_ReadOnly),
                'hwp_cur_shape' : ogr.Open('../../test_data/harv_samp_cur/harv_samp_cur.shp'),
                'hwp_fut_shape' : ogr.Open('../../test_data/harv_samp_fut/harv_samp_fut.shp'),
                'lulc_cur_year' : 2000,
                'lulc_fut_year' : 2030,
                'storage_fut' : storage_mod_fut,
                'seq_delta' : invest_carbon_core.mimic(lulc, '../../carbon_output/seq_delta.tif'),
                'calc_value' : False,
                'biomass_cur' : invest_carbon_core.mimic(lulc, '../../carbon_output/biomass_cur.tif'),
                'biomass_fut' : invest_carbon_core.mimic(lulc, '../../carbon_output/biomass_fut.tif'),
                'volume_cur' : invest_carbon_core.mimic(lulc, '../../carbon_output/volume_cur.tif'),
                'volume_fut' : invest_carbon_core.mimic(lulc, '../../carbon_output/volume_fut.tif')}

        carbon.harvestProductInfo(args)

        vectorize_dataset_equality(self, args['biomass_cur'], gdal.Open('../../test_data/carbon_bio_cur_regression.tif'))
        vectorize_dataset_equality(self, args['biomass_fut'], gdal.Open('../../test_data/carbon_bio_fut_regression.tif'))
        vectorize_dataset_equality(self, args['volume_cur'], gdal.Open('../../test_data/carbon_vol_cur_regression.tif'))
        vectorize_dataset_equality(self, args['volume_fut'], gdal.Open('../../test_data/carbon_vol_fut_regression.tif'))

        for dataset in ('seq_delta.tif', 'biomass_cur.tif', 'volume_cur.tif',
                        'biomass_fut.tif', 'volume_fut.tif'):
            os.remove('../../carbon_output/' + dataset)

    def test_harvestProductInfo_cur(self):
        """Verify that harvestProductInfo produces the correct results when 
            operating strictly within a current context.
            This is verified by a regression test."""

        #Create a working copy of the existing storage (regression) raster
        storage_orig = gdal.Open('../../test_data/carbon_regression.tif', gdal.GA_ReadOnly)
        driver = gdal.GetDriverByName('MEM')
        storage_mod_cur = driver.CreateCopy('temp0.tif', storage_orig, 0)

        lulc = gdal.Open('../../test_data/lulc_samp_cur', gdal.GA_ReadOnly)

        #set up arguments
        args = {'lulc_cur' : lulc,
                'storage_cur' : storage_mod_cur,
                'carbon_pools' : dbf.Dbf('../../test_data/carbon_pools_float.dbf'),
                'hwp_cur_shape' : ogr.Open('../../test_data/harv_samp_cur/harv_samp_cur.shp'),
                'lulc_cur_year' : 2000,
                'calc_value' : False,
                'biomass_cur' : invest_carbon_core.mimic(lulc, '../../carbon_output/biomass_cur.tif'),
                'volume_cur' : invest_carbon_core.mimic(lulc, '../../carbon_output/volume_cur.tif')}

        carbon.harvestProductInfo(args)

        vectorize_dataset_equality(self, args['biomass_cur'], gdal.Open('../../test_data/carbon_bio_curOnly_regression.tif'))
        vectorize_dataset_equality(self, args['volume_cur'], gdal.Open('../../test_data/carbon_vol_curOnly_regression.tif'))

        for dataset in ('biomass_cur.tif', 'volume_cur.tif'):
            os.remove('../../carbon_output/' + dataset)

    def test_getFields(self):
        """Verify that getFields() produces the correct results."""

        dataset = ogr.Open('../../test_data/harv_samp_cur/harv_samp_cur.shp', 0)
        layer = dataset.GetLayerByName('harv_samp_cur')
        feature = layer.GetFeature(3)

        #this dict contains the known contents of feature ID 3
        referenceDict = {'C_den_cur': 0.5,
                          'Freq_cur': 5,
                          'BCEF_cur': 1.0,
                          'Cut_cur': 12.199999809299999,
                          'Decay_cur': 11,
                          'Start_date': 1946}

        outputDict = carbon.getFields(feature)

        for key, value in outputDict.iteritems():
            self.assertEqual(referenceDict[key], value)

    def test_carbon_mask_smoke(self):
        """Smoke test for the mask function."""
        lulc1 = np.zeros((1, 0))
        lulc2 = np.zeros((1, 0))
        nodata = {'input': 0, 'output': 0} #set a nodata value

        carbon.carbon_mask(nodata, lulc1, lulc2)
        pass

    def test_carbon_mask_1D_arrays(self):
        """Verify the output of carbon_mask with a 100-length array"""
        length = 100
        data = np.random.random_integers(1, 6, (1, length))
        mask = np.random.random_integers(0, 1, (1, length))
        nodata = {'input':-2, 'output':-2} #set a nodata value

        #run carbon_mask
        output = carbon.carbon_mask(nodata, data, mask)

        #verify the contents of output against pool and lulc data
        for x in range(data.shape[1]):
            currentValue = output[0][x]
            if currentValue == -2:
                self.assertEqual(mask[0][x], 0)
            else:
                self.assertEqual(currentValue, data[0][x])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(CarbonTestSuite)
    unittest.TextTestRunner(verbosity=2).run(suite)
