import unittest

class InvestCoreInitTest(unittest.TestCase):
    def test_is_release(self):
        # import invest_natcap here because importing it with all the other
        # import statements causes an exception to be thrown when I try to
        # access its __version__attribute below.
        import invest_natcap

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

