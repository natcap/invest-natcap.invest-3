"""This file contains test cases for classes contained within the module
invest_natcap.iui.iui_validator."""

import unittest

from invest_natcap.iui import iui_validator

TEST_DATA = 'data/'

class CheckerTester(unittest.TestCase):
    """This class defines commonly-used methods for checker classes in
    iui_validator.  Since all of the checker classes have a uniform call
    structure, we can abstract certain logic away from the actual test classes
    into this convenient superclass."""

    def check(self):
        """Call the established checker's run_checks function with
        self.validate_as as input.

        prerequisites:
            * a checker object has been created at self.checker
            * the validation dictionary has been saved at self.validate_as.

        returns a string with length > 0 if an error is found.  None or '' if
        no error is found."""

        return self.checker.run_checks(self.validate_as)

    def assertNoError(self):
        """Call self.check and assert that no error is found with the input
        dictionary.

        returns nothing"""

        error = self.check()
        if error != None:
            self.assertEqual(error, '')

    def assertError(self):
        """Call self.check and assert that an error is found with the input
        dictionary.

        returns nothing"""

        error = self.check()
        self.assertNotEqual(error, '', msg='No error message produced')
        self.assertNotEqual(error, None, msg='No error message produced')

class FileCheckerTester(CheckerTester):
    """Test the class iui_validator.FileChecker"""
    def setUp(self):
        self.validate_as = {'type': 'file',
                            'value': TEST_DATA + 'iui/text_test.txt'}
        self.checker = iui_validator.FileChecker()

    def test_uri_exists(self):
        """Assert that the FileChecker can open a file."""
        self.assertNoError()

    def test_nonexistent_uri(self):
        """Assert that the FileChecker fails if given a false URI."""
        self.validate_as['value'] += 'a'
        self.assertError()

class FolderCheckerTester(CheckerTester):
    """Test the class iui_validator.FileChecker"""
    def setUp(self):
        self.validate_as = {'type': 'folder',
                       'value': TEST_DATA}
        self.checker = iui_validator.FolderChecker()

    def test_folder_exists(self):
        """Assert that the FolderChecker can verify a folder exists."""
        self.assertNoError()

    def test_not_folder(self):
        """Assert that the FolderChecker fails if given a false URI."""
        self.validate_as['value'] += 'a'
        self.assertError()

class GDALCheckerTester(CheckerTester):
    """Test the class iui_validate.GDALChecker"""
    def setUp(self):
        self.validate_as = {'type': 'GDAL',
                            'value': TEST_DATA +
                            'base_data/terrestrial/lulc_samp_cur'}
        self.checker = iui_validator.GDALChecker()

    def test_opens(self):
        """Assert that GDALChecker can open a file."""
        self.assertNoError()

    def test_not_exists(self):
        """Assert that GDALChecker fails if given a bad URI"""
        self.validate_as['value'] += 'aaa'
        self.assertError()

class OGRCheckerTester(CheckerTester):
    """Test the class iui_validator.OGRChecker"""
    def setUp(self):
        self.validate_as = {'type':'OGR',
                            'value':TEST_DATA +
                            '/wave_energy_data/samp_input/AOI_WCVI.shp'}
        self.checker = iui_validator.OGRChecker()

    def test_file_layers(self):
        """Assert tha OGRChecker can validate layer restrictions."""
        layer = {'name': {'inheritFrom': 'file'}}
        self.validate_as['layers'] = [layer]

        incremental_additions = [('name', {'inheritFrom': 'file'}),
                                 ('type', 'polygons'),
                                 ('projection', 'Transverse_Mercator'),
                                 ('datum', 'WGS_1984')]

        for key, value in incremental_additions:
            self.validate_as['layers'][0][key] = value
            self.assertNoError()

    def test_fields_exist(self):
        """Assert that OGRChecker can validate that fields exist."""
        updates = {'layers': [{'name': 'harv_samp_cur'}],
                   'value': TEST_DATA + '/carbon/input/harv_samp_cur.shp',
                   'fieldsExist': ['Start_date', 'Cut_cur', 'BCEF_cur']}
        self.validate_as.update(updates)
        self.assertNoError()

        self.validate_as['fieldsExist'].append('nonexistent_field')
        self.assertError()

class DBFCheckerTester(CheckerTester):
        """Test the class iui_validator.DBFChecker"""
        def setUp(self):
            self.validate_as = {'type': 'DBF',
                                'value': TEST_DATA +
                                '/carbon/input/carbon_pools_samp.dbf',
                                'fieldsExist': []}
            self.checker = iui_validator.DBFChecker()

        def test_fields_exist(self):
            """Assert that DBFChecker can verify fields exist."""
            self.validate_as['fieldsExist'] = ['C_above', 'LULC', 'C_soil']
            self.assertNoError()

        def test_nonexistent_fields(self):
            """Assert that DBFChecker fails if a bad fieldname is provided."""
            self.validate_as['fieldsExist'].append('nonexistent_field')
            self.assertError()

        def test_restrictions(self):
            """Assert that DBFchecker can handle per-field restrictions."""
            regexp_int = {'pattern': '[0-9]*'}
            date_regexp = {'pattern': '[0-9]{4}|0'}
            num_restriction = {'field': 'BCEF_cur',
                               'validateAs': {'type': 'number',
                                              'allowedValues': regexp_int}}
            const_restriction = {'field': 'BCEF_cur',
                                 'validateAs': {'type': 'number',
                                                'greaterThan': 0,
                                                'gteq': 1,
                                                'lteq': 2,
                                                'lessThan': 2}}
            field_restriction = {'field': 'C_den_cur',
                                 'validateAs': {'type': 'number',
                                                'lessThan': 'BCEF_cur'}}
            str_restriction = {'field': 'Start_date',
                               'validateAs': {'type': 'string',
                                              'allowedValues': date_regexp}}

            self.validate_as['restrictions'] = [num_restriction,
                                                const_restriction,
                                                field_restriction,
                                                str_restriction]
            self.assertNoError()

class CSVCheckerTester(CheckerTester):
        """Test the class iui_validator.CSVChecker"""
        def setUp(self):
            self.validate_as = {'type': 'CSV',
                                'value': TEST_DATA +
                                '/wave_energy_data/samp_input/Machine_PelamisParamCSV.csv',
                                'fieldsExist': []}
            self.checker = iui_validator.CSVChecker()

        def test_fields_exist(self):
            """Assert that CSVChecker can verify fields exist"""
            self.validate_as['fieldsExist'] = ['NAME', 'VALUE', 'NOTE']
            self.assertNoError()

        def test_nonexistent_fields(self):
            """Assert that CSVChecker fails fails if given a bad fieldname."""
            self.validate_as['fieldsExist'].append('nonexistent_field')
            self.assertError()

        def test_restrictions(self):
            """Assert that CSVChecker can validate per-field restrictions."""
            regexp_name = {'pattern': '[a-z]+', 'flag': 'ignoreCase'}
            regexp_float = {'pattern': '[0-9]*\\.?[0-9]+'}
            num_restriction = {'field': 'VALUE',
                               'validateAs': {'type': 'number',
                                              'allowedValues': regexp_float}}
            const_restriction = {'field': 'VALUE',
                                 'validateAs': {'type': 'number',
                                                'greaterThan': 0}}
            str_restriction = {'field': 'NAME',
                               'validateAs': {'type': 'string',
                                              'allowedValues': regexp_name}}

            self.validate_as['restrictions'] = [num_restriction,
                                                const_restriction,
                                                str_restriction]
            self.assertNoError()

class PrimitiveCheckerTester(CheckerTester):
    """Test the class iui_validator.PrimitiveChecker."""
    def setUp(self):
        self.validate_as = {'type': 'string',
                            'allowedValues': {'pattern': '[a-z]+'}}
        self.checker = iui_validator.PrimitiveChecker()

    def test_value(self):
        """Assert that PrimitiveChecker can validate a regexp."""
        self.validate_as['value'] = 'aaaabasd'
        self.assertNoError()

    def test_value_not_allowed(self):
        """Assert that PrimitiveChecker fails on a non-matching string."""
        self.validate_as['value'] = '12341aasd'
        self.assertError()

    def test_ignore_case_flag(self):
        """Assert that PrimitiveChecker recognizes 'ignoreCase' flag."""
        self.validate_as['value'] = 'AsdAdnS'
        self.validate_as['allowedValues']['flag'] = 'ignoreCase'
        self.assertNoError()

    def test_dot_all_flag(self):
        """Assert that PrimitiveChecker regognizes 'dotAll' flag."""
        self.validate_as['value'] = 'asda\n'
        self.validate_as['allowedValues']['flag'] = 'dotAll'
        self.validate_as['allowedValues']['pattern'] = '[a-z]+.+'
        self.assertNoError()

class NumberCheckerTester(CheckerTester):
    """Test the class iui_validator.NumberChecker"""
    def setUp(self):
        self.validate_as = {'type':'number',
                            'value': 5}
        self.checker = iui_validator.NumberChecker()

    def test_gt(self):
        """Assert that NumberChecker validates 'greaterThan'"""
        self.validate_as['greaterThan'] = 2
        self.assertNoError()

    def test_lt(self):
        """Assert that NumberChecker validates 'lessThan'"""
        self.validate_as['lessThan'] = 7
        self.assertNoError()

    def test_gteq(self):
        """Assert that NumberChecker validates 'gteq'"""
        self.validate_as['gteq'] = 5
        self.assertNoError()

    def test_lteq(self):
        """Assert that NumberChecker validates 'lteq'"""
        self.validate_as['lteq'] = 5
        self.assertNoError()

    def test_all(self):
        """Assert that NumberChecker validates combinations of flags."""
        self.validate_as['lteq'] = 5
        self.validate_as['lessThan'] = 6
        self.validate_as['gteq'] = 5
        self.validate_as['greaterThan'] = 4
        self.assertNoError()


