import unittest

import invest_natcap

class InvestCoreInitTest(unittest.TestCase):
    def setUp(self):
        # Want to re-import each time here, since I may change some variables as
        # part of the test.
        invest_natcap = reload(invest_natcap)

    def test_is_release(self):
        # set the invest_version to something that should not be a release,
        # verify False is returned and reset the invest_natcap module.
        invest_natcap.__version__ = '2.4.5'
        self.assertEqual(invest_natcap.is_release(), True)
        invest_natcap = reload(invest_natcap)

        # Try the invest_version with an alpha version string.
        invest_natcap.__version__ = '2.4.5a1'
        self.assertEqual(invest_natcap.is_release(), True)
        invest_natcap = reload(invest_natcap)

        # Now provide a build ID. This should not be recognized as an actual
        # release.
        invest_natcap.__version__ = 'dev327:2.4.5 [e80e888529cd]'
        self.assertEqual(invest_natcap.is_release(), False)
        invest_natcap = reload(invest_natcap)

