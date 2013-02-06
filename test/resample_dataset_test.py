"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess
import logging

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from nose.plugins.skip import SkipTest
import numpy as np
from invest_natcap import raster_utils
import invest_test_core

LOGGER = logging.getLogger('invest_core')

class TestResampleDatasets(unittest.TestCase):
    def test_assert_datasets_in_same_projection(self):
        raster_1 = '../../invest-data/Base_Data/Marine/DEMs/claybark_dem'

        base_dir = 'data/test_out/resample_datasets'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        raster_utils.resample_dataset(raster_1, 250, os.path.join(base_dir, 'resampled.tif'))
