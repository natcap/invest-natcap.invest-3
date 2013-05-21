"""The invest_natcap.testing package defines core testing routines and
functionality."""

import unittest

class GISTest(unittest.TestCase):
    """A test class for our GIS testing functions."""

    def assertRastersEqual(self, a_uri, b_uri):
        """Tests if datasets a and b are 'almost equal' to each other on a per
            pixel basis

            aUri - a URI to a gdal dataset
            bUri - a URI to a  gdal dataset

            returns True if a and b are equal to each other"""

        logger.debug('Asserting datasets A: %s, B: %s', aUri, bUri)

        for uri in [aUri, bUri]:
            if not os.path.exists(uri):
                raise IOError('File "%s" not found on disk' % uri)

        a_dataset = gdal.Open(aUri)
        b_dataset = gdal.Open(bUri)

        self.assertEqual(a_dataset.RasterXSize, b_dataset.RasterXSize,
            "x dimensions are different a=%s, second=%s" %
            (a_dataset.RasterXSize, b_dataset.RasterXSize))
        self.assertEqual(a_dataset.RasterYSize, b_dataset.RasterYSize,
            "y dimensions are different a=%s, second=%s" %
            (a_dataset.RasterYSize, b_dataset.RasterYSize))
        self.assertEqual(a_dataset.RasterCount, b_dataset.RasterCount,
            "different number of rasters a=%s, b=%s" % (
            (a_dataset.RasterCount, b_dataset.RasterCount))

        for bandNumber in range(1, a_dataset.RasterCount + 1):
            band_a = a_dataset.GetRasterBand(bandNumber)
            band_a = b_dataset.GetRasterBand(bandNumber)

            a_array = band_a.ReadAsArray(0, 0, band_a.XSize, band_a.YSize)
            b_array = band_a.ReadAsArray(0, 0, band_b.XSize, band_b.YSize)

            try:
                np.testing.assert_array_almost_equal(aArray, bArray)
            except AssertionError:
                for row_index in xrange(bandA.YSize):
                    for a, b in zip(aArray[row_index], bArray[row_index]):
                        self.assertAlmostEqual(
                            a, b, msg='%s != %s ... Failed at row %s' % (a, b, row_index))
