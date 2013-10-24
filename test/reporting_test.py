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
    def test_generate_html(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""
        
        #raise SkipTest
        
        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)
        
        output_uri = os.path.join(TEST_OUT, 'html_test_dict.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_dict.html')
        
        sample_dict = {
                    0: {'date':'9/13', 'price':'expensive', 'product':'chips'},
                    1: {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                    2: {'date':'5/12', 'price':'moderate', 'product':'mints'}
                }

        columns = {
            1 : {'name': 'date', 'editable':False},
            2 : {'name': 'price', 'editable':False},
            0 : {'name': 'product', 'editable':True}}
        
        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
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
                        'src': 'table_style.css'}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)
    
    def test_generate_html_csv(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""

        #raise SkipTest
        
        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)
        
        output_uri = os.path.join(TEST_OUT, 'html_test_csv.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_csv.html')
        csv_uri = os.path.join(REPORTING_DATA, 'csv_test.csv')

        columns = {
            0 : {'name': 'ws_id', 'editable':False},
            1 : {'name': 'precip_mn', 'editable':False},
            2 : {'name': 'wyield_mn', 'editable':False},
            3 : {'name': 'wyield_vol', 'editable':True}}
        
        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
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
                        'src': 'table_style.css'}
                    ],
                'out_uri': output_uri}
        
        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)
    
    def test_generate_html_shape(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""
        
        #raise SkipTest
        
        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)
        
        output_uri = os.path.join(TEST_OUT, 'html_test_shp.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_shp.html')
        shape_uri = os.path.join(REPORTING_DATA, 'shape_test.shp')

        columns = {
            0 : {'name': 'ws_id', 'editable':False},
            1 : {'name': 'precip_mn', 'editable':False},
            2 : {'name': 'wyield_mn', 'editable':False},
            3 : {'name': 'wyield_vol', 'editable':True}}
        
        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
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
                        'src': 'table_style.css'}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_robust(self):
        """Regression test for making a robust html page. Pass in a table
            element, css style, and javascript source. This table should be
            sortable"""
        
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
            1 : {'name': 'date', 'editable':False},
            2 : {'name': 'price', 'editable':False},
            0 : {'name': 'product', 'editable':True}}
        
        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict,
                        'position': 1},
                    {
                        'type': 'text',
                        'section': 'body',
                        'position': 0,
                        'text': 'Here is a sortable table!'},
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

