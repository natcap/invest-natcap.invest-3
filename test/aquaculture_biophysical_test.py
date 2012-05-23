"""URI level tests for the aquaculture biophysical module"""

import os, sys
import unittest

from invest_natcap.aquaculture import aquaculture_biophysical
import invest_test_core

class TestAquacultureBiophysical(unittest.TestCase):
    def test_aquaculture_biophysical_smoke(self):
        """Smoke test for aquaculture_biophysical function.  Shouldn't crash with \
#zero length inputs"""

        args = {}
        

        aquaculture_biophysical.execute(args)
