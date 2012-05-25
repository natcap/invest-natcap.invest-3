"""URI level tests for the aquaculture biophysical module"""

import os, sys
import unittest

from invest_natcap.finfish_aquaculture import finfish_aquaculture_valuation
import invest_test_core

class TestFinfishAquacultureValuation(unittest.TestCase):
    def test_finfish_aquaculture_valuation_smoke(self):
        """Smoke test for finfish_aquaculture_biophysical function.  Shouldn't crash with \
#zero length inputs"""

        args = {}

        #args['names']: Numeric text string (positive int or float)
        #args['f_type']:text string
        args['p_per_kg']= 2.25
        args['frac_p'] = .3
        args['discount'] = 0.000192

        finfish_aquaculture_valuation.execute(args)