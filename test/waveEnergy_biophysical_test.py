import os
import sys
import unittest

from invest.wave_energy import waveEnergy_biophysical
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

    def test_waveEnergy_extrapWaveData(self):
        wave_base_data_uri = './data/test_data/wave_Energy/test_input/sampleWCWaveData.txt'
        if os.path.isfile(wave_base_data_uri):
            waveData = waveEnergy_biophysical.extrapolateWaveData(wave_base_data_uri)

#            print waveData
        else:
            print 'NOT A FILE'

suite = unittest.TestLoader().loadTestsFromTestCase(TestWaveEnergyBiophysical)
unittest.TextTestRunner(verbosity=2).run(suite)
