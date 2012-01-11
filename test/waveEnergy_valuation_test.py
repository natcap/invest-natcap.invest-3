import os
import sys
import unittest

import numpy as np
from invest_natcap.wave_energy import waveEnergy_valuation
import invest_test_core

class TestWaveEnergyValuation(unittest.TestCase):
    def test_waveEnergy_smoke(self):
        """This function invokes the valuation part of the wave energy model given URI inputs.
        It will do filehandling and open/create appropriate objects to 
        pass to the core wave energy valuation processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - A python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and ouput folder/files will be saved.
        args['land_gridPts_uri'] - A CSV file path containing the Landing and Power Grid Connection Points table.
        args['machine_econ_uri'] - A CSV file path for the machine economic parameters table.
        args['numberOfMachines'] - An integer specifying the number of machines.
        args['projection_uri'] - A path for the projection to transform coordinates from decimal degrees to meters.
        args['captureWE'] - We need the captured wave energy output from biophysical run.
        args['globa_dem'] - We need the depth of the locations for calculating costs.
        args['']
        """
        
        
        
        args = {}
        args['workspace_dir'] = './data/test_data/wave_Energy'
        args['wave_base_data_uri'] = './data/test_data/wave_Energy/samp_input/WaveData'
        args['land_gridPts_uri'] = './data/test_data/wave_Energy/samp_input/LandGridPts_WCVI_CSV.csv'
        args['machine_econ_uri'] = './data/test_data/wave_Energy/samp_input/Machine_PelamisEconCSV.csv'
        args['numberOfMachines'] = 28
        args['projection_uri'] = './data/test_data/wave_Energy/test_input/WGS_1984_UTM_Zone_10N.prj'
        args['capturedWE'] = './data/test_data/wave_Energy/test_input/aoiCapWE.tif'
        args['global_dem'] = './data/test_data/wave_Energy/samp_input/global_dem'
        args['wave_data_shape_path'] = './data/test_data/wave_Energy/Intermediate/WaveData_clipZ.shp'
        
        waveEnergy_valuation.execute(args)

        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Intermediate/raster_projected.tif',
            args['workspace_dir'] + '/regression_tests/raster_projected.tif')
