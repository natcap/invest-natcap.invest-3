"""URI level tests for the aquaculture core module"""

import os, sys
import unittest

from invest_natcap.finfish_aquaculture import finfish_aquaculture_core
import invest_test_core

class TestFinfishAquacultureCore(unittest.TestCase):
    def test_finfish_aquaculture_core_smoke(self):
        """Smoke test for finfish_aquaculture_core."""

        #TBH, I'm unsure about what core tests should be, since we seem to just call
        #it from biophysical when it's done packing