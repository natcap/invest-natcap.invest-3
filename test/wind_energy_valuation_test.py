"""URI level tests for the wind_energy valuation module"""

import os.path
import sys
from osgeo import gdal
import unittest
from nose.plugins.skip import SkipTest

from invest_natcap.wind_energy import wind_energy_valuation
import invest_test_core

class TestWindEnergyValuation(unittest.TestCase):
    def test_wind_energy_valuation(self):
        """Doc String"""
        out_dir = './data/test_out/wind_energy/wind_energy_valuation/'
        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        args = {}
        args['workspace_dir'] = out_dir
        args['harvested_energy_uri'] = os.path.join(
                regression_dir, 'harvested_masked.tif')
        args['distance_uri'] = os.path.join(regression_dir, 'distance_mask.tif')
        args['biophysical_data_uri'] = os.path.join(
                regression_dir, 'wind_points_reprojected.shp')
        args['turbine_info_uri'] = os.path.join(
                input_dir, 'turbine_parameters.csv')
        args['grid_points_uri'] = os.path.join(
                input_dir, 'land_grid_points.csv')
        args['number_of_machines'] = 30
        args['dollar_per_kWh'] = 1.81
        #args['suffix'] = ''
        
        wind_energy_valuation.execute(args)

        # start making up some tests
