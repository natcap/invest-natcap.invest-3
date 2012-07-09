"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np
from invest_natcap import raster_utils
import invest_test_core


class TestSedimentBiophysical(unittest.TestCase):
    def test_calculate_slope(self):
        dem_points = {
            (0.0,0.0): 50,
            (0.0,1.0): 100,
            (1.0,0.0): 90,
            (1.0,1.0): 0,
            (0.5,0.5): 45}

        n = 100

        base_dir = 'data/test_out/raster_utils'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dem_uri = os.path.join(base_dir,'raster_dem.tif')
        dem_dataset = invest_test_core.make_sample_dem(n,n,dem_points, 5.0, -1, dem_uri)

        slope_uri = os.path.join(base_dir,'raster_slope.tif')
        raster_utils.calculate_slope(dem_dataset, slope_uri)

        subprocess.Popen(["qgis", dem_uri, slope_uri])
