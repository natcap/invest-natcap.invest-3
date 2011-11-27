import os, sys
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')
os.chdir(cmd_folder)
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

suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCore)
unittest.TextTestRunner(verbosity=2).run(suite)
