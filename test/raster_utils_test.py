"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess
import logging

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from nose.plugins.skip import SkipTest
import numpy as np
from invest_natcap import raster_utils
import invest_test_core

LOGGER = logging.getLogger('invest_core')

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

    def test_create_rat_with_no_rat(self):
        test_out = './data/test_out/raster_utils/create_rat/'
        out_uri = os.path.join(test_out, 'test_RAT.tif')

        if not os.path.isdir(test_out):
            os.makedirs(test_out)
        
        dr = gdal.GetDriverByName('GTiff')
 
        ds = dr.Create(out_uri, 5, 5, 1, gdal.GDT_Int32)
        
        srs = osr.SpatialReference()
        srs.SetUTM(11,1)
        srs.SetWellKnownGeogCS('NAD27')
        ds.SetProjection(srs.ExportToWkt())
        ds.SetGeoTransform([444720, 30, 0, 3751320, 0 , -30])

        matrix = np.array([[1,2,3,4,5],
                           [5,4,3,2,1],
                           [3,2,4,5,1],
                           [2,1,3,4,5],
                           [4,5,1,2,3]])

        band = ds.GetRasterBand(1)
        band.SetNoDataValue(-1)
        band.WriteArray(matrix)
        band = None

        tmp_dict = {1:'farm', 2:'swamp', 3:'marsh', 4:'forest', 5:'river'}
        field_1 = 'LULC'
        field_2 = 'DESC'
        
        ds_rat = raster_utils.create_rat(ds, tmp_dict, field_1, field_2)

        band = ds_rat.GetRasterBand(1)
        rat = band.GetDefaultRAT()
        
        for x in range(4):
            self.assertEqual(x+1, rat.GetValueAsInt(x,0))
            self.assertEqual(tmp_dict[x+1], rat.GetValueAsString(x, 1))
             
        band = None
        rat = None
        ds = None
        ds_rat = None
        


