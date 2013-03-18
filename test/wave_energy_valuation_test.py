import os
import sys
import unittest
import logging

import numpy as np
from osgeo import ogr
from invest_natcap.wave_energy import wave_energy_valuation
import invest_test_core
from invest_natcap.dbfpy import dbf

LOGGER = logging.getLogger('wave_energy_valuation_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaveEnergyValuation(unittest.TestCase):
    def test_wave_energy_valuation_regression(self):
        """A regression test for valuation file to make sure that the output
        raster and output shapefile are what is expected.
        """
        args = {}
        test_dir = './data/wave_energy_data/'
        output_dir = './data/test_out/wave_energy_valuation_output'
        args['workspace_dir'] = output_dir
        args['wave_base_data_uri'] = test_dir + 'samp_input/WaveData'
        args['land_gridPts_uri'] = \
            test_dir + 'samp_input/LandGridPts_WCVI_221.csv'
        args['machine_econ_uri'] = \
            test_dir + 'samp_input/Machine_PelamisEconCSV.csv'
        args['number_of_machines'] = 28
        args['global_dem'] = test_dir + 'samp_input/global_dem'
        
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        
        wave_data_shape_path = \
            test_dir + 'test_input/WEM_InputOutput_Pts_Bio.shp'
        wave_data_copy_path = \
            test_dir + os.sep + 'test_input/WEM_InputOutputs_Bio_copy.shp'
        wave_data_shape = ogr.Open(wave_data_shape_path)
        if os.path.isfile(wave_data_copy_path):
            os.remove(wave_data_copy_path)
        wave_data_shape_copy = \
            ogr.GetDriverByName('ESRI Shapefile').\
                CopyDataSource(wave_data_shape, wave_data_copy_path)
        wave_data_shape_copy.Destroy()
        args['wave_data_shape_path'] = wave_data_copy_path

        wave_energy_valuation.execute(args)
        regression_dir = './data/wave_energy_regression_data/'
        
        #Regression Check for NPV raster
        invest_test_core.assertTwoDatasetEqualURI(self,
            output_dir + os.sep + 'Output/npv_usd.tif',
            regression_dir + 'npv_usd_regression.tif')
        
        #Regression Check for NPV percentile raster
        invest_test_core.assertTwoDatasetEqualURI(self,
            output_dir + os.sep + 'Output/npv_rc.tif',
            regression_dir + 'npv_rc_regression.tif')
        
        #Regression Check for LandPts_prj shapefile
        landing_shape_path = output_dir + os.sep + 'Output/LandPts_prj.shp'
        regression_landing_shape_path = \
            regression_dir + 'LandPts_prj_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, landing_shape_path, 
                                                 regression_landing_shape_path)
        
        #Regression Check for GridPts_prj shapefile
        grid_shape_path = output_dir + os.sep + 'Output/GridPts_prj.shp'
        regression_grid_shape_path = \
            regression_dir + 'GridPts_prj_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, grid_shape_path, 
                                                 regression_grid_shape_path)
        
        #Regression Check for WEM_InputOutput_Pts shapefile
        regression_wave_data_shape_path = \
            regression_dir + 'WEM_InputOutput_Pts_val_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, wave_data_copy_path, 
                                                 regression_wave_data_shape_path)

        try:
            regression_table = dbf.Dbf(regression_dir + os.sep + \
                                      'npv_rc_regression.tif.vat.dbf')
            db_file = dbf.Dbf(output_dir + os.sep + 'Output/npv_rc.tif.vat.dbf')
            value_array = []
            count_array = []
            val_range_array = []
            for rec, reg_rec in zip(db_file, regression_table):
                self.assertEqual(rec['VALUE'], reg_rec['VALUE'])
                self.assertEqual(rec['COUNT'], reg_rec['COUNT'])
                self.assertEqual(rec['VAL_RANGE'], reg_rec['VAL_RANGE'])
            db_file.close()
            regression_table.close()
        except IOError, error:
            self.assertTrue(False, 'The dbf file could not be opened')
