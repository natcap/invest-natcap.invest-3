import os
import sys
import unittest

import numpy as np
from invest_natcap.wave_energy import waveEnergy_biophysical
import invest_test_core

class TestWaveEnergyBiophysical(unittest.TestCase):
    def test_waveEnergy_smoke(self):
        args = {}
        args['workspace_dir'] = './data/test_data/wave_Energy'
        args['wave_base_data_uri'] = './data/test_data/wave_Energy/samp_input/WaveData'
        args['analysis_area_uri'] = 'West Coast of North America and Hawaii'
        args['machine_perf_uri'] = './data/test_data/wave_Energy/samp_input/Machine_PelamisPerfCSV.csv'
        args['machine_param_uri'] = './data/test_data/wave_Energy/samp_input/Machine_PelamisParamCSV.csv'
        args['dem_uri'] = './data/test_data/wave_Energy/samp_input/global_dem'
        args['AOI_uri'] = './data/test_data/wave_Energy/samp_input/AOI_WCVI.shp'
        waveEnergy_biophysical.execute(args)

        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Intermediate/capwe_mwh.tif',
            args['workspace_dir'] + '/regression_tests/capwe_mwh_regression.tif')
        
        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Intermediate/wp_kw.tif',
            args['workspace_dir'] + '/regression_tests/wp_kw_regression.tif')
        
        #Check Following Shapefiles:
        
            #WaveData_clipZ
            
            #landingPoints
            
            #gridPoint


    def test_waveEnergy_extrapWaveData(self):
        wave_base_data_uri = './data/test_data/wave_Energy/test_input/sampWaveDataTest.txt'
        if os.path.isfile(wave_base_data_uri):
            waveData = waveEnergy_biophysical.extrapolateWaveData(wave_base_data_uri)
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

            testDict = {(580, 507): matrix1, (580, 508): matrix2}
            keys = [(580, 507), (580, 508)]
            for key in testDict:
                if key in waveData:
                    for i, ar in enumerate(testDict[key]):
                        for index, val in enumerate(ar):
                            self.assertEqual(val, float(waveData[key][i][index]))
                else:
                    self.assertEqual(0, 1, 'Keys do not match')
            for val, val2 in zip(row, waveData[0]):
                self.assertEqual(val, val2)
            for val, val2 in zip(col, waveData[1]):
                self.assertEqual(val, val2)

        else:
            print 'NOT A FILE'
