"""URI level tests for the biodiversity biophysical module"""

import os
import sys
import shutil

from osgeo import gdal
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.biodiversity import biodiversity_biophysical
import invest_test_core

class TestBiodiversityBiophysical(unittest.TestCase):
    def test_biodiversity_biophysical_sample_regression(self):
        """A regression test for the biodiversity model with all 
            possible inputs"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/all_inputs/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/'
        output_dir = os.path.join(out_dir, 'output')

        reg_rarity_c = os.path.join(regression_dir, 'rarity_c.tif')
        reg_rarity_f = os.path.join(regression_dir, 'rarity_f.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c.tif')
        reg_quality_f = os.path.join(regression_dir, 'quality_out_f.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c.tif')
        reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f.tif')

        rarity_c = os.path.join(output_dir, 'rarity_c.tif')
        rarity_f = os.path.join(output_dir, 'rarity_f.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c.tif')
        quality_f = os.path.join(output_dir, 'quality_out_f.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c.tif')
        deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f.tif')

        invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_f, quality_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_c, deg_sum_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_sample_regression_suffix(self):
        """A regression test for the biodiversity model with all 
            possible inputs and suffix"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/suffix/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        args['suffix'] = 'test'

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/suffix/'
        output_dir = os.path.join(out_dir, 'output')

        reg_rarity_c = os.path.join(regression_dir, 'rarity_c_test.tif')
        reg_rarity_f = os.path.join(regression_dir, 'rarity_f_test.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c_test.tif')
        reg_quality_f = os.path.join(regression_dir, 'quality_out_f_test.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c_test.tif')
        reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f_test.tif')

        rarity_c = os.path.join(output_dir, 'rarity_c_test.tif')
        rarity_f = os.path.join(output_dir, 'rarity_f_test.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c_test.tif')
        quality_f = os.path.join(output_dir, 'quality_out_f_test.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c_test.tif')
        deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f_test.tif')

        invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_f, quality_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_c, deg_sum_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_sample_regression_no_options(self):
        """A regression test for the biodiversity model with only the 
            required inputs"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/no_options/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        #args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        #args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        #args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/no_access/'
        output_dir = os.path.join(out_dir, 'output')

        #reg_rarity_c = os.path.join(regression_dir, 'rarity_c.tif')
        #reg_rarity_f = os.path.join(regression_dir, 'rarity_f.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c.tif')
        #reg_quality_f = os.path.join(regression_dir, 'quality_out_f.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c.tif')
        #reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f.tif')

        #rarity_c = os.path.join(output_dir, 'rarity_c.tif')
        #rarity_f = os.path.join(output_dir, 'rarity_f.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c.tif')
        #quality_f = os.path.join(output_dir, 'quality_out_f.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c.tif')
        #deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f.tif')

        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        #invest_test_core.assertTwoDatasetEqualURI(
        #   self, reg_quality_f, quality_f)
        #invest_test_core.assertTwoDatasetEqualURI(
        #        self, reg_deg_sum_c, deg_sum_c)
        #invest_test_core.assertTwoDatasetEqualURI(
            #self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_sample_regression_with_access(self):
        """A regression test for the biodiversity model with only the 
            optional access input"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/access/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        #args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        #args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/'
        output_dir = os.path.join(out_dir, 'output')

        #reg_rarity_c = os.path.join(regression_dir, 'rarity_c.tif')
        #reg_rarity_f = os.path.join(regression_dir, 'rarity_f.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c.tif')
        #reg_quality_f = os.path.join(regression_dir, 'quality_out_f.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c.tif')
        #reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f.tif')

        #rarity_c = os.path.join(output_dir, 'rarity_c.tif')
        #rarity_f = os.path.join(output_dir, 'rarity_f.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c.tif')
        #quality_f = os.path.join(output_dir, 'quality_out_f.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c.tif')
        #deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f.tif')

        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        #invest_test_core.assertTwoDatasetEqualURI(
        #   self, reg_quality_f, quality_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_c, deg_sum_c)
        #invest_test_core.assertTwoDatasetEqualURI(
        #   self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_sample_regression_base(self):
        """A regression test for the biodiversity model with both
            current and base landcovers. No access or future lancover"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/cur_bse/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        #args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        #args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/no_access'
        output_dir = os.path.join(out_dir, 'output')

        reg_rarity_c = os.path.join(regression_dir, 'rarity_c.tif')
        #reg_rarity_f = os.path.join(regression_dir, 'rarity_f.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c.tif')
        #reg_quality_f = os.path.join(regression_dir, 'quality_out_f.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c.tif')
        #reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f.tif')

        rarity_c = os.path.join(output_dir, 'rarity_c.tif')
        #rarity_f = os.path.join(output_dir, 'rarity_f.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c.tif')
        #quality_f = os.path.join(output_dir, 'quality_out_f.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c.tif')
        #deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f.tif')

        invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        #invest_test_core.assertTwoDatasetEqualURI(
        #        self, reg_quality_f, quality_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_c, deg_sum_c)
        #invest_test_core.assertTwoDatasetEqualURI(
        #        self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_sample_regression_future(self):
        """A regression test for the biodiversity model with both
            current and future landcovers. No access or base lancover"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/cur_fut/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        #args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        #args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/no_access'
        output_dir = os.path.join(out_dir, 'output')

        #reg_rarity_c = os.path.join(regression_dir, 'rarity_c.tif')
        #reg_rarity_f = os.path.join(regression_dir, 'rarity_f.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c.tif')
        reg_quality_f = os.path.join(regression_dir, 'quality_out_f.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c.tif')
        reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f.tif')

        #rarity_c = os.path.join(output_dir, 'rarity_c.tif')
        #rarity_f = os.path.join(output_dir, 'rarity_f.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c.tif')
        quality_f = os.path.join(output_dir, 'quality_out_f.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c.tif')
        deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f.tif')

        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_f, quality_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_c, deg_sum_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_sample_regression_fut_access(self):
        """A regression test for the biodiversity model with both
            current and future landcovers as well as access. No base lancover"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/fut_access/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        #args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/'
        output_dir = os.path.join(out_dir, 'output')

        #reg_rarity_c = os.path.join(regression_dir, 'rarity_c.tif')
        #reg_rarity_f = os.path.join(regression_dir, 'rarity_f.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c.tif')
        reg_quality_f = os.path.join(regression_dir, 'quality_out_f.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c.tif')
        reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f.tif')

        #rarity_c = os.path.join(output_dir, 'rarity_c.tif')
        #rarity_f = os.path.join(output_dir, 'rarity_f.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c.tif')
        quality_f = os.path.join(output_dir, 'quality_out_f.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c.tif')
        deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f.tif')

        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_f, quality_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_c, deg_sum_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_sample_regression_fut_bse(self):
        """A regression test for the biodiversity model with both
            current, future, and base landcovers. No access"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/fut_bse/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        #args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/no_access'
        output_dir = os.path.join(out_dir, 'output')

        reg_rarity_c = os.path.join(regression_dir, 'rarity_c.tif')
        reg_rarity_f = os.path.join(regression_dir, 'rarity_f.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c.tif')
        reg_quality_f = os.path.join(regression_dir, 'quality_out_f.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c.tif')
        reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f.tif')

        rarity_c = os.path.join(output_dir, 'rarity_c.tif')
        rarity_f = os.path.join(output_dir, 'rarity_f.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c.tif')
        quality_f = os.path.join(output_dir, 'quality_out_f.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c.tif')
        deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f.tif')

        invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_f, quality_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_c, deg_sum_c)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_sample_regression_bse_access(self):
        """A regression test for the biodiversity model with both
            current and base landcovers as well as access. No future lancover"""
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/bse_access/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        #args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)
    
        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/'
        output_dir = os.path.join(out_dir, 'output')

        reg_rarity_c = os.path.join(regression_dir, 'rarity_c.tif')
        #reg_rarity_f = os.path.join(regression_dir, 'rarity_f.tif')
        reg_quality_c = os.path.join(regression_dir, 'quality_out_c.tif')
        #reg_quality_f = os.path.join(regression_dir, 'quality_out_f.tif')
        reg_deg_sum_c = os.path.join(regression_dir, 'deg_sum_out_c.tif')
        #reg_deg_sum_f = os.path.join(regression_dir, 'deg_sum_out_f.tif')

        rarity_c = os.path.join(output_dir, 'rarity_c.tif')
        #rarity_f = os.path.join(output_dir, 'rarity_f.tif')
        quality_c = os.path.join(output_dir, 'quality_out_c.tif')
        #quality_f = os.path.join(output_dir, 'quality_out_f.tif')
        deg_sum_c = os.path.join(output_dir, 'deg_sum_out_c.tif')
        #deg_sum_f = os.path.join(output_dir, 'deg_sum_out_f.tif')

        invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_c, rarity_c)
        #invest_test_core.assertTwoDatasetEqualURI(self, reg_rarity_f, rarity_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_quality_c, quality_c)
        #invest_test_core.assertTwoDatasetEqualURI(
        #        self, reg_quality_f, quality_f)
        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_deg_sum_c, deg_sum_c)
        #invest_test_core.assertTwoDatasetEqualURI(
        #        self, reg_deg_sum_f, deg_sum_f)
    
    def test_biodiversity_biophysical_default_smoke(self):
        """Smoke test for biodiversity_biophysical function.  
            Shouldn't crash with zero length inputs"""
        
        #raise SkipTest
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input'
        out_dir = './invest-data/test/data/test_out/biodiversity/samp_workspace/smoke/'
      
        # copy the workspace to test_out so that it can be properly managed on
        # everyones machine without polluting their test/data/ directory
        shutil.copytree(input_dir, out_dir)
        
        args = {}
        args['workspace_dir'] = out_dir
        args['landuse_cur_uri'] = os.path.join(input_dir, 'lc_samp_cur_b.tif')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(
                input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        # using 1 because we get more interesting results. Using a higher number
        # makes the quality_out raster have numbers that just bump to 1
        args['half_saturation_constant'] = 1 
        #args['suffix'] = ''

        biodiversity_biophysical.execute(args)

    def test_biodiversity_biophysical_open_amb(self):
        """Test multiple uri types for open_ambiguous_raster and assert that
            the proper behavior is seen"""
        #raise SkipTest
        reg_dir = './invest-data/test/data/biodiversity_regression_data/'
        uri_1 = os.path.join(reg_dir, 'empty_dir')
        uri_2 = os.path.join(reg_dir, 'test_dir')
        uri_3 = os.path.join(reg_dir, 'test_open_amb')
        uri_4 = os.path.join(reg_dir, 'test_empty_open_amb')
        uri_5 = os.path.join(reg_dir, 'test_none_open_amb')
        
        uri_list = [uri_1, uri_2, uri_3, uri_4, uri_5]
        uri_results = [None, 1, 1, None, None]
        for uri, res in zip(uri_list, uri_results):
            ds = biodiversity_biophysical.open_ambiguous_raster(uri)
            if not ds is None:
                self.assertEqual(res, 1)
            else:
                self.assertEqual(res, ds)

    def test_biodiversity_biophysical_make_dict_from_csv(self):
        """Test a few hand made CSV files to make sure make_dict_from_csv
            returns properly """
        #raise SkipTest
        reg_dir = './invest-data/test/data/biodiversity_regression_data/'
        csv_uri = os.path.join(reg_dir, 'test_csv.csv')
        field = 'LULC'

        result_dict = {'0':{'LULC':'0','DESC':'farm','RARITY':'0.4'},
                       '3':{'LULC':'3','DESC':'water','RARITY':'1.0'},
                       '23':{'LULC':'23','DESC':'swamp','RARITY':'0.2'}}
        created_dict = \
            biodiversity_biophysical.make_dictionary_from_csv(csv_uri, field)

        self.assertEqual(result_dict, created_dict)
        
    def test_biodiversity_biophysical_check_projections(self):
        """Test a list of gdal datasets and assert that we see success and
            failures where we would expect """
        #raise SkipTest
        reg_dir = './invest-data/test/data/biodiversity_regression_data/samp_input/'
        ds_1 = gdal.Open(os.path.join(reg_dir, 'lc_samp_bse_b.tif'))
        ds_2 = gdal.Open(os.path.join(reg_dir, 'lc_samp_cur_b.tif'))
        ds_3 = gdal.Open(os.path.join(reg_dir, 'lc_samp_fut_b.tif'))

        ds_dict = {'_c':ds_2, '_b':ds_1, '_f':ds_3}

        result = biodiversity_biophysical.check_projections(ds_dict, 1.0)
        
        self.assertTrue(result)

    def test_biodiversity_biophysical_check_projections_fail(self):
        """Test a list of gdal datasets and assert that we see success and
            failures where we would expect """
        #raise SkipTest
        reg_dir = './invest-data/test/data/biodiversity_regression_data/'
        ds_1 = gdal.Open(os.path.join(reg_dir, 'samp_input/lc_samp_bse_b.tif'))
        ds_2 = gdal.Open(os.path.join(reg_dir, 'samp_input/lc_samp_cur_b.tif'))
        ds_3 = gdal.Open(os.path.join(reg_dir, 'unprojected_raster.tif'))

        ds_dict = {'_c':ds_2, '_b':ds_1,'_f':ds_3}

        result = biodiversity_biophysical.check_projections(ds_dict, 1.0)
        
        # Asserting not True because we expect to get False back
        self.assertTrue(not result)

    def test_biodiversity_biophsyical_threat_names_match(self):
        """Test hand created dictionaries representing the formats of the
            threats and sensitivity CSV files """
        #raise SkipTest
        threat_dict = \
            {'crp':{'THREAT':'crp','MAX_DIST':'8','WEIGHT':0.3},
            'road':{'THREAT':'road','MAX_DIST':'5','WEIGHT':0.3},
             'bld':{'THREAT':'bld','MAX_DIST':'7','WEIGHT':0.3}}
        sens_dict = \
            {'0':{'LULC':'0','HABITAT':'1','L_crp':'0.8',
                  'L_road':'0.5','L_bld':'0.9'},
             '1': {'LULC':'0','HABITAT':'1','L_crp':'0.8',
                  'L_road':'0.5','L_bld':'0.9'},
             '2': {'LULC':'0','HABITAT':'1','L_crp':'0.8',
                   'L_road':'0.5','L_bld':'0.9'},
             '3': {'LULC':'0','HABITAT':'1','L_crp':'0.8',
                   'L_road':'0.5','L_bld':'0.9'}}


        result = biodiversity_biophysical.threat_names_match(
                threat_dict, sens_dict, 'L_')

        self.assertTrue(result)
    
    def test_biodiversity_biophsyical_threat_names_match_fail(self):
        """Test hand created dictionaries representing the formats of the
            threats and sensitivity CSV files. We purposely put an error in
            here so that the function will return False """
        #raise SkipTest
        threat_dict =\
            {'crp':{'THREAT':'crp','MAX_DIST':'8','DECAY':'0','WEIGHT':0.3},
            'road':{'THREAT':'road','MAX_DIST':'5','DECAY':'1','WEIGHT':0.3},
             'bld':{'THREAT':'bld','MAX_DIST':'7','DECAY':'0','WEIGHT':0.3}}
        sens_dict = \
            {'0':{'LULC':'0', 'HABITAT':'1', 'L_crp':'0.8',
                'Lroad':'0.5', 'L_bld':'0.9'},
             '1': {'LULC':'0', 'HABITAT':'1', 'L_crp':'0.8',
                 'Lroad':'0.5', 'L_bld':'0.9'},
             '2': {'LULC':'0', 'HABITAT':'1', 'L_crp':'0.8',
                 'Lroad':'0.5', 'L_bld':'0.9'},
             '3': {'LULC':'0', 'HABITAT':'1', 'L_crp':'0.8',
                 'Lroad':'0.5', 'L_bld':'0.9'}}


        result = biodiversity_biophysical.\
                     threat_names_match(threat_dict, sens_dict, 'L_')

        #asserting not true because we expect to get False back
        self.assertTrue(not result)
