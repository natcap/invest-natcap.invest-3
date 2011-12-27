"""URI level tests for the carbon biophysical module"""

import unittest

from osgeo import gdal
from nose.plugins.skip import SkipTest

from invest_natcap.sediment import sediment_biophysical
import invest_cython_core
import invest_test_core


class TestSedimentBiophysical(unittest.TestCase):
    """Main testing class for the biophysical sediment tests"""
    def test_sediment_biophysical_re(self):
        """Test for sediment_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = './data/sediment_biophysical_output'
        base_dir = './data/sediment_test_data'
        args['dem_uri'] = '%s/dem' % base_dir
        args['erosivity_uri'] = '%s/erosivity' % base_dir
        args['erodibility_uri'] = '%s/erodibility.tif' % base_dir
        args['landuse_uri'] = '%s/landuse_90.tif' % base_dir

        #shapefile
        args['watersheds_uri'] = '%s/watersheds.shp' % base_dir
        args['subwatersheds_uri'] = '%s/subwatersheds.shp' % base_dir
        args['reservoir_locations_uri'] = '%s/reservoir_loc.shp' % base_dir
        args['reservoir_properties_uri'] = '%s/reservoir_prop' % base_dir

        #table
        args['biophysical_table_uri'] = '%s/biophysical_table.csv' % base_dir

        #primatives
        args['threshold_flow_accumulation'] = 1000
        args['slope_threshold'] = 70.0

        sediment_biophysical.execute(args)

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
