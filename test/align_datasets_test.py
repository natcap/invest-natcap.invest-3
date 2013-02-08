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

        reduced_raster = os.path.join(base_dir, 'reduced.tif')
        regression_dir = 'data/resize_resample_regression'
        #call through each interpolation scheme to make sure it works
        for interpolation_type in ["nearest", "bilinear", "cubic", "cubic_spline", "lanczos"]:
            reduced_raster = os.path.join(base_dir, 'reduced'+interpolation_type+'.tif')
            raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, reduced_raster, interpolation_type)
            invest_test_core.assertTwoDatasetEqualURI(self, reduced_raster, os.path.join(regression_dir, os.path.basename(reduced_raster)))



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

    def test_align_dataset_list(self):
        base_data = 'data/base_data'
        precip = os.path.join(base_data, 'Freshwater', 'precip')
        lulc_samp_cur = os.path.join(base_data, 'terrestrial', 'lulc_samp_cur')

        out_dir = 'data/test_out/align_terrestrial/'
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        precip_out = os.path.join(out_dir, os.path.basename(precip)+'.align.tif')
        lulc_samp_cur_out = os.path.join(out_dir, os.path.basename(lulc_samp_cur)+'.align.tif')

        pixel_size=60.0
        raster_utils.align_dataset_list([precip, lulc_samp_cur], [precip_out, lulc_samp_cur_out], ["nearest", "nearest"], pixel_size, "intersection", 1)

        lulc_samp_cur_regression = 'data/align_regression/lulc_samp_cur.align.tif'
        precip_regression = 'data/align_regression/precip.align.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, precip_out, precip_regression)
        invest_test_core.assertTwoDatasetEqualURI(self, lulc_samp_cur_out, lulc_samp_cur_regression)

        aoi_uri = os.path.join('data', 'hydropower_data', 'test_input', 'watersheds.shp')
        precip_aoi_out = os.path.join(out_dir, os.path.basename(precip)+'.aoi_align.tif')
        lulc_samp_cur_aoi_out = os.path.join(out_dir, os.path.basename(lulc_samp_cur)+'.aoi_align.tif')
        raster_utils.align_dataset_list([precip, lulc_samp_cur], [precip_aoi_out, lulc_samp_cur_aoi_out], ["nearest", "nearest"], pixel_size, "intersection", 1, aoi_uri=aoi_uri)

        lulc_samp_cur_aoi_regression = 'data/align_regression/lulc_samp_cur.aoi_align.tif'
        precip_aoi_regression = 'data/align_regression/precip.aoi_align.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, precip_aoi_out, precip_aoi_regression)
        invest_test_core.assertTwoDatasetEqualURI(self, lulc_samp_cur_aoi_out, lulc_samp_cur_aoi_regression)
