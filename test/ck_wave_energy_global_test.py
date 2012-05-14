import os
import sys
import unittest
import logging

import numpy as np
from osgeo import ogr
from invest_natcap.ck_wave_energy import wave_energy_biophysical
import invest_test_core
from invest_natcap.dbfpy import dbf

LOGGER = logging.getLogger('ck_wave_energy_global_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaveEnergyBiophysical(unittest.TestCase):
    def test_wave_energy_biophysical_regression(self):
        """A regression test for wave_energy_biophysical that passes
           in sample inputs with the area of interest.  It runs the outputs
           againts regression files that are known to be accurate"""
        args = {}
        test_dir = './data/wave_energy_data/'
        output_dir = './data/test_out/ck_we_global_out_WD'
        args['workspace_dir'] = output_dir
        args['wave_base_data_uri'] = test_dir + 'samp_input/WaveData'
        args['analysis_area_uri'] = 'Global(Eastern Hemisphere)'
        args['machine_perf_uri'] = \
            test_dir + 'samp_input/Machine_WaveDragon.csv'
        args['machine_param_uri'] = \
            test_dir + 'samp_input/Machine_WaveDragon_Param.csv'
        args['dem_uri'] = test_dir + 'samp_input/global_dem'
        
        #New input for the global shapefile information
        args['bin_attributes'] = test_dir + 'ck_new_input/new_grid.csv'
        args['global_shape'] = test_dir + 'ck_new_input/new_global_shape.shp'
        
#        args['aoi_uri'] = test_dir + 'samp_input/AOI_WCVI.shp'
        
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        wave_energy_biophysical.execute(args)
#        
#        regression_dir = './data/wave_energy_regression_data/'
#        
#        #assert that the captured wave energy output raster is equivalent 
#        #to the regression test
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            output_dir + os.sep + 'Output/capwe_mwh.tif',
#            regression_dir + 'capwe_mwh_regression.tif')
#        
#        #assert that the wave power output raster is equivalent to the 
#        #regression test
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            output_dir + os.sep + 'Output/wp_kw.tif',
#            regression_dir + 'wp_kw_regression.tif')
#        
#        #Regression Check for wave power percentile raster
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            output_dir + os.sep + 'Output/wp_rc.tif',
#            regression_dir + '/wp_rc_regression.tif')
#        
#        #Regression Check for captured wave energy percentile raster
#        invest_test_core.assertTwoDatasetEqualURI(self,
#            output_dir + os.sep + 'Output/capwe_rc.tif',
#            regression_dir + 'capwe_rc_regression.tif')        
#        
#        #Regression Check for WEM_InputOutput_Pts shapefile
#        wave_data_shape_path = \
#            output_dir + os.sep + 'Intermediate/WEM_InputOutput_Pts.shp'
#        regression_shape_path = \
#            regression_dir + 'WEM_InputOutput_Pts_bio_regression.shp'
#        invest_test_core.assertTwoShapesEqualURI(self, wave_data_shape_path, 
#                                                 regression_shape_path)
#        
#        #Regression check to make sure the dbf files with the attributes for the
#        #percentile rasters are correct
#        try:
#            regression_table = \
#                dbf.Dbf(regression_dir + 'wp_rc_regression.tif.vat.dbf')
#            db_file = dbf.Dbf(output_dir + os.sep + 'Output/wp_rc.tif.vat.dbf')
#            value_array = []
#            count_array = []
#            val_range_array = []
#            for rec, reg_rec in zip(db_file, regression_table):
#                self.assertEqual(rec['VALUE'], reg_rec['VALUE'])
#                self.assertEqual(rec['COUNT'], reg_rec['COUNT'])
#                self.assertEqual(rec['VAL_RANGE'], reg_rec['VAL_RANGE'])
#            db_file.close()
#            regression_table.close()
#        except IOError, error:
#            self.assertTrue(False, 'The dbf file could not be opened')
#
#        try:
#            regression_table = \
#                dbf.Dbf(regression_dir + 'capwe_rc_regression.tif.vat.dbf')
#            db_file = dbf.Dbf(output_dir + os.sep + 'Output/capwe_rc.tif.vat.dbf')
#            value_array = []
#            count_array = []
#            val_range_array = []
#            for rec, reg_rec in zip(db_file, regression_table):
#                self.assertEqual(rec['VALUE'], reg_rec['VALUE'])
#                self.assertEqual(rec['COUNT'], reg_rec['COUNT'])
#                self.assertEqual(rec['VAL_RANGE'], reg_rec['VAL_RANGE'])
#            db_file.close()
#            regression_table.close()
#        except IOError, error:
#            self.assertTrue(False, 'The dbf file could not be opened')
#
#    def test_wave_energy_extrapolate_wave_data(self):
#        """A test for the extrapolate_wate_data function that
#           compares hand calculated results against the returned
#           function generated results
#        """
#        wave_base_data_uri = \
#            './data/wave_energy_data/test_input/sampWaveDataTest.txt'
#        if os.path.isfile(wave_base_data_uri):
#            wave_data = \
#               wave_energy_biophysical.extrapolate_wave_data(wave_base_data_uri)
#            LOGGER.debug('Extrapolated Wave Data : %s', wave_data)
#            #Hand generated results
#            row = np.array([.25, 1.0, 2.0, 3.0, 4.0, 5.0])
#            col = np.array([.125, .5, 1.0, 1.5, 2.0, 2.5])
#            matrix1 = np.array([[0., 0., 0., 0., 0., 0.],
#                                [0., 0., 0., 3.0, 0., 0.],
#                                [0., 0., 0., 0., 24.0, 27.0],
#                                [0., 0., 0., 0., 3.0, 219.0],
#                                [0., 0., 0., 0., 0., 84.0],
#                                [0., 0., 0., 0., 0., 12.0]])
#            matrix2 = np.array([[0., 0., 0., 0., 0., 0.],
#                                [0., 0., 0., 3.0, 0., 0.],
#                                [0., 0., 0., 0., 24.0, 21.0],
#                                [0., 0., 0., 0., 3.0, 219.0],
#                                [0., 0., 0., 0., 0., 78.0],
#                                [0., 0., 0., 0., 0., 12.0]])
#            #Place hand generated results in dictionary
#            test_dict = {(580, 507): matrix1, (580, 508): matrix2}
#            #Check hand generated results vs. function results
#            for key, value in test_dict.iteritems():
#                if key in wave_data['bin_matrix']:
#                    self.assertTrue((value == \
#                                     np.array(wave_data['bin_matrix'][key], 
#                                              dtype='f')).all)
#                else:
#                    self.assertEqual(0, 1, 'Keys do not match')
#            #Check rows/column header results
#            for val, val2 in zip(row, wave_data['periods']):
#                self.assertEqual(val, val2)
#            for val, val2 in zip(col, wave_data['heights']):
#                self.assertEqual(val, val2)
#        else:
#            print 'NOT A FILE: ' + wave_base_data_uri
