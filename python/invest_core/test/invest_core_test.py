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
import logging
import math
logger = logging.getLogger('invest_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestCore(unittest.TestCase):
    def testflowDirectionSimple(self):
        """Regression test for flow direction on a DEM with an example
        constructed by hand"""

        driver = gdal.GetDriverByName("MEM")

        #Create a 3x3 dem raster
        dem = driver.Create('', 3, 3, 1, gdal.GDT_Float32)
        dem.GetRasterBand(1).SetNoDataValue(-1.0)
        dem.GetRasterBand(1).WriteArray(np.array([[902, 909, 918], [895, 904, 916], [893, 904, 918]]))

        flow = invest_core.newRasterFromBase(dem,
            '', 'MEM', 0, gdal.GDT_Byte)
        invest_core.flowDirection(dem, flow)
        flowMatrix = flow.ReadAsArray(0, 0, 3, 3)
        self.assertEqual(128, flowMatrix[1][1],
                         'Incorrect flow, should be 128 != %s' % flowMatrix[1][1])

        dem.GetRasterBand(1).WriteArray(np.array([[190, 185, 181], [189, 185, 182], [189, 185, 182]]))
        flow = invest_core.newRasterFromBase(dem,
            '', 'MEM', 0, gdal.GDT_Byte)
        flowDir = invest_core.flowDirection(dem, flow)
        flow = flowDir.ReadAsArray(0, 0, 3, 3)
        self.assertEqual(8, flowMatrix[1][1],
                         'Incorrect flow, should be 8 != %s' % flowMatrix[1][1])


    def testflowDirection(self):
        """Regression test for flow direction on a DEM"""
        dem = gdal.Open('../../../sediment_test_data/dem')
        flow = invest_core.newRasterFromBase(dem,
            '../../../test_out/flow.tif', 'GTiff', 0, gdal.GDT_Byte)
        invest_core.flowDirection(dem, flow)

    def testslopeCalculation(self):
        """Regression test for slope calculation"""
        dem = gdal.Open('../../../sediment_test_data/dem')
        slope = invest_core.calculateSlope(dem, uri='../../../test_out/slope.tif')
        regressionSlope = \
            gdal.Open('../../../sediment_test_data/slopeRegression.tif')
        invest_test_core.assertTwoDatasetsEqual(self, slope, regressionSlope)

    def testvectorizeRasters(self):
        r1 = gdal.Open('../../../test_data/lulc_samp_cur')
        r2 = gdal.Open('../../../test_data/precip')

        def op(a, b):
            return np.sqrt(a ** 2 + b ** 2)

        invest_core.vectorizeRasters([r1, r2], op,
            rasterName='../../../test_out/rasterizeRasters.tiff', datatype=gdal.GDT_Float32)

    def testvectorizeRastersWaveEnergy(self):
        r1 = gdal.Open('../../../test_data/wave_Energy/samp_data/input/global_dem')
        r2 = gdal.Open('../../../test_data/wave_Energy/waveHeight.tif')

        def op(a, b):
            return np.sqrt(a ** 2 + b ** 2)

        invest_core.vectorizeRasters([r1, r2], op,
            rasterName='../../../test_out/rasterizeRasters.tiff', datatype=gdal.GDT_Float32)

    def testinterpolateMatrix(self):
        """Test the matrix interpolation function"""

        def assertEqualInterpPoints(x, y, newx, newy, z):
            for xVal in x:
                for yVal in y:
                    i = x.tolist().index(xVal)
                    j = y.tolist().index(yVal)
                    ii = newx.tolist().index(xVal)
                    jj = newy.tolist().index(yVal)
                    self.assertAlmostEquals(z[j][i], interpz[jj][ii], 5,
                                    "z[%s][%s], interpz[%s][%s], %s != %s" %
                                    (i, j, ii, jj, z[j][i], interpz[jj][ii]))

        #Create a non-trivial somewhat random matrix
        x = np.array([-4.2, 3, 6, 10, 11])
        y = np.array([-9, 3, 6, 10])
        z = np.array([[0., 8., 11., 12.5, 0.0],
           [0., 1., 1., 0., 0.],
           [-7.2, 3., 1.2, 0., 0.],
           [0., 4.9, 2.5, 0, 0.]])
        #print z.shape

        #print 'x', x
        #print 'y', y
        #print 'z', z

        newx = np.array([-8.2, -4.2, 0, 2.5, 3, 5, 6, 7.5, 10, 11, 15.2, 100.0])
        newy = np.array([-9, 0, 2.5, 3, 5, 6, 7.5, 10, 22.2, 100.0])

        #print 'newx', newx
        #print 'newy', newy
        logging.debug('calling interpolate matrix')
        interpz = invest_core.interpolateMatrix(x, y, z, newx, newy)
        #print 'interpz:', interpz
        logging.debug('testing the result of interpolate matrix')
        assertEqualInterpPoints(x, y, newx, newy, z)


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
                       gdal.GDT_Float32, -5.0, '../../../test_out/subwatershed.tif', shp)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCore)
    unittest.TextTestRunner(verbosity=2).run(suite)
