"""URI level tests for the sediment module"""

import unittest
import logging
import os
import subprocess

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.sediment import sediment
import invest_cython_core
import invest_test_core
from invest_natcap.sediment import sediment_core
from invest_natcap import raster_utils


LOGGER = logging.getLogger('sediment_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestSediment(unittest.TestCase):
    """Main testing class for the sediment tests"""
    def test_sediment_dinf_flow_dir(self):
        raise SkipTest
        """A test constructed by hand to test the low level dinf direction and
            flow functions.  Intent is the the test case is small enough to be
            hand calculatable, yet large enough to be non-trivial."""
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

        invest_cython_core.flow_direction_inf(dem, flow_direction,
                                              [0, 0, 6, 6])

        invest_cython_core.flow_accumulation_dinf(flow_direction,
                                                  flow_accumulation, dem)

    def test_sediment_re(self):
        """Test for sediment function running with default InVEST 
           sample input."""
#        raise SkipTest
        args = {}
        args['workspace_dir'] = './data/test_out/sediment_output'
        args['suffix'] = '_foo'
        base_dir = './data/sediment_test_data'
        args['dem_uri'] = '%s/dem' % base_dir
        args['erosivity_uri'] = '%s/erosivity' % base_dir
        args['erodibility_uri'] = '%s/erodibility.tif' % base_dir
        args['landuse_uri'] = '%s/landuse_90.tif' % base_dir

        #shapefile
        args['watersheds_uri'] = '%s/watersheds.shp' % base_dir
        args['reservoir_locations_uri'] = '%s/reservoir_loc.shp' % base_dir
        args['reservoir_properties_uri'] = '%s/reservoir_prop' % base_dir

        #table
        args['biophysical_table_uri'] = '%s/biophysical_table.csv' % base_dir

        #primatives
        args['threshold_flow_accumulation'] = 1000
        args['slope_threshold'] = 70.0

        args['sediment_threshold_table_uri'] = os.path.join(base_dir, 'sediment_threshold_table.csv')
        args['sediment_valuation_table_uri'] = os.path.join(base_dir, 'sediment_valuation_table.csv')

        intermediate_dir = os.path.join(args['workspace_dir'], 'Intermediate')

        intermediate_files = ['dem_clip.tif', 'flow_accumulation.tif', 
                              'slope.tif', 'ls.tif', 
                              'flow_direction.tif', 'retention.tif', 'c_factor.tif',
                              'p_factor.tif', 'v_stream.tif', 'effective_retention.tif',
                              'sed_ret_eff.tif', 'pixel_sed_flow.tif']
        output_dir = os.path.join(args['workspace_dir'], 'Output')

        output_files = ['usle.tif', 'pixel_export.tif', 'pixel_retained.tif']

        sediment.execute(args)

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + os.sep + "/Intermediate/flow_direction%s.tif" % args['suffix'],
            './data/sediment_regression_data/flow_direction_regression.tif')

        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + os.sep + "/Intermediate/flow_accumulation%s.tif" % args['suffix'],
            './data/sediment_regression_data/flow_accumulation_regression.tif')

    def test_sediment_simple_1(self):
        """This test is a smaller version of a real world case that failed"""
        #Create two 3x3 rasters in memory
        raise SkipTest
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
        invest_cython_core.flow_direction_inf(dem, [0, 0, 3, 3], flow_raster)
        flow_array = flow_raster.GetRasterBand(1).ReadAsArray(1, 1, 1, 1)

        #Direction 4.712385 was calculated by hand
        self.assertAlmostEqual(flow_array[0][0], 4.712389)

    def test_sediment_simple_2(self):
        """This test is a smaller version of a real world case that failed"""
        raise SkipTest
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
        invest_cython_core.flow_direction_inf(dem, [0, 0, 3, 3], flow)
        flowArray = flow.GetRasterBand(1).ReadAsArray(1, 1, 1, 1)

        #Direction 5.117281 was calculated by hand
        self.assertAlmostEqual(flowArray[0][0], 5.117281)

    def test_sediment_simple_3(self):
        """This test is a smaller version of a real world case that failed"""
        raise SkipTest
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
        invest_cython_core.flow_direction_inf(dem, [0, 0, 3, 3], flow)
        flowArray = flow.GetRasterBand(1).ReadAsArray(1, 1, 1, 1)

        #Direction 5.117281 was calculated by hand
        self.assertAlmostEqual(flowArray[0][0], 0.0)

    def test_effective_retention(self):
        """Call effective retention with some sample datasets"""
        raise SkipTest
        dem_points = {
            (0.0,0.0): 50,
            (0.0,1.0): 100,
            (1.0,0.0): 90,
            (1.0,1.0): 0,
            (0.5,0.5): 45}

        retention_points = {
            (0.0,0.0): 0.5,
            (0.0,1.0): 0.25,
            (1.0,0.0): 0.1,
            (1.0,1.0): 0,
            (0.5,0.5): 0.3}

        n = 100

        base_dir = 'data/test_out/sediment'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dem_uri = os.path.join(base_dir,'random_dem.tif')
        dem = invest_test_core.make_sample_dem(n,n,dem_points, 5.0, -1, dem_uri)

        retention_efficiency_uri = \
            os.path.join(base_dir, 'retention_efficiency.tif')
        retention_efficiency_dataset = invest_test_core.make_sample_dem(n, n, 
            retention_points, 0.0, -1, retention_efficiency_uri)

        flow_uri = os.path.join(base_dir,'random_dem_flow.tif')
        flow_dataset = raster_utils.new_raster_from_base(dem, flow_uri, 'GTiff',
                                                 -1, gdal.GDT_Float32)
        invest_cython_core.flow_direction_inf(dem, [0, 0, n, n], flow_dataset)

        flow_accumulation_uri = os.path.join(base_dir, 'flow_accumulation.tif')
        flow_accumulation_dataset = raster_utils.flow_accumulation_dinf(flow_dataset, dem, 
                                                                flow_accumulation_uri)

        stream_uri = os.path.join(base_dir, 'streams.tif')
        stream_dataset = raster_utils.stream_threshold(flow_accumulation_dataset, 20, stream_uri)

        effective_retention_uri = os.path.join(base_dir, 'effective_retention.tif')
        effective_retention_dataset = sediment_core.effective_retention(flow_dataset, 
            retention_efficiency_dataset, stream_dataset, effective_retention_uri)

        raster_utils.calculate_raster_stats(dem)
        raster_utils.calculate_raster_stats(flow_dataset)
        raster_utils.calculate_raster_stats(effective_retention_dataset)
