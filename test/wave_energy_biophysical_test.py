import os
import sys
import unittest
import logging

import numpy as np
from osgeo import ogr
from invest_natcap.wave_energy import wave_energy_biophysical
import invest_test_core
from invest_natcap.dbfpy import dbf

LOGGER = logging.getLogger('wave_energy_biophysical_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaveEnergyBiophysical(unittest.TestCase):
    def test_wave_energy_biophysical_regression(self):
        """A regression test for wave_energy_biophysical that passes
           in sample inputs with the area of interest.  It runs the outputs
           againts regression files that are known to be accurate"""
        args = {}
        args['workspace_dir'] = './data/wave_energy_data'
        args['wave_base_data_uri'] = args['workspace_dir'] + os.sep + 'samp_input/WaveData'
        args['analysis_area_uri'] = 'West Coast of North America and Hawaii'
        args['machine_perf_uri'] = args['workspace_dir'] + os.sep + 'samp_input/Machine_PelamisPerfCSV.csv'
        args['machine_param_uri'] = args['workspace_dir'] + os.sep + 'samp_input/Machine_PelamisParamCSV.csv'
        args['dem_uri'] = args['workspace_dir'] + os.sep + 'samp_input/global_dem'
        args['aoi_uri'] = args['workspace_dir'] + os.sep + 'samp_input/AOI_WCVI.shp'
        wave_energy_biophysical.execute(args)
        regression_dir = './data/wave_energy_regression_data'
        #assert that the output raster is equivalent to the regression test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/capwe_mwh.tif',
            regression_dir + '/capwe_mwh_regression.tif')
        
        #assert that the output raster is equivalent to the regression test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/wp_kw.tif',
            regression_dir + '/wp_kw_regression.tif')
        
        #Regression Check for wave power percentile raster
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/wp_rc.tif',
            regression_dir + '/wp_rc_regression.tif')
        
        #Regression Check for captured wave energy percentile raster
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/capwe_rc.tif',
            regression_dir + '/capwe_rc_regression.tif')        
        
        #Regression Check for WEM_InputOutput_Pts shapefile
        wave_data_shape_path = args['workspace_dir'] + '/Intermediate/WEM_InputOutput_Pts.shp'
        regression_shape_path = regression_dir + '/WEM_InputOutput_Pts_bio_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, wave_data_shape_path, regression_shape_path)
        #Regression check to make sure the dbf files with the attributes for the
        #percentile rasters are correct
        try:
            regression_table = dbf.Dbf(regression_dir + os.sep + 'wp_rc_regression.tif.vat.dbf')
            db_file = dbf.Dbf(args['workspace_dir'] + os.sep + 'Output/wp_rc.tif.vat.dbf')
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

        try:
            regression_table = dbf.Dbf(regression_dir + os.sep + 'capwe_rc_regression.tif.vat.dbf')
            db_file = dbf.Dbf(args['workspace_dir'] + os.sep + 'Output/capwe_rc.tif.vat.dbf')
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

    def test_wave_energy_extrapolate_wave_data(self):
        """A test for the extrapolate_wate_data function that
           compares hand calculated results against the returned
           function generated results
        """
        wave_base_data_uri = './data/wave_energy_data/test_input/sampWaveDataTest.txt'
        if os.path.isfile(wave_base_data_uri):
            wave_data = wave_energy_biophysical.extrapolate_wave_data(wave_base_data_uri)
            #Hand generated results
            row = np.array([.25, 1.0, 2.0, 3.0, 4.0, 5.0])
            col = np.array([.125, .5, 1.0, 1.5, 2.0, 2.5])
            matrix1 = np.array([[0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 3.0, 0., 0.],
                                [0., 0., 0., 0., 24.0, 27.0],
                                [0., 0., 0., 0., 3.0, 219.0],
                                [0., 0., 0., 0., 0., 84.0],
                                [0., 0., 0., 0., 0., 12.0]])
            matrix2 = np.array([[0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 3.0, 0., 0.],
                                [0., 0., 0., 0., 24.0, 21.0],
                                [0., 0., 0., 0., 3.0, 219.0],
                                [0., 0., 0., 0., 0., 78.0],
                                [0., 0., 0., 0., 0., 12.0]])
            #Place hand generated results in dictionary
            test_dict = {(580, 507): matrix1, (580, 508): matrix2}
            #Check hand generated results vs. function results
            for key, value in test_dict.iteritems():
                if key in wave_data:
                    self.assertTrue((value == np.array(wave_data[key], dtype='f')).all)
                else:
                    self.assertEqual(0, 1, 'Keys do not match')
            #Check rows/column header results
            for val, val2 in zip(row, wave_data[0]):
                self.assertEqual(val, val2)
            for val, val2 in zip(col, wave_data[1]):
                self.assertEqual(val, val2)
        else:
            print 'NOT A FILE: ' + wave_base_data_uri
