"""URI level tests for the carbon biophysical module"""

import os
import sys
import unittest
import logging
import re

from nose.plugins.skip import SkipTest

from invest_natcap.carbon import carbon_combined
from invest_natcap.carbon import carbon_utils
import invest_test_core
import html_test_utils


class TestCarbonBiophysical(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = './invest-data/test/data/test_out/carbon_output'
        self.output_dir = os.path.join(self.workspace_dir, 'output')

        if os.path.exists(self.output_dir):
            for out_file in os.listdir(self.output_dir):
                uri = os.path.join(self.output_dir, out_file)
                os.remove(uri)

    def assertDatasetEqual(self, output_filename, ref_filename=None):
        """Asserts that the output data set equals the reference data set."""
        if not ref_filename:
            ref_filename = output_filename
        output_uri = os.path.join(self.workspace_dir, 'output', output_filename)
        ref_uri = os.path.join('./invest-data/test/data/carbon_regression_data', ref_filename)
        invest_test_core.assertTwoDatasetEqualURI(self, output_uri, ref_uri)

    def assertDatasetsEqual(self, *files):
        """Calls assertDatasetEqual() for each file in the list of files."""
        for filename in files:
            if isinstance(filename, str):
                self.assertDatasetEqual(filename)
            else:
                self.assertDatasetEqual(*filename)

    def assert_table_contains_rows(self, table_id, rows, suffix=''):
        uri = os.path.join(self.workspace_dir, 'output',
                           'summary%s.html' % suffix)

        html_test_utils.assert_table_contains_rows_uri(self, uri, table_id, rows)

    def test_carbon_biophysical_sequestration(self):
        """Test for carbon_biophysical function with various parameters."""

        def execute_model(do_sequest=False, do_redd=False, do_uncertainty=False, do_hwp=False,
                          suffix=''):
            """Executes the carbon biophysical model with the appropriate parameters."""
            args = {}
            args['workspace_dir'] = self.workspace_dir
            args['lulc_cur_uri'] = "./invest-data/test/data/base_data/terrestrial/lulc_samp_cur"
            args['do_biophysical'] = True
            args['do_valuation'] = False

            if do_uncertainty:
                args['do_uncertainty'] = True
                args['carbon_pools_uncertain_uri'] = (
                    './invest-data/test/data/carbon/input/carbon_pools_samp_uncertain.csv')
                args['confidence_threshold'] = 90
            else:
                args['carbon_pools_uri'] = './invest-data/test/data/carbon/input/carbon_pools_samp.csv'

            if do_sequest:
                args['lulc_fut_uri'] = "./invest-data/test/data/base_data/terrestrial/lulc_samp_fut"
                args['lulc_cur_year'] = 2000
                args['lulc_fut_year'] = 2030

            if do_redd:
                args['lulc_redd_uri'] = './invest-data/test/data/carbon/input/lulc_samp_redd.tif'

            if do_hwp:
                args['hwp_cur_shape_uri'] = "./invest-data/test/data/carbon/input/harv_samp_cur.shp"

                if do_sequest:
                    args['hwp_fut_shape_uri'] = "./invest-data/test/data/carbon/input/harv_samp_fut.shp"

            if suffix:
                args['suffix'] = suffix

            if do_redd and do_hwp:
                self.fail('The model doesn\'t currently support REDD analysis with HWP!')

            carbon_combined.execute(args)

        # Make sure nothing breaks when we run the model with the bare minimum.
        execute_model()

        execute_model(do_sequest=True, do_hwp=True, suffix='hwp')
        self.assertDatasetsEqual('tot_C_cur_hwp.tif',
                                 'tot_C_fut_hwp.tif',
                                 'sequest_fut_hwp.tif')

        execute_model(do_sequest=True, do_hwp=True, do_uncertainty=True, suffix='hwp')
        self.assertDatasetsEqual('tot_C_cur_hwp.tif',
                                 'tot_C_fut_hwp.tif',
                                 'sequest_fut_hwp.tif',
                                 'conf_fut_hwp.tif')

        execute_model(do_sequest=True, do_uncertainty=True, do_redd=True)
        self.assertDatasetsEqual('tot_C_cur.tif',
                                'tot_C_base.tif',
                                'tot_C_redd.tif',
                                'sequest_base.tif',
                                'conf_base.tif',
                                'sequest_redd.tif',
                                'conf_redd.tif')

        self.assert_table_contains_rows(
            'biophysical_table',
            [['Current', 41401439.7949, 'n/a'],
             ['Baseline', 37875383.0229, -3526095.89057],
             ['REDD policy', 41502289.835, 100847.723038]])

        execute_model(do_sequest=True, do_hwp=True, suffix='_foo_bar')
        self.assertDatasetEqual('tot_C_cur_foo_bar.tif',
                                'tot_C_cur_hwp.tif')

    def test_carbon_biophysical_uk(self):
        """Test carbon_biophysical function for UK data."""

        args = {}
        args['do_biophysical'] = True
        args['do_valuation'] = False
        args['workspace_dir'] = self.workspace_dir
        args['lulc_cur_uri'] = './invest-data/test/data/carbon/uk_data/gb_lulc_2000'
        args['lulc_fut_uri'] = './invest-data/test/data/carbon/uk_data/gb_lulc_2007'
        args['carbon_pools_uri'] = './invest-data/test/data/carbon/uk_data/Carbon_pools_conifers.dbf'
        args['lulc_cur_year'] = 2000
        args['lulc_fut_year'] = 2007
        args['hwp_cur_shape_uri'] = "./invest-data/test/data/carbon/uk_data/GB_Harvest_rates_cur.shp"
        args['hwp_fut_shape_uri'] = "./invest-data/test/data/carbon/uk_data/GB_Harvest_rates_fut.shp"

        carbon_combined.execute(args)

    def test_carbon_valuation(self):
        """Regression test for carbon valuation.

        A few pixels have been tested by hand against the
        following python snippet:

        >>> def f(V,sequest,yr_fut,yr_cur,r,c):
        ...     sum = 0
        ...     for t in range(yr_fut-yr_cur):
        ...             sum += 1/((1+(r/100.0))**t*(1+c/100.0)**t)
        ...     return sum*V*sequest/(yr_fut-yr_cur)
        ...
        >>> V=43.0
        >>> yr_cur=2000
        >>> yr_fut=2030
        >>> sequest=1.0
        >>> sequest=-57.8494
        >>> f(V,sequest,yr_fut,yr_cur,r,c)
        -1100.9511853253725
            """

        def execute_model(carbon_units='Carbon',
                          do_redd=False,
                          do_uncertainty=False,
                          suffix=''):
            args = {}
            args['do_biophysical'] = False
            args['do_valuation'] = True
            args['workspace_dir'] = self.workspace_dir
            args['sequest_uri'] = './invest-data/test/data/carbon_regression_data/sequest_base.tif'
            args['V'] = 43.0
            args['r'] = 7.0
            args['c'] = 0.0
            args['yr_cur'] = 2000
            args['yr_fut'] = 2030
            args['carbon_price_units'] = carbon_units
            if suffix:
                args['suffix'] = suffix

            if do_uncertainty:
                args['conf_uri'] = (
                    './invest-data/test/data/carbon_regression_data/conf_base.tif')

            if do_redd:
                args['sequest_redd_uri'] = (
                    './invest-data/test/data/carbon_regression_data/sequest_redd.tif')

            if do_uncertainty and do_redd:
                args['conf_redd_uri'] = (
                    './invest-data/test/data/carbon_regression_data/conf_redd.tif')

            carbon_combined.execute(args)

        execute_model()
        self.assertDatasetEqual('value_seq.tif', 'value_seq_base.tif')

        execute_model(carbon_units='Carbon Dioxide (CO2)', suffix='c02')
        self.assertDatasetEqual('value_seq_c02.tif')

        execute_model(do_uncertainty=True)
        self.assertDatasetsEqual(('value_seq.tif', 'value_seq_base.tif'),
                                 ('val_mask.tif', 'val_mask_base.tif'),
                                 ('seq_mask.tif', 'seq_mask_base.tif'))

        self.assert_table_contains_rows('change_table',
            [['Future', -3526095.89057, -67106273.81],
             ['Future (confident cells only)', -3530157.48653, -67183571.67]])

        execute_model(do_uncertainty=True, do_redd=True)
        self.assertDatasetsEqual('value_seq_base.tif',
                                 'val_mask_base.tif',
                                 'seq_mask_base.tif',
                                 'value_seq_redd.tif',
                                 'val_mask_redd.tif',
                                 'seq_mask_redd.tif')

        self.assert_table_contains_rows('change_table',
            [['Baseline', -3526095.89057, -67106273.81],
             ['Baseline (confident cells only)', -3530157.48653, -67183571.67],
             ['REDD policy', 100847.723038, 1919265.76],
             ['REDD policy (confident cells only)', 100847.723038, 1919265.76]])

        self.assert_table_contains_rows('comparison_table',
            [['REDD policy vs Baseline', 3626943.61361, 69025539.56],
             ['REDD policy vs Baseline (confident cells only)',
              3631005.20957, 69102837.43]])

    def test_carbon_combined(self):
        """Test combined carbon model, feeding biophysical into valuation."""
        args = {}
        args['workspace_dir'] = self.workspace_dir
        args['lulc_cur_uri'] = "./invest-data/test/data/base_data/terrestrial/lulc_samp_cur"
        args['do_biophysical'] = True
        args['do_valuation'] = True
        args['do_uncertainty'] = True
        args['carbon_pools_uncertain_uri'] = (
            './invest-data/test/data/carbon/input/carbon_pools_samp_uncertain.csv')
        args['confidence_threshold'] = 90
        args['carbon_pools_uri'] = './invest-data/test/data/carbon/input/carbon_pools_samp.csv'
        args['lulc_fut_uri'] = "./invest-data/test/data/base_data/terrestrial/lulc_samp_fut"
        args['lulc_cur_year'] = 2000
        args['lulc_fut_year'] = 2030
        args['lulc_redd_uri'] = './invest-data/test/data/carbon/input/lulc_samp_redd.tif'
        args['V'] = 43.0
        args['r'] = 7.0
        args['c'] = 0.0
        args['yr_cur'] = 2000
        args['yr_fut'] = 2030
        args['carbon_price_units'] = 'Carbon'
        carbon_combined.execute(args)

        self.assertDatasetsEqual('value_seq_base.tif',
                                 'val_mask_base.tif',
                                 'seq_mask_base.tif',
                                 'value_seq_redd.tif',
                                 'val_mask_redd.tif',
                                 'seq_mask_redd.tif')

        self.assert_table_contains_rows(
            'biophysical_table',
            [['Current', 41401439.7949, 'n/a'],
             ['Baseline', 37875383.0229, -3526095.89057],
             ['REDD policy', 41502289.835, 100847.723038]])

        self.assert_table_contains_rows(
            'change_table',
            [['Baseline', -3526095.89057, -67106273.81],
             ['Baseline (confident cells only)', -3530157.48653, -67183571.67],
             ['REDD policy', 100847.723038, 1919265.76],
             ['REDD policy (confident cells only)', 100847.723038, 1919265.76]])

        self.assert_table_contains_rows(
            'comparison_table',
            [['REDD policy vs Baseline', 3626943.61361, 69025539.56],
             ['REDD policy vs Baseline (confident cells only)',
              3631005.20957, 69102837.43]])
