'''
python -m unittest test_crop_production_io
'''

import unittest
import os
import pprint
import tempfile
import shutil

from numpy import testing
import numpy as np
import pygeoprocessing as pygeo

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


class TestCreateCropsInAOIList(unittest.TestCase):
    def setUp(self):
        d = {'crop_lookup_table_uri': os.path.join(
            input_dir, 'crop_lookup_table.csv')}

        self.vars_dict = {
            'crop_lookup_dict': io.read_crop_lookup_table(d)['crop_lookup_dict'],
            'lulc_map_uri': test_data.create_lulc_map(test_data.aoi_dict)
        }

    def test_read_crop_lookup_table(self):
        guess = io.create_crops_in_aoi_list(self.vars_dict)
        # print guess


class TestReadNutritionTable(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {
            'nutrition_table_uri': os.path.join(
                input_dir, 'nutrition_table.csv'),
            'crops_in_aoi_list': ['corn', 'soy', 'rice']
        }

    def test_read_nutrition_table(self):
        guess = io.read_nutrition_table(self.vars_dict)
        nutrition_table_dict = guess['nutrition_table_dict']
        # pp.pprint(nutrition_table_dict)
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
        # pp.pprint(economics_table_dict)
        keys = economics_table_dict.keys()
        assert(type(economics_table_dict[keys[0]]['price_per_tonne']) in [float, int])


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
            'do_yield_regression': True,
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
            'fertilizer_maps_dir':  os.path.join(
                input_dir, 'fertilizer_maps'),
        }

    def test_fetch_fertilizer_maps(self):
        guess = io.fetch_fertilizer_maps(self.vars_dict)
        fertilizer_maps_dict = guess['fertilizer_maps_dict']
        keys = fertilizer_maps_dict.keys()
        assert(type(fertilizer_maps_dict[keys[0]]) is str)


class TestGetInputs(unittest.TestCase):
    def setUp(self):
        self.args = test_data.get_args()

    def test_get_inputs(self):
        guess = io.get_inputs(self.args)
        # pp.pprint(guess)
        keys = guess.keys()
        assert('percentile_yield_dict' in keys)
        assert('observed_yields_maps_dict' in keys)
        assert('percentile_yield_dict' in keys)
        assert('nutrition_table_dict' in keys)
        assert('economics_table_dict' in keys)
        assert('fertilizer_maps_dict' in keys)
        assert('crop_lookup_dict' in keys)
        # l = [i for i in guess.keys() if i not in self.args.keys()]
        # pp.pprint(l)


class TestCreateResultsTable(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def test_run1(self):
        vars_dict = test_data.get_vars_dict()
        vars_dict['crop_production_dict'] = {
            'corn': 1.0,
            'soy': 2.0,
            'rice': 3.0
        }
        vars_dict['output_yield_func_dir'] = self.tempdir
        vars_dict['crop_total_nutrition_dict'] = {
            'corn': {
                'ca': 13,
                'energy': 12,
                'fe': 14,
                'lipid': 11,
                'mg': 15,
                'percent_refuse': 0.5,
                'ph': 16,
                'protein': 10},
            'rice': {
                'ca': 33,
                'energy': 32,
                'fe': 34,
                'lipid': 31,
                'mg': 35,
                'percent_refuse': 0.7,
                'ph': 36,
                'protein': 30},
            'soy': {
                'ca': 23,
                'energy': 22,
                'fe': 24,
                'lipid': 21,
                'mg': 25,
                'percent_refuse': 0.2,
                'ph': 26,
                'protein': 20}}
        vars_dict['economics_table_dict'] = {
            'corn': {
                'total_returns': 1.0,
                'total_revenue': 1.0,
                'total_cost': 0.0
            },
            'soy': {
                'total_returns': 1.0,
                'total_revenue': 1.0,
                'total_cost': 0.0
            },
            'rice': {
                'total_returns': 1.0,
                'total_revenue': 1.0,
                'total_cost': 0.0
            }
        }
        guess = io.create_results_table(vars_dict)
        check = pygeo.get_lookup_from_csv(
            os.path.join(self.tempdir, 'results_table.csv'), 'crop')
        # pp.pprint(check)

    def tearDown(self):
        shutil.rmtree(self.tempdir)


if __name__ == '__main__':
    test_data.get_vars_dict()
    unittest.main()
