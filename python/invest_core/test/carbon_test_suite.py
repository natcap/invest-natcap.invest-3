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

    def test_carbon_iterFeatures_cur(self):
        """Verify that iterFeatures correctly calculates HWP per layer.
            IterFeatures has three modes of operation:
            
            1. suffix='cur',
            2. suffix='cur', yrFut!=None
            3. suffix='fut'
            
            This test will test the first mode, which would be invoked if the
            user provided HWP data for the current scenario only."""

        #set up our arguments
        shapeURI = '../../test_data/harv_samp_cur/harv_samp_cur.shp'
        hwp_shape = ogr.Open(shapeURI)

        #copy the old shapefile to a new shapefile that we can modify
        ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(hwp_shape, "testMemShape")
        copied_shape = ogr.Open('./testMemShape', 1)
        temp_layer = copied_shape.GetLayerByName('harv_samp_cur')

        #Create a hardwood products pool that will get calculated later
        hwp_def = ogr.FieldDefn("hwp_pool", ogr.OFTReal)
        temp_layer.CreateField(hwp_def)

        #set the year of current land use
        yrCur = 2000

        #call carbon.iterFeatures using our copied shapefile
        carbon.iterFeatures(temp_layer, 'cur', yrCur)

        #reopen the OGR shapefile we used previously
        copied_shape = ogr.Open(shapeURI)
        hwp_layer = copied_shape.GetLayerByName('harv_samp_cur')

        #Determine what HWP values should have been stored per layer
        featureDict = {}
        for feature in hwp_layer:
            #first, initialize layer fields by index
            fieldArgs = {'Cut_cur' : feature.GetFieldIndex('Cut_cur'),
                         'Freq_cur' : feature.GetFieldIndex('Freq_cur'),
                         'Decay_cur' : feature.GetFieldIndex('Decay_cur'),
                         'C_den_cur' : feature.GetFieldIndex('C_den_cur'),
                         'BCEF_cur' : feature.GetFieldIndex('BCEF_cur'),
                         'Start_date' : feature.GetFieldIndex('Start_date')}

            #then, replace the indices with actual items
            for key, index in fieldArgs.iteritems():
                fieldArgs[key] = feature.GetField(index)

            #set the parameters for the summation calculation
            limit = math.ceil(((yrCur - fieldArgs['Start_date'])\
                                    / fieldArgs['Freq_cur'])) - 1.0
            endDate = yrCur
            decay = fieldArgs['Decay_cur']
            startDate = fieldArgs['Start_date']
            freq = fieldArgs['Freq_cur']

            #calculate the feature's HWP carbon pool
            sum = carbon.calcFeatureHWP(limit, decay, endDate, startDate, freq)

            #set the HWP carbon pool for this feature.
            featureDict[feature.GetFID()] = fieldArgs['Cut_cur'] * sum

        #reopen the shapefile that contains calculated HWP values
        hwp_shape = ogr.Open('./testMemShape')
        hwp_layer = hwp_shape.GetLayerByName('harv_samp_cur')

        #Assert that HWP values stored in the shapefile match our dict entries
        for fid in featureDict:
            feature = hwp_layer.GetFeature(fid)
            index = feature.GetFieldIndex('hwp_pool')
            self.assertAlmostEqual(feature.GetField(index), featureDict[fid], 8)

        #remove working files.
        for ext in ('dbf', 'prj', 'shp', 'shx'):
            os.remove('./testMemShape/harv_samp_cur.' + ext)

        os.removedirs('./testMemShape')
        pass

    def test_carbon_iterFeatures_cur_avg(self):
        """Verify that iterFeatures correctly calculates HWP per layer with avg
            IterFeatures has three modes of operation:
            
            1. suffix='cur',
            2. suffix='cur', yrFut!=None
            3. suffix='fut'
            
            This test will test the second mode, which would be invoked if the
            user provided HWP data for current and future scenarios.  This part
            of iterFeatures calculates HWP for the current landscape, but in a
            future context."""

        #set up our arguments
        shapeURI = '../../test_data/harv_samp_cur/harv_samp_cur.shp'
        hwp_shape = ogr.Open(shapeURI)
        ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(hwp_shape, 'testShapeCur')
        yrCur = 2000
        yrFut = 2030

        #Open the copied file
        hwp_shape = ogr.Open('testShapeCur', 1)
        hwp_layer = hwp_shape.GetLayerByName('harv_samp_cur')

        #Create a hardwood products pool that will get calculated later
        hwp_def = ogr.FieldDefn("hwp_pool", ogr.OFTReal)
        hwp_layer.CreateField(hwp_def)

        #call carbon.iterFeatures
        carbon.iterFeatures(hwp_layer, 'cur', yrCur, yrFut)

        #reopen the original shapefile
        copied_shape = ogr.Open(shapeURI)
        hwp_layer = copied_shape.GetLayerByName('harv_samp_cur')

        #Determine what values should have been stored per layer
        featureDict = {}
        avg = math.floor((yrFut + yrCur) / 2.0)
        for feature in hwp_layer:
            #first, initialize layer fields by index
            fieldArgs = {'Cut_cur' : feature.GetFieldIndex('Cut_cur'),
                         'Freq_cur' : feature.GetFieldIndex('Freq_cur'),
                         'Decay_cur' : feature.GetFieldIndex('Decay_cur'),
                         'C_den_cur' : feature.GetFieldIndex('C_den_cur'),
                         'BCEF_cur' : feature.GetFieldIndex('BCEF_cur'),
                         'Start_date' : feature.GetFieldIndex('Start_date')}

            #then, replace the indices with actual items
            for key, index in fieldArgs.iteritems():
                fieldArgs[key] = feature.GetField(index)

            #set the parameters for the summation calculation
            limit = math.ceil(((avg - fieldArgs['Start_date'])\
                                / fieldArgs['Freq_cur'])) - 1.0
            endDate = yrFut
            decay = fieldArgs['Decay_cur']
            startDate = fieldArgs['Start_date']
            freq = fieldArgs['Freq_cur']

            #calculate the feature's HWP carbon pool
            sum = carbon.calcFeatureHWP(limit, decay, endDate, startDate, freq)

            #set the HWP carbon pool for this feature.
            featureDict[feature.GetFID()] = fieldArgs['Cut_cur'] * sum

        #reopen the shapefile that contains calculated HWP values
        hwp_shape = ogr.Open('./testShapeCur')
        hwp_layer = hwp_shape.GetLayerByName('harv_samp_cur')

        #Assert that HWP values stored in the shapefile match our dict entries
        for fid in featureDict:
            feature = hwp_layer.GetFeature(fid)
            index = feature.GetFieldIndex('hwp_pool')
            self.assertAlmostEqual(feature.GetField(index), featureDict[fid], 8)

        #remove working files.
        for ext in ('dbf', 'prj', 'shp', 'shx'):
            os.remove('./testShapeCur/harv_samp_cur.' + ext)

        os.removedirs('./testShapeCur')
        pass

    def test_carbon_iterFeatures_fut(self):
        """Verify that iterFeatures correctly calculates future HWP per shape
            IterFeatures has three modes of operation:
            
            1. suffix='cur',
            2. suffix='cur', yrFut!=None
            3. suffix='fut'
            
            This test will test the third mode, which would be invoked if the
            user provided HWP data for current and future scenarios.  This part
            of iterFeatures calculates HWP for the future landscape."""

        #set up our arguments
        shapeURI = '../../test_data/harv_samp_fut/harv_samp_fut.shp'
        hwp_shape = ogr.Open(shapeURI)
        ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(hwp_shape, 'testShapeFut')
        yrCur = 2000
        yrFut = 2030

        #Open the copied file
        hwp_shape = ogr.Open('testShapeFut', 1)
        hwp_layer = hwp_shape.GetLayerByName('harv_samp_fut')

        #Create a hardwood products pool that will get calculated later
        hwp_def = ogr.FieldDefn("hwp_pool", ogr.OFTReal)
        hwp_layer.CreateField(hwp_def)

        #call carbon.iterFeatures
        carbon.iterFeatures(hwp_layer, 'fut', yrCur, yrFut)

        #reopen the original shapefile
        copied_shape = ogr.Open(shapeURI)
        hwp_layer = copied_shape.GetLayerByName('harv_samp_fut')

        #Determine what values should have been stored per layer
        featureDict = {}
        avg = math.floor((yrFut + yrCur) / 2.0)
        for feature in hwp_layer:
            #first, initialize layer fields by index
            fieldArgs = {'Cut_fut' : feature.GetFieldIndex('Cut_fut'),
                         'Freq_fut' : feature.GetFieldIndex('Freq_fut'),
                         'Decay_fut' : feature.GetFieldIndex('Decay_fut'),
                         'C_den_fut' : feature.GetFieldIndex('C_den_fut'),
                         'BCEF_fut' : feature.GetFieldIndex('BCEF_fut')}

            #then, replace the indices with actual items
            for key, index in fieldArgs.iteritems():
                fieldArgs[key] = feature.GetField(index)

            #set the parameters for the summation calculation
            limit = math.ceil(((yrFut - avg)\
                                / fieldArgs['Freq_fut'])) - 1.0
            decay = fieldArgs['Decay_fut']
            startDate = avg
            endDate = yrFut
            freq = fieldArgs['Freq_fut']

            #calculate the feature's HWP carbon pool
            sum = carbon.calcFeatureHWP(limit, decay, endDate, startDate, freq)

            #set the HWP carbon pool for this feature.
            featureDict[feature.GetFID()] = fieldArgs['Cut_fut'] * sum

        #reopen the shapefile that contains calculated HWP values
        hwp_shape = ogr.Open('./testShapeFut')
        hwp_layer = hwp_shape.GetLayerByName('harv_samp_fut')

        #Assert that HWP values stored in the shapefile match our dict entries
        for fid in featureDict:
            feature = hwp_layer.GetFeature(fid)
            index = feature.GetFieldIndex('hwp_pool')
            self.assertAlmostEqual(feature.GetField(index), featureDict[fid], 8)

        #remove working files.
        for ext in ('dbf', 'prj', 'shp', 'shx'):
            os.remove('./testShapeFut/harv_samp_fut.' + ext)

        os.removedirs('./testShapeFut')
        pass

    def test_currentHarvestProducts(self):
        """Verify that currentHarvestProducts() produces the correct results.
            This is accomplished by a regression test against 
            test_data/currentHWP_regression.tif."""

        #Create a working copy of the existing storage (regression) raster
        storage_orig = gdal.Open('../../test_data/carbon_regression.tif', gdal.GA_ReadOnly)
        driver = gdal.GetDriverByName('MEM')
        storage_mod = driver.CreateCopy('temp.tif', storage_orig, 0)

        #set up arguments
        args = {'lulc_cur' : gdal.Open('../../test_data/lulc_samp_cur', gdal.GA_ReadOnly),
                'storage_cur' : storage_mod,
                'hwp_cur_shape' : ogr.Open('../../test_data/harv_samp_cur/harv_samp_cur.shp'),
                'lulc_cur_year' : 2000}

        #run harvestProducts()
        carbon.harvestProducts(args, ('cur',))

        #verify that the output is corrent
        example = gdal.Open('../../test_data/currentHWP_regression.tif')
        vectorize_dataset_equality(self, example, storage_mod)
        pass

    def test_futureHarvestProducts(self):
        """Verify that futureHarvestProducts() produces the correct results.
            This is accomplished by a regression test against 
            test_data/futureHWP_regression.tif."""

        #Create a working copy of the existing storage (regression) raster
        storage_orig = gdal.Open('../../test_data/carbon_regression.tif', gdal.GA_ReadOnly)
        driver = gdal.GetDriverByName('MEM')
        storage_cur = driver.CreateCopy('temp.tif', storage_orig, 0)
        storage_fut = driver.CreateCopy('temp.tif', storage_orig, 0)

        #set up arguments
        args = {'lulc_cur' : gdal.Open('../../test_data/lulc_samp_cur', gdal.GA_ReadOnly),
                'storage_cur' : storage_cur,
                'storage_fut' : storage_fut,
                'hwp_cur_shape' : ogr.Open('../../test_data/harv_samp_cur/harv_samp_cur.shp'),
                'hwp_fut_shape' : ogr.Open('../../test_data/harv_samp_fut/harv_samp_fut.shp'),
                'lulc_cur_year' : 2000,
                'lulc_fut_year' : 2030}

        #run harvestProducts()
        carbon.harvestProducts(args, ('cur', 'fut'))

        #verify that the output is corrent
        example = gdal.Open('../../test_data/futureHWP_regression.tif')
        vectorize_dataset_equality(self, example, storage_fut)
        pass

    def test_carbon_execute_default_filepaths(self):
        """Verify datasets exist at the appropriate filepaths.
            
            Verify that a user-specified filepath appears in the filesystem,
            and that a datset at the default filepath also appears in the 
            correct place."""

        #set output directory
        output_dir = '../../carbon_output'

        #ensure no file exists at the default storage_cur path
        default_path = output_dir + os.sep + 'tot_C_cur.tif'

        if os.path.exists(default_path):
            os.remove(default_path)

        #set the filepath for storage_cur
        storage_cur = '../../carbon_output/storage_cur.tif'

        args = {'lulc_cur' : '../../test_data/lulc_samp_cur',
                'storage_cur' : storage_cur,
                'carbon_pools' : '../../test_data/carbon_pools_float.dbf',
                'output_dir' : output_dir,
                'lulc_fut' : '../../test_data/lulc_samp_fut',
                'calc_value' : False,
                'calc_uncertainty' : False}

        invest_carbon_core.execute(args)

        #try to open storage_cur file, the URI to which we manually set.
        storage_cur_raster = gdal.Open(storage_cur, gdal.GA_ReadOnly)

        #if the file exists, storage_cur_raster should not be None
        self.assertNotEqual(storage_cur_raster, None)

        #try to open the storage_fut file, the URI to which is set to default
        storage_fut_raster = gdal.Open(output_dir + os.sep + 'tot_C_fut.tif')

        #if the file exists, storage_fut_raster should not be None
        self.assertNotEqual(storage_fut_raster, None)

        #this file should not exist, so default_cur_exists should be False
        default_cur_exists = os.path.exists(default_path)
        self.assertEqual(default_cur_exists, False)

        #delete all datasets created
        for filename in ('storage_cur.tif', 'tot_C_fut.tif', 'sequest.tif'):
            os.remove(output_dir + os.sep + filename)
        invest_test.removeCreatedFiles()

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
