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

class TestRasterUtils(unittest.TestCase):
    def test_reclassify_dataset(self):
        base_dir = 'invest-data/test/data/test_out/reclassify_dataset'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        output_uri = os.path.join(base_dir, 'reclassified.tif')
        base_uri = 'invest-data/test/data/base_data/terrestrial/lulc_samp_cur'
        dataset = gdal.Open(base_uri)
        value_map = {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.5}

        reclassified_ds = raster_utils.reclassify_dataset(
            dataset, value_map, output_uri, gdal.GDT_Float32, -1.0)

        regression_uri = 'invest-data/test/data/reclassify_regression/reclassified.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, regression_uri, output_uri)
