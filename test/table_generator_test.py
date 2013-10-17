"""Unit Tests For Table Generator Module"""

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

class TestTableGenerator(unittest.TestCase):
    def test_get_column_headers(self):
        """Unit test for getting the column headers from a dictionary"""
        raise SkipTest
        sample_dict = {
                'col_1' : {'id': 0},
                'col_2' : {'id': 2},
                'col_3' : {'id': 1}}

        expected_result = ['col_1', 'col_3', 'col_2']

        col_headers = table_generator.get_column_headers(sample_dict)

        self.assertEqual(expected_result, col_headers)
    
    def test_get_column_headers_robust(self):
        """Unit test for getting the column headers from a more complicated
            dictionary setup"""
        raise SkipTest
        sample_dict = {
                'date' : {'id': 1, 'time':'day'},
                'price' : {'id': 6, 'price':'expensive'},
                'product' : {'id': 0, 'product':'chips'},
                'comments' : {'id': 2, 'comment':'bad product'}}

        expected_result = ['product', 'date', 'comments', 'price']

        col_headers = table_generator.get_column_headers(sample_dict)

        self.assertEqual(expected_result, col_headers)
    
    def test_get_row_data(self):
        """Unit test for getting the row data from a dictionary"""
        raise SkipTest
        sample_dict = {
                    0: {'col_1':'value_1', 'col_2':'value_4'},
                    1: {'col_1':'value_2', 'col_2':'value_5'},
                    2: {'col_1':'value_3', 'col_2':'value_6'}}

        col_headers = ['col_1', 'col_2']

        expected_result = [
                ['value_1', 'value_4'],
                ['value_2', 'value_5'],
                ['value_3', 'value_6']]

        row_data = table_generator.get_row_data(sample_dict, col_headers)

        self.assertEqual(expected_result, row_data)
    
    def test_get_row_data_robust(self):
        """Unit test for getting the row data from a more complicated
            dictionary"""
        raise SkipTest
        sample_dict = {
                3: {'date':'09-13', 'price':.54, 'product':'chips'},
                0: {'date':'08-14', 'price':23.4, 'product':'mustard'},
                1: {'date':'04-13', 'price':100, 'product':'hats'},
                2: {'date':'06-12', 'price':56.50, 'product':'gloves'}}

        col_headers = ['product', 'price', 'date']

        expected_result = [
                ['mustard', 23.4, '08-14'],
                ['hats', 100, '04-13'],
                ['gloves', 56.50, '06-12'],
                ['chips', .54, '09-13']]

        row_data = table_generator.get_row_data(sample_dict, col_headers)

        self.assertEqual(expected_result, row_data)

    def test_generate_table(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""
        raise SkipTest
        sample_dict = {
                'cols':{
                    'date' : {'id': 1, 'time':'day'},
                    'price' : {'id': 2, 'price':'expensive'},
                    'product' : {'id': 0, 'product':'chips'}},
                'rows':{
                    0: {'date':'9/13', 'price':'expensive', 'product':'chips'},
                    1: {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                    2: {'date':'5/12', 'price':'moderate', 'product':'mints'}}
                }

        expected_result = ("<table><thead><tr><th>product</th>"
                "<th>date</th><th>price</th></tr></thead>"
                "<tbody><tr><td>chips</td><td>9/13</td><td>expensive</td></tr>"
                "<tr><td>peanuts</td><td>3/13</td><td>cheap</td></tr>"
                "<tr><td>mints</td><td>5/12</td><td>moderate</td></tr>"
                "</tbody></table>")

        table_string = table_generator.generate_table(sample_dict)

        self.assertEqual(expected_result, table_string)
    
    def test_generate_table_attributes(self):
        """Unit test for creating a table from a dictionary as a string
            representing html using attributes"""
        raise SkipTest
        sample_dict = {
                'cols':{
                    'date' : {'id': 1, 'time':'day'},
                    'price' : {'id': 2, 'price':'expensive'},
                    'product' : {'id': 0, 'product':'chips'}},
                'rows':{
                    0: {'date':'9/13', 'price':'expensive', 'product':'chips'},
                    1: {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                    2: {'date':'5/12', 'price':'moderate', 'product':'mints'}}
                }

        attributes= {'class':'sortable', 'border':'1'}

        expected_result = ("<table border=1 class=sortable><thead><tr>"
                "<th>product</th><th>date</th><th>price</th></tr></thead>"
                "<tbody><tr><td>chips</td><td>9/13</td><td>expensive</td></tr>"
                "<tr><td>peanuts</td><td>3/13</td><td>cheap</td></tr>"
                "<tr><td>mints</td><td>5/12</td><td>moderate</td></tr>"
                "</tbody></table>")

        table_string = table_generator.generate_table(sample_dict, attributes)

        self.assertEqual(expected_result, table_string)
    
    def test_generate_html(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""
        raise SkipTest
        
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
                        'data_type':'CSV',
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
