import unittest

from invest_natcap.iui import iui_validator

TEST_DATA = 'data/'

class CheckerTester(unittest.TestCase):
    def assertError(self, error):
        if error != None:
            self.assertEqual(error, '')

    def assertNotError(self, error):
        if error != None:
            self.assertNotEqual(error, '')

class FileCheckerTester(CheckerTester):
    def setUp(self):
        self.validate_as = {'type': 'file',
                       'value': TEST_DATA +
                       '/base_data/terrestrial/lulc_samp_cur/hdr.adf'}
        self.checker = iui_validator.FileChecker()

    def test_uri_exists(self):
        error = self.checker.run_checks(self.validate_as)
        self.assertError(error)

    def test_nonexistent_uri(self):
        #this should fail, so we check that an error message is there.
        self.validate_as['value'] += 'a'
        error = self.checker.run_checks(self.validate_as)
        self.assertNotError(error)


class FolderCheckerTester(CheckerTester):
    def setUp(self):
        self.validate_as = {'type': 'folder',
                       'value': TEST_DATA}
        self.checker = iui_validator.FolderChecker()

    def test_folder_exists(self):
        error = self.checker.run_checks(self.validate_as)
        self.assertError(error)

    def test_not_folder(self):
        error = self.checker.run_checks(self.validate_as)
        self.assertNotError(error)


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
            error = self.checker.run_checks(self.validate_as)
            self.assertError(error)


