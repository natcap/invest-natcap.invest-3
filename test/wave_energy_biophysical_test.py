import os
import sys
import unittest

import numpy as np
from osgeo import ogr
from invest_natcap.wave_energy import wave_energy_biophysical
import invest_test_core

class TestWaveEnergyBiophysical(unittest.TestCase):
    def test_wave_energy_biophysical(self):
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
        
        #Regression Check for WEM_InputOutput_Pts shapefile
        wave_data_shape_path = args['workspace_dir'] + '/Intermediate/WEM_InputOutput_Pts.shp'
        regression_shape_path = regression_dir + '/WEM_InputOutput_Pts_bio_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, wave_data_shape_path, regression_shape_path)

    def test_wave_energy_extrapolate_wave_data(self):
        wave_base_data_uri = './data/wave_energy_data/test_input/sampWaveDataTest.txt'
        if os.path.isfile(wave_base_data_uri):
            wave_data = wave_energy_biophysical.extrapolate_wave_data(wave_base_data_uri)
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

            test_dict = {(580, 507): matrix1, (580, 508): matrix2}
            for key, value in test_dict.iteritems():
                if key in wave_data:
                    self.assertTrue((value == wave_data[key]).all, msg)
                else:
                    self.assertEqual(0, 1, 'Keys do not match')
            for val, val2 in zip(row, wave_data[0]):
                self.assertEqual(val, val2)
            for val, val2 in zip(col, wave_data[1]):
                self.assertEqual(val, val2)
        else:
            print 'NOT A FILE'
