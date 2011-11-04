import unittest
from osgeo import gdal
import numpy as np
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

    def checkEqual(a, b):
        """Assert that a == b"""
        unitTest.assertAlmostEqual(a, b)

    assertArrayEqual = np.vectorize(checkEqual)

    for bandNumber in range(1, a.RasterCount + 1):
        bandA = a.GetRasterBand(bandNumber)
        bandB = b.GetRasterBand(bandNumber)

        for i in range(bandA.YSize):
            aArray = bandA.ReadAsArray(0, i, bandA.XSize, 1)
            bArray = bandB.ReadAsArray(0, i, bandB.XSize, 1)
            assertArrayEqual(aArray, bArray)
