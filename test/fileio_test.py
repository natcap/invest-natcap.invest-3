"""This test file contains unittests for invest_natcap.iui.fileio."""

import unittest

from invest_natcap.iui import fileio

TEST_DATA = 'data/'

class CSVHandlerTest(unittest.TestCase):
    # This is a unittest to test the table handling functionality of the
    # CSVHandler class.
    def setUp(self):
        # If we haven't already declared what self.input_file should be (as
        # happens in subclasses of CSVHandlerTest), define it here.
        if not hasattr(self, 'input_file'):
            self.input_file = './data/iui/Guild.csv'

        # Open the table handler.
        self.handler = fileio.find_handler(self.input_file)

    def test_get_fieldnames(self):
        #Assert fieldnames found in self.file match expected fieldnames
        expected_fieldnames = ['species', 'ns_cavity', 'ns_ground', 'fs_spring',
            'fs_summer', 'alpha']

        fieldnames = self.handler.get_fieldnames()
        for name, exp_name in zip(fieldnames, expected_fieldnames):
            self.assertEqual(name, exp_name)

    def test_get_file_object(self):
        # Assert that the file object is not None.  The better way to test this
        # would be to check the python object type ... don't yet know a
        # generalized way to do this.
        file_obj = self.handler.get_file_object()
        self.assertNotEqual(file_obj, None, 'File object found to be None')

    def test_get_map(self):
        table_map = self.handler.get_map('species', 'ns_ground')

        self.assertEqual(issubclass(table_map.__class__, dict), True,
            'get_map() does not return a dict.')

        expected_map = {'Apis': 1.0,
                        'Bombus': 0.0}
        for species, ns_ground in table_map.iteritems():
            self.assertEqual(species in expected_map, True,
                'Species %s not expected' % species)
            self.assertEqual(expected_map[species], ns_ground)

class DBFHandlerTest(CSVHandlerTest):
    """This is a unittest to test the table handling functionality of the
    DBFHandler class."""
    def setUp(self):
        self.input_file = './data/iui/Guild.dbf'
        CSVHandlerTest.setUp(self)

