"""URI level tests for the biodiversity biophysical module"""

import os, sys
import unittest

from invest_natcap.biodiversity import biodiversity_biophysical
import invest_test_core

class TestBiodiversityBiophysical(unittest.TestCase):
    def test_biodiversity_biophysical_smoke(self):
        """Smoke test for biodiversity_biophysical function.  Shouldn't crash with \
           zero length inputs"""
        input_dir = './data/biodiversity_data/samp_input/'
        out_dir = './data/test_out/biodiversity/'
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        args = {}
        args['workspace_dir'] = input_dir
        args['landuse_cur_uri'] = input_dir + 'lc_samp_cur_b/w001001.adf'
        #args['landuse_bas_uri'] = input_dir + 'lc_samp_bse_b/w001001.adf'
        #args['landuse_fut_uri'] = input_dir + 'lc_samp_fut_b/w001001.adf'
        args['threat_uri'] = input_dir + 'threats_samp.csv'
        args['sensitivity_uri'] = input_dir + 'sensitivity_samp.csv'
        args['access_uri'] = input_dir + 'access_samp.shp'
        args['half_saturation_constant'] = 30
        args['results_suffix'] = input_dir + ''

        biodiversity_biophysical.execute(args)
