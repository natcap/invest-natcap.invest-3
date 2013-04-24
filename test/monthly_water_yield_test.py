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
        #raise SkipTest
        test_dir = './data/monthly_water_yield'
        output_dir = './data/test_out/monthly_water_yield/construct_step_data'
        raster_utils.create_directories([output_dir])

        samp_data_uri = os.path.join(
                test_dir, 'regression/sample_step_data.csv')

        result_dict = monthly_water_yield.construct_time_step_data(
                samp_data_uri)

        expected_dict = {
                '01/1988':{
                           (44.583,-123.384):10,(44.593,-123.405):5,
                           (44.341,-123.365):0,(44.417,-123.47):7},
                '02/1988':{
                           (44.583,-123.384):10,(44.593,-123.405):6,
                           (44.642,-123.566):7,(44.597,-123.582):5,
                           (44.341,-123.365):11},
                '03/1988':{
                           (41.417,-122.47):6, (41.417,-122.47):2}
                }

        self.assertEqual(result_dict, expected_dict)


