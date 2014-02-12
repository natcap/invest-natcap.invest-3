"""Unit Tests For Style Module"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest
import invest_natcap.testing as testing

#from invest_natcap import reporting
from invest_natcap.reporting import style
import invest_test_core

STYLE_DATA = os.path.join('invest-data/test/data', 'style_data')
REGRESSION_DATA = os.path.join(
    'invest-data/test/data', 'style_data', 'regression_data')
TEST_OUT = os.path.join('invest-data/test/data', 'test_out')

class TestStyleModule(testing.GISTest):
    def test_shape_to_svg(self):
        """Regression test for creating an svg image from an OGR shapefile"""

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'shape_to_svg_test.svg')
        test_shape_uri = os.path.join(STYLE_DATA, 'subwatersheds.shp')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_shape_to_svg.svg')
        tmp_uri = os.path.join(STYLE_DATA, 'tmp_uri.shp')
        css_uri = os.path.join(STYLE_DATA, 'test_css.css')

        args = {}
        args['size'] = (400, 600)
        args['field_id'] = 'subws_id'
        args['key_id'] = 'subws_id'
        args['proj_type'] = 'mercator'

        style.shape_to_svg(test_shape_uri, output_uri, css_uri, args)

        #self.assertFiles(output_uri, reg_uri)

    def test_grayscale_raster(self):
        """Regression test for interpolating a gdal raster to a gdal integer
            raster with values between 0 and 255"""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        input_raster_uri = os.path.join(STYLE_DATA, 'grayscale_input_test.tif')
        output_uri = os.path.join(TEST_OUT, 'style_grayscale_raster.tif')
        reg_uri = os.path.join(REGRESSION_DATA, 'reg_grayscale_raster.tif')

        style.grayscale_raster(input_raster_uri, output_uri)

        self.assertFiles(output_uri, reg_uri)

    def test_tif_to_png(self):
        """Regression test for converting a tif raster to a png image
        """

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        input_raster_uri = os.path.join(REGRESSION_DATA, 'reg_grayscale_raster.tif')
        output_uri = os.path.join(TEST_OUT, 'tif_to_png_raster.png')
        reg_uri = os.path.join(REGRESSION_DATA, 'png_reg_raster.png')

        style.tif_to_png(input_raster_uri, output_uri)

        self.assertFiles(output_uri, reg_uri)

    def test_create_thumbnail(self):
        """Regression test for creating a thumbnail"""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        input_raster_uri = os.path.join(REGRESSION_DATA, 'png_reg_raster.png')
        output_uri = os.path.join(TEST_OUT, 'png_thumbnail.png')
        reg_uri = os.path.join(REGRESSION_DATA, 'png_thumbnail_reg.png')

        size = (256, 256)

        style.create_thumbnail(input_raster_uri, output_uri, size)

        self.assertFiles(output_uri, reg_uri)
