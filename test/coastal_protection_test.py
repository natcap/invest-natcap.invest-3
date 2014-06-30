from __future__ import print_function

import unittest
import logging
import os
import math
import numpy as np
import random
import csv
import shutil

from osgeo import gdal
from osgeo import ogr
from nose.plugins.skip import SkipTest

import invest_test_core
from invest_natcap import raster_utils
from invest_natcap.coastal_protection \
    import coastal_protection
from invest_natcap.coastal_protection \
    import coastal_protection_core


LOGGER = logging.getLogger('coastal_protection_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestCoastalProtection(unittest.TestCase):
    """Main testing class for the coastal protection tests"""
    
    def setUp(self):
        """ Set up function
        """
        pass

    def test_functionality(self):
        """ test function docstring here.
            
            Inputs:

            Outputs:
        """
        pass

    def tare_down(self):
        """ Clean up code."""
        # Do nothing for now 
        pass
