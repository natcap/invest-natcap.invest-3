"""URI level tests for the carbon biophysical module"""

import os
import sys
import unittest
import logging

from nose.plugins.skip import SkipTest

from invest_natcap.carbon import carbon_biophysical
from invest_natcap.carbon import carbon_valuation
import invest_test_core

class TestCarbonBiophysical(unittest.TestCase):
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

        def assertDatasetEqual(output_filename, ref_filename=None):
            """Asserts that the output data set equals the reference data set."""
            if not ref_filename:
                ref_filename = output_filename
            output_uri = os.path.join(workspace_dir, 'output', output_filename)
            ref_uri = os.path.join('./invest-data/test/data/carbon_regression_data', ref_filename)
            invest_test_core.assertTwoDatasetEqualURI(self, output_uri, ref_uri)

        def assertDatasetsEqual(*files):
            """Calls assertDatasetEqual for each file in the list of files."""
            for filename in files:
                if isinstance(filename, str):
                    assertDatasetEqual(filename)
                else:
                    assertDatasetEqual(*filename)

        
        # Make sure nothing breaks when we run the model with the bare minimum.
        execute_model()

        execute_model(do_sequest=True, do_hwp=True)
        assertDatasetsEqual('tot_C_cur.tif', 
                            'tot_C_fut.tif', 
                            ('sequest_fut.tif', 'sequest.tif'))
        
        execute_model(do_sequest=True, do_hwp=True, use_uncertainty=True)
        assertDatasetsEqual('tot_C_cur.tif', 
                            'tot_C_fut.tif', 
                            ('sequest_fut.tif', 'sequest.tif'),
                            ('conf_fut.tif', 'conf.tif'))

        execute_model(do_sequest=True, do_hwp=True, use_uncertainty=True, do_redd=True)
        assertDatasetsEqual('tot_C_cur.tif', 
                            'tot_C_fut.tif', 
                            ('sequest_fut.tif', 'sequest.tif'),
                            ('conf_fut.tif', 'conf.tif'), 
                            'sequest_redd.tif', 
                            'conf_redd.tif')

        execute_model(do_sequest=True, do_hwp=True, suffix='_foo_bar')
        assertDatasetEqual('tot_C_cur_foo_bar.tif', 
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

        args = {}
        args['workspace_dir'] = './invest-data/test/data/test_out/carbon_valuation_output'
        args['sequest_uri'] = './invest-data/test/data/carbon_regression_data/sequest.tif'
        args['V'] = 43.0
        args['r'] = 7.0
        args['c'] = 0.0
        args['yr_cur'] = 2000
        args['yr_fut'] = 2030
        args['carbon_price_units'] = 'Carbon'
        carbon_valuation.execute(args)

        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(
            self,
            os.path.join(args['workspace_dir'], 'output', "value_seq.tif"),
            os.path.join('./invest-data/test/data/carbon_regression_data/value_seq_c.tif'))

        args['carbon_price_units'] = 'Carbon Dioxide (CO2)'
        carbon_valuation.execute(args)

        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(
            self,
            os.path.join(args['workspace_dir'], 'output', "value_seq.tif"),
            os.path.join('./invest-data/test/data/carbon_regression_data/value_seq_c02.tif'))
