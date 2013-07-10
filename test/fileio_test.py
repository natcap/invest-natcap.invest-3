"""This test file contains unittests for invest_natcap.iui.fileio."""

import unittest
import os

from invest_natcap.iui import fileio

TEST_DATA = 'invest-data/test/data/'

class TableTestTemplate():
    # This is a unittest to test the table handling functionality of the
    # CSVHandler class.
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
            ns_ground = float(ns_ground)
            self.assertEqual(species in expected_map, True,
                'Species %s not expected' % species)
            self.assertEqual(expected_map[species], ns_ground)

    def test_get_table_dictionary(self):
        # verify the number of rows in the dictionary.
        # Fieldnames are expected to be present, tested by test_get_fieldnames

        table_dictionary = self.handler.get_table_dictionary('species')
        self.assertEqual(len(table_dictionary), 2)

        for key, value in table_dictionary.iteritems():
            self.assertEqual(issubclass(value.__class__, dict), True,
                'The value of the table dictionary must be the row dictionary.')

    def test_get_table_row(self):
        # get_table_row should return a dictionary if it can find the requested
        # value.
        row_dict = self.handler.get_table_row('species', 'Bombus')
        self.assertEqual(issubclass(row_dict.__class__, dict), True,
            'get_table_row should return a dictionary; row with species' +
            ' \'Bombus\' should exist in the sample table.')

        # get_table_row should return None if it can't find the requested value
        empty_row_dict = self.handler.get_table_row('species', 'empty')
        self.assertEqual(empty_row_dict, None, 'get_table_row should return' +
            ' None when requesting a field or value that does not exist')

        # get_table_row should raise a KeyError when a bad fieldname is
        # provided.
        self.assertRaises(KeyError, self.handler.get_table_row,
            'does_not_exist', '')

    def test_set_field_mask(self):
        # Set a field mask to test out.
        self.handler.set_field_mask('(^ns_)|(^fs_)', trim=3)
        fieldnames = self.handler.get_fieldnames()
        expected_fieldnames = ['species', 'cavity', 'ground', 'spring',
            'summer', 'alpha']

        # Check that the field mask is applied correctly.
        for name, exp_name in zip(fieldnames, expected_fieldnames):
            self.assertEqual(name, exp_name, 'Setting a mask of (^ns_)|(^fs_)' +
                ' and a trim of 3 should have given %s, instead found %s' %
                (exp_name, name))

class CSVHandlerTest(TableTestTemplate, unittest.TestCase):
    """This is a unittest to test the table handling functionality of the
    DBFHandler class."""
    def setUp(self):
        self.input_file = './invest-data/test/data/iui/Guild.dbf'
        self.handler = fileio.find_handler(self.input_file)

class DBFHandlerTest(TableTestTemplate, unittest.TestCase):
    """This is a unittest to test the table handling functionality of the
    DBFHandler class."""
    def setUp(self):
        self.input_file = './invest-data/test/data/iui/Guild.dbf'
        self.handler = fileio.find_handler(self.input_file)

class JSONHandlerTest(unittest.TestCase):
    def setUp(self):
        self.uri = './invest-data/test/data/iui/test_resources/resources.json'
        self.handler = fileio.JSONHandler(self.uri)

    def test_get_attributes(self):
        """Get_attributes should return a dictionary of attributes with some
        entries.."""
        attributes = self.handler.get_attributes()
        self.assertNotEqual(len(attributes), 0)

        # If we give a filepath to a json file that does not exist, the
        # attributes dictionary should have no entries whatsoever.
        self.handler = fileio.JSONHandler('')
        attributes = self.handler.get_attributes()
        self.assertEqual(len(attributes), 0)

class ResourceHandlerTest(unittest.TestCase):
    def setUp(self):
        self.uri = './invest-data/test/data/iui/test_resources/'
        self.handler = fileio.ResourceHandler(self.uri)

    def test_get_icon(self):
        icon_path = self.handler.icon('application')
        icon_uri = os.sep.join(icon_path.split(os.sep)[-1:])
        self.assertEqual(icon_uri, 'test_image.png')

        # Assert keyError raised when bogus key requested.
        self.assertRaises(KeyError, self.handler.icon, 'not-present')

class ResourceManager(unittest.TestCase):
    def test_no_overrides(self):
        """Assert defaults used when necessary."""
        # Provide an overrides dir that doesn't exist, defaults should be used
        self.overrides_dir = ''
        self.manager = fileio.ResourceManager(self.overrides_dir)
        icon_path = os.sep.join(self.manager.icon('application').split(os.sep)[-1:])
        self.assertEquals(os.path.basename(icon_path), 'natcap_logo.png')

        # Once we have more entries in the default resource file, this test
        # should also verify that those entries are not overridden by the user.

    def test_overrides(self):
        """Assert overrides used when necessary."""
        self.overrides_dir = './invest-data/test/data/iui/test_resources'
        self.manager = fileio.ResourceManager(self.overrides_dir)
        icon_path = os.sep.join(self.manager.icon('application').split(os.sep)[-1:])
        default_icon_path = 'test_image.png'
        self.assertEqual(default_icon_path, icon_path)

class SaveModelRun(unittest.TestCase):
    def test_save_model_run(self):
        arguments = {
            u'a': 1,
            'b': 2,
            'c': 3,
            0: {'a': 4,
                'b': 5},
            1: [1, 2, 3, 4]
        }

        module = 'invest_natcap.pollination.pollination'
        out_file = os.path.join('invest-data/test/data', 'iui', 'model_run.txt')

        fileio.save_model_run(arguments, module, out_file)

