from __future__ import print_function

import unittest
import logging
import os
import math
import numpy as np
import random
import csv
import shutil
import json

from osgeo import gdal
from osgeo import ogr
from nose.plugins.skip import SkipTest

import invest_test_core
from invest_natcap import raster_utils
from invest_natcap.nearshore_wave_and_erosion \
    import nearshore_wave_and_erosion
from invest_natcap.nearshore_wave_and_erosion \
    import nearshore_wave_and_erosion_core


LOGGER = logging.getLogger('nearshore_wave_and_eroasion_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestNearshoreWaveAndErosionCore(unittest.TestCase):
    """Main testing class for the nearshore wave and erosion core model tests"""
    
    def setUp(self):
        """ Set up function
        """
        pass

    def test_compute_transects(self):
        """Compute transects algorithm"""
        shore_raster_uri = '../../NearshoreWaveAndErosion/tests/shore.tif'
        assert os.path.isfile(shore_raster_uri)

        landmass_raster_uri = '../../NearshoreWaveAndErosion/tests/landmass.tif'
        assert os.path.isfile(landmass_raster_uri)

        bathymetry_raster_uri = '../../NearshoreWaveAndErosion/tests/bathymetry.tif'
        assert os.path.isfile(bathymetry_raster_uri)

        args_uri = '../../NearshoreWaveAndErosion/tests/nearshore_wave_and_erosion_test_archive.json'    

        with open(args_uri) as args_file:
            contents = json.load(args_file)
            args = contents['arguments']
            args['landmass_raster_uri'] = landmass_raster_uri
            args['shore_raster_uri'] = shore_raster_uri
            args['bathymetry_raster_uri'] = bathymetry_raster_uri
            nearshore_wave_and_erosion_core.compute_transects(args)

    def tare_down(self):
        """ Clean up code."""
        # Do nothing for now 
        pass
