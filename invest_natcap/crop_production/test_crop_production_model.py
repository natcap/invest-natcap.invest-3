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

from raster import Raster, RasterFactory
import crop_production_model as model

workspace_dir = '../../test/invest-data/test/data/crop_production/'
input_dir = '../../test/invest-data/test/data/crop_production/input/'
pp = pprint.PrettyPrinter(indent=4)


class TestCreateYieldFuncOutputFolder(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run1(self):
        guess = model.create_yield_func_output_folder(self.vars_dict, 'observed')
        pass


class TestCreateResultsTable(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

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
