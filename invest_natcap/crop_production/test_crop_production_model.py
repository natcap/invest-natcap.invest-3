'''
python -m unittest test_crop_production_model
'''

import unittest
import os
import pprint
import tempfile

import gdal
from numpy import testing
import numpy as np
from affine import Affine

from ..raster import Raster, RasterFactory
import crop_production_model as model

workspace_dir = '../../test/invest-data/test/data/crop_production/'
input_dir = '../../test/invest-data/test/data/crop_production/input/'
pp = pprint.PrettyPrinter(indent=4)

# set arguments
shape = (180, 360)
affine = Affine(1, 0, -180, 0, -1, 90)
proj = 4326
datatype = gdal.GDT_Float64
nodata_val = -9999

global_raster_factory = RasterFactory(
    proj,
    datatype,
    nodata_val,
    shape[0],
    shape[1],
    affine=affine)


class TestCreateYieldFuncOutputFolder(unittest.TestCase):
    def setUp(self):
        corn_observed = global_raster_factory.horizontal_ramp(1.0, 10.0)

        self.vars_dict = {
            'output_dir': tempfile.mkdtemp(),
            'results_suffix': 'scenario1',
            'create_crop_production_maps': True,
        }

    def test_run1(self):
        guess = model.create_yield_func_output_folder(
            self.vars_dict, 'observed')

        assert(os.path.exists(guess['output_yield_func_dir']))
        assert(os.path.exists(guess['output_production_maps_dir']))


class TestCreateResultsTableObserved(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'observed_yield_maps_dir': 'path/to/dir',
            'percentile_yield_tables_dir': 'path/to/dir',
            'percentile_yield_dict': {},
            'crop_lookup_dict': {},
            'crop_lookup_table_uri': 'path/to/file',
            'economics_table_dict': {},
            'climate_bin_maps_dir': 'path/to/dir',
            'lulc_map_uri': 'path/to/file',
            'modeled_fertilizer_maps_dir': 'path/to/dir',
            'do_nutrition': True,
            'do_yield_observed': True,
            'workspace_dir': 'path/to/dir',
            'modeled_irrigation_map_uri': 'path/to/file',
            'spatial_dataset_dir': 'path/to/dir',
            'modeled_fertilizer_maps_dict': {},
            'modeled_yield_tables_dir': 'path/to/dir',
            'modeled_yield_dict': {},
            'economics_table_uri': 'path/to/file',
            'do_yield_regression_model': True,
            'observed_yields_maps_dict': {},
            'nutrition_table_dict': {},
            'do_economic_returns': True,
            'create_crop_production_maps': True,
            'climate_bin_maps_dict': {},
            'results_suffix': 'scenario_1',
            'nutrition_table_uri': 'path/to/file',
            'do_yield_percentile': True
        }

    def test_run1(self):
        guess = model.create_yield_func_output_folder(self.vars_dict, 'observed')
        pass


class TestCalcObservedYield(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'lulc_map_uri': os.path.join(input_dir, 'lulc_map.tif'),
            'crop_lookup_dict': {
                1: 'corn',
            },
            'observed_yields_maps_dict': {
                'corn': os.path.join(  # global raster of 5's
                    input_dir,
                    'spatial_dataset/observed_yield/corn_yield_map.tif'),
            },
            'tmp_observed_dir': tempfile.mkdtemp(),
        }

    def test_run1(self):
        guess = model.calc_observed_yield(self.vars_dict, 'observed')
        pass


if __name__ == '__main__':
    unittest.main()
