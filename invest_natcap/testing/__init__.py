"""The invest_natcap.testing package defines core testing routines and
functionality."""

import unittest
import os
import logging
import shutil
import functools

import numpy
from osgeo import gdal

LOGGER = logging.getLogger('invest_natcap.testing')


def save_workspace(new_workspace):
    def test_inner_func(item):
        @functools.wraps(item)
        def test_and_remove_workspace(self, *args, **kwargs):
            item(self)

            # remove the contents of the old folder
            try:
                shutil.rmtree(new_workspace)
            except OSError:
                pass

            # copy the workspace to the target folder
            old_workspace = self.workspace_dir
            shutil.copytree(old_workspace, new_workspace)
        return test_and_remove_workspace
    return test_inner_func


class GISTest(unittest.TestCase):
    """A test class for our GIS testing functions."""

    def assertRastersEqual(self, a_uri, b_uri):
        """Tests if datasets a and b are 'almost equal' to each other on a per
            pixel basis

            aUri - a URI to a gdal dataset
            bUri - a URI to a  gdal dataset

            returns True if a and b are equal to each other"""

        LOGGER.debug('Asserting datasets A: %s, B: %s', a_uri, b_uri)

        for uri in [a_uri, b_uri]:
            if not os.path.exists(uri):
                raise IOError('File "%s" not found on disk' % uri)

        a_dataset = gdal.Open(a_uri)
        b_dataset = gdal.Open(b_uri)

        self.assertEqual(a_dataset.RasterXSize, b_dataset.RasterXSize,
            "x dimensions are different a=%s, second=%s" %
            (a_dataset.RasterXSize, b_dataset.RasterXSize))
        self.assertEqual(a_dataset.RasterYSize, b_dataset.RasterYSize,
            "y dimensions are different a=%s, second=%s" %
            (a_dataset.RasterYSize, b_dataset.RasterYSize))
        self.assertEqual(a_dataset.RasterCount, b_dataset.RasterCount,
            "different number of rasters a=%s, b=%s" % (
            (a_dataset.RasterCount, b_dataset.RasterCount)))

        for band_number in range(1, a_dataset.RasterCount + 1):
            band_a = a_dataset.GetRasterBand(band_number)
            band_b = b_dataset.GetRasterBand(band_number)

            a_array = band_a.ReadAsArray(0, 0, band_a.XSize, band_a.YSize)
            b_array = band_a.ReadAsArray(0, 0, band_b.XSize, band_b.YSize)

            try:
                numpy.testing.assert_array_almost_equal(a_array, b_array)
            except AssertionError:
                for row_index in xrange(band_a.YSize):
                    for pixel_a, pixel_b in zip(a_array[row_index], b_array[row_index]):
                        self.assertAlmostEqual(pixel_a, pixel_b,
                            msg='%s != %s ... Failed at row %s' %
                            (pixel_a, pixel_b, row_index))
