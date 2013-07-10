import os, sys
import unittest
import random
import logging
import math

from osgeo import ogr, gdal, osr
from osgeo.gdalconst import *
import numpy as np
from nose.plugins.skip import SkipTest

from invest_natcap.dbfpy import dbf
import invest_cython_core
from invest_natcap.invest_core import invest_core
import invest_test_core

logger = logging.getLogger('invest_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestInvestCore(unittest.TestCase):
    def testflowDirectionD8(self):
        """Regression test for flow direction on a DEM"""
        dem = gdal.Open('./invest-data/test/data/sediment_test_data/dem')
        flow = invest_cython_core.newRasterFromBase(dem,
            './invest-data/test/data/test_out/flow.tif', 'GTiff', 0, gdal.GDT_Float32)
        invest_cython_core.flowDirectionD8(dem,
            [0, 0, dem.RasterXSize, dem.RasterYSize], flow)
        regressionFlow = \
            gdal.Open('./invest-data/test/data/sediment_test_data/flowregression.tif')
        invest_test_core.assertTwoDatasetsEqual(self, flow, regressionFlow)

    def testflowDirectionD8Simple(self):
        """Regression test for flow direction on a DEM with an example
        constructed by hand"""
        driver = gdal.GetDriverByName("MEM")

        #Create a 3x3 dem raster
        dem = driver.Create('', 3, 3, 1, gdal.GDT_Float32)
        dem.GetRasterBand(1).SetNoDataValue(-1.0)
        dem.GetRasterBand(1).WriteArray(np.array([[902, 909, 918], [895, 904, 916], [893, 904, 918]]).transpose())

        flow = invest_cython_core.newRasterFromBase(dem,
            '', 'MEM', 0, gdal.GDT_Byte)
        invest_cython_core.flowDirectionD8(dem,
            [0, 0, dem.RasterXSize, dem.RasterYSize], flow)
        flowMatrix = flow.ReadAsArray(0, 0, 3, 3)
        self.assertEqual(128, flowMatrix[1][1],
                         'Incorrect flow, should be 128 != %s' % flowMatrix[1][1])

        dem.GetRasterBand(1).WriteArray(np.array([[190, 185, 181], [189, 185, 182], [189, 185, 182]]).transpose())
        flow = invest_cython_core.newRasterFromBase(dem,
            '', 'MEM', 0, gdal.GDT_Byte)
        flowDir = invest_cython_core.flowDirectionD8(dem,
            [0, 0, dem.RasterXSize, dem.RasterYSize], flow)
        flowMatrix = flowDir.ReadAsArray(0, 0, 3, 3)
        self.assertEqual(8, flowMatrix[1][1],
                         'Incorrect flow, should be 8 != %s' % flowMatrix[1][1])

        dem.GetRasterBand(1).WriteArray(np.array([[343, 332, 343],
                                                      [340, 341, 343],
                                                      [345, 338, 343]]).transpose())
        flow = invest_cython_core.newRasterFromBase(dem,
            '', 'MEM', 0, gdal.GDT_Byte)
        flowDir = invest_cython_core.flowDirectionD8(dem,
            [0, 0, dem.RasterXSize, dem.RasterYSize], flow)
        flowMatrix = flowDir.ReadAsArray(0, 0, 3, 3)
        self.assertEqual(16, flowMatrix[1][1],
                         'Incorrect flow, should be 16 != %s' % flowMatrix[1][1])

        dem.GetRasterBand(1).WriteArray(np.array([[194, 191, 191],
                                                      [191, 188, 188],
                                                      [191, 189, 189]]).transpose())
        flow = invest_cython_core.newRasterFromBase(dem,
            '', 'MEM', 0, gdal.GDT_Byte)
        flowDir = invest_cython_core.flowDirectionD8(dem,
            [0, 0, dem.RasterXSize, dem.RasterYSize], flow)
        flowMatrix = flowDir.ReadAsArray(0, 0, 3, 3)
        self.assertEqual(4, flowMatrix[1][1],
                         'Incorrect flow, should be 4 != %s' % flowMatrix[1][1])



    def testslopeCalculation(self):
        """Regression test for slope calculation"""
        dem = gdal.Open('./invest-data/test/data/sediment_test_data/dem')
        slope_output = invest_cython_core.newRasterFromBase(dem,
            './invest-data/test/data/test_out/slope.tif', 'GTiff', -1, gdal.GDT_Float32)
        invest_cython_core.calculate_slope(dem,
            [0, 0, dem.RasterXSize, dem.RasterYSize], slope_output)
        regressionSlope = \
            gdal.Open('./invest-data/test/data/sediment_test_data/slopeRegression.tif')
        invest_test_core.assertTwoDatasetsEqual(self, slope_output, regressionSlope)

    def testvectorizeRasters(self):
        r1 = gdal.Open('./invest-data/test/data/base_data/terrestrial/lulc_samp_cur')
        r2 = gdal.Open('./invest-data/test/data/base_data/Freshwater/precip')

        def op(a, b):
            return np.sqrt(a ** 2 + b ** 2)

        invest_core.vectorizeRasters([r1, r2], op,
            rasterName='./invest-data/test/data/test_out/rasterizeRasters.tiff', datatype=gdal.GDT_Float32)

    def testinterpolateMatrix(self):
        """Test the matrix interpolation function"""
        def assertEqualInterpPoints(x, y, newx, newy, z):
            for xVal in x:
                for yVal in y:
                    i = x.tolist().index(xVal)
                    j = y.tolist().index(yVal)
                    ii = newx.tolist().index(xVal)
                    jj = newy.tolist().index(yVal)
                    self.assertAlmostEquals(z[j][i], interpz[jj][ii], 5,
                                    "z[%s][%s], interpz[%s][%s], %s != %s" %
                                    (i, j, ii, jj, z[j][i], interpz[jj][ii]))

        #Create a non-trivial somewhat random matrix
        x = np.array([-4.2, 3, 6, 10, 11])
        y = np.array([-9, 3, 6, 10])
        z = np.array([[0., 8., 11., 12.5, 0.0],
           [0., 1., 1., 0., 0.],
           [-7.2, 3., 1.2, 0., 0.],
           [0., 4.9, 2.5, 0, 0.]])
        #print z.shape

        #print 'x', x
        #print 'y', y
        #print 'z', z

        newx = np.array([-8.2, -4.2, 0, 2.5, 3, 5, 6, 7.5, 10, 11, 15.2, 100.0])
        newy = np.array([-9, 0, 2.5, 3, 5, 6, 7.5, 10, 22.2, 100.0])

        #print 'newx', newx
        #print 'newy', newy
        logging.debug('calling interpolate matrix')
        interpz = invest_cython_core.interpolateMatrix(x, y, z, newx, newy)
        #print 'interpz:', interpz
        logging.debug('testing the result of interpolate matrix')
        assertEqualInterpPoints(x, y, newx, newy, z)


    def testRasterDiff(self):
        driver = gdal.GetDriverByName("MEM")

        xDim, yDim = 417, 219
        testA, testB = -248.23, 1829.2

        #Create a blank xDim x yDim raster
        datasetA = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetA.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetA.GetRasterBand(1).Fill(testA)

        datasetB = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetB.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetB.GetRasterBand(1).Fill(testB)

        datasetC = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetC.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetC.GetRasterBand(1).Fill(testA - testB)

        datasetOut = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetOut.GetRasterBand(1).SetNoDataValue(-11.0)

        invest_core.rasterDiff(datasetA.GetRasterBand(1),
                               datasetB.GetRasterBand(1),
                               datasetOut.GetRasterBand(1))

        invest_test_core.assertTwoDatasetsEqual(self, datasetOut, datasetC)

    def testRasterAdd(self):
        driver = gdal.GetDriverByName("MEM")

        xDim, yDim = 417, 219
        testA, testB = -248.23, 1829.2

        #Create a blank xDim x yDim raster
        datasetA = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetA.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetA.GetRasterBand(1).Fill(testA)

        datasetB = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetB.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetB.GetRasterBand(1).Fill(testB)

        datasetC = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetC.GetRasterBand(1).SetNoDataValue(-11.0)
        datasetC.GetRasterBand(1).Fill(testA + testB)

        datasetOut = driver.Create('', xDim, yDim, 1, gdal.GDT_Float64)
        datasetOut.GetRasterBand(1).SetNoDataValue(-11.0)

        invest_core.rasterAdd(datasetA.GetRasterBand(1),
                              datasetB.GetRasterBand(1),
                              datasetOut.GetRasterBand(1))

        invest_test_core.assertTwoDatasetsEqual(self, datasetOut, datasetC)


    def test_carbon_pixel_area(self):
        """Verify the correct output of carbon.pixelArea()"""

        dataset = gdal.Open('./invest-data/test/data/carbon_regression_data/sequest_regression.tif',
                            gdal.GA_ReadOnly)
        area = invest_cython_core.pixelArea(dataset)

        #assert the output of pixelArea against the known value 
        #(it's 30x30 meters) so 0.09 Ha
        self.assertEqual(0.09, area)

    def test_wave_energy_pixel_size_in_meters(self):
        """Verify the correct output of wave_energy.pixel_size_in_meters()"""
        #This file is known/tested to have the right conversion
        correct_pixel_path = './invest-data/test/data/wave_energy_regression_data/npv_usd_regression.tif'
        dataset_correct_pixel = gdal.Open(correct_pixel_path, gdal.GA_ReadOnly)
        dataset = gdal.Open('./invest-data/test/data/wave_energy_data/samp_input/global_dem',
                            gdal.GA_ReadOnly)
        #We need to get a point from the shapefile in the same vacinity as
        #the projection
        shape = ogr.Open('./invest-data/test/data/wave_energy_regression_data/WEM_InputOutput_Pts_bio_regression.shp')
        layer = shape.GetLayer(0)
        feat = layer.GetNextFeature()
        geom = feat.GetGeometryRef()
        lat = geom.GetX()
        longitude = geom.GetY()
        #Create Coordinate Transformation from lat/long to meters
        srs_prj = osr.SpatialReference()
        srs_prj.SetWellKnownGeogCS("WGS84")
        source_sr = srs_prj
        trg_prj = osr.SpatialReference()
        trg_prj.ImportFromWkt(dataset_correct_pixel.GetProjectionRef())
        target_sr = trg_prj
        coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
        #Convert the shapefiles geometry point to lat/long
        coord_trans_opposite = osr.CoordinateTransformation(target_sr, source_sr)
        point_decimal_degree = coord_trans_opposite.TransformPoint(lat, longitude)
        #Get the size of the pixels in meters
        pixel_size_tuple = invest_cython_core.pixel_size_in_meters(dataset,
                                                                   coord_trans,
                                                                   point_decimal_degree)
        geo_tran = dataset_correct_pixel.GetGeoTransform()
        logger.debug('correct pixel sizes : %s : %s', geo_tran[1], geo_tran[5])
        logger.debug('returned pixel sizes %s : %s', pixel_size_tuple[0], pixel_size_tuple[1])
        #assert that the x and y pixels are the same size.
        #take absolute value because we are not concerned with direction
        #but size.
        self.assertEqual(pixel_size_tuple[0], abs(geo_tran[1]))
        self.assertEqual(pixel_size_tuple[1], abs(geo_tran[5]))

    def test_createRasterFromVectorExtents(self):
        fsencoding = sys.getfilesystemencoding()
        shp = ogr.Open('./invest-data/test/data/sediment_test_data/subwatersheds.shp'.\
                       encode(fsencoding))
        raster = invest_cython_core.createRasterFromVectorExtents(30, 30,
                       gdal.GDT_Float32, -5.0, './invest-data/test/data/test_out/subwatershed.tif', shp)
