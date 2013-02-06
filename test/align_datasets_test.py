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

class TestAlignDatasets(unittest.TestCase):
    def test_align_datasets(self):
        data_dir = 'data/align_datasets_data'
        raster_1 = os.path.join(data_dir, 'H[eelgrass]_S[finfishaquaculturecomm]_Risk.tif')
        raster_2 = os.path.join(data_dir, 'H[eelgrass]_S[shellfishaquaculturecomm]_Risk.tif')
        base_dir = 'data/test_out/align_datasets'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        raster_1_out = raster_1 + '.out.tif'
        raster_2_out = raster_2 + '.out.tif'
        pixel_size = 1000.0
        raster_utils.align_dataset_list([raster_1, raster_2], 100.0, [raster_1_out, raster_2_out], "intersection",
                                        0)

        #TODO: regression asserts
