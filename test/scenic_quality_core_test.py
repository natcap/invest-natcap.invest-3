from __future__ import print_function

import unittest
import logging
import os
import sys
import subprocess
import math
import numpy as np
import random
import time
import csv
import glob
import shutil

from osgeo import gdal
from osgeo import ogr
from nose.plugins.skip import SkipTest

import invest_test_core
from invest_natcap import raster_utils
from invest_natcap.scenic_quality \
    import scenic_quality as sq
from invest_natcap.scenic_quality \
    import scenic_quality_core as sqc


LOGGER = logging.getLogger('scenic_quality_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestScenicQualitylity(unittest.TestCase):
    """Main testing class for the scenic quality tests"""
    
    def make_input_data(self):
        args = {}
        return args

    def setUp(self):
        pass

    def test_get_perimeter_cells(self):
        DEM_size = 9
        elevation = np.zeros((DEM_size, DEM_size))
        viewpoint = (DEM_size/2+2, DEM_size/2-2)
        radius = 3
	perimeter = sqc.get_perimeter_cells(elevation.shape, viewpoint, radius)
        #print('perimeter', perimeter)
        elevation[perimeter] = 1
        elevation[viewpoint[0], viewpoint[1]] = 2
        #print(elevation)

    def test_visibility(self):
        DEM_size = 9
        elevation = np.zeros((DEM_size, DEM_size))
        nodata = -1
        viewpoint = (DEM_size/2, DEM_size/2)
        obs_elev = 1.0
        tgt_elev = 0.0
        max_dist = 2
        cell_size = 1.0
        refraction_coeff = 1.0
        alg_version = 'python'
        visibility = sqc.compute_viewshed(elevation, nodata, viewpoint, \
            obs_elev, tgt_elev, max_dist, cell_size, refraction_coeff, \
            alg_version)
        visibility[DEM_size/2, DEM_size/2] = 2
        print(visibility)

    def tare_down(self):
        """ Clean up code."""
        # Do nothing for now 
        pass
