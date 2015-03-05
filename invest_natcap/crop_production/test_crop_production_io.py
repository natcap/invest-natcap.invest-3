import unittest
import os
import pprint

from numpy import testing
import numpy as np

import crop_production_io as io

workspace_dir = '../../test/invest-data/test/data/crop_production/'
input_dir = os.path.join(workspace_dir, 'input')
pp = pprint.PrettyPrinter(indent=4)


class TestIOReadCropLookupTable(unittest.TestCase):
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


class TestIOReadNutritionTable(unittest.TestCase):
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


class TestIOReadEconomicsTable(unittest.TestCase):
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


# NOT IMPLEMENTED YET
class TestIOReadPercentileYieldTable(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'percentile_table_uri': os.path.join(
                input_dir,
                'spatial_dataset/climate_percentile_yield/percentile_yield_table.csv'),
        }

    def test_read_percentile_yield_table(self):
        guess = io.read_percentile_yield_table(self.vars_dict)
        pp.pprint(guess)

        percentile_table_dict = guess['percentile_table_dict']
        keys = percentile_table_dict.keys()
        assert(type(percentile_table_dict[keys[0]][1]['yield_25th']) in [float, int])


# NOT IMPLEMENTED YET
class TestIOReadRegressionModelYieldTable(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'spatial_dataset_dir': os.path.join(input_dir, 'spatial_dataset'),
        }

    def test_read_regression_model_yield_table(self):
        guess = io.read_regression_model_table(self.vars_dict)
        pp.pprint(guess)


class TestIOFetchObservedYieldMaps(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'observed_yield_maps_dir': os.path.join(
                input_dir, 'spatial_dataset/observed_yield/'),
        }

    def test_fetch_observed_yield_maps(self):
        guess = io.fetch_observed_yield_maps(self.vars_dict)
        observed_yield_maps_dict = guess['observed_yields_maps_dict']
        keys = observed_yield_maps_dict.keys()
        assert(type(observed_yield_maps_dict[keys[0]]) is str)


class TestIOFetchClimateBinMaps(unittest.TestCase):
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


# UNIMPLEMENTED FUNCTIONS MUST BE IMPLEMENTED FIRST
class TestIOFetchSpatialDataset(unittest.TestCase):
    def setUp(self):
        # Create Spatial Dataset Directory

        self.vars_dict = {
            'spatial_dataset_dir': None,
        }

    def test_fetch_spatial_dataset(self):
        guess = io.fetch_spatial_dataset(self.vars_dict)
        pp.pprint(guess)


class TestIOFetchModeledFertilizerMaps(unittest.TestCase):
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


class TestIOFetchArgs(unittest.TestCase):
    def setUp(self):
        self.args = {
            'workspace_dir': workspace_dir,
            'results_suffix': 'scenario_name',
            'lulc_map_uri': os.path.join(input_dir, 'lulc_map.tif'),
            'crop_lookup_table_uri': os.path.join(
                input_dir, 'crop_lookup_table.csv'),
            'spatial_dataset_dir': os.path.join(input_dir, 'spatial_dataset'),
            'create_crop_production_maps': True,
            'do_yield_observed': True,
            'do_yield_percentile': True,
            'do_yield_regression_model': True,
            'modeled_fertilizer_maps_dir': os.path.join(
                input_dir, 'modeled_fertilizer_maps'),
            'modeled_irrigation_map_uri':  os.path.join(
                input_dir, 'irrigation_map.tif'),
            'do_nutrition': True,
            'nutrition_table_uri': os.path.join(
                input_dir, 'nutrition_table.csv'),
            'do_economic_returns': True,
            'economics_table_uri': os.path.join(
                input_dir, 'economics_table.csv'),
        }

    def test_fetch_args(self):
        guess = io.fetch_args(self.args)
        pp.pprint(guess)


class TestIOCreateOutputs(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run(self):
        guess = io.create_outputs(self.vars_dict)
        pp.pprint(guess)


if __name__ == '__main__':
    unittest.main()
