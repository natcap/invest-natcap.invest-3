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

class URICheckerTester(CheckerTester):
    def setUp(self):
        self.validate_as = {'type': 'file',
                       'value': TEST_DATA +
                       '/base_data/terrestrial/lulc_samp_cur/hdr.adf'}
        self.checker = iui_validator.URIChecker()

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
