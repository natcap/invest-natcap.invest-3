"""Unit Tests For Reporting Package"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest
import invest_natcap.testing as testing

#from invest_natcap import reporting
import invest_natcap.reporting as reporting
from invest_natcap.reporting import table_generator
import invest_test_core

REPORTING_DATA = os.path.join('invest-data/test/data', 'reporting_data')
REGRESSION_DATA = os.path.join(
    'invest-data/test/data', 'reporting_data', 'regression_data')
TEST_OUT = os.path.join('invest-data/test/data', 'test_out')

class TestReportingPackage(testing.GISTest):
    def test_generate_html_smoke(self):
        """Regression test for creating a html report with no elements passed
            in. Expecting a blank html page created."""

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_smoke.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_smoke.html')

        report_args = {
                'title': 'Test Title',
                'elements': [],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html(self):
        """Regression test for creating a html report with a table element
            from a dictionary and an external css file"""

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_dict.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_dict.html')
        css_uri = '../reporting_data/table_style.css'

        sample_dict = {
                    0: {'date':'9/13', 'price':'expensive', 'product':'chips'},
                    1: {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                    2: {'date':'5/12', 'price':'moderate', 'product':'mints'}
                }

        columns = {
            1 : {'name': 'date', 'total':False},
            2 : {'name': 'price', 'total':False},
            0 : {'name': 'product', 'total':False}}

        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
                        'checkbox': False,
                        'total': False,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict,
                        'position': 0},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'position': 0,
                        'src': css_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_csv(self):
        """Regression test for creating a html report with a table element
            from a CSV file and an external css file"""

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_csv.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_csv.html')
        csv_uri = os.path.join(REPORTING_DATA, 'csv_test.csv')
        css_uri = '../reporting_data/table_style.css'

        columns = {
            0 : {'name': 'ws_id', 'total':False},
            1 : {'name': 'precip_mn', 'total':False},
            2 : {'name': 'wyield_mn', 'total':False},
            3 : {'name': 'wyield_vol', 'total':True}}

        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
                        'checkbox': False,
                        'total': False,
                        'data_type':'csv',
                        'columns':columns,
                        'key':'ws_id',
                        'data': csv_uri,
                        'position': 0},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'position': 0,
                        'src': css_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_shape(self):
        """Regression test for creating a html report with a table element
            from a shapefile and an external css file"""

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_shp.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_shp.html')
        shape_uri = os.path.join(REPORTING_DATA, 'shape_test.shp')
        css_uri = '../reporting_data/table_style.css'

        columns = {
            0 : {'name': 'ws_id', 'total':False},
            1 : {'name': 'precip_mn', 'total':False},
            2 : {'name': 'wyield_mn', 'total':False},
            3 : {'name': 'wyield_vol', 'total':True}}

        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
                        'checkbox': False,
                        'total': False,
                        'data_type':'shapefile',
                        'columns':columns,
                        'key':'ws_id',
                        'data': shape_uri,
                        'position': 0},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'position': 0,
                        'src': css_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_robust(self):
        """Regression test for making a robust html page. Pass in a table
            element from a dictionary, css style, and javascript source.
            This table should be sortable"""

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_sorttable.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_sortable.html')
        css_uri = '../reporting_data/table_style.css'
        jsc_uri = '../reporting_data/sorttable.js'

        sample_dict = {
                    0: {'date':'9/13', 'price':'expensive', 'product':'chips'},
                    1: {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                    2: {'date':'5/12', 'price':'moderate', 'product':'mints'}
                }

        columns = {
            1 : {'name': 'date', 'total':False},
            2 : {'name': 'price', 'total':False},
            0 : {'name': 'product', 'total':True}}

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': False,
                        'total': False,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict,
                        'position': 1},
                    {
                        'type': 'text',
                        'section': 'body',
                        'position': 0,
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'position': 0,
                        'src': css_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 1,
                        'src': jsc_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_add_head_element_link(self):
        """Unit test for adding link head elements to html file"""
        #raise SkipTest

        args = {'format':'link', 'src':'example_style.css'}

        expected_result = \
                '<link rel=stylesheet type=text/css href=example_style.css>'

        result = reporting.add_head_element(args)

        self.assertEqual(expected_result, result)

    def test_add_head_element_script(self):
        """Unit test for adding script head elements to html file"""
        #raise SkipTest

        args = {'format':'script', 'src':'example_script.js'}

        expected_result = \
                '<script type=text/javascript src=example_script.js></script>'

        result = reporting.add_head_element(args)

        self.assertEqual(expected_result, result)

    def test_generate_html_checkbox(self):
        """Regression test for making a robust html page. Pass in a table
            element from a dictionary, css style, javascript source,
            and enable checkbox column. This table should be sortable
            with a checkbox column that does selected totals"""

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_checkbox.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_checkbox.html')
        css_uri = '../reporting_data/table_style.css'
        jsc_uri = '../reporting_data/sorttable.js'
        jquery_uri = '../reporting_data/jquery-1.10.2.min.js'
        jsc_fun_uri = '../reporting_data/total_functions.js'

        sample_dict = {
                    0: {'date':'9/13', 'price':100, 'product':'chips'},
                    1: {'date':'3/13', 'price':25, 'product':'peanuts'},
                    2: {'date':'5/12', 'price':60, 'product':'mints'}
                }

        columns = {
            1 : {'name': 'date', 'total':False},
            2 : {'name': 'price', 'total':True},
            0 : {'name': 'product', 'total':False}}

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total': False,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict,
                        'position': 1},
                    {
                        'type': 'text',
                        'section': 'body',
                        'position': 0,
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'position': 0,
                        'src': css_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 1,
                        'src': jsc_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 2,
                        'src': jquery_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 3,
                        'src': jsc_fun_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_javascript_totals(self):
        """Regression test for making a robust html page. Pass in a table
            element from a dictionary, css style, javascript source,
            and enable checkbox column as well as constant totals.
            This table should be sortable with a checkbox column that
            does selected totals"""

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_javascript_totals.html')
        reg_uri = os.path.join(
                REGRESSION_DATA, 'regres_html_test_javascript_totals.html')
        css_uri = '../reporting_data/table_style.css'
        jsc_uri = '../reporting_data/sorttable.js'
        jquery_uri = '../reporting_data/jquery-1.10.2.min.js'
        jsc_fun_uri = '../reporting_data/total_functions.js'

        sample_dict = {
                    0: {'date':'13', 'price':'1', 'product':'chips'},
                    1: {'date':'3', 'price':'2', 'product':'peanuts'},
                    2: {'date':'5', 'price':'3', 'product':'mints'}
                }

        columns = {
            1 : {'name': 'date', 'total':False},
            2 : {'name': 'price', 'total':True},
            0 : {'name': 'product', 'total':False}}

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total':True,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict,
                        'position': 1},
                    {
                        'type': 'text',
                        'section': 'body',
                        'position': 0,
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'position': 0,
                        'src': css_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 1,
                        'src': jsc_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 2,
                        'src': jquery_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 3,
                        'src': jsc_fun_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_multiple_tables(self):
        """Regression test for making a html page with multiple tables.
        """

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_multi_tables.html')
        reg_uri = os.path.join(
                REGRESSION_DATA, 'regres_html_test_multi_tables.html')
        css_uri = '../reporting_data/table_style.css'
        jsc_uri = '../reporting_data/sorttable.js'
        jquery_uri = '../reporting_data/jquery-1.10.2.min.js'
        jsc_fun_uri = '../reporting_data/total_functions.js'
        csv_uri = os.path.join(REPORTING_DATA, 'csv_test.csv')

        sample_dict = {
                    0: {'date':'13', 'price':'1.5', 'product':'chips'},
                    1: {'date':'3', 'price':'2.25', 'product':'peanuts'},
                    2: {'date':'5', 'price':'3.2', 'product':'mints'}
                }

        columns = {
            1 : {'name': 'date', 'total':False},
            2 : {'name': 'price', 'total':True},
            0 : {'name': 'product', 'total':False}}

        columns_csv = {
            0 : {'name': 'ws_id', 'total':False},
            1 : {'name': 'precip_mn', 'total':False},
            2 : {'name': 'wyield_mn', 'total':False},
            3 : {'name': 'wyield_vol', 'total':True}}

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total':True,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict,
                        'position': 1},
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total':True,
                        'data_type':'csv',
                        'columns':columns_csv,
                        'key':'ws_id',
                        'data': csv_uri,
                        'position': 2},
                    {
                        'type': 'text',
                        'section': 'body',
                        'position': 0,
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'position': 0,
                        'src': css_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 1,
                        'src': jsc_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 2,
                        'src': jquery_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'position': 3,
                        'src': jsc_fun_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)
