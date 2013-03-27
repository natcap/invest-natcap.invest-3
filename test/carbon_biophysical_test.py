"""URI level tests for the carbon biophysical module"""

import os, sys
import unittest

from nose.plugins.skip import SkipTest

from invest_natcap.carbon import carbon_biophysical
import invest_test_core

class TestCarbonBiophysical(unittest.TestCase):
    def test_carbon_biophysical_sequestration_hwp(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = './data/test_out/carbon_output'
        args['lulc_cur_uri'] = "./data/base_data/terrestrial/lulc_samp_cur"
        args['lulc_fut_uri'] = "./data/base_data/terrestrial/lulc_samp_fut"
        args['carbon_pools_uri'] = './data/carbon/input/carbon_pools_samp.dbf'
        args['lulc_cur_year'] = 2000
        args['lulc_fut_year'] = 2030
        args['hwp_cur_shape_uri'] = "./data/carbon/input/harv_samp_cur.shp"
        args['hwp_fut_shape_uri'] = "./data/carbon/input/harv_samp_fut.shp"

        carbon_biophysical.execute(args)

        #assert that './data/test_data/tot_C_cur.tif' equals
        #./data/carbon_output/Output/tot_C_cur.tif
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/output/tot_C_cur.tif",
            './data/carbon_regression_data/tot_C_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/output/tot_C_fut.tif",
            './data/carbon_regression_data/tot_C_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/output/sequest.tif",
            './data/carbon_regression_data/sequest_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/intermediate/bio_hwp_cur.tif",
            './data/carbon_regression_data/bio_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/intermediate/bio_hwp_fut.tif",
            './data/carbon_regression_data/bio_hwp_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/intermediate/c_hwp_cur.tif",
            './data/carbon_regression_data/c_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/intermediate/c_hwp_fut.tif",
            './data/carbon_regression_data/c_hwp_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/intermediate/vol_hwp_cur.tif",
            './data/carbon_regression_data/vol_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/intermediate/vol_hwp_fut.tif",
            './data/carbon_regression_data/vol_hwp_fut_regression.tif')


    def test_carbon_biophysical_sequestration_hwp_different_lulcs(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""
        raise SkipTest
        args = {}
        args['workspace_dir'] = './data/test_out/carbon_uk_output'
        args['lulc_cur_uri'] = './data/carbon/uk_data/gb_lulc_2000'
        args['lulc_fut_uri'] = './data/carbon/uk_data/gb_lulc_2007'
        args['carbon_pools_uri'] = './data/carbon/uk_data/Carbon_pools_conifers.dbf'
        args['lulc_cur_year'] = 2000
        args['lulc_fut_year'] = 2007
        args['hwp_cur_shape_uri'] = "./data/carbon/uk_data/GB_Harvest_rates_cur.shp"
        args['hwp_fut_shape_uri'] = "./data/carbon/uk_data/GB_Harvest_rates_fut.shp"

        carbon_biophysical.execute(args)
