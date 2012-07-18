import os, sys
import unittest
import random
import logging

from osgeo import ogr, gdal, osr
from osgeo.gdalconst import *
import numpy as np

from invest_natcap.biodiversity import biodiversity_core

LOGGER = logging.getLogger('water_yield_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestBiodiversityCore(unittest.TestCase):
    def test_biodiversity_core_pixel_count(self):
        """Test a GDAL raster dataset to make sure the correct pixel counts are
            being returned"""

        samp_lulc_cur_uri = \
            './data/biodiversity_regression_data/samp_input/lc_samp_cur_b.tif'
        ds = gdal.Open(samp_lulc_cur_uri)

        results = biodiversity_core.raster_pixel_count(ds)

        ds = None

        LOGGER.debug('Pixel Counts : %s', results)

    def test_biodiversity_core_pixel_count_hand(self):
        """Test a hand created GDAL raster dataset to make sure the correct
            pixel counts are being returned"""

        driver = gdal.GetDriverByName('MEM')
        dataset_type = gdal.GDT_Int32

        dataset = driver.Create('', 5, 5, 1, dataset_type)

        srs = osr.SpatialReference()
        srs.SetUTM( 11, 1 )
        srs.SetWellKnownGeogCS( 'NAD27' )
        dataset.SetProjection( srs.ExportToWkt() )

        dataset.SetGeoTransform( [444720, 30, 0, 3751320, 0, -30 ] )

        raster = np.array([[1,1,5,5,3],
                           [8,3,3,5,2],
                           [9,7,-1,3,5],
                           [13,3,5,9,4],
                           [9,7,3,-1,1]])

        dataset.GetRasterBand(1).WriteArray(raster)
        dataset.GetRasterBand(1).SetNoDataValue(-1)

        results = biodiversity_core.raster_pixel_count(dataset)
        manual_count = {1:3, 2:1, 3:6, 4:1, 5:5, 7:2, 8:1, 9:3, 13:1}
        self.assertEqual(results, manual_count)
        dataset = None

        LOGGER.debug('Hand Pixel Counts : %s', results)

    def test_biodiversity_core_raster_from_dict(self):
        """Test mapping a set of values from a dictionary to a raster by hand
        creating a raster and dictionary"""
        
        out_dir = './data/test_out/biodiversity/raster_from_dict/'
        
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        out_uri = os.path.join(out_dir, 'normal.tif')
        
        driver = gdal.GetDriverByName('MEM')
        dataset_type = gdal.GDT_Int32

        dataset = driver.Create('', 5, 5, 1, dataset_type)

        srs = osr.SpatialReference()
        srs.SetUTM( 11, 1 )
        srs.SetWellKnownGeogCS( 'NAD27' )
        dataset.SetProjection( srs.ExportToWkt() )

        dataset.SetGeoTransform( [444720, 30, 0, 3751320, 0, -30 ] )

        raster = np.array([[256,1,1,1,256],
                           [256,3,3,3,256],
                           [2,2,2,2,256],
                           [256,1,1,2,2],
                           [256,256,3,256,256]])

        dataset.GetRasterBand(1).SetNoDataValue(256)
        dataset.GetRasterBand(1).WriteArray(raster)

        test_dict = {'1':{'sensitivity':0.75}, 
                     '2':{'sensitivity':0.5},
                     '3':{'sensitivity':1.0}}
        field = 'sensitivity'
        out_nodata = -1.0
        out_raster =\
            biodiversity_core.raster_from_dict(dataset, out_uri, test_dict,\
                field, out_nodata, False)

        expected_array =  np.array([[-1.0,0.75,0.75,0.75,-1.0],
                                    [-1.0,1.0,1.0,1.0,-1.0],
                                    [0.5,0.5,0.5,0.5,-1.0],
                                    [-1.0,0.75,0.75,0.5,0.5],
                                    [-1.0,-1.0,1.0,-1.0,-1.0]])

        result_array = out_raster.GetRasterBand(1).ReadAsArray()
        LOGGER.debug('result array : %s', result_array)
        LOGGER.debug('expected array : %s', expected_array)
        self.assertTrue((expected_array==result_array).all())

    def test_biodiversity_core_raster_from_dict_error(self):
        """Test mapping a set of values from a dictionary to a raster by hand
        creating a raster and dictionary. However, this time let us purposfully
        leave out a value from the sensitivity table and assert that an
        exception was raised"""
        
        out_dir = './data/test_out/biodiversity/raster_from_dict/'
        
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        out_uri = os.path.join(out_dir, 'error.tif')
        
        driver = gdal.GetDriverByName('MEM')
        dataset_type = gdal.GDT_Int32

        dataset = driver.Create('', 5, 5, 1, dataset_type)

        srs = osr.SpatialReference()
        srs.SetUTM( 11, 1 )
        srs.SetWellKnownGeogCS( 'NAD27' )
        dataset.SetProjection( srs.ExportToWkt() )

        dataset.SetGeoTransform( [444720, 30, 0, 3751320, 0, -30 ] )

        raster = np.array([[256,1,1,1,256],
                           [256,3,3,3,256],
                           [2,2,2,2,256],
                           [256,1,1,2,2],
                           [256,256,3,256,256]])

        dataset.GetRasterBand(1).SetNoDataValue(256)
        dataset.GetRasterBand(1).WriteArray(raster)

        test_dict = {'1':{'sensitivity':0.75}, 
                     '3':{'sensitivity':1.0}}
        field = 'sensitivity'
        out_nodata = -1.0
        self.assertRaises(KeyError, biodiversity_core.raster_from_dict, dataset,
                out_uri, test_dict, field, out_nodata, True,
                error_message='missing key')

