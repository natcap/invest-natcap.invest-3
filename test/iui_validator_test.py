import unittest

from invest_natcap.iui import iui_validator

TEST_DATA = 'data/'

class CheckerTester(unittest.TestCase):
    def check(self):
        return self.checker.run_checks(self.validate_as)

    def assertNoError(self):
        error = self.check()
        if error != None:
            self.assertEqual(error, '')

    def assertError(self):
        error = self.check()
        self.assertNotEqual(error, '')

class FileCheckerTester(CheckerTester):
    def setUp(self):
        self.validate_as = {'type': 'file',
                       'value': TEST_DATA +
                       '/base_data/terrestrial/lulc_samp_cur/hdr.adf'}
        self.checker = iui_validator.FileChecker()

    def test_uri_exists(self):
        self.assertNoError()

    def test_nonexistent_uri(self):
        #this should fail, so we check that an error message is there.
        self.validate_as['value'] += 'a'
        self.assertError()


class FolderCheckerTester(CheckerTester):
    def setUp(self):
        self.validate_as = {'type': 'folder',
                       'value': TEST_DATA}
        self.checker = iui_validator.FolderChecker()

    def test_folder_exists(self):
        self.assertNoError()

    def test_not_folder(self):
        self.assertError()


class OGRCheckerTester(CheckerTester):
    def setUp(self):
        self.validate_as = {'type':'OGR',
                            'value':TEST_DATA +
                            '/wave_energy_data/samp_input/AOI_WCVI.shp'}
        self.checker = iui_validator.OGRChecker()

    def test_file_layers(self):
        layer = {'name': {'inheritFrom': 'file'}}
        self.validate_as['layers'] = [layer]

        incremental_additions = [('name', {'inheritFrom': 'file'}),
                                 ('type', 'polygons'),
                                 ('projection', 'Transverse_Mercator')]

        for key, value in incremental_additions:
            self.validate_as['layers'][0][key] = value
            self.assertNoError()

    def test_fields_exist(self):
        updates = {'layers': [{'name': 'harv_samp_cur'}],
                   'value': TEST_DATA + '/carbon/input/harv_samp_cur.shp',
                   'fieldsExist': ['Start_date', 'Cut_cur', 'BCEF_cur']}
        self.validate_as.update(updates)
        self.assertNoError()

        self.validate_as['fieldsExist'].append('nonexistent_field')
        self.assertError()

class DBFCheckerTester(CheckerTester):
        def setUp(self):
            self.validate_as = {'type': 'DBF',
                                'value': TEST_DATA +
                                '/carbon/input/carbon_pools_samp.dbf',
                                'fieldsExist': []}
            self.checker = iui_validator.DBFChecker()

        def test_fields_exist(self):
            self.validate_as['fieldsExist'] = ['C_above', 'LULC', 'C_soil']
            self.assertNoError()

        def test_nonexistent_fields(self):
            self.validate_as['fieldsExist'].append('nonexistent_field')
            self.assertError()

        def test_restrictions(self):
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






