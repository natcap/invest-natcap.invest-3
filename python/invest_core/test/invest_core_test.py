import os, sys
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')
import invest_core
import invest_test_core
import unittest
from osgeo import ogr, gdal, osr
from osgeo.gdalconst import *
from dbfpy import dbf
import numpy as np
import random

class TestInvestCore(unittest.TestCase):
    def testvectorizeRasters(self):
        r1 = gdal.Open('../../../test_data/lulc_samp_cur')
        r2 = gdal.Open('../../../test_data/precip')

        def op(a, b):
            return a + b

        invest_core.vectorizeRasters([r1, r2], op,
            rasterName='rasterizeRasters.tiff', datatype=gdal.GDT_Float32)

    def testinterpolateMatrix(self):
        """Test the matrix interpolation function"""

        #Create a non-trivial somewhat random matrix
        x = np.array([-4.2, 3, 6, 10])
        y = np.array([-9, 3, 6, 10])
        z = np.array([[0., 0., 0., 0],
           [0., 1., 1., 0.],
           [-7.2, 3., 1.2, 0.],
           [0., 4.9, 2.5, 0]])

        newx = np.array([-4.2, 0, 2.5, 3, 5, 6, 7.5, 10, 15.2])
        newy = np.array([-9, 0, 2.5, 3, 5, 6, 7.5, 10, 22.2])

        interpz = invest_core.interpolateMatrix(x, y, z, newx, newy)

        for xVal in x:
            for yVal in y:
                i = x.tolist().index(xVal)
                j = y.tolist().index(yVal)
                ii = newx.tolist().index(xVal)
                jj = newy.tolist().index(yVal)
                self.assertAlmostEquals(z[i][j], interpz[ii][jj], 5,
                                        "%s != %s" % (z[i][j], interpz[ii][jj]))

    def testRasterDiff(self):
        driver = gdal.GetDriverByName("MEM")

        xDim, yDim = 417, 219
        testA, testB = -248.23, 1829.2

        #Create a blank xDim x yDim raster
        datasetA = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetA.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetA.GetRasterBand(1).Fill(testA)

        datasetB = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetB.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetB.GetRasterBand(1).Fill(testB)

        datasetC = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetC.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetC.GetRasterBand(1).Fill(testA - testB)

        datasetOut = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetOut.GetRasterBand(1).SetNoDataValue(-11.0)

        invest_core.rasterDiff(datasetA.GetRasterBand(1),
                               datasetB.GetRasterBand(1),
                               datasetOut.GetRasterBand(1))

        invest_test_core.assertTwoDatasetsEqual(self, datasetOut, datasetC)

    def testRasterAdd(self):
        driver = gdal.GetDriverByName("MEM")

        xDim, yDim = 417, 219
        testA, testB = -248.23, 1829.2

        #Create a blank xDim x yDim raster
        datasetA = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetA.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetA.GetRasterBand(1).Fill(testA)

        datasetB = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetB.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetB.GetRasterBand(1).Fill(testB)

        datasetC = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetC.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetC.GetRasterBand(1).Fill(testA + testB)

        datasetOut = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetOut.GetRasterBand(1).SetNoDataValue(-11.0)

        invest_core.rasterAdd(datasetA.GetRasterBand(1),
                              datasetB.GetRasterBand(1),
                              datasetOut.GetRasterBand(1))

        invest_test_core.assertTwoDatasetsEqual(self, datasetOut, datasetC)


    def test_carbon_pixel_area(self):
        """Verify the correct output of carbon.pixelArea()"""

        dataset = gdal.Open('../../../test_data/carbon_regression.tif',
                            gdal.GA_ReadOnly)
        area = invest_core.pixelArea(dataset)

        #assert the output of pixelArea against the known value 
        #(it's 30x30 meters) so 0.09 Ha
        self.assertEqual(0.09, area)

    def test_createRasterFromVectorExtents(self):
        fsencoding = sys.getfilesystemencoding()
        shp = ogr.Open('../../../sediment_test_data/subwatersheds.shp'.\
                       encode(fsencoding))
        raster = invest_core.createRasterFromVectorExtents(30, 30,
                       gdal.GDT_Float32, -5.0, 'subwatershed.tif', shp)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCore)
    unittest.TextTestRunner(verbosity=2).run(suite)
