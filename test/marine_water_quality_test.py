"""URI level tests for the marine water quality module"""

import unittest
import logging
import os

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.marine_water_quality import marine_water_quality_biophysical
import invest_test_core

LOGGER = logging.getLogger('marine_water_quality_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


class TestMWQBiophysical(unittest.TestCase):
    """Main testing class for the MWQ biophysical tests"""
    def test_marine_water_quality_biophysical(self):
        output_base = './invest-data/test/data/test_out/marine_water_quality_test/'
        input_dir = './invest-data/test/data/marine_water_quality_data/'

        args = {}
        args['workspace'] = output_base
        args['aoi_poly_uri'] = os.path.join(input_dir, 'AOI_clay_soundwideWQ.shp')
        args['pixel_size'] = 100.0
        args['kps'] = 0.001
        args['land_poly_uri'] = os.path.join(input_dir, '3005_VI_landPolygon.shp')
        args['source_points_uri'] = os.path.join(input_dir, 'floathomes_centroids.shx')
        args['source_point_data_uri'] = os.path.join(input_dir, 'WQM_PAR.csv')
        args['tide_e_points_uri'] = os.path.join(input_dir,'TideE_WGS1984_BCAlbers.shp')
#        args['adv_uv_points_uri'] = os.path.join(input_dir,'ADVuv_WGS1984_BCAlbers.shp')

        if not os.path.isdir(output_base):
            os.mkdir(output_base)
        
        marine_water_quality_biophysical.execute(args)
