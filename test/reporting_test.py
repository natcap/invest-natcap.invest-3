"""Unit Tests For Reporting Package"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest
import invest_natcap.testing

#from invest_natcap import reporting 
import invest_natcap.reporting as reporting 
from invest_natcap.reporting import table_generator
import invest_test_core

class TestReportingPackage(unittest.TestCase):
    def test_generate_html(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""
        #raise SkipTest
        
        out_dir = 'invest-data/test/data/test_out'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        output_uri = os.path.join(out_dir, 'html_test.html')

        columns = {
            'date' : {'id': 1, 'editable':False},
            'price' : {'id': 2, 'editable':False},
            'product' : {'id': 0, 'editable':True}}
        
        sample_dict = {
                    0: {'date':'9/13', 'price':'expensive', 'product':'chips'},
                    1: {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                    2: {'date':'5/12', 'price':'moderate', 'product':'mints'}
                }

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


        expected_result = ("<html><head><title>Test Title</title>"
                "<link rel=stylesheet type=text/css href=table_style.css>"
                "</head><body><table><thead><tr><th>product</th>"
                "<th>date</th><th>price</th></tr></thead>"
                "<tbody><tr><td>chips</td><td>9/13</td><td>expensive</td></tr>"
                "<tr><td>peanuts</td><td>3/13</td><td>cheap</td></tr>"
                "<tr><td>mints</td><td>5/12</td><td>moderate</td></tr>"
                "</tbody></table></body></html>")

        table_string = reporting.generate_report(report_args)

        self.assertEqual(expected_result, table_string)
    
    def test_generate_html_csv(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""
        #raise SkipTest
        
        out_dir = 'invest-data/test/data/test_out'
        data_dir = 'invest-data/test/data/reporting_data'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        output_uri = os.path.join(out_dir, 'html_test.html')
        csv_uri = os.path.join(data_dir, 'csv_test.csv')

        columns = {
            'ws_id' : {'id': 0, 'editable':False},
            'precip_mn' : {'id': 1, 'editable':False},
            'wyield_mn' : {'id': 2, 'editable':False},
            'wyield_vol' : {'id': 3, 'editable':True}}
        
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


        expected_result = ("<html><head><title>Test Title</title>"
                "<link rel=stylesheet type=text/css href=table_style.css>"
                "</head><body><table><thead><tr><th>ws_id</th>"
                "<th>precip_mn</th><th>wyield_mn</th><th>wyield_vol</th></tr></thead>"
                "<tbody><tr><td>0</td><td>1880</td><td>1070</td><td>4590</td></tr>"
                "<tr><td>1</td><td>1892</td><td>1111</td><td>9420</td></tr>"
                "<tr><td>2</td><td>1838</td><td>1010</td><td>1945</td></tr>"
                "</tbody></table></body></html>")

        table_string = reporting.generate_report(report_args)

        self.assertEqual(expected_result, table_string)
    
    def test_generate_html_shape(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""
        #raise SkipTest
        
        out_dir = 'invest-data/test/data/test_out'
        data_dir = 'invest-data/test/data/reporting_data'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        output_uri = os.path.join(out_dir, 'html_test.html')
        shape_uri = os.path.join(data_dir, 'shape_test.shp')

        columns = {
            'ws_id' : {'id': 0, 'editable':False},
            'precip_mn' : {'id': 1, 'editable':False},
            'wyield_mn' : {'id': 2, 'editable':False},
            'wyield_vol' : {'id': 3, 'editable':True}}
        
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


        expected_result = ("<html><head><title>Test Title</title>"
                "<link rel=stylesheet type=text/css href=table_style.css>"
                "</head><body><table><thead><tr><th>ws_id</th>"
                "<th>precip_mn</th><th>wyield_mn</th><th>wyield_vol</th></tr></thead>"
                "<tbody><tr><td>0</td><td>1880.0</td><td>1070.0</td><td>4590</td></tr>"
                "<tr><td>1</td><td>1892.0</td><td>1111.0</td><td>9420</td></tr>"
                "<tr><td>2</td><td>1838.0</td><td>1010.0</td><td>1945</td></tr>"
                "</tbody></table></body></html>")

        table_string = reporting.generate_report(report_args)

        self.assertEqual(expected_result, table_string)
    def test_add_head_element_link(self):
        """Unit test for adding link head elements to html file"""
        #raise SkipTest
       
        args = {'format':'link', 'src':'example_style.css'}

        expected_result = \
                '<link rel=stylesheet type=text/css href=example_style.css'

        result = reporting.add_head_element(args)

        self.assertEqual(expected_result, result)

    def test_add_head_element_script(self):
        """Unit test for adding script head elements to html file"""
        args = {'format':'script', 'src':'example_script.js'}
        #raise SkipTest

        expected_result = \
                '<script type=text/javascript src=example_script.js></script>'

        result = reporting.add_head_element(args)

        self.assertEqual(expected_result, result)

