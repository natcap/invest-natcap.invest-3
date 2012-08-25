"""URI level tests for the wind_energy biophysical module"""

import os, sys
from osgeo import gdal
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_biophysical
import invest_test_core

class TestWindEnergyBiophysical(unittest.TestCase):
    def test_wind_energy_biophysical(self):
        """Doc String"""

        # start making up some tests
