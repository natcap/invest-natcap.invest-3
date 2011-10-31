import os, sys
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')
import carbon_core
import unittest
from osgeo import ogr, gdal
from osgeo.gdalconst import *
from dbfpy import dbf
import numpy as np

class TestInvestCarbonCore(unittest.TestCase):
    def test_carbon_core_nodata(self):
        """Test several raster sizes that have only nodata values"""
        driver = gdal.GetDriverByName("GTIFF")

        for xDim, yDim, inNoData, outNodata in [(1, 1, 255, 1.0),
                                                (10, 10, 255, 21.0),
                                                (443, 953, 2, 1.0),
                                                (719, 211, 12, 111.5)]:
            #Create a blank xDim x yDim raster
            lulc = driver.Create('../../../test_data/test_blank_input', xDim, yDim, 1,
                                 gdal.GDT_Byte)
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

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCarbonCore)
    unittest.TextTestRunner(verbosity=2).run(suite)





