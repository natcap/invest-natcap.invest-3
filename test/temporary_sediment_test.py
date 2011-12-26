import os, sys
import random
import logging
import math
import unittest

import numpy as np
from osgeo import ogr, gdal, osr
from osgeo.gdalconst import *

from invest.invest_core import invest_core
import invest_cython_core
import invest_test_core
from invest.dbfpy import dbf

logger = logging.getLogger('invest_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestCore(unittest.TestCase):
    def testflowDirection(self):
        """Regression test for flow direction on a DEM"""
        dem = gdal.Open('./data/sediment_test_data/dem')
        flow = invest_cython_core.newRasterFromBase(dem,
            './data/test_out/flow.tif', 'GTiff', 0, gdal.GDT_Float32)
        invest_cython_core.flowDirectionD8(dem, flow)
        regressionFlow = \
            gdal.Open('./data/sediment_test_data/flowregression.tif')
        invest_test_core.assertTwoDatasetsEqual(self, flow, regressionFlow)

    def testflowAccumulation(self):
        """Regression test for flowDirection accumulation on a DEM"""
        dem = gdal.Open('./data/sediment_test_data/dem')
        flowDirection = invest_cython_core.newRasterFromBase(dem,
            './data/test_out/flowDirection.tif', 'GTiff', 0, gdal.GDT_Byte)
        invest_cython_core.flowDirectionD8(dem, flowDirection)

        accumulation = invest_cython_core.newRasterFromBase(dem,
            './data/test_out/accumulation.tif', 'GTiff', -1, gdal.GDT_Float32)
        invest_cython_core.flowAccumulationD8(flowDirection, accumulation)

suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCore)
unittest.TextTestRunner(verbosity=2).run(suite)
