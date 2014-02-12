"""Unit Tests For Style Module"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest
import invest_natcap.testing as testing

#from invest_natcap import reporting
from invest_natcap import style
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

