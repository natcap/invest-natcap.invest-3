"""URI level tests for the carbon biophysical module"""

import os
import sys
import unittest
import logging
import re

import numpy.random

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

        # Parameters to tweak for the biophysical model.
        self.do_biophysical = False
        self.do_sequest = False
        self.do_redd = False
        self.do_uncertainty = False
        self.do_hwp = False
        self.suffix = ''

        # Parameters to tweak for the valuation model.
        self.do_valuation = False
        self.carbon_units = 'Carbon'

    def execute(self):
        """Executes the carbon model based on the state of instance vars."""
        args = {}
        args['workspace_dir'] = self.workspace_dir
        args['do_biophysical'] = self.do_biophysical
        args['do_valuation'] = self.do_valuation
        args['do_uncertainty'] = self.do_uncertainty

        if self.suffix:
            args['suffix'] = self.suffix

        # Set up biophysical args.
        if self.do_biophysical:
            args['lulc_cur_uri'] = (
                "./invest-data/test/data/base_data/terrestrial/lulc_samp_cur")

            if self.do_uncertainty:
                numpy.random.seed(1) # Make the Monte Carlo simulation predictable.
                args['carbon_pools_uncertain_uri'] = (
                    './invest-data/test/data/carbon/input/'
                    'carbon_pools_samp_uncertain.csv')
                args['confidence_threshold'] = 90
            else:
                args['carbon_pools_uri'] = (
                    './invest-data/test/data/carbon/input/'
                    'carbon_pools_samp.csv')

            if self.do_sequest:
                args['lulc_fut_uri'] = "./invest-data/test/data/base_data/terrestrial/lulc_samp_fut"
                args['lulc_cur_year'] = 2000
                args['lulc_fut_year'] = 2030

            if self.do_redd:
                args['lulc_redd_uri'] = './invest-data/test/data/carbon/input/lulc_samp_redd.tif'

            if self.do_hwp:
                args['hwp_cur_shape_uri'] = "./invest-data/test/data/carbon/input/harv_samp_cur.shp"

            if self.do_sequest and self.do_hwp:
                    args['hwp_fut_shape_uri'] = "./invest-data/test/data/carbon/input/harv_samp_fut.shp"

            if self.do_redd and self.do_hwp:
                raise Exception(
                    "The model doesn't currently support REDD analysis with HWP")

        if self.do_valuation:
            args['V'] = 43.0
            args['r'] = 7.0
            args['c'] = 0.0
            args['carbon_price_units'] = self.carbon_units

            # If we're running the stand-alone valuation model (without biophysical),
            # then add a bunch of extra data, since it won't be threaded from
            # the biophysical model to the valuation model.
            if not self.do_biophysical:
                args['sequest_uri'] = './invest-data/test/data/carbon_regression_data/sequest_base.tif'
                args['yr_cur'] = 2000
                args['yr_fut'] = 2030

                if self.do_uncertainty:
                    args['conf_uri'] = (
                        './invest-data/test/data/carbon_regression_data/conf_base.tif')

                if self.do_redd:
                    args['sequest_redd_uri'] = (
                        './invest-data/test/data/carbon_regression_data/sequest_redd.tif')

                if self.do_uncertainty and self.do_redd:
                    args['conf_redd_uri'] = (
                        './invest-data/test/data/carbon_regression_data/conf_redd.tif')

        carbon_combined.execute(args)

    def check(self):
        """Helper method to check that results are what we expect.

        Doesn't work well together with suffixes.
        """
        if self.suffix:
            raise Exception(
                "This method doesn't work well if suffixes are enabled.")

        if self.do_biophysical:
            self.check_biophysical()

        if self.do_valuation:
            self.check_valuation()

    def check_biophysical(self):
        """Checks that biophysical results are what we expect."""
        self.assert_dataset_equal('tot_C_cur.tif')
        self.assert_table_contains_rows(
            'biophysical_table',
            [['Current', 41401439.7949, 'n/a']])

        if self.do_uncertainty:
            self.assert_dataset_equal('conf_base.tif')

            if not self.do_hwp:
                self.assert_table_contains_rows(
                    'biophysical_uncertainty',
                    [['Current', 41393866.8552, 1952277.85499, 'n/a', 'n/a']])

                if self.do_sequest:
                    if self.do_redd:
                        self.assert_table_contains_rows(
                            'biophysical_uncertainty',
                            [['Baseline', 37873479.3608, 1918933.29091,
                              -3520387.68116, 871671.317364],
                             ['REDD policy', 41494778.9465, 1952644.64532,
                              100912.043313, 14000.0796437]])
                    else:
                        self.assert_table_contains_rows(
                            'biophysical_uncertainty',
                            [['Future', 37873479.3608, 1918933.29091,
                              -3520387.68116, 871671.317364]])


        if self.do_redd:
            self.assert_datasets_equal('tot_C_base.tif',
                                     'tot_C_redd.tif',
                                     'sequest_base.tif',
                                     'sequest_redd.tif')

            self.assert_table_contains_rows(
                'biophysical_table',
                [['Baseline', 37875383.0229, -3526095.89057],
                 ['REDD policy', 41502289.83, 100847.723038]])

            if self.do_uncertainty:
                self.assert_dataset_equal('conf_redd.tif')

    def check_valuation(self):
        """Checks that valuation results are what we expect."""
        if self.do_redd:
            self.assert_datasets_equal('value_seq_base.tif',
                                     'value_seq_redd.tif')

            self.assert_table_contains_rows(
                'change_table',
                [['Baseline', -3526095.89057, -67106273.81],
                 ['REDD policy', 100847.723038, 1919265.76]])

            self.assert_table_contains_rows(
                'comparison_table',
                [['REDD policy vs Baseline', 3626943.61361, 69025539.56]])

            if self.do_uncertainty:
                self.assert_datasets_equal('val_mask_base.tif',
                                         'seq_mask_base.tif',
                                         'val_mask_redd.tif',
                                         'seq_mask_redd.tif')

                self.assert_table_contains_rows(
                    'change_table',
                    [['Baseline (confident cells only)', -3530157.48653, -67183571.67],
                     ['REDD policy (confident cells only)', 100847.723038, 1919265.76]])

                self.assert_table_contains_rows(
                    'comparison_table',
                    [['REDD policy vs Baseline (confident cells only)',
                      3631005.20957, 69102837.43]])

                if self.do_biophysical and not self.do_hwp:
                    self.assert_table_contains_rows(
                        'valuation_uncertainty',
                        [['Baseline', -3520387.68116, 871671.317364,
                          -66997669.6454, 16589066.9578],
                         ['REDD policy', 100912.043313, 14000.0796437,
                          1920490.6827, 266440.175324]])
        else:
            # No REDD analysis.
            self.assert_dataset_equal('value_seq.tif', 'value_seq_base.tif')

            if self.do_uncertainty:
                self.assert_table_contains_rows(
                    'change_table',
                    [['Future', -3526095.89057, -67106273.81],
                     ['Future (confident cells only)', -3530157.48653,
                      -67183571.67]])

                self.assert_datasets_equal(
                    ('value_seq.tif', 'value_seq_base.tif'),
                    ('val_mask.tif', 'val_mask_base.tif'),
                    ('seq_mask.tif', 'seq_mask_base.tif'))


    def assert_dataset_equal(self, output_filename, ref_filename=None):
        """Asserts that the output data set equals the reference data set."""
        if not ref_filename:
            ref_filename = output_filename
        output_uri = os.path.join(self.output_dir, output_filename)
        ref_uri = os.path.join('./invest-data/test/data/carbon_regression_data', ref_filename)
        invest_test_core.assertTwoDatasetEqualURI(self, output_uri, ref_uri)

    def assert_datasets_equal(self, *files):
        """Calls assert_dataset_equal() for each file in the list of files."""
        for filename in files:
            if isinstance(filename, str):
                self.assert_dataset_equal(filename)
            else:
                self.assert_dataset_equal(*filename)

    def assert_table_contains_rows(self, table_id, rows, suffix=''):
        """Assert that the table with the given id contains the given rows."""
        uri = os.path.join(self.output_dir, 'summary%s.html' % suffix)
        html_test_utils.assert_table_contains_rows_uri(self, uri, table_id, rows)

    def test_biophysical(self):
        """Test the basic biophysical model."""
        self.do_biophysical = True
        self.execute()
        self.check()

    def test_biophysical_sequest_hwp(self):
        """Test biophysical with sequestration and HWP."""
        self.do_biophysical = True
        self.do_sequest = True
        self.do_hwp = True
        self.suffix = 'hwp'
        self.execute()
        self.assert_datasets_equal('tot_C_cur_hwp.tif',
                                 'tot_C_fut_hwp.tif',
                                 'sequest_fut_hwp.tif')

    def test_biophysical_sequest_hwp_uncertainty(self):
        """Test biophysical with sequestration, HWP, and uncertainty."""
        self.do_biophysical = True
        self.do_sequest = True
        self.do_hwp = True
        self.do_uncertainty = True
        self.suffix = 'hwp'
        self.execute()
        self.assert_datasets_equal('tot_C_cur_hwp.tif',
                                 'tot_C_fut_hwp.tif',
                                 'sequest_fut_hwp.tif',
                                 'conf_fut_hwp.tif')

    def test_biophysical_redd(self):
        """Test biophysical with REDD analysis (and uncertainty)."""
        self.do_biophysical = True
        self.do_sequest = True
        self.do_uncertainty = True
        self.do_redd = True
        self.execute()
        self.check()


    def test_carbon_biophysical_uk(self):
        """Test carbon_biophysical function for UK data."""

        args = {}
        args['do_biophysical'] = True
        args['do_valuation'] = False
        args['do_uncertainty'] = False
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
        self.do_valuation = True
        self.execute()
        self.check()

    def test_valuation_units(self):
        """Test valuation with different units."""
        self.do_valuation = True
        self.carbon_units = 'Carbon Dioxide (CO2)'
        self.suffix = 'c02'
        self.execute()
        self.assert_dataset_equal('value_seq_c02.tif')

    def test_valuation_uncertainty(self):
        """Test valuation with uncertainty."""
        self.do_valuation = True
        self.do_uncertainty = True
        self.execute()
        self.check()

    def test_valuation_uncertainty_redd(self):
        """Test valuation with REDD and uncertainty."""
        self.do_valuation = True
        self.do_uncertainty = True
        self.do_redd = True
        self.execute()
        self.check()

    def test_carbon_combined(self):
        """Test combined carbon model.

        In this combined model, the output from the biophysical model becomes
        the input to the valuation model.
        """
        self.do_biophysical = True
        self.do_sequest = True
        self.do_redd = True
        self.do_uncertainty = True
        self.do_valuation = True
        self.execute()
        self.check()
