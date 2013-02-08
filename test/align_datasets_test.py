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
    def test_resize_and_resample_dataset(self):
        raster_1 = 'data/align_datasets_data/dem_30m_fill_clip.tif'

        bounding_box = raster_utils.get_bounding_box(raster_1)

        base_dir = 'data/test_out/align_datasets'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        resized_raster = os.path.join(base_dir, 'resized.tif')

        width = abs(bounding_box[2]-bounding_box[0])
        height = abs(bounding_box[3]-bounding_box[1])

        bounding_box[0] -= width
        bounding_box[2] += width
        bounding_box[1] += height
        bounding_box[3] -= height

        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 30, resized_raster, "nearest")

        resized_278_raster = os.path.join(base_dir, 'resized_278.tif')
        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, resized_278_raster, "nearest")

        bounding_box = raster_utils.get_bounding_box(raster_1)
        rescaled_278_raster = os.path.join(base_dir, 'rescaled_278.tif')
        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, rescaled_278_raster, "nearest")

        pixel_size = raster_utils.pixel_size(gdal.Open(raster_1))
        bounding_box[0] += 13.5*pixel_size
        bounding_box[1] -= 1.5*pixel_size
        bounding_box[2] -= width/4.0
        bounding_box[3] += height/4.0

        #TODO: regression rasters for check this stuff
        reduced_278_raster = os.path.join(base_dir, 'reduced_278.tif')
        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, reduced_278_raster, "nearest")
        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, reduced_278_raster, "bilinear")
        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, reduced_278_raster, "cubic")
        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, reduced_278_raster, "cubic_spline")
        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, reduced_278_raster, "lanczos")
        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 9, reduced_278_raster, "lanczos")

        
        #This tests if the datasets can be aligned well.
        dataset_uri_list = [raster_1, reduced_278_raster]
        
        raster_utils.align_dataset_list(
            dataset_uri_list, 17, map(lambda x: x+"_union.tif", dataset_uri_list), "union", 0, "cubic")
        raster_utils.align_dataset_list(
            dataset_uri_list, 17, map(lambda x: x+"_intersection.tif", dataset_uri_list), "intersection", 0, "cubic")

    def test_assert_datasets_in_same_projection(self):
        raster_1 = 'data/align_datasets_data/H[eelgrass]_S[finfishaquaculturecomm]_Risk.tif'
        raster_2 = 'data/align_datasets_data/H[eelgrass]_S[shellfishaquaculturecomm]_Risk.tif'

        #These are in the same projection, so no exception expected
        raster_utils.assert_datasets_in_same_projection([raster_1, raster_2])
        
        raster_3 = 'data/clip_data/global_clipped.tif'
        #Raster 3 is unprojected, so I expect an unprojected error
        self.assertRaises(raster_utils.DatasetUnprojected,raster_utils.assert_datasets_in_same_projection,[raster_3])

        raster_4 = 'data/align_datasets_data/dem_30m_fill_clip.tif'
        #raster 1 and 4 are projected but in different projections..
        self.assertRaises(raster_utils.DifferentProjections,raster_utils.assert_datasets_in_same_projection,[raster_1, raster_4])

    def test_align_datasets(self):
        data_dir = 'data/align_datasets_data'
        raster_1 = os.path.join(data_dir, 'H[eelgrass]_S[finfishaquaculturecomm]_Risk.tif')
        raster_2 = os.path.join(data_dir, 'H[eelgrass]_S[shellfishaquaculturecomm]_Risk.tif')
        base_dir = 'data/test_out/align_datasets'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        raster_1_out = os.path.join(base_dir, os.path.basename(raster_1) + '.out.tif')
        raster_2_out = os.path.join(base_dir, os.path.basename(raster_2) + '.out.tif')
        pixel_size = 1000.0
        #raster_utils.align_dataset_list([raster_1, raster_2], 100.0, [raster_1_out, raster_2_out], "intersection", 0)
        raster_utils.align_dataset_list([raster_1, raster_2], 100.0, [raster_1_out, raster_2_out], "union", 0, "lanczos")

        #TODO: regression asserts
