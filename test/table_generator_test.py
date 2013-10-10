"""Unit Tests For Table Generator Module"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest
import invest_natcap.testing

from invest_natcap import table_generator
import invest_test_core

class TestTableGenerator(unittest.TestCase):
    def test_get_column_headers(self):
        """Unit test for getting the column headers from a dictionary"""
        #raise SkipTest
        sample_dict = {
                'col_1' : {'id': 0},
                'col_2' : {'id': 2},
                'col_3' : {'id': 1}}

        expected_result = ['col_1', 'col_3', 'col_2']

        col_headers = table_generator.get_column_headers(sample_dict)

        self.assertEqual(expected_result, col_headers)
    
    def test_get_column_headers_robust(self):
        """Unit test for getting the column headers from a dictionary"""
        #raise SkipTest
        sample_dict = {
                'date' : {'id': 1, 'time':'day'},
                'price' : {'id': 6, 'price':'expensive'},
                'product' : {'id': 0, 'product':'chips'},
                'comments' : {'id': 2, 'comment':'bad product'}}

        expected_result = ['product', 'date', 'comments', 'price']

        col_headers = table_generator.get_column_headers(sample_dict)

        self.assertEqual(expected_result, col_headers)

    def test_generate_table(self):
        """Unit test for creating a table from a dictionary as a string
            representing html"""
        #raise SkipTest
        sample_dict = {
                'cols':{
                    'date' : {'id': 1, 'time':'day'},
                    'price' : {'id': 6, 'price':'expensive'},
                    'product' : {'id': 0, 'product':'chips'}},
                'rows':{
                    0: {'date':'9/13', 'price':'expensive', 'product':'chips'},
                    1: {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                    2: {'date':'5/12', 'price':'moderate', 'product':'mints'}}
                }
        expected_result = ['product', 'date', 'comments', 'price']

        col_headers = table_generator.get_column_headers(sample_dict)

        self.assertEqual(expected_result, col_headers)
