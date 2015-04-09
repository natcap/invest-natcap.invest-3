'''
python -m unittest test_crop_production_io
'''

import unittest
import os
import pprint
import tempfile

from numpy import testing
import numpy as np

import crop_production_io as io
import test_data

workspace_dir = '../../test/invest-data/test/data/crop_production/'
input_dir = os.path.join(workspace_dir, 'input')
pp = pprint.PrettyPrinter(indent=4)


class TestReadCropLookupTable(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'crop_lookup_table_uri': os.path.join(
                input_dir, 'crop_lookup_table.csv'),

        }

    def test_read_crop_lookup_table(self):
        guess = io.read_crop_lookup_table(self.vars_dict)
        crop_lookup_dict = guess['crop_lookup_dict']
        keys = crop_lookup_dict.keys()
        assert(all(map(lambda x: (type(x) is int), keys)))


class TestReadNutritionTable(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'nutrition_table_uri': os.path.join(
                input_dir, 'nutrition_table.csv'),
        }

    def test_read_nutrition_table(self):
        guess = io.read_nutrition_table(self.vars_dict)
        nutrition_table_dict = guess['nutrition_table_dict']
        keys = nutrition_table_dict.keys()
        assert(type(nutrition_table_dict[keys[0]]['energy']) in [float, int])


class TestReadEconomicsTable(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'economics_table_uri': os.path.join(
                input_dir, 'economics_table.csv'),
        }

    def test_read_economics_table(self):
        guess = io.read_economics_table(self.vars_dict)
        economics_table_dict = guess['economics_table_dict']
        keys = economics_table_dict.keys()
        assert(type(economics_table_dict[keys[0]]['price']) in [float, int])


class TestReadPercentileYieldTables(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'percentile_yield_tables_dir': os.path.join(
                input_dir,
                'spatial_dataset/climate_percentile_yield/'),
        }

    def test_read_percentile_yield_table(self):
        guess = io.read_percentile_yield_tables(self.vars_dict)
        # pp.pprint(guess)

        percentile_table_dict = guess['percentile_yield_dict']
        keys = percentile_table_dict.keys()
        assert(type(percentile_table_dict[keys[0]][1]['yield_25th']) in [float, int])


class TestReadRegressionModelYieldTables(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'modeled_yield_tables_dir': os.path.join(input_dir, 'spatial_dataset/climate_regression_yield/'),
        }

    def test_read_regression_model_yield_table(self):
        guess = io.read_regression_model_yield_tables(self.vars_dict)
        # pp.pprint(guess)

        modeled_yield_dict = guess['modeled_yield_dict']
        keys = modeled_yield_dict.keys()
        assert(type(modeled_yield_dict[keys[0]][1]['yield_ceiling']) in [float, int])


class TestFetchObservedYieldMaps(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'observed_yield_maps_dir': os.path.join(
                input_dir, 'spatial_dataset/observed_yield/'),
        }

    def test_fetch_observed_yield_maps(self):
        guess = io.fetch_observed_yield_maps(self.vars_dict)
        observed_yield_maps_dict = guess['observed_yields_maps_dict']
        # pp.pprint(observed_yield_maps_dict)
        keys = observed_yield_maps_dict.keys()
        assert(type(observed_yield_maps_dict[keys[0]]) is str)


class TestFetchClimateBinMaps(unittest.TestCase):
    def setUp(self):
        # Create Spatial Dataset Directory

        self.vars_dict = {
            'climate_bin_maps_dir': os.path.join(
                input_dir, 'spatial_dataset/climate_bin_maps/'),
        }

    def test_fetch_climate_bin_maps(self):
        guess = io.fetch_climate_bin_maps(self.vars_dict)
        climate_bin_maps_dict = guess['climate_bin_maps_dict']
        keys = climate_bin_maps_dict.keys()
        assert(type(climate_bin_maps_dict[keys[0]]) is str)


class TestFetchSpatialDataset(unittest.TestCase):
    def setUp(self):
        # Create Spatial Dataset Directory

        self.vars_dict = {
            'spatial_dataset_dir': os.path.join(
                input_dir, 'spatial_dataset/'),
            'do_yield_observed': True,
            'do_yield_percentile': True,
            'do_yield_regression_model': True,
        }

    def test_fetch_spatial_dataset(self):
        guess = io.fetch_spatial_dataset(self.vars_dict)
        # pp.pprint(guess)
        keys = guess.keys()
        assert('percentile_yield_dict' in keys)
        assert('observed_yields_maps_dict' in keys)
        assert('percentile_yield_dict' in keys)


class TestFetchModeledFertilizerMaps(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'modeled_fertilizer_maps_dir':  os.path.join(
                input_dir, 'fertilizer_maps'),
        }

    def test_fetch_modeled_fertilizer_maps(self):
        guess = io.fetch_modeled_fertilizer_maps(self.vars_dict)
        modeled_fertilizer_maps_dict = guess['modeled_fertilizer_maps_dict']
        keys = modeled_fertilizer_maps_dict.keys()
        assert(type(modeled_fertilizer_maps_dict[keys[0]]) is str)


class TestFetchArgs(unittest.TestCase):
    def setUp(self):
        self.args = test_data.get_args()

    def test_fetch_args(self):
        guess = io.fetch_args(self.args)
        # pp.pprint(guess)
        keys = guess.keys()
        assert('percentile_yield_dict' in keys)
        assert('observed_yields_maps_dict' in keys)
        assert('percentile_yield_dict' in keys)
        assert('nutrition_table_dict' in keys)
        assert('economics_table_dict' in keys)
        assert('modeled_fertilizer_maps_dict' in keys)
        assert('crop_lookup_dict' in keys)
        # l = [i for i in guess.keys() if i not in self.args.keys()]
        # pp.pprint(l)


if __name__ == '__main__':
    test_data.get_vars_dict()
    unittest.main()
