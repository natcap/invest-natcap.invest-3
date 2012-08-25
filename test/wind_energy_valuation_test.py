"""URI level tests for the wind_energy valuation module"""

import os, sys
from osgeo import gdal
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_valuation
import invest_test_core

class TestWindEnergyValuation(unittest.TestCase):
    def test_wind_energy_valuation(self):
        """Doc String"""

        # start making up some tests
