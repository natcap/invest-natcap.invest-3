"""URI level tests for the biodiversity biophysical module"""

import os, sys
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.biodiversity import biodiversity_biophysical
import invest_test_core

class TestBiodiversityBiophysical(unittest.TestCase):
    def test_biodiversity_biophysical_sample_smoke(self):
        """Smoke test for biodiversity_biophysical function.  Shouldn't crash with \
           zero length inputs"""

        raise SkipTest

        input_dir = './data/biodiversity_regression_data/samp_input'
        out_dir = './data/test_out/biodiversity/'
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        args = {}
        args['workspace_dir'] = input_dir
        args['landuse_cur_uri'] = \
                os.path.join(input_dir, 'lc_samp_cur_b.tif')
        args['landuse_bas_uri'] = os.path.join(input_dir, 'lc_samp_bse_b.tif')
        args['landuse_fut_uri'] = os.path.join(input_dir, 'lc_samp_fut_b.tif')
        args['threat_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        args['half_saturation_constant'] = 30
        args['results_suffix'] = ''

        biodiversity_biophysical.execute(args)
    
    def test_biodiversity_biophysical_default_smoke(self):
        """Smoke test for biodiversity_biophysical function.  Shouldn't crash with \
           zero length inputs"""
        
        #raise SkipTest
        
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
        args['threat_uri'] = os.path.join(input_dir, 'threats_samp.csv')
        args['sensitivity_uri'] = os.path.join(input_dir , 'sensitivity_samp.csv')
        args['access_uri'] = os.path.join(input_dir , 'access_samp.shp')
        args['half_saturation_constant'] = 30
        args['results_suffix'] = ''

        biodiversity_biophysical.execute(args)
