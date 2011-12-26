"""URI level tests for the carbon biophysical module"""

import os, sys
import unittest

from invest.carbon import carbon_biophysical
import invest_test_core

class TestCarbonBiophysical(unittest.TestCase):
    def test_carbon_biophysical_smoke(self):
        """Smoke test for carbon_biophysical function.  Shouldn't crash with \
#zero length inputs"""

        args = {}
        args['workspace_dir'] = './data/carbon_output'
        args['lulc_cur_uri'] = "./data/base_data/terrestrial/lulc_samp_cur"
        args['carbon_pools_uri'] = './data/carbon/input/carbon_pools_samp.dbf'

        carbon_biophysical.execute(args)

    def test_carbon_biophysical_sequestration(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration on lulc maps."""

        args = {}
        args['workspace_dir'] = './data/carbon_output'
        args['lulc_cur_uri'] = "./data/base_data/terrestrial/lulc_samp_cur"
        args['lulc_fut_uri'] = "./data/base_data/terrestrial/lulc_samp_fut"
        args['carbon_pools_uri'] = './data/carbon/input/carbon_pools_samp.dbf'

        carbon_biophysical.execute(args)

    def test_carbon_biophysical_sequestration_hwp(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = './data/carbon_output'
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
            args['workspace_dir'] + "/Output/tot_C_cur.tif",
            './data/test_data/tot_C_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Output/tot_C_fut.tif",
            './data/test_data/tot_C_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Output/sequest.tif",
            './data/test_data/sequest_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/bio_hwp_cur.tif",
            './data/test_data/bio_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/bio_hwp_fut.tif",
            './data/test_data/bio_hwp_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/c_hwp_cur.tif",
            './data/test_data/c_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/c_hwp_fut.tif",
            './data/test_data/c_hwp_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/vol_hwp_cur.tif",
            './data/test_data/vol_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/vol_hwp_fut.tif",
            './data/test_data/vol_hwp_fut_regression.tif')

suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonBiophysical)
unittest.TextTestRunner(verbosity=2).run(suite)
