"""URI level tests for the carbon biophysical module"""

import os
import sys
import unittest

from invest.sediment import sediment_biophysical
from osgeo import ogr
from osgeo import gdal
from osgeo import osr

from invest.invest_core import invest_core
import invest_cython_core
import invest_test_core
from invest.dbfpy import dbf


class TestSedimentBiophysical(unittest.TestCase):
    def test_sediment_biophysical_regression(self):
        """Test for sediment_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = './data/sediment_biophysical_output'
        baseDir = './data/sediment_test_data'
        args['dem_uri'] = '%s/dem' % baseDir
        args['erosivity_uri'] = '%s/erosivity' % baseDir
        args['erodibility_uri'] = '%s/erodibility.tif' % baseDir
        args['landuse_uri'] = '%s/landuse_90.tif' % baseDir

        #shapefile
        args['watersheds_uri'] = '%s/watersheds.shp' % baseDir
        args['subwatersheds_uri'] = '%s/subwatersheds.shp' % baseDir
        args['reservoir_locations_uri'] = '%s/reservoir_loc.shp' % baseDir
        args['reservoir_properties_uri'] = '%s/reservoir_prop' % baseDir

        #table
        args['biophysical_table_uri'] = '%s/biophysical_table.csv' % baseDir

        #primatives
        args['threshold_flow_accumulation'] = 1000
        args['slope_threshold'] = 70.0

        sediment_biophysical.execute(args)

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


        #Regression tests go here
#        #assert that '../../test_data/tot_C_cur.tif' equals
#        #../../carbon_output/Output/tot_C_cur.tif
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Output/tot_C_cur.tif",
#            '../../test_data/tot_C_cur_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Output/tot_C_fut.tif",
#            '../../test_data/tot_C_fut_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Output/sequest.tif",
#            '../../test_data/sequest_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/bio_hwp_cur.tif",
#            '../../test_data/bio_hwp_cur_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/bio_hwp_fut.tif",
#            '../../test_data/bio_hwp_fut_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/c_hwp_cur.tif",
#            '../../test_data/c_hwp_cur_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/c_hwp_fut.tif",
#            '../../test_data/c_hwp_fut_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/vol_hwp_cur.tif",
#            '../../test_data/vol_hwp_cur_regression.tif')
#
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            args['workspace_dir'] + "/Intermediate/vol_hwp_fut.tif",
#            '../../test_data/vol_hwp_fut_regression.tif')


suite = unittest.TestLoader().loadTestsFromTestCase(TestSedimentBiophysical)
unittest.TextTestRunner(verbosity=2).run(suite)
