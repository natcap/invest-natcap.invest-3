import unittest
import carbon_core
import data_handler
import numpy as np
import os
from dbfpy import dbf

try:
    from osgeo import ogr, gdal
    from osgeo.gdalconst import *
    import numpy
    use_numeric = False
except ImportError:
    import ogr, gdal
    from gdalconst import *
    import Numeric

class TestCarbonCore(unittest.TestCase):
    def test_carbon_core_smoke(self):
        """Smoke test for carbon_core function.  Shouldn't crash with
        zero length inputs"""
        driver = gdal.GetDriverByName("GTIFF")
        lulc_path = '../../test_data/test_blank_input'
        lulc = driver.Create(lulc_path, 1, 1, 1, gdal.GDT_Byte)
        lulc.GetRasterBand(1).SetNoDataValue(-1.0)

        output_path = '../../test_data/test_blank_output'
        output = driver.Create(output_path, 1, 1, 1, gdal.GDT_Byte)
        output.GetRasterBand(1).SetNoDataValue(-1.0)

        args = { 'lulc_cur':lulc,
                'carbon_pools': dbf.Dbf('../../test_data/test_blank_dbf', new=True),
                'storage_cur': output,
                'calc_value' : False}
        
        carbon_core.execute(args)
        
        #close the two created datasets and dbf file.
        lulc = None
        output = None
        data_handler.close(args['carbon_pools'])
        
        os.remove(output_path)
        os.remove('../../test_data/test_blank_dbf')
        os.remove(lulc_path)
        pass

    def test_carbon_core_with_inputs(self):
        """Test carbon_core using realistic inputs."""
        driver = gdal.GetDriverByName("GTIFF")
        lulc = gdal.Open('../../test_data/lulc_samp_cur', GA_ReadOnly)
        out_dict = {'uri':'../../test_real_output.tif',
                    'input':False,
                    'type': 'gdal',
                    'dataType': 6}
        output = data_handler.mimic(lulc, out_dict)
        args = { 'lulc_cur': lulc,
                'carbon_pools': dbf.Dbf('../../test_data/carbon_pools_int.dbf'),
                'storage_cur': output,
                'calc_value' : False}

        carbon_core.execute(args)
        output = data_handler.close(output)
        os.remove(out_dict['uri'])
        pass

    def test_carbon_core_with_HWP_inputs(self):
        """Test carbon_core using realistic inputs.  Includes HWP"""
        driver = gdal.GetDriverByName("GTIFF")
        lulc = gdal.Open('../../test_data/lulc_samp_cur', GA_ReadOnly)
        out_dict = {'uri':'../../carbon_output/test_real_output_hwp.tif',
                    'input':False,
                    'type': 'gdal',
                    'dataType': 6}
        output = data_handler.mimic(lulc, out_dict)
        args = { 'lulc_cur': lulc,
                'carbon_pools': dbf.Dbf('../../test_data/carbon_pools_int.dbf'),
                'storage_cur': output,
                'calc_value' : False,
                'hwp_cur_shape': ogr.Open('../../test_data/harv_samp_cur/harv_samp_cur.shp')}

        

        carbon_core.execute(args)
        output = data_handler.close(output)
        #os.remove(out_dict['uri'])
        pass


    def test_build_pools(self):
        """Verify the correct construction of the pools dict"""
        db = dbf.Dbf('../../test_data/carbon_pools_float.dbf', readOnly=1)
        pools = carbon_core.build_pools_dict(db, 1, -1, 255)
        numRecords = db.recordCount
        poolsLen = len(pools)

        #adding one extra value to the expected length of the pools dict
        #Extra entry represents the nodata value.
        self.assertEqual(numRecords + 1, poolsLen, 'Expected ' + str(numRecords) +
                         ' records in the pools dict, but found ' + str(poolsLen) + ' instead')
        pass

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonCore)
    unittest.TextTestRunner(verbosity=2).run(suite)

