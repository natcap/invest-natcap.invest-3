import os
import sys
import unittest
import logging

import numpy as np
from osgeo import ogr
from invest_natcap.wave_energy import wave_energy_valuation
import invest_test_core

LOGGER = logging.getLogger('wave_energy_valuation_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaveEnergyValuation(unittest.TestCase):
    def test_wave_energy_valuation_regression(self):
        """A regression test for valuation file to make sure that the output
        raster and output shapefile are what is expected.
        """
        args = {}
        args['workspace_dir'] = './data/wave_energy_data'
        args['wave_base_data_uri'] = args['workspace_dir'] + os.sep + 'samp_input/WaveData'
        args['land_gridPts_uri'] = args['workspace_dir'] + os.sep + 'samp_input/LandGridPts_WCVI_221.csv'
        args['machine_econ_uri'] = args['workspace_dir'] + os.sep + 'samp_input/Machine_PelamisEconCSV.csv'
        args['number_of_machines'] = 28
        args['global_dem'] = args['workspace_dir'] + os.sep + 'samp_input/global_dem'
        args['wave_data_shape_path'] = args['workspace_dir'] + os.sep + 'Intermediate/WEM_InputOutput_Pts.shp'
        
        wave_energy_valuation.execute(args)
        regression_dir = './data/wave_energy_regression_data'
        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/npv_usd.tif',
            regression_dir + '/npv_usd_regression.tif')

        #Regression Check for LandPts_prj shapefile
        landing_shape_path = args['workspace_dir'] + '/Output/LandPts_prj.shp'
        regression_landing_shape_path = regression_dir + '/LandPts_prj_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, landing_shape_path, regression_landing_shape_path)
        #Regression Check for GridPts_prj shapefile
        grid_shape_path = args['workspace_dir'] + '/Output/GridPts_prj.shp'
        regression_grid_shape_path = regression_dir + '/GridPts_prj_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, grid_shape_path, regression_grid_shape_path)
        #Regression Check for WEM_InputOutput_Pts shapefile
        wave_data_shape_path = args['workspace_dir'] + '/Intermediate/WEM_InputOutput_Pts.shp'
        regression_wave_data_shape_path = regression_dir + '/WEM_InputOutput_Pts_val_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, wave_data_shape_path, regression_wave_data_shape_path)
