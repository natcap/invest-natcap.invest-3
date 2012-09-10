import os, sys
import unittest
import random
import logging
import csv

from osgeo import ogr, gdal, osr
from osgeo.gdalconst import *
import numpy as np
from nose.plugins.skip import SkipTest

from invest_natcap import raster_utils
from invest_natcap.wind_energy import wind_energy_core
import invest_test_core

LOGGER = logging.getLogger('wind_energy_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestWindEnergyCore(unittest.TestCase):
    def test_wind_energy_core(self):
        # start testing
