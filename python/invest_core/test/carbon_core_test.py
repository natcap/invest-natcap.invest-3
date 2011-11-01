import os, sys
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')
import carbon_core
import unittest
from osgeo import ogr, gdal, osr
from osgeo.gdalconst import *
from dbfpy import dbf
import numpy as np
import random

class TestInvestCarbonCore(unittest.TestCase):
    def test_carbon_core_nodata(self):
        """Test several raster sizes that have only nodata values"""
        driver = gdal.GetDriverByName("GTIFF")

        for xDim, yDim, inNoData, outNodata in [(1, 1, 255, 1.0),
                                                (10, 10, 255, 21.0),
                                                (443, 953, 2, 1.0),
                                                (719, 211, 12, 111.5)]:
            #Create a blank xDim x yDim raster
            lulc = driver.Create('../../../test_data/test_blank_input', xDim,
                                 yDim, 1, gdal.GDT_Byte)
            lulc.GetRasterBand(1).SetNoDataValue(inNoData)
            #Fill raster with nodata 
            lulc.GetRasterBand(1).Fill(lulc.GetRasterBand(1).GetNoDataValue())

            #Create the output raster
            tot_C_cur = driver.Create('../../../test_data/tot_C_cur_blank_output',
                xDim, yDim, 1, gdal.GDT_Float32)
            tot_C_cur.GetRasterBand(1).SetNoDataValue(outNodata)

            args = { 'lulc_cur': lulc,
                    'carbon_pools': dbf.Dbf('../../../test_data/test_blank_dbf',
                                            new=True),
                    'tot_C_cur': tot_C_cur}
            carbon_core.biophysical(args)

            #Check that the resulting 'tot_C_cur' raster contains only
            #no data values
            data = tot_C_cur.GetRasterBand(1).ReadAsArray(0, 0,
                tot_C_cur.RasterXSize, tot_C_cur.RasterYSize)
            sum = np.sum(data, dtype=np.float64)
            self.assertAlmostEqual(sum, xDim * yDim * outNodata)

    def test_carbon_storage(self):
        """Test of calculateCarbonStorage against a random LULC array, includes tests on nodata values"""

        #picked some largish x and y dimensions that are prime numbers
        xDim, yDim = (710, 569)
        driver = gdal.GetDriverByName("GTIFF")
        lulc = driver.Create('../../../test_data/test_input', xDim, yDim, 1,
                                 gdal.GDT_Byte)

        #Made up carbon pools, last entry is the nodata value
        pools = {0: 4.3, 1: 4.3, 2: 5.7, 3: 10.0, 4:-255.0}

        lulc.GetRasterBand(1).SetNoDataValue(len(pools) - 1)

        #Set the seed so it always has the same "random" output
        np.random.seed(123456)

        #Make a random lulc that consists of lulc types 0..lenth of pools
        array = np.random.random_integers(0, len(pools) - 1, size=(yDim, xDim))

        lulc.GetRasterBand(1).WriteArray(array, 0, 0)

        #Create the output raster
        tot_C_cur = driver.Create('../../../test_data/tot_C_cur',
            xDim, yDim, 1, gdal.GDT_Float64)
        tot_C_cur.GetRasterBand(1).SetNoDataValue(-255.0)

        carbon_core.calculateCarbonStorage(pools, lulc.GetRasterBand(1),
                                           tot_C_cur.GetRasterBand(1))

        #verify the contents of output against pool and lulc data, since
        #pools include nodata value (last one) we should also end up testing
        #those values
        data = tot_C_cur.GetRasterBand(1).ReadAsArray(0, 0,
                tot_C_cur.RasterXSize, tot_C_cur.RasterYSize)
        for x in xrange(xDim):
            for y in xrange(yDim):
                self.assertAlmostEqual(pools[array[y][x]], data[y][x])

    def test_carbon_pixel_area(self):
        """Verify the correct output of carbon.pixelArea()"""

        dataset = gdal.Open('../../../test_data/carbon_regression.tif',
                            gdal.GA_ReadOnly)

        srs = osr.SpatialReference()
        srs.SetProjection(dataset.GetProjection())
        linearUnits = srs.GetLinearUnits()
        geotransform = dataset.GetGeoTransform()
        #take absolute value since sometimes negative widths/heights
        areaMeters = abs(geotransform[1] * geotransform[5] *
                         (linearUnits ** 2))
        result = areaMeters / (10 ** 4) #convert m^2 to Ha

        #run pixelArea()
        area = carbon_core.pixelArea(dataset)

        #assert the output of pixelArea against our calculation
        self.assertEqual(result, area)

    def test_carbon_diff_smoke(self):
        """Smoke test for the diff function."""
        lulc1 = np.zeros((1, 0))
        lulc2 = np.zeros((1, 0))
        nodata = {'input': 0, 'output': 0} #set a nodata value

        carbon_core.carbon_diff(nodata, lulc1, lulc2)

    def test_carbon_diff_1D_arrays(self):
        length = 100
        lulc1 = np.zeros((1, length))
        lulc2 = np.ones((1, length))
        nodata = {'input':-2, 'output':-2} #set a nodata value

        #run carbon_diff
        output = carbon_core.carbon_diff(nodata, lulc1, lulc2)

        #verify the contents of output against pool and lulc data
        for x in range(lulc1.shape[1]):
            self.assertEqual(output[0][x], 1, 'Difference was not correctly \
                calculated.')

    def test_carbon_add_smoke(self):
        """Smoke test for the diff function."""
        lulc1 = np.zeros((1, 0))
        lulc2 = np.zeros((1, 0))
        nodata = {'cur': 0, 'fut': 0} #set a nodata value

        carbon_core.carbon_add(nodata, lulc1, lulc2)

    def test_carbon_add_1D_arrays(self):
        """Testing adding of 2 carbon arrays"""
        length = 100
        lulc1 = np.zeros((1, length))
        lulc2 = np.zeros((1, length))
        for x in range(length):
            lulc1[0][x] = 15.0 * random.random()
            lulc2[0][x] = 10.0 * random.random()

        nodata = {'input':-2, 'output':-2} #set a nodata value

        #run carbon_add
        output = carbon_core.carbon_add(nodata, lulc1, lulc2)

        #verify the contents of output against pool and lulc data
        for x in range(lulc1.shape[1]):
            self.assertEqual(output[0][x], lulc1[0][x] + lulc2[0][x],
                             'Sum was not correctly calculated.')

    def test_carbon_value_1D_array(self):
        """Test of carbon_value against a 1D input/output array"""
        #setup the three args to carbon_seq
        length = 100
        lulc = np.ones((1, length))
        nodata = {'input':-1, 'output':-1}

        #run carbon_value
        output = carbon_core.carbon_value(nodata, lulc, 3, 2.0, 4.0)

        #verify the output data was calculated and mapped correctly
        #Each value should equal 2.66666666666
        for x in range(lulc.shape[1]):
            self.assertAlmostEqual(output[0][x], 2.6666666666, 8)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCarbonCore)
    unittest.TextTestRunner(verbosity=2).run(suite)





