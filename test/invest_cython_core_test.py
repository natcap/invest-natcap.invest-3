"""URI level tests for the cython core module"""

import unittest

from osgeo import gdal
from nose.plugins.skip import SkipTest

from invest_natcap.sediment import sediment_biophysical
import invest_cython_core
import invest_test_core


class TestCythonCore(unittest.TestCase):
    """Main testing class for the Cython sediment tests"""
    def test_flow_direction_d8(self):
        """Regression test for flow direction with D8 algorithm on a DEM"""
        raise SkipTest
        dem = gdal.Open('./data/sediment_test_data/dem')
        flow = invest_cython_core.newRasterFromBase(dem,
            './data/test_out/testflowAccumulationD8_flow.tif', 'GTiff', 0,
            gdal.GDT_Float32)
        invest_cython_core.flowDirectionD8(dem, flow)
        regression_flow = \
            gdal.Open('./data/sediment_test_data/flowregression.tif')
        invest_test_core.assertTwoDatasetsEqual(self, flow, regression_flow)

    def test_flow_accumulation_d8(self):
        """Regression test for flow_direction accumulation with D8 algorithm 
            on a DEM"""

        dem = gdal.Open('./data/sediment_test_data/dem')
        flow_direction = invest_cython_core.newRasterFromBase(dem,
            './data/test_out/testflowAccumulationD8_flowDirection.tif',
            'GTiff', 0, gdal.GDT_Byte)
        invest_cython_core.flowDirectionD8(dem, flow_direction)

        accumulation = invest_cython_core.newRasterFromBase(dem,
            './data/test_out/testflowAccumulationD8_accumulation.tif',
            'GTiff', -1, gdal.GDT_Float32)
        invest_cython_core.flowAccumulationD8(flow_direction, accumulation)
