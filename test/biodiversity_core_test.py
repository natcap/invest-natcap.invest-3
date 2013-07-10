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
from invest_natcap.biodiversity import biodiversity_core
import invest_test_core

LOGGER = logging.getLogger('biodiversity_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestBiodiversityCore(unittest.TestCase):
    def test_biodiversity_core_pixel_count(self):
        """Test a GDAL raster dataset to make sure the correct pixel counts are
            being returned"""
        #raise SkipTest

        samp_lulc_cur_uri = \
            './invest-data/test/data/biodiversity_regression_data/samp_input/lc_samp_cur_b.tif'
        ds = gdal.Open(samp_lulc_cur_uri)

        results = biodiversity_core.raster_pixel_count(ds)

        expected_results = \
                {1:5724, 2:422, 3:20, 6:403, 7:40, 8:2134, 11:1748, 16:6283,
                 18:2829, 20:1675, 21:10940, 24:15524, 32:3814, 33:3399, \
                 39:274, 40:1, 49: 504, 51:175, 52:746, 53:67418, 54:183419, \
                 55:266, 56:22836, 57:6711, 58:39266, 59:24049, 60:79733, \
                 61:20146, 62:1470, 66:242, 67:170388, 68:26102, 71:23748, \
                 72:2322, 73:1172, 74:546, 75:1, 76:160, 78:1, 79:7001, \
                 80:7197, 81:1606, 82:10442, 83:69676, 84:2506, 85:118181, \
                 86:10807, 87:107541, 88:5629, 89:3424, 90:22816, 91:2296, \
                 92:12278, 93:6750, 95:74}

        ds = None

        self.assertEqual(results, expected_results)

    def test_biodiversity_core_pixel_count_hand(self):
        """Test a hand created GDAL raster dataset to make sure the correct
            pixel counts are being returned"""
        #raise SkipTest
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

    def test_biodiversity_core_map_raster_to_dict_values_regression(self):
        """A regression test for map_raster_to_dict_values"""
        #raise SkipTest
        out_dir = './invest-data/test/data/test_out/biodiversity/map_raster_to_dict_values/'
        input_dir = './invest-data/test/data/biodiversity_regression_data/samp_input/'
                
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        out_uri = os.path.join(out_dir, 'raster_from_dict_regression.tif')
        sensitivity_uri = os.path.join(input_dir, 'sensitivity_samp.csv')
        dataset = gdal.Open(os.path.join(input_dir, 'lc_samp_cur_b.tif'))
        
        sensitivity_dict = {}
        sensitivity_file = open(sensitivity_uri)
        reader = csv.DictReader(sensitivity_file)
        for row in reader:
            sensitivity_dict[row['LULC']] = row
        sensitivity_file.close()
       
        field = 'L_crp'
        out_nodata = -1.0

        out_raster = \
            biodiversity_core.map_raster_to_dict_values(dataset, out_uri, \
                    sensitivity_dict, field, out_nodata, 'values_required')

        regression_dir = \
            './invest-data/test/data/biodiversity_regression_data/regression_outputs/'

        regression_ds = \
                gdal.Open(os.path.join(regression_dir, 'sens_crp_c.tif'))

        invest_test_core.assertTwoDatasetsEqual(self, out_raster, regression_ds)

    def test_biodiversity_core_map_raster_to_dict_values(self):
        """Test mapping a set of values from a dictionary to a raster by hand
        creating a raster and dictionary"""
        
        out_dir = './invest-data/test/data/test_out/biodiversity/map_raster_to_dict_values/'
        
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        out_uri = os.path.join(out_dir, 'raster_from_dict.tif')
        
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
        out_raster = \
            biodiversity_core.map_raster_to_dict_values(dataset, out_uri, \
                test_dict, field, out_nodata, 'none')

        expected_array =  np.array([[-1.0,0.75,0.75,0.75,-1.0],
                                    [-1.0,1.0,1.0,1.0,-1.0],
                                    [0.5,0.5,0.5,0.5,-1.0],
                                    [-1.0,0.75,0.75,0.5,0.5],
                                    [-1.0,-1.0,1.0,-1.0,-1.0]])

        result_array = out_raster.GetRasterBand(1).ReadAsArray()
        LOGGER.debug('result array : %s', result_array)
        LOGGER.debug('expected array : %s', expected_array)
        self.assertTrue((expected_array==result_array).all())

    def test_biodiversity_core_map_raster_to_dict_values_error(self):
        """Test mapping a set of values from a dictionary to a raster by hand
        creating a raster and dictionary. However, this time let us purposfully
        leave out a value from the sensitivity table and assert that an
        exception was raised"""
        #raise SkipTest 
        out_dir = './invest-data/test/data/test_out/biodiversity/map_raster_to_dict_values/'
        
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
        self.assertRaises(Exception, biodiversity_core.map_raster_to_dict_values,
                dataset, out_uri, test_dict, field, out_nodata,
                'values_required', error_message='missing key')

    def test_biodiversity_core_make_raster_from_shape(self):
        """A regression test for make_raster_from_shape """
        #raise SkipTest
        test_dir = './invest-data/test/data/biodiversity_regression_data/samp_input/'
        out_dir = './invest-data/test/data/test_out/biodiversity/make_raster_from_shape/'
        shape_uri = os.path.join(test_dir, 'access_samp.shp')
        base_ds_uri = os.path.join(test_dir, 'lc_samp_cur_b.tif')
        out_uri = os.path.join(out_dir, 'new_raster.tif')
        regression_ds_uri = \
            './invest-data/test/data/biodiversity_regression_data/access_regression.tif'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        base_ds = gdal.Open(base_ds_uri)
        regression_ds = gdal.Open(regression_ds_uri)
        shape = ogr.Open(shape_uri)
        attr = 'ACCESS'

        base_raster = \
            raster_utils.new_raster_from_base(base_ds, out_uri, 'GTiff', \
                -1, gdal.GDT_Float32) 

        new_raster = \
            biodiversity_core.make_raster_from_shape(base_raster, shape, attr)

        invest_test_core.assertTwoDatasetsEqual(self, regression_ds, new_raster)

