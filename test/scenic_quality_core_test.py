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

class TestScenicQuality(unittest.TestCase):
    """Main testing class for the scenic quality tests"""
    
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

    def test_visibility_basic_array(self):
        DEM_size = 30
        elevation = np.zeros((DEM_size, DEM_size))
        nodata = -1
        viewpoint = (DEM_size/2, DEM_size/2)
        elevation[viewpoint[0]+1, viewpoint[1]+1] = 2.
        obs_elev = 1.0
        tgt_elev = 0.0
        max_dist = 10 
        cell_size = 5.0
        refraction_coeff = 1.0
        alg_version = 'python'
        visibility = sqc.compute_viewshed(elevation, nodata, viewpoint, \
            obs_elev, tgt_elev, max_dist, cell_size, refraction_coeff, \
            alg_version)
        visibility[DEM_size/2, DEM_size/2] = 2
        print(visibility)

    def test_visibility_flat_surface(self):
        structure_uri = "../../AQ_Rob/Block_Island fast alg/SQ/1 pt/e911_132.shp"
        shapefile = ogr.Open(structure_uri)
        assert shapefile is not None
        base_dem_uri = "../../AQ_Rob/Block_Island fast alg/SQ/bi_100meters/hdr.adf"
        flat_dem_uri = "flat_dem.tif"
        raster_utils.new_raster_from_base_uri( \
            base_dem_uri, flat_dem_uri, 'GTiff', 0., gdal.GDT_Float32, \
            fill_value = 0., n_rows = 100, n_cols = 100)
	raster = gdal.Open(flat_dem_uri, gdal.GA_Update)
        band = raster.GetRasterBand(1)
        array = band.ReadAsArray()
        
        pass

    def test_visibility_simple_obstacles(self):
        pass

    def test_visibility_multiple_points(self):
        pass

    def tare_down(self):
        """ Clean up code."""
        # Do nothing for now 
        pass
