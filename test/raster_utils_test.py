"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess

from osgeo import gdal
from osgeo import ogr
from nose.plugins.skip import SkipTest
import numpy as np
from invest_natcap import raster_utils
import invest_test_core


class TestRasterUtils(unittest.TestCase):
    def test_clip_datset(self):
        raise SkipTest
        base_dir = 'data/test_out/raster_utils'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        data_dir = 'data/sediment_test_data'
        dem_uri = os.path.join(data_dir,'dem')
        dem = gdal.Open(dem_uri)
        aoi_uri = os.path.join(data_dir,'subwatersheds.shp')
        aoi = ogr.Open(aoi_uri)
        
        clip_dataset = os.path.join(base_dir,'clipped.tif')
        raster_utils.clip_dataset(dem, aoi, clip_dataset)

#        subprocess.Popen(["qgis", dem_uri, aoi_uri, clip_dataset])


    def test_calculate_slope(self):
        raise SkipTest
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

    def test_calculate_value_not_in_array(self):
        array = np.array([-1,2,5,-8,-9])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)

        array = np.array([-1,-1,-1])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)

        array = np.array([-1.1,-1.2,-1.2])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)
