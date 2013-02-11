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
    def test_vectorize_datasets(self):
        base_dir = 'data/test_out/vectorize_datasets'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dataset_uri_list = ['data/base_data/terrestrial/lulc_samp_cur',
                            'data/base_data/Freshwater/precip']

        def vector_op(lulc, precip):
            return lulc + precip

        datatype_out = gdal.GDT_Float32
        nodata_out = -100.0
        pixel_size_out = 30.0
        bounding_box_mode = "union"
        dataset_to_align_index = 0

        dataset_out_uri = os.path.join(base_dir, 'vectorized_datasets.tif')

        raster_utils.vectorize_datasets(
            dataset_uri_list, vector_op, dataset_out_uri, datatype_out, nodata_out,
            pixel_size_out, bounding_box_mode, resample_method_list=None, 
            dataset_to_align_index=dataset_to_align_index, aoi_uri=None)
