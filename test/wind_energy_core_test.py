import os, sys
import unittest
import random
import logging
import csv

from osgeo import ogr
from osgeo import gdal
from osgeo import osr
from osgeo.gdalconst import *
import numpy as np
from nose.plugins.skip import SkipTest

from invest_natcap import raster_utils
from invest_natcap.wind_energy import wind_energy_core
import invest_test_core

LOGGER = logging.getLogger('wind_energy_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestWindEnergyCore(unittest.TestCase):
    def test_wind_energy_core_distance_transform_dataset(self):
        """A regression test for the distance_transform_dataset function"""
        
        regression_dir = './data/wind_energy_regression_data/biophysical_core_tests/'

        reg_transformed_dataset_uri = os.path.join(
                regression_dir, 'distance_mask.tif')

        reg_dataset_uri = os.path.join(regression_dir, 'aoi_raster.tif')
        reg_dataset = gdal.Open(reg_dataset_uri)

        output_dir = './data/test_out/wind_energy_biophysical/distance_transform_dataset/'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        min_dist = 7000 
        max_dist = 80000
        out_nodata = -32768.0
        out_uri = os.path.join(output_dir, 'transformed_ds.tif')


        result = wind_energy_core.distance_transform_dataset(
                reg_dataset, min_dist, max_dist, out_nodata, out_uri)

        reg_dataset = None
        result = None

        invest_test_core.assertTwoDatasetEqualURI(
                self, reg_transformed_dataset_uri, out_uri)


    def test_wind_energy_core(self):
        """Do the main run here if possible"""
        raise SkipTest
        # start testing
