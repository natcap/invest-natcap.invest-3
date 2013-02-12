"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess
import logging
import glob

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

        dataset_uri_list = glob.glob('data/vectorize_datasets_data/*.tif')

        def vector_op(*pixel_list):
            return sum(pixel_list)

        datatype_out = gdal.GDT_Float32
        nodata_out = -100.0
        pixel_size_out = 30.0
        bounding_box_mode = "union"
        dataset_to_align_index = 0

        aoi_uri = None
        dataset_noaoi_union_out_uri = os.path.join(base_dir, 'vectorized_union_datasets_noaoi.tif')
        raster_utils.vectorize_datasets(
            dataset_uri_list, vector_op, dataset_noaoi_union_out_uri, datatype_out, nodata_out,
            pixel_size_out, bounding_box_mode, resample_method_list=None, 
            dataset_to_align_index=dataset_to_align_index, aoi_uri=aoi_uri)

        dataset_union_out_uri = os.path.join(base_dir, 'vectorized_union_datasets.tif')

        aoi_uri = 'data/vectorize_datasets_data/aoi_test.shp'
        raster_utils.vectorize_datasets(
            dataset_uri_list, vector_op, dataset_union_out_uri, datatype_out, nodata_out,
            pixel_size_out, bounding_box_mode, resample_method_list=None, 
            dataset_to_align_index=dataset_to_align_index, aoi_uri=aoi_uri)

        bounding_box_mode = "intersection"
        dataset_intersection_out_uri = os.path.join(base_dir, 'vectorized_intersection_datasets.tif')
        raster_utils.vectorize_datasets(
            dataset_uri_list, vector_op, dataset_intersection_out_uri, datatype_out, nodata_out,
            pixel_size_out, bounding_box_mode, resample_method_list=None, 
            dataset_to_align_index=dataset_to_align_index, aoi_uri=aoi_uri)
