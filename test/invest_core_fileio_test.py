import unittest
from csv import DictReader
import invest_natcap.invest_core.fileio
import os 

GUILDS_URI = './invest-data/test/data/iui/Guild.csv'
TEST_DIR = './invest-data/test/data/iui/'

class CSVDriverTest(unittest.TestCase):
    def setUp(self):
        self.driver = invest_natcap.invest_core.fileio.CSVDriver(GUILDS_URI)

    def test_get_file_object(self):
        """Assert for CSVDriver that the class of the CSVDriver underlying object"""
        file_object = self.driver.get_file_object()
        is_instance_of_csv = isinstance(file_object, DictReader)
        self.assertEqual(True, is_instance_of_csv)

    def test_get_fieldnames(self):
        """Assert for CSVDriver that the fieldnames of the driver's table"""
        reg_fieldnames = ['species', 'NS_cavity', 'NS_ground', 'FS_spring',
                          'FS_summer', 'Alpha']

        fieldnames = self.driver.get_fieldnames()
        self.assertEqual(reg_fieldnames, fieldnames)

    def test_read_table(self):
        """Assert for CSVDriver that the table read by the driver"""
        reg_table = [{'FS_summer': 0.5, 'FS_spring': 0.5, 'Alpha': 500,
                      'NS_cavity': 1, 'NS_ground': 1, 'species': 'Apis'},
                     {'FS_summer': 0.6, 'FS_spring': 0.4, 'Alpha': 1500,
                      'NS_cavity': 1, 'NS_ground': 0, 'species': 'Bombus'}]
        table = self.driver.read_table()
        self.assertEqual(table, reg_table)

    def test_write_table(self):
        """Assert for CSVDriver that that we can write correctly to a CSV"""
        orig_table = self.driver.read_table()

        # Build a new uri and write the table to this new uri
        new_uri = TEST_DIR + 'test_csv.csv'
        self.driver.write_table(orig_table, uri=new_uri)

        # Open a new instance of CSVDriver for this new table and check it to
        # ensure it's the same as the original table.
        new_driver = invest_natcap.invest_core.fileio.CSVDriver(new_uri)
        new_table = new_driver.read_table()
        self.assertEqual(orig_table, new_table)

        # Cleanup: remove the new table on disk.
        os.remove(new_uri)

class TableHandlerTest(unittest.TestCase):
    def setUp(self):
        self.handler = invest_natcap.invest_core.fileio.TableHandler(GUILDS_URI)

    def test_get_table(self):
        """Assert the functionality of get_table()"""
        reg_table = [{'fs_summer': 0.5, 'fs_spring': 0.5, 'alpha': 500,
                      'ns_cavity': 1, 'ns_ground': 1, 'species': 'Apis'},
                     {'fs_summer': 0.6, 'fs_spring': 0.4, 'alpha': 1500,
                      'ns_cavity': 1, 'ns_ground': 0, 'species': 'Bombus'}]
        self.assertEqual(self.handler.get_table(), reg_table)

    def test_set_field_mask_front(self):
        """Assert the functionality of set_field_mask() (front trim)"""
        reg_table = [{'summer': 0.5, 'spring': 0.5, 'alpha': 500,
                      'ns_cavity': 1, 'ns_ground': 1, 'species': 'Apis'},
                     {'summer': 0.6, 'spring': 0.4, 'alpha': 1500,
                      'ns_cavity': 1, 'ns_ground': 0, 'species': 'Bombus'}]
        self.handler.set_field_mask('^fs_', 3)
        self.assertEqual(self.handler.get_table(), reg_table)

    def test_set_field_mask_back(self):
        """Assert the functionality of set_field_mask() (back trim)"""
        reg_table = [{'fs_summer': 0.5, 'fs_spring': 0.5, 'alpha': 500,
                      'ns_cavity': 1, 'ns': 1, 'species': 'Apis'},
                     {'fs_summer': 0.6, 'fs_spring': 0.4, 'alpha': 1500,
                      'ns_cavity': 1, 'ns': 0, 'species': 'Bombus'}]
        self.handler.set_field_mask('ns_ground', 7, 'back')
        self.assertEqual(self.handler.get_table(), reg_table)

    def test_get_fieldnames_orig(self):
        """Assert the functionality of get_fieldnames() (original case)"""
        fieldnames = self.handler.get_fieldnames('orig')
        reg_fieldnames = ['species', 'NS_cavity', 'NS_ground', 'FS_spring',
            'FS_summer', 'Alpha']
        self.assertEqual(fieldnames, reg_fieldnames)

    def test_get_fieldnames_lower(self):
        """Assert the functionality of get_fieldnames() (lowercase)"""
        fieldnames = self.handler.get_fieldnames('lower')
        reg_fieldnames = ['species', 'ns_cavity', 'ns_ground', 'fs_spring',
            'fs_summer', 'alpha']
        self.assertEqual(fieldnames, reg_fieldnames)

    def test_get_table_dictionary_key(self):
        """Assert the functionality of get_table_dictionary() (with key)"""
        reg_dict = {'Bombus': {'fs_summer': 0.6,
                               'fs_spring': 0.4,
                               'alpha': 1500,
                               'ns_cavity': 1,
                               'ns_ground': 0,
                               'species': 'Bombus'},
                    'Apis': {'fs_summer': 0.5,
                             'fs_spring': 0.5,
                             'alpha': 500,
                             'ns_cavity': 1,
                             'ns_ground': 1,
                             'species': 'Apis'}}
        test_dict = self.handler.get_table_dictionary('species')
        self.assertEqual(reg_dict, test_dict)

    def test_get_table_dictionary_nokey(self):
        """Assert the functionality of get_table_dictionary() (without key)"""
        reg_dict = {'Bombus': {'fs_summer': 0.6,
                               'fs_spring': 0.4,
                               'alpha': 1500,
                               'ns_cavity': 1,
                               'ns_ground': 0},
                    'Apis': {'fs_summer': 0.5,
                             'fs_spring': 0.5,
                             'alpha': 500,
                             'ns_cavity': 1,
                             'ns_ground': 1}}
        test_dict = self.handler.get_table_dictionary('species', False)
        self.assertEqual(reg_dict, test_dict)

    def test_get_table_row(self):
        """Assert the functionality of get_table_row()"""
        reg_row = {'fs_summer': 0.5, 'fs_spring': 0.5, 'alpha': 500,
                   'ns_cavity': 1, 'ns_ground': 1, 'species': 'Apis'}
        row = self.handler.get_table_row('fs_summer', 0.5)
        self.assertEqual(row, reg_row)

    def test_get_map(self):
        """Assert the functionality of get_map()"""
        reg_map = {'Bombus': 1500, 'Apis': 500}
        test_map = self.handler.get_map('species', 'alpha')
        self.assertEqual(test_map, reg_map)
