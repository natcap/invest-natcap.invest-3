import os, sys
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../')
import carbon_core
import unittest
from osgeo import ogr, gdal
from osgeo.gdalconst import *
from dbfpy import dbf

class TestInvestCarbonCore(unittest.TestCase):
    def test_carbon_core_smoke(self):
        """Smoke test for carbon_uncertainty function.  Shouldn't crash with
        zero length inputs"""
        driver = gdal.GetDriverByName("GTIFF")

        #Create a blank 1x1 raster
        lulc = driver.Create('../../../test_data/test_blank_input', 1, 1, 1,
                             gdal.GDT_Byte)
        lulc.GetRasterBand(1).SetNoDataValue(-1.0)
        #Fill raster with nodata 
        lulc.GetRasterBand(1).Fill(-1.0)

        #Create the output raster
        tot_C_cur = driver.Create('../../../test_data/tot_C_cur_blank_output',
            lulc.RasterXSize, lulc.RasterYSize, 1, gdal.GDT_Float32)
        tot_C_cur.GetRasterBand(1).SetNoDataValue(-1.0)

        args = { 'lulc_cur': lulc,
                'carbon_pools': dbf.Dbf('../../../test_data/test_blank_dbf',
                                        new=True),
                'tot_C_cur': tot_C_cur}
        carbon_core.biophysical(args)

        #This is how GDAL closes its datasets in python
        output = None

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInvestCarbonCore)
    unittest.TextTestRunner(verbosity=2).run(suite)





