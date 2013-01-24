import unittest
import invest_natcap.iui.modelui_test

loader = unittest.TestLoader()
suite = loader.loadTestsFromModule(invest_natcap.iui.modelui_test)
unittest.TextTestRunner(verbosity=2).run(suite)

