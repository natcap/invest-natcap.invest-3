"""URI level tests for the sediment biophysical module"""

import unittest
import logging
import os

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap import postprocessing
from invest_natcap.sediment import sediment_biophysical
import invest_cython_core
import invest_test_core

LOGGER = logging.getLogger('sediment_biophysical_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestSedimentBiophysical(unittest.TestCase):
    """Main testing class for the biophysical sediment tests"""
    def test_sediment_dinf_flow_dir(self):
        """A test constructed by hand to test the low level dinf direction and
            flow functions.  Intent is the the test case is small enough to be
            hand calculatable, yet large enough to be non-trivial."""
        raise SkipTest
        base = gdal.Open('./data/sediment_test_data/dem', gdal.GA_ReadOnly)

        projection = base.GetProjection()
        geotransform = base.GetGeoTransform()

        dem = invest_cython_core.newRaster(6, 6, projection, geotransform,
            'GTiff', -1, gdal.GDT_Float32, 1,
            './data/sediment_6x6_output/dem.tif')
        flow_direction = invest_cython_core.newRasterFromBase(dem,
            './data/sediment_6x6_output/flow_direction.tif',
            'GTiff', -5.0, gdal.GDT_Float32)
        flow_accumulation = invest_cython_core.newRasterFromBase(dem,
            './data/sediment_6x6_output/flow_accumulation.tif',
            'GTiff', -5.0, gdal.GDT_Float32)

        #This is a test case that was calculated by hand
        dem_array = np.array([[130, 130, 130, 130, 130, 130],
                              [130, 120, 112, 111, 115, 130],
                              [130, 109, 110, 108, 109, 130],
                              [130, 106, 103, 105, 102, 130],
                              [130, 109, 106, 104, 100, 130],
                              [130, 130, 130, 130, 130, 130]])
        dem.GetRasterBand(1).WriteArray(dem_array, 0, 0)

        invest_cython_core.flow_direction_inf(dem, flow_direction)

        invest_cython_core.flow_accumulation_dinf(flow_direction,
                                                  flow_accumulation, dem)

    def test_sediment_biophysical_re(self):
        """Test for sediment_biophysical function running with default InVEST 
           sample input."""
        raise SkipTest
        args = {}
        args['workspace_dir'] = './data/sediment_biophysical_output'
        base_dir = './data/sediment_test_data'
        args['dem_uri'] = '%s/dem' % base_dir
        args['erosivity_uri'] = '%s/erosivity' % base_dir
        args['erodibility_uri'] = '%s/erodibility.tif' % base_dir
        args['landuse_uri'] = '%s/landuse_90.tif' % base_dir

        #shapefile
        args['watersheds_uri'] = '%s/watersheds.shp' % base_dir
        args['subwatersheds_uri'] = '%s/subwatersheds.shp' % base_dir
        args['reservoir_locations_uri'] = '%s/reservoir_loc.shp' % base_dir
        args['reservoir_properties_uri'] = '%s/reservoir_prop' % base_dir

        #table
        args['biophysical_table_uri'] = '%s/biophysical_table.csv' % base_dir

        #primatives
        args['threshold_flow_accumulation'] = 1000
        args['slope_threshold'] = 70.0

        sediment_biophysical.execute(args)

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + os.sep + "/Intermediate/flow_direction.tif",
            './data/sediment_regression_data/flow_direction_regression.tif')

    def test_sediment_biophysical_simple_1(self):
        """This test is a smaller version of a real world case that failed"""
        #Create two 3x3 rasters in memory
        base = gdal.Open('./data/sediment_test_data/dem', gdal.GA_ReadOnly)
        cols = 3
        rows = 3
        projection = base.GetProjection()
        geotransform = base.GetGeoTransform()
        dem = invest_cython_core.newRaster(cols, rows, projection,
            geotransform, 'GTiff', -1, gdal.GDT_Float32, 1,
            './data/sediment_3x3_output/dem.tif')
        flow_raster = invest_cython_core.newRasterFromBase(dem, '',
            'MEM', -5.0, gdal.GDT_Float32)

        #This is a test case that was calculated by hand
        array = np.array([[111, 115, 999],
                          [108, 109, 999],
                          [105, 102, 999]])

        dem.GetRasterBand(1).WriteArray(array, 0, 0)
        invest_cython_core.flow_direction_inf(dem, flow_raster)
        flow_array = flow_raster.GetRasterBand(1).ReadAsArray(1, 1, 1, 1)

        #Direction 4.712385 was calculated by hand
        self.assertAlmostEqual(flow_array[0][0], 4.712389)

    def test_sediment_biophysical_simple_2(self):
        """This test is a smaller version of a real world case that failed"""
        #Create two 3x3 rasters in memory
        base = gdal.Open('./data/sediment_test_data/dem', gdal.GA_ReadOnly)
        cols = 3
        rows = 3
        projection = base.GetProjection()
        geotransform = base.GetGeoTransform()
        dem = invest_cython_core.newRaster(cols, rows, projection,
            geotransform, 'MEM', -1, gdal.GDT_Float32, 1, '')
        flow = invest_cython_core.newRasterFromBase(dem, '', 'MEM', -5.0,
                                                    gdal.GDT_Float32)

        #This is a test case that was calculated by hand
        array = np.array([[249, 246, 243],
                          [241, 238, 235],
                          [233, 231, 228]])
        dem.GetRasterBand(1).WriteArray(array, 0, 0)
        invest_cython_core.flow_direction_inf(dem, flow)
        flowArray = flow.GetRasterBand(1).ReadAsArray(1, 1, 1, 1)

        #Direction 5.117281 was calculated by hand
        self.assertAlmostEqual(flowArray[0][0], 5.117281)

    def test_sediment_biophysical_simple_3(self):
        """This test is a smaller version of a real world case that failed"""
        #Create two 3x3 rasters in memory
        base = gdal.Open('./data/sediment_test_data/dem', gdal.GA_ReadOnly)
        cols = 3
        rows = 3
        projection = base.GetProjection()
        geotransform = base.GetGeoTransform()
        dem = invest_cython_core.newRaster(cols, rows, projection,
            geotransform, 'MEM', -1, gdal.GDT_Float32, 1, '')
        flow = invest_cython_core.newRasterFromBase(dem, '', 'MEM', -5.0,
                                                    gdal.GDT_Float32)

        #This is a test case that was calculated by hand
        array = np.array([[120, 109, 110],
                          [120, 106, 103],
                          [120, 109, 106]])
        dem.GetRasterBand(1).WriteArray(array, 0, 0)
        invest_cython_core.flow_direction_inf(dem, flow)
        flowArray = flow.GetRasterBand(1).ReadAsArray(1, 1, 1, 1)

        #Direction 5.117281 was calculated by hand
        self.assertAlmostEqual(flowArray[0][0], 0.0)


    def test_postprocessing_flow_direction(self):
        """Test for a postprocessing quiver plot."""
        raise SkipTest
        args = {}
        args['workspace_dir'] = './data/sediment_biophysical_output'
        postprocessing.plot_flow_direction(args['workspace_dir'] + os.sep +
            'Intermediate' + os.sep + 'flow.tif',
            args['workspace_dir'] + os.sep + 'Intermediate' + os.sep +
            'flow_arrows.png')
