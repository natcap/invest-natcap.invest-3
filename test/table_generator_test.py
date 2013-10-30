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
    def test_get_dictionary_values_ordered(self):
        """Unit test for getting values from a dictionary in order"""
        
        #raise SkipTest
        
        sample_dict = {
                0 : {'name': 'col_1'},
                2 : {'name': 'col_2'},
                1 : {'name': 'col_3'}}

        expected_result = ['col_1', 'col_3', 'col_2']

        col_headers = table_generator.get_dictionary_values_ordered(
                sample_dict, 'name')

        self.assertEqual(expected_result, col_headers)
    
    def test_get_dictionary_values_ordered_robust(self):
        """Unit test for getting dictionary values in order, with a non trivial
            dictionary input"""
        
        #raise SkipTest
        
        sample_dict = {
                1 : {'name': 'date', 'time':'day'},
                6 : {'name': 'price', 'price':'expensive'},
                0 : {'name': 'product', 'product':'chips'},
                2 : {'name': 'comments', 'comment':'bad product'}}

        expected_result = ['product', 'date', 'comments', 'price']

        col_headers = table_generator.get_dictionary_values_ordered(
                sample_dict, 'name')

        self.assertEqual(expected_result, col_headers)
    
    def test_get_dictionary_values_ordered_bool(self):
        """Unit test for getting dictionary values in order, with boolean
            values"""
        
        #raise SkipTest
        
        sample_dict = {
                1 : {'name': 'date', 'total':False},
                6 : {'name': 'price', 'total':True},
                0 : {'name': 'product', 'total':False},
                2 : {'name': 'comments', 'total':True}}

        expected_result = [False, False, True, True]

        tot_col = table_generator.get_dictionary_values_ordered(
                sample_dict, 'total')

        self.assertEqual(expected_result, tot_col)
    
    def test_get_row_data(self):
        """Unit test for getting the row data from a dictionary"""
        
        #raise SkipTest
        
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
        
        #raise SkipTest
        
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
        
        #raise SkipTest
        
        sample_dict = {
                'cols':{
                   1 : {'name':'date', 'total':False},
                   2 : {'name': 'price', 'total':False},
                   0 : {'name':'product', 'total':False}},
                'rows':{
                   0 : {'date':'9/13', 'price':'expensive', 'product':'chips'},
                   1 : {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                   2 : {'date':'5/12', 'price':'moderate', 'product':'mints'}},
                'checkbox':False,
                'total':False
                }

        expected_result = ("<table id=my_table><thead><tr><th>product</th>"
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
        
        #raise SkipTest
        
        sample_dict = {
                'cols':{
                    1: {'name':'date', 'total':False},
                    2: {'name': 'price', 'total':False},
                    0: {'name':'product', 'total':False}},
                'rows':{
                    0: {'date':'9/13', 'price':'expensive', 'product':'chips'},
                    1: {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                    2: {'date':'5/12', 'price':'moderate', 'product':'mints'}},
                'checkbox':False,
                'total':False
                }

        attributes= {'class':'sortable', 'border':'1'}

        expected_result = ("<table id=my_table border=1 class=sortable><thead><tr>"
                "<th>product</th><th>date</th><th>price</th></tr></thead>"
                "<tbody><tr><td>chips</td><td>9/13</td><td>expensive</td></tr>"
                "<tr><td>peanuts</td><td>3/13</td><td>cheap</td></tr>"
                "<tr><td>mints</td><td>5/12</td><td>moderate</td></tr>"
                "</tbody></table>")

        table_string = table_generator.generate_table(sample_dict, attributes)

        self.assertEqual(expected_result, table_string)
    
    def test_add_checkbox_column(self):
        """Unit test for adding a checkbox column to the table definition"""
        
        #raise SkipTest
        
        sample_dict = {
                'cols':{
                   1 : {'name':'date', 'total':False},
                   2 : {'name': 'price', 'total':True},
                   0 : {'name':'product', 'total':False}},
                'rows':{
                   0 : {'date':'9/13', 'price':'expensive', 'product':'chips'},
                   1 : {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                   2 : {'date':'5/12', 'price':'moderate', 'product':'mints'}}
                }

        expected_rows = {
                   0 : {'date':'9/13', 'price':'expensive', 'product':'chips',
                       'Select':'<input type="checkbox" name="cb" value="1">'},
                   1 : {'date':'3/13', 'price':'cheap', 'product':'peanuts',
                       'Select':'<input type="checkbox" name="cb" value="1">'},
                   2 : {'date':'5/12', 'price':'moderate', 'product':'mints',
                       'Select':'<input type="checkbox" name="cb" value="1">'}}

        expected_cols = {
                1 : {'name':'Select', 'total':False},
                2 : {'name': 'date', 'total':False},
                3 : {'name': 'price', 'total':True},
                0 : {'name':'product', 'total':False}}

        col_dict, row_dict = table_generator.add_checkbox_column(
                sample_dict['cols'], sample_dict['rows'])

        self.assertEqual(col_dict, expected_cols)
        self.assertEqual(row_dict, expected_rows)
    
    def test_add_totals_row(self):
        """Unit test for adding a totals row"""
        
        #raise SkipTest

        cols = ['product', 'shipped', 'units', 'price']
        total_cols = [False, False, True, True]

        data_class = 'totalCol'
        row_class = 'totalColumn'

        expected_result = ("<tr class=%s><td>Total</td><td>--</td>"
            "<td class=%s>--</td><td class=%s>--</td></tr>" %
            (row_class, data_class, data_class))

        totals_html = table_generator.add_totals_row(
                cols, total_cols, 'Total', row_class, data_class)

        self.assertEqual(expected_result, totals_html)
