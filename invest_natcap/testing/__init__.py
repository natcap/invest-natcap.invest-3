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
    """Decorator to save a workspace to a new location."""

    # item is the function being decorated
    def test_inner_func(item):

        # this decorator indicates that this innermost function is wrapping up
        # the function passed in as item.
        @functools.wraps(item)
        def test_and_remove_workspace(self, *args, **kwargs):
            # This inner function actually executes the test function and then
            # moves the workspace to the folder passed in by the user.
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

    def assertVectorsEqual(self, aUri, bUri):
        """Tests if shapes a and b are equal to each other on a
           layer, feature, and field basis

           unitTest - an instance of a unittest object
           aUri - a URI to a ogr shapefile
           bUri - a URI to a ogr shapefile

           returns True if a and b are equal to each other"""

        for uri in [aUri, bUri]:
            if not os.path.exists(uri):
                raise IOError('File "%s" not found on disk' % uri)

        shape = ogr.Open(aUri)
        shape_regression = ogr.Open(bUri)

        # Check that the shapefiles have the same number of layers
        layer_count = shape.GetLayerCount()
        layer_count_regression = shape_regression.GetLayerCount()
        unitTest.assertEqual(layer_count, layer_count_regression,
                         'The shapes DO NOT have the same number of layers')

        for layer_num in range(layer_count):
            # Get the current layer
            layer = shape.GetLayer(layer_num)
            layer_regression = shape_regression.GetLayer(layer_num)
            # Check that each layer has the same number of features
            feat_count = layer.GetFeatureCount()
            feat_count_regression = layer_regression.GetFeatureCount()
            unitTest.assertEqual(feat_count, feat_count_regression,
                             'The layers DO NOT have the same number of features')

            unitTest.assertEqual(layer.GetGeomType(), layer_regression.GetGeomType(),
                'The layers do not have the same geometry type')


            # Get the first features of the layers and loop through all the features
            feat = layer.GetNextFeature()
            feat_regression = layer_regression.GetNextFeature()
            while feat is not None:
                # Check that the field counts for the features are the same
                layer_def = layer.GetLayerDefn()
                layer_def_regression = layer_regression.GetLayerDefn()
                field_count = layer_def.GetFieldCount()
                field_count_regression = layer_def_regression.GetFieldCount()
                unitTest.assertEqual(field_count, field_count_regression,
                                 'The shapes DO NOT have the same number of fields')

                for fld_index in range(field_count):
                    # Check that the features have the same field values
                    field = feat.GetField(fld_index)
                    field_regression = feat_regression.GetField(fld_index)
                    unitTest.assertEqual(field, field_regression,
                                         'The field values DO NOT match')
                    # Check that the features have the same field name
                    field_ref = feat.GetFieldDefnRef(fld_index)
                    field_ref_regression = \
                        feat_regression.GetFieldDefnRef(fld_index)
                    field_name = field_ref.GetNameRef()
                    field_name_regression = field_ref_regression.GetNameRef()
                    unitTest.assertEqual(field_name, field_name_regression,
                                         'The fields DO NOT have the same name')
                # Check that the features have the same geometry
                geom = feat.GetGeometryRef()
                geom_regression = feat_regression.GetGeometryRef()

                unitTest.assertTrue(geom.Equals(geom_regression))

                if layer.GetGeomType() != ogr.wkbPoint:
                    # Check that the features have the same area,
                    # but only if the shapefile's geometry is not a point, since
                    # points don't have area to check.
                    unitTest.assertEqual(geom.Area(), geom_regression.Area())

                feat = None
                feat_regression = None
                feat = layer.GetNextFeature()
                feat_regression = layer_regression.GetNextFeature()

        shape = None
        shape_regression = None
