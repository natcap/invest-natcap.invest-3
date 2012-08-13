"""URI level tests for the biodiversity biophysical module"""

import os, sys
from osgeo import gdal
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.biodiversity import biodiversity_biophysical
import invest_test_core

class TestBiodiversityBiophysical(unittest.TestCase):
    def test_biodiversity_biophysical_sample_smoke(self):
        """Smoke test for biodiversity_biophysical function.  Shouldn't crash with \
           zero length inputs"""

        #raise SkipTest

        input_dir = './data/biodiversity_regression_data/samp_input'
        out_dir = './data/test_out/biodiversity/'
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        args = {}
        args['workspace_dir'] = input_dir
        args['landuse_cur_uri'] = \
                os.path.join(input_dir, 'lc_samp_cur_b.tif')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        #args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        args['half_saturation_constant'] = 30
        args['results_suffix'] = ''

        biodiversity_biophysical.execute(args)
    
    def test_biodiversity_biophysical_default_smoke(self):
        """Smoke test for biodiversity_biophysical function.  Shouldn't crash with \
           zero length inputs"""
        
        raise SkipTest
        
        input_dir = './data/biodiversity_data/samp_input'
        out_dir = './data/test_out/biodiversity/'
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        args = {}
        args['workspace_dir'] = input_dir
        args['landuse_cur_uri'] = \
                os.path.join(input_dir, 'lc_samp_cur_b/')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b/')
        args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b/')
        args['threats_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        args['half_saturation_constant'] = 30
        args['results_suffix'] = ''

        biodiversity_biophysical.execute(args)

    def test_biodiversity_biophysical_open_amb(self):
        """Test multiple uri types for open_ambiguous_raster and assert that
            the proper behavior is seen """
        #raise SkipTest
        reg_dir = './data/biodiversity_regression_data/'
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
        reg_dir = './data/biodiversity_regression_data/'
        csv_uri = os.path.join(reg_dir, 'test_csv.csv')
        field = 'LULC'

        result_dict = {'0':{'LULC':'0','DESC':'farm','RARITY':'0.4'},
                       '3':{'LULC':'3','DESC':'water','RARITY':'1.0'},
                       '23':{'LULC':'23','DESC':'swamp','RARITY':'0.2'}}
        created_dict =\
            biodiversity_biophysical.make_dictionary_from_csv(csv_uri, field)

        self.assertEqual(result_dict, created_dict)
        
    def test_biodiversity_biophysical_check_projections(self):
        """Test a list of gdal datasets and assert that we see success and
            failures where we would expect """

        reg_dir = './data/biodiversity_regression_data/samp_input/'
        ds_1 = gdal.Open(os.path.join(reg_dir, 'lc_samp_bse_b.tif'))
        ds_2 = gdal.Open(os.path.join(reg_dir, 'lc_samp_cur_b.tif'))
        ds_3 = gdal.Open(os.path.join(reg_dir, 'lc_samp_fut_b.tif'))

        ds_dict = {'_c':ds_2, '_b':ds_1,'_f':ds_3}

        result = biodiversity_biophysical.check_projections(ds_dict, 1.0)
        
        self.assertTrue(not result)

    def test_biodiversity_biophysical_check_projections_fail(self):
        """Test a list of gdal datasets and assert that we see success and
            failures where we would expect """

        reg_dir = './data/biodiversity_regression_data/'
        ds_1 = gdal.Open(os.path.join(reg_dir, 'samp_input/lc_samp_bse_b.tif'))
        ds_2 = gdal.Open(os.path.join(reg_dir, 'samp_input/lc_samp_cur_b.tif'))
        ds_3 = gdal.Open(os.path.join(reg_dir, 'unprojected_raster.tif'))

        ds_dict = {'_c':ds_2, '_b':ds_1,'_f':ds_3}

        result = biodiversity_biophysical.check_projections(ds_dict, 1.0)
        
        self.assertTrue(result)

    def test_biodiversity_biophsyical_compare_threats_sensitivity(self):
        """Test hand created dictionaries representing the formats of the
            threats and sensitivity CSV files """

        threat_dict =\
            {'crp':{'THREAT':'crp','MAX_DIST':'8','DECAY':'0','WEIGHT':0.3},
            'road':{'THREAT':'road','MAX_DIST':'5','DECAY':'1','WEIGHT':0.3},
             'bld':{'THREAT':'bld','MAX_DIST':'7','DECAY':'0','WEIGHT':0.3}}
        sens_dict = \
            {'0':{'LULC':'0','HABITAT':'1','L_crp':'0.8','L_road':'0.5','L_bld':'0.9'},
             '1': {'LULC':'0','HABITAT':'1','L_crp':'0.8','L_road':'0.5','L_bld':'0.9'},
             '2': {'LULC':'0','HABITAT':'1','L_crp':'0.8','L_road':'0.5','L_bld':'0.9'},
             '3': {'LULC':'0','HABITAT':'1','L_crp':'0.8','L_road':'0.5','L_bld':'0.9'}}


        result = biodiversity_biophysical.\
                     compare_threats_sensitivity(threat_dict, sens_dict)

        self.assertTrue(not result)
    
    def test_biodiversity_biophsyical_compare_threats_sensitivity_fail(self):
        """Test hand created dictionaries representing the formats of the
            threats and sensitivity CSV files. We purposely put an error in
            here so that the function will return True """

        threat_dict =\
            {'crp':{'THREAT':'crp','MAX_DIST':'8','DECAY':'0','WEIGHT':0.3},
            'road':{'THREAT':'road','MAX_DIST':'5','DECAY':'1','WEIGHT':0.3},
             'bld':{'THREAT':'bld','MAX_DIST':'7','DECAY':'0','WEIGHT':0.3}}
        sens_dict = \
            {'0':{'LULC':'0','HABITAT':'1','L_crp':'0.8','Lroad':'0.5','L_bld':'0.9'},
             '1': {'LULC':'0','HABITAT':'1','L_crp':'0.8','Lroad':'0.5','L_bld':'0.9'},
             '2': {'LULC':'0','HABITAT':'1','L_crp':'0.8','Lroad':'0.5','L_bld':'0.9'},
             '3': {'LULC':'0','HABITAT':'1','L_crp':'0.8','Lroad':'0.5','L_bld':'0.9'}}


        result = biodiversity_biophysical.\
                     compare_threats_sensitivity(threat_dict, sens_dict)

        self.assertTrue(result)
