"""URI level tests for the carbon biophysical module"""

import os
import sys
import unittest

from nose.plugins.skip import SkipTest

from invest_natcap.carbon import carbon_biophysical
from invest_natcap.carbon import carbon_valuation
import invest_test_core

class TestCarbonBiophysical(unittest.TestCase):
    def test_carbon_biophysical_sequestration_hwp(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

        args = {}
        args['workspace_dir'] = './data/test_out/carbon_output'
        args['lulc_cur_uri'] = "./data/base_data/terrestrial/lulc_samp_cur"
        args['carbon_pools_uri'] = './data/carbon/input/carbon_pools_samp.dbf'
        carbon_biophysical.execute(args)



        args['lulc_fut_uri'] = "./data/base_data/terrestrial/lulc_samp_fut"
        args['lulc_cur_year'] = 2000
        args['lulc_fut_year'] = 2030
        args['hwp_cur_shape_uri'] = "./data/carbon/input/harv_samp_cur.shp"
        args['hwp_fut_shape_uri'] = "./data/carbon/input/harv_samp_fut.shp"

        carbon_biophysical.execute(args)

        #assert that './data/test_data/tot_C_cur.tif' equals
        #./data/carbon_output/Output/tot_C_cur.tif
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/output/tot_C_cur.tif",
            './data/carbon_regression_data/tot_C_cur.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/output/tot_C_fut.tif",
            './data/carbon_regression_data/tot_C_fut.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + "/output/sequest.tif",
            './data/carbon_regression_data/sequest.tif')

    def test_carbon_biophysical_uk(self):
        """Test for carbon_biophysical function running with sample input to \
do sequestration and harvested wood products on lulc maps."""

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
        args['workspace_dir'] = './data/test_out/carbon_valuation_output'
        args['sequest_uri'] = './data/carbon_regression_data/sequest.tif'
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
            os.path.join('./data/carbon_regression_data/value_seq_c.tif'))

        args['carbon_price_units'] = 'Carbon Dioxide (CO2)'
        carbon_valuation.execute(args)

        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(
            self,
            os.path.join(args['workspace_dir'], 'output', "value_seq.tif"),
            os.path.join('./data/carbon_regression_data/value_seq_c02.tif'))
