"""URI level tests for the carbon biophysical module"""

import os
import sys
import unittest
import logging
import re

from nose.plugins.skip import SkipTest

from invest_natcap.carbon import carbon_biophysical
from invest_natcap.carbon import carbon_valuation
import invest_test_core


class TestCarbonBiophysical(unittest.TestCase):

    def assertDatasetEqual(self, workspace_dir, output_filename, ref_filename=None):
        """Asserts that the output data set equals the reference data set."""
        if not ref_filename:
            ref_filename = output_filename
        output_uri = os.path.join(workspace_dir, 'output', output_filename)
        ref_uri = os.path.join('./invest-data/test/data/carbon_regression_data', ref_filename)
        invest_test_core.assertTwoDatasetEqualURI(self, output_uri, ref_uri)

    def assertDatasetsEqual(self, workspace_dir, *files):
        """Calls assertDatasetEqual() for each file in the list of files."""
        for filename in files:
            if isinstance(filename, str):
                self.assertDatasetEqual(workspace_dir, filename)
            else:
                self.assertDatasetEqual(workspace_dir, *filename)

    def test_carbon_biophysical_sequestration_hwp(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        workspace_dir = './invest-data/test/data/test_out/carbon_output'

        def execute_model(do_sequest=False, do_redd=False, use_uncertainty=False, do_hwp=False,
                          suffix=''):
            """Executes the carbon biophysical model with the appropriate parameters."""
            args = {}
            args['workspace_dir'] = workspace_dir
            args['lulc_cur_uri'] = "./invest-data/test/data/base_data/terrestrial/lulc_samp_cur"

            if use_uncertainty:
                args['use_uncertainty'] = True
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

            carbon_biophysical.execute(args)

        # Make sure nothing breaks when we run the model with the bare minimum.
        execute_model()

        execute_model(do_sequest=True, do_hwp=True)
        self.assertDatasetsEqual(workspace_dir,
                                 'tot_C_cur.tif', 
                                 'tot_C_fut.tif', 
                                 ('sequest_fut.tif', 'sequest.tif'))
        
        execute_model(do_sequest=True, do_hwp=True, use_uncertainty=True)
        self.assertDatasetsEqual(workspace_dir,
                                 'tot_C_cur.tif', 
                                 'tot_C_fut.tif', 
                                 ('sequest_fut.tif', 'sequest.tif'),
                                 ('conf_fut.tif', 'conf.tif'))

        execute_model(do_sequest=True, do_hwp=True, use_uncertainty=True, do_redd=True)
        self.assertDatasetsEqual(workspace_dir,
                                 'tot_C_cur.tif', 
                                 'tot_C_fut.tif', 
                                 ('sequest_base.tif', 'sequest.tif'),
                                 ('conf_base.tif', 'conf.tif'), 
                                 'sequest_redd.tif', 
                                 'conf_redd.tif')

        execute_model(do_sequest=True, do_hwp=True, suffix='_foo_bar')
        self.assertDatasetEqual(workspace_dir,
                                'tot_C_cur_foo_bar.tif', 
                                'tot_C_cur.tif')

    def test_carbon_biophysical_uk(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/carbon_uk_output'
        args['lulc_cur_uri'] = './invest-data/test/data/carbon/uk_data/gb_lulc_2000'
        args['lulc_fut_uri'] = './invest-data/test/data/carbon/uk_data/gb_lulc_2007'
        args['carbon_pools_uri'] = './invest-data/test/data/carbon/uk_data/Carbon_pools_conifers.dbf'
        args['lulc_cur_year'] = 2000
        args['lulc_fut_year'] = 2007
        args['hwp_cur_shape_uri'] = "./invest-data/test/data/carbon/uk_data/GB_Harvest_rates_cur.shp"
        args['hwp_fut_shape_uri'] = "./invest-data/test/data/carbon/uk_data/GB_Harvest_rates_fut.shp"

        carbon_biophysical.execute(args)

    def test_carbon_valuation_regression(self):
        """Regression test for carbon_valuation function.  A few pixels have 
            been tested by hand against the following python snippet:
            
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

        workspace_dir = './invest-data/test/data/test_out/carbon_valuation_output'

        def execute_model(carbon_units='Carbon', do_redd=False, use_uncertainty=False):
            args = {}
            args['workspace_dir'] = workspace_dir
            args['sequest_uri'] = './invest-data/test/data/carbon_regression_data/sequest.tif'
            args['V'] = 43.0
            args['r'] = 7.0
            args['c'] = 0.0
            args['yr_cur'] = 2000
            args['yr_fut'] = 2030
            args['carbon_price_units'] = carbon_units

            if use_uncertainty:
                args['conf_uri'] = (
                    './invest-data/test/data/carbon_regression_data/conf.tif')

            if do_redd:
                args['sequest_redd_uri'] = (
                    './invest-data/test/data/carbon_regression_data/sequest_redd.tif')

            if use_uncertainty and do_redd:
                args['conf_redd_uri'] = (
                    './invest-data/test/data/carbon_regression_data/conf_redd.tif')

            carbon_valuation.execute(args)

        def assertSummaryContainsRow(row_title, first_val, second_val):
            '''Asserts that the HTML summary file contains the given row.'''
            filename = os.path.join(workspace_dir, 'output', 'summary.html')
            summary = open(filename, 'r').read()
            rows = summary.split('<tr>')
            row_title_cell = '<td>%s</td>' % row_title
            for row in rows:
                # Check if this is the row we're looking for.
                if row_title_cell in row:
                    # Split the row into its cells
                    cells = row.split('<td>')
                    
                    # Strip off the '<td>' and '<tr>' artifacts from the strings
                    cells = map(lambda cell: re.sub(r'<[^>]*>', '', cell), cells)

                    # Make sure each cell contains what we expect.
                    self.assertEqual('', cells[0])
                    self.assertEqual(row_title, cells[1])
                    self.assertAlmostEqual(first_val, float(cells[2]), places=1)
                    self.assertAlmostEqual(second_val, float(cells[3]), places=1)
                    return

            # If the right row wasn't found in the summary file, then fail.
            self.fail('Row with title \'%s\' not found in the HTML summary file.' 
                      % row_title)


        execute_model()
        self.assertDatasetEqual(workspace_dir, 'value_seq.tif', 'value_seq_c.tif')

        execute_model(carbon_units='Carbon Dioxide (CO2)')
        self.assertDatasetEqual(workspace_dir, 'value_seq.tif', 'value_seq_c02.tif')            

        execute_model(use_uncertainty=True)
        self.assertDatasetsEqual(workspace_dir, 
                                 ('value_seq.tif', 'value_seq_c.tif'),
                                 'val_mask.tif',
                                 'seq_mask.tif')
        assertSummaryContainsRow('Baseline', -2622682.18139, -49913105.53)
        assertSummaryContainsRow('Baseline (confident cells only)', -4049305.95339, -77063698.76)

        execute_model(use_uncertainty=True, do_redd=True)
        self.assertDatasetsEqual(workspace_dir, 
                                 ('value_seq_base.tif', 'value_seq_c.tif'),
                                 ('val_mask_base.tif', 'val_mask.tif'),
                                 ('seq_mask_base.tif', 'seq_mask.tif'),
                                 'value_seq_redd.tif',
                                 'val_mask_redd.tif',
                                 'seq_mask_redd.tif')
        assertSummaryContainsRow('REDD policy', -848059.364479, -16139728.72)
        assertSummaryContainsRow('REDD policy (confident cells only)',
                                 98348.6095097, 1871704.36)
        assertSummaryContainsRow('REDD policy vs Baseline',
                                 1774622.81692, 33773376.81)

