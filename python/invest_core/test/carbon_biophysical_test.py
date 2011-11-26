"""URI level tests for the carbon biophysical module"""

import os, sys
import unittest
import invest_test_core

#Add current directory and parent path for import tests
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')

import carbon_biophysical

class TestCarbonBiophysical(unittest.TestCase):
    def test_carbon_biophysical_smoke(self):
        """Smoke test for carbon_biophysical function.  Shouldn't crash with \
#zero length inputs"""

        args = {}
        args['workspace_dir'] = '../../carbon_output'
        args['lulc_cur_uri'] = "../../carbon/input/lulc_samp_cur"
        args['carbon_pools_uri'] = '../../carbon/input/carbon_pools_float.dbf'

        carbon_biophysical.execute(args)

    def test_carbon_biophysical_sequestration(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration on lulc maps."""

        args = {}
        args['workspace_dir'] = '../../carbon_output'
        args['lulc_cur_uri'] = "../../carbon/input/lulc_samp_cur"
        args['lulc_fut_uri'] = "../../carbon/input/lulc_samp_fut"
        args['carbon_pools_uri'] = '../../carbon/input/carbon_pools_float.dbf'

        carbon_biophysical.execute(args)

    def test_carbon_biophysical_sequestration_hwp(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = '../../carbon_output'
        args['lulc_cur_uri'] = "../../carbon/input/lulc_samp_cur"
        args['lulc_fut_uri'] = "../../carbon/input/lulc_samp_fut"
        args['carbon_pools_uri'] = '../../carbon/input/carbon_pools_float.dbf'
        args['lulc_cur_year'] = 2000
        args['lulc_fut_year'] = 2030
        args['hwp_cur_shape_uri'] = "../../carbon/input/harv_samp_cur"
        args['hwp_fut_shape_uri'] = "../../carbon/input/harv_samp_fut"

        carbon_biophysical.execute(args)

        #assert that '../../test_data/tot_C_cur.tif' equals
        #../../carbon_output/Output/tot_C_cur.tif
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Output/tot_C_cur.tif",
            '../../test_data/tot_C_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Output/tot_C_fut.tif",
            '../../test_data/tot_C_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Output/sequest.tif",
            '../../test_data/sequest_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/bio_hwp_cur.tif",
            '../../test_data/bio_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/bio_hwp_fut.tif",
            '../../test_data/bio_hwp_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/c_hwp_cur.tif",
            '../../test_data/c_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/c_hwp_fut.tif",
            '../../test_data/c_hwp_fut_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/vol_hwp_cur.tif",
            '../../test_data/vol_hwp_cur_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/Intermediate/vol_hwp_fut.tif",
            '../../test_data/vol_hwp_fut_regression.tif')

suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonBiophysical)
unittest.TextTestRunner(verbosity=2).run(suite)
