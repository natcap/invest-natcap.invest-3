"""Helper functions for doing unit tests like functions to test the equality
    of entire rasters, etc."""

import unittest
import logging
import random

import numpy as np
from osgeo import gdal
from osgeo import ogr

logger = logging.getLogger('invest_core')

def assertTwoDatasetEqualURI(unitTest, aUri, bUri):
    """Tests if datasets a and b are 'almost equal' to each other on a per
        pixel basis
        
        unitTest - an instance of a unittest object
        aUri - a URI to a gdal dataset
        bUri - a URI to a  gdal dataset
        
        returns True if a and b are equal to each other"""

    assertTwoDatasetsEqual(unitTest, gdal.Open(aUri), gdal.Open(bUri))

def assertTwoDatasetsEqual(unitTest, a, b):
    """Tests if datasets a and b are 'almost equal' to each other on a per
        pixel basis
        
        unitTest - an instance of a unittest object
        a - a gdal dataset
        b - a gdal dataset
        
        returns True if a and b are equal to each other"""
    unitTest.assertEqual(a.RasterXSize, b.RasterXSize,
                         "x dimensions are different a="
                         + str(a.RasterXSize) + 
                         ", second = " + str(b.RasterXSize))
    unitTest.assertEqual(a.RasterYSize, b.RasterYSize,
                         "y dimensions are different a="
                         + str(a.RasterYSize) + 
                         ", second = " + str(b.RasterYSize))
    unitTest.assertEqual(a.RasterCount, b.RasterCount,
                         "different number of rasters a="
                         + str(a.RasterCount) + 
                         ", b = " + str(b.RasterCount))

    for bandNumber in range(1, a.RasterCount + 1):
        bandA = a.GetRasterBand(bandNumber)
        bandB = b.GetRasterBand(bandNumber)

        aArray = bandA.ReadAsArray(0, 0, bandA.XSize, bandA.YSize)
        bArray = bandB.ReadAsArray(0, 0, bandB.XSize, bandB.YSize)
        try:
            np.testing.assert_array_almost_equal(aArray, bArray)
        except AssertionError:
            for a, b in zip(aArray[0], bArray[0]):
                unitTest.assertAlmostEqual(a, b, msg=str('%s != %s ... Failed at' +
                    ' row %s')%(a, b, bandNumber))

def assertTwoShapesEqualURI(unitTest, aUri, bUri):
    """Tests if shapes a and b are equal to each other on a
       layer, feature, and field basis
    
       unitTest - an instance of a unittest object
       aUri - a URI to a ogr shapefile
       bUri - a URI to a ogr shapefile
    
       returns True if a and b are equal to each other"""
    
    assertTwoShapesEqual(unitTest, ogr.Open(aUri), ogr.Open(bUri))

def assertTwoShapesEqual(unitTest, shape, shape_regression):
    """Tests if shapes a and b are equal to each other on a
       layer, feature, and field basis
    
       unitTest - an instance of a unittest object
       shape - an ogr shapefile
       shape_regression - an ogr shapefile
    
       returns True if a and b are equal to each other"""
    
    layer_count = shape.GetLayerCount()
    layer_count_regression = shape_regression.GetLayerCount()
    unitTest.assertEqual(layer_count, layer_count_regression,
                     'The shapes DO NOT have the same number of layers')
    for layer_num in range(layer_count):
        layer = shape.GetLayer(layer_num)
        layer.ResetReading()
        layer_regression = shape_regression.GetLayer(layer_num)
        feat_count = layer.GetFeatureCount()
        feat_count_regression = layer_regression.GetFeatureCount()
        unitTest.assertEqual(feat_count, feat_count_regression,
                         'The layers DO NOT have the same number of features')
        feat = layer.GetNextFeature()
        feat_regression = layer_regression.GetNextFeature()
        while feat is not None:
            layer_def = layer.GetLayerDefn()
            layer_def_regression = layer_regression.GetLayerDefn()
            field_count = layer_def.GetFieldCount()
            field_count_regression = layer_def_regression.GetFieldCount()
            unitTest.assertEqual(field_count, field_count_regression,
                             'The shapes DO NOT have the same number of fields')
            for fld_index in range(field_count):
                field = feat.GetField(fld_index)
                field_regression = feat_regression.GetField(fld_index)
                unitTest.assertEqual(field, field_regression,
                                     'The field values DO NOT match')
                field_ref = feat.GetFieldDefnRef(fld_index)
                field_ref_regression = \
                    feat_regression.GetFieldDefnRef(fld_index)
                field_name = field_ref.GetNameRef()
                field_name_regression = field_ref_regression.GetNameRef()
                unitTest.assertEqual(field_name, field_name_regression, 
                                     'The fields DO NOT have the same name')
            feat.Destroy()
            feat_regression.Destroy()
            feat = layer.GetNextFeature()
            feat_regression = layer_regression.GetNextFeature()
    shape.Destroy()
    shape_regression.Destroy()

def makeRandomRaster(cols, rows, uri='test.tif', format='GTiff', min=0, max=1,
                     type='int'):
    """Create a new raster with random int values.
        
        cols - an int, the number of columns in the output raster
        rows - an int, the number of rows in the output raster
        uri - a string for the path to the file
        format - a string representing the GDAL format code such as 
            'GTiff' or 'MEM'.  See http://gdal.org/formats_list.html for a
            complete list of formats.
        min - the minimum value allowed for a given pixel.
        max - the maximum value allowed for a given pixel.
        type - a string. the type of number to be randomized.  Either 'int' or
               'float'.
            
        returns a new dataset with random values."""

    driver = gdal.GetDriverByName(format)
    dataset = driver.Create(uri, cols, rows, 1, gdal.GDT_Float32)
    band = dataset.GetRasterBand(1)

    if type == 'int':
        def get_rand():
            return random.randint(min, max)
    else:
        def get_rand():
            return random.random()*max

    for i in range(0, band.YSize):
        array = band.ReadAsArray(0, i, band.XSize, 1)
        for j in range(0, band.XSize):
            array[0][j] = get_rand()
        dataset.GetRasterBand(1).WriteArray(array, 0, i)

    return dataset


def assertTwoDatasets(unit, firstDS, secondDS, checkEqual, dict=None):
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

        fastCheck = np.vectorize(checkEqual)
        fastCheck(firstArray, secondArray)


def assertThreeDatasets(unit, firstDS, secondDS, thirdDS, checkMask, nodata):
    firstDSBand = firstDS.GetRasterBand(1)
    secondDSBand = secondDS.GetRasterBand(1)
    maskBand = thirdDS.GetRasterBand(1)
    unit.assertEqual(firstDSBand.XSize, maskBand.XSize,
                      "Dimensions differ: first=" + str(firstDSBand.XSize) + 
                       ", second = " + str(maskBand.XSize))
    unit.assertEqual(firstDSBand.YSize, maskBand.YSize,
                      "Dimensions differ: first=" + str(firstDSBand.YSize) + 
                      ", second = " + str(maskBand.YSize))

    for i in range(0, firstDSBand.YSize):
        inputArray = firstDSBand.ReadAsArray(0, i, firstDSBand.XSize, 1)
        outputArray = secondDSBand.ReadAsArray(0, i, firstDSBand.XSize, 1)
        maskArray = maskBand.ReadAsArray(0, i, firstDSBand.XSize, 1)

        fastCheck = np.vectorize(checkMask)
        fastCheck(inputArray, outputArray, maskArray)


def vectorize_dataset_equality_pools(unit, firstDS, secondDS, dict):
    """Assert that the pixel values of secondDS match those of firstDS when
        the input dict is mapped.
        
        unit - the 'self' object from the unittesting framework
        firstDS - an open GDAL raster dataset
        secondDS - an open GDAL raster dataset
        dict - a dictionary mapping values of firstDS to what they should have
            been recorded as in secondDS.
            
        no return value"""

    def checkEqual(a, b):
        """Assert that dict[a] == b"""
        unit.assertAlmostEqual(dict[a], b, 6)

    assertTwoDatasets(unit, firstDS, secondDS, checkEqual, dict)

def vectorize_dataset_equality_mask(unit, firstDS, secondDS, mask):
    """Assert that the pixel values of firstDS have been masked correctly.
        
        unit - the 'self' object from the unittesting framework
        firstDS - an open GDAL raster dataset
        secondDS - an open GDAL raster dataset
        mask - an open GDAL raster dataset

        no return value"""

    nodata = carbon.build_nodata_dict(firstDS, secondDS)

    def checkMask(a, b, c):
        if b == nodata['output']:
            unit.assertEqual(c, 0)
        else:
            unit.assertAlmostEqual(a, b, 6)

    assertThreeDatasets(unit, firstDS, secondDS, mask, checkMask, nodata)



def vectorize_dataset_equality(unit, firstDS, secondDS):
    """Assert that the pixel values of secondDS match those of firstDS.
        
        unit - the 'self' object from the unittesting framework
        firstDS - an open GDAL raster dataset
        secondDS - an open GDAL raster dataset

        no return value"""

    def checkEqual(a, b):
        """Assert that a == b to 6 decimal places"""
        unit.assertAlmostEqual(a, b, 6)

    assertTwoDatasets(unit, firstDS, secondDS, checkEqual)
