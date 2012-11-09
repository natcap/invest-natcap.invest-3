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
        """A smoke test to make sure valuation does not crash with default
            input"""
        out_dir = './data/test_out/wind_energy/valuation/'
        input_dir = './data/wind_energy_data/'
        regression_dir = './data/wind_energy_regression_data/'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        args = {}
        args['workspace_dir'] = out_dir
        args['aoi_uri'] = os.path.join(
                input_dir, 'reprojected_distance_aoi.shp')
        args['biophysical_data_uri'] = os.path.join(
                regression_dir, 'wind_points_reprojected.shp')
        args['turbine_info_uri'] = os.path.join(
                input_dir, 'turbine_parameters.csv')
        args['grid_points_uri'] = os.path.join(
                input_dir, 'land_grid_points.csv')
        #args['land_polygon_uri'] = os.path.join(
        #        regression_dir, 'global_poly_clip.shp')
        args['number_of_machines'] = 30
        args['dollar_per_kWh'] = 1.81
        args['suffix'] = ''
        
        wind_energy_valuation.execute(args)

        # start making up some tests
