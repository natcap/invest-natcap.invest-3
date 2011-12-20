import os, sys
import random
import logging
import math
import unittest

from osgeo import ogr, gdal, osr
from osgeo.gdalconst import *
from dbfpy import dbf
import numpy as np
from nose.exc import SkipTest

import invest_core
import invest_cython_core
import invest_test_core

logger = logging.getLogger('invest_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestCore(unittest.TestCase):
    def testflowDirection(self):
        raise SkipTest("haven't refactored this test yet")
        """Regression test for flow direction on a DEM"""
        dem = gdal.Open('../../../sediment_test_data/dem')
        flow = invest_cython_core.newRasterFromBase(dem,
            '../../../test_out/flow.tif', 'GTiff', 0, gdal.GDT_Float32)
        invest_cython_core.flowDirectionD8(dem, flow)
        regressionFlow = \
            gdal.Open('../../../sediment_test_data/flowregression.tif')
        invest_test_core.assertTwoDatasetsEqual(self, flow, regressionFlow)

    def testflowAccumulation(self):
        raise SkipTest("haven't refactored this test yet")
        """Regression test for flowDirection accumulation on a DEM"""
        dem = gdal.Open('../../../sediment_test_data/dem')
        flowDirection = invest_cython_core.newRasterFromBase(dem,
            '../../../test_out/flowDirection.tif', 'GTiff', 0, gdal.GDT_Byte)
        invest_cython_core.flowDirectionD8(dem, flowDirection)

        accumulation = invest_cython_core.newRasterFromBase(dem,
            '../../../test_out/accumulation.tif', 'GTiff', -1, gdal.GDT_Float32)
        invest_cython_core.flowAccumulationD8(flowDirection, accumulation)

suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCore)
unittest.TextTestRunner(verbosity=2).run(suite)
