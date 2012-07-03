import unittest
import invest_natcap.invest_core.fileio

GUILDS_URI = './data/iui/Guild.csv'

class CSVDriverTest(unittest.TestCase):
    def setUp(self):
        print ''
        self.driver = invest_natcap.invest_core.fileio.CSVDriver(GUILDS_URI)

    def test_get_file_object(self):
        print self.driver.get_file_object()

    def test_get_fieldnames(self):
        print self.driver.get_fieldnames()

    def test_read_table(self):
        print self.driver.read_table()

class TableHandlerTest(unittest.TestCase):
    def setUp(self):
        self.handler = invest_natcap.invest_core.fileio.TableHandler(GUILDS_URI)

    def test_get_table(self):
        """Assert the functionality of get_table()"""
        reg_table = [{'fs_summer': '0.5', 'fs_spring': '0.5', 'alpha': '500',
                      'ns_cavity': '1', 'ns_ground': '1', 'species': 'Apis'},
                     {'fs_summer': '0.6', 'fs_spring': '0.4', 'alpha': '1500',
                      'ns_cavity': '1', 'ns_ground': '0', 'species': 'Bombus'}]
        self.assertEqual(self.handler.get_table(), reg_table)

    def test_set_field_mask(self):
        """Assert the functionality of set_field_mask()"""
        reg_table = [{'summer': '0.5', 'spring': '0.5', 'alpha': '500',
                      'ns_cavity': '1', 'ns_ground': '1', 'species': 'Apis'},
                     {'summer': '0.6', 'spring': '0.4', 'alpha': '1500',
                      'ns_cavity': '1', 'ns_ground': '0', 'species': 'Bombus'}]
        self.handler.set_field_mask('^fs_', 3)
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
        reg_dict = {'Bombus': {'fs_summer': '0.6',
                               'fs_spring': '0.4',
                               'alpha': '1500',
                               'ns_cavity': '1',
                               'ns_ground': '0',
                               'species': 'Bombus'},
                    'Apis': {'fs_summer': '0.5',
                             'fs_spring': '0.5',
                             'alpha': '500',
                             'ns_cavity': '1',
                             'ns_ground': '1',
                             'species': 'Apis'}}
        test_dict = self.handler.get_table_dictionary('species')
        self.assertEqual(reg_dict, test_dict)

    def test_get_table_dictionary_nokey(self):
        """Assert the functionality of get_table_dictionary() (without key)"""
        reg_dict = {'Bombus': {'fs_summer': '0.6',
                               'fs_spring': '0.4',
                               'alpha': '1500',
                               'ns_cavity': '1',
                               'ns_ground': '0'},
                    'Apis': {'fs_summer': '0.5',
                             'fs_spring': '0.5',
                             'alpha': '500',
                             'ns_cavity': '1',
                             'ns_ground': '1'}}
        test_dict = self.handler.get_table_dictionary('species', False)
        self.assertEqual(reg_dict, test_dict)

    def test_get_table_row(self):
        """Assert the functionality of get_table_row()"""
        reg_row = {'fs_summer': '0.5', 'fs_spring': '0.5', 'alpha': '500',
                   'ns_cavity': '1', 'ns_ground': '1', 'species': 'Apis'}
        row = self.handler.get_table_row('fs_summer', '0.5')
        self.assertEqual(row, reg_row)

    def test_get_map(self):
        """Assert the functionality of get_map()"""
        reg_map = {'Bombus': '1500', 'Apis': '500'}
        test_map = self.handler.get_map('species', 'alpha')
        self.assertEqual(test_map, reg_map)
