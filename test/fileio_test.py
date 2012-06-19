"""This test file contains unittests for invest_natcap.iui.fileio."""

import unittest

from invest_natcap.iui import fileio

TEST_DATA = 'data/'

class CSVHandlerTest(unittest.TestCase):
    def setUp(self):
        if not hasattr(self, 'input_file'):
            self.input_file = './data/iui/Guild.csv'
        self.handler = fileio.find_handler(self.input_file)

    def test_get_fieldnames(self):
        expected_fieldnames = ['species', 'ns_cavity', 'ns_ground', 'fs_spring',
            'fs_summer', 'alpha']

        fieldnames = self.handler.get_fieldnames()
        for name, exp_name in zip(fieldnames, expected_fieldnames):
            self.assertEqual(name, exp_name)

class DBFHandlerTest(CSVHandlerTest):
    def setUp(self):
        self.input_file = './data/iui/Guild.dbf'
        CSVHandlerTest.setUp(self)

