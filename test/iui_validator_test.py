import unittest

from invest_natcap.iui import iui_validator

TEST_DATA = 'data/'

class URICheckerTester(unittest.TestCase):
    def test_uri_exists(self):
        validate_as = {'type': 'file',
                       'value': TEST_DATA +
                       '/base_data/terrestrial/lulc_samp_cur/hdr.adf'}
        checker = iui_validator.URIChecker()
        error = checker.run_checks(validate_as)
        self.assertEqual(error, '')

        #this should fail, so we check that an error message is there.
        validate_as['value'] += 'a'
        error = checker.run_checks(validate_as)
        self.assertNotEqual(error, '')
