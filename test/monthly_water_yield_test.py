import sys
import os
import unittest
import math
import csv
import logging

from osgeo import osr
from osgeo import ogr
from osgeo import gdal
from osgeo.gdalconst import *
from invest_natcap.dbfpy import dbf
import numpy as np

from invest_natcap.monthly_water_yield import monthly_water_yield
import invest_test_core
from invest_natcap import raster_utils
from nose.plugins.skip import SkipTest

LOGGER = logging.getLogger('monthly_water_yield_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestMonthlyWaterYield(unittest.TestCase):

    def test_monthly_water_yield_construct_step_data(self):
        """A unit test for constructing the dictionary from step data
        """
        raise SkipTest
        test_dir = './invest-data/test/data/monthly_water_yield'
        output_dir = './invest-data/test/data/test_out/monthly_water_yield/construct_step_data'
        raster_utils.create_directories([output_dir])

        samp_data_uri = os.path.join(
                test_dir, 'regression/sample_step_data.csv')

        result_dict = monthly_water_yield.construct_time_step_data(
                samp_data_uri)

        LOGGER.debug('Constructed Dict: %s', result_dict)

        expected_dict = {
                '01/1988':{
                    0:{'date':'01/1988','lati':'44.583','long':'-123.384', 'p':'10'},
                    1:{'date':'01/1988','lati':'44.593','long':'-123.405', 'p':'5'},
                    2:{'date':'01/1988','lati':'44.341','long':'-123.365', 'p':'0'},
                    3:{'date':'01/1988','lati':'44.417','long':'-123.47', 'p':'7'}
                    },
                '02/1988':{
                    0:{'date':'02/1988','lati':'44.583','long':'-123.384', 'p':'10'},
                    1:{'date':'02/1988','lati':'44.593','long':'-123.405', 'p':'6'},
                    2:{'date':'02/1988','lati':'44.642','long':'-123.566', 'p':'7'},
                    3:{'date':'02/1988','lati':'44.597','long':'-123.582', 'p':'5'},
                    4:{'date':'02/1988','lati':'44.341','long':'-123.365', 'p':'11'}
                    },
                '03/1988':{
                    0:{'date':'03/1988','lati':'41.417','long':'-122.47', 'p':'6'},
                    1:{'date':'03/1988','lati':'41.417','long':'-122.47', 'p':'2'}
                    }
                }
       
        LOGGER.debug('Expected Dict: %s', expected_dict)
        
        self.assertEqual(result_dict, expected_dict)

    def test_monthly_water_yield_create_alphas(self):
        """A regression test for creating the alpha rasters
        """

        raise SkipTest
        test_dir = './invest-data/test/data/monthly_water_yield'
        output_dir = './invest-data/test/data/test_out/monthly_water_yield/create_alphas'
        regression_dir = os.path.join(test_dir, 'regression')

        raster_utils.create_directories([output_dir])

        slope_uri = os.path.join(regression_dir, 'slope.tif') 
        smax_uri = os.path.join(test_dir, 'samp_input/smax_200m.tif') 
        sandy_sa = 0.25
        out_nodata = float(np.finfo(np.float32).min) + 1.0

        alpha_one_uri = os.path.join(output_dir, 'alpha_one.tif')
        alpha_two_uri = os.path.join(output_dir, 'alpha_two.tif')
        alpha_three_uri = os.path.join(output_dir, 'alpha_three.tif')
        alpha_uri_list = [alpha_one_uri, alpha_two_uri, alpha_three_uri]
        
        alpha_table = {'alpha_one':{'a_one':0.07, 'b_one':0.01, 'c_one':0.002},
                       'alpha_two':{'a_two':0.2, 'b_two':2.2},
                       'alpha_three':{'a_three':1.44, 'b_three':0.68}}

        monthly_water_yield.calculate_alphas(
            slope_uri, sandy_sa, smax_uri, alpha_table, out_nodata,
            alpha_uri_list)

        for out_uri in ['alpha_one.tif', 'alpha_two.tif', 'alpha_three.tif']:
            reg_uri = os.path.join(regression_dir, out_uri)
            test_uri = os.path.join(output_dir, out_uri)
            invest_test_core.assertTwoDatasetEqualURI(self, reg_uri, test_uri)
