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
