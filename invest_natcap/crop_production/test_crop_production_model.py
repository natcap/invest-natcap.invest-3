'''
python -m unittest test_crop_production_model
'''

import unittest
import os
import pprint
import tempfile
import shutil

import gdal
from numpy import testing
import numpy as np
from affine import Affine

import crop_production_model as model
from raster import Raster, RasterFactory
from vector import Vector
import test_data

workspace_dir = '../../test/invest-data/test/data/crop_production/'
input_dir = '../../test/invest-data/test/data/crop_production/input/'
pp = pprint.PrettyPrinter(indent=4)


class TestCreateYieldFuncOutputFolder(unittest.TestCase):
    def setUp(self):
        corn_observed = test_data.create_global_raster_factory(
            gdal.GDT_Float32).horizontal_ramp(1.0, 10.0)

        self.vars_dict = {
            'output_dir': os.path.join(workspace_dir, 'output'),
            'results_suffix': 'test_output_folder_generation',
            'create_crop_production_maps': True,
        }
        # self.output_yield_func_dir = None

    def test_run1(self):
        guess = model._create_yield_func_output_folder(
            self.vars_dict, 'observed')

        assert(os.path.exists(guess['output_yield_func_dir']))
        assert(os.path.exists(guess['output_production_maps_dir']))

        self.output_yield_func_dir = guess['output_yield_func_dir']

    def tearDown(self):
        shutil.rmtree(self.output_yield_func_dir)


class TestGetObservedYieldFromDataset(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        crop = 'corn'
        lulc_raster = test_data.create_lulc_map2(test_data.aoi_dict)
        aoi_vector = Vector.from_shapely(
            lulc_raster.get_aoi(),
            lulc_raster.get_projection())
        base_raster_float = lulc_raster.set_datatype(gdal.GDT_Float32)
        observed_yield = 1.0
        corn_observed = test_data.create_global_raster_factory(
            gdal.GDT_Float32).uniform(observed_yield)

        vars_dict = {
            'observed_yields_maps_dict': {crop: corn_observed.uri}
        }
        guess_yield_over_aoi = model._get_observed_yield_from_dataset(
            vars_dict,
            crop,
            aoi_vector,
            base_raster_float)
        assert((guess_yield_over_aoi == observed_yield).all())


class TestGetYieldGivenLULC(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        observed_yield = 2.0
        lulc_raster = test_data.create_lulc_map2(test_data.aoi_dict)
        observed_yield_over_aoi_raster = lulc_raster.ones().set_datatype(
            gdal.GDT_Float32) * observed_yield
        crop = "corn"

        vars_dict = {
            'crop_lookup_dict': test_data.get_crop_lookup_table(
                os.path.join(input_dir, 'crop_lookup_table.csv')),
            'observed_yields_maps_dict': test_data.get_observed_yield_maps_dict()
        }

        # print lulc_raster
        # print observed_yield_over_aoi_raster
        # print vars_dict['crop_lookup_dict'].items()
        guess_yield_over_aoi = model._get_yield_given_lulc(
            vars_dict,
            crop,
            lulc_raster,
            observed_yield_over_aoi_raster)

        guess_total = guess_yield_over_aoi.get_band(1).sum()
        check_total = observed_yield * lulc_raster.get_shape()[0]
        assert(guess_total == check_total)


class TestCalculateProductionForCrop(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        observed_yield = 2.0
        lulc_raster = test_data.create_lulc_map2(test_data.aoi_dict)
        observed_yield_over_aoi_raster = lulc_raster.ones().set_datatype(
            gdal.GDT_Float32) * observed_yield
        crop = "corn"

        vars_dict = {
            'crop_lookup_dict': test_data.get_crop_lookup_table(
                os.path.join(input_dir, 'crop_lookup_table.csv')),
            'observed_yields_maps_dict': test_data.get_observed_yield_maps_dict(),
            'create_crop_production_maps': False,
            'output_production_maps_dir': None
        }

        ObservedLocalYield_raster = model._get_yield_given_lulc(
            vars_dict,
            crop,
            lulc_raster,
            observed_yield_over_aoi_raster)

        guess_Production_raster = model._calculate_production_for_crop(
            vars_dict,
            crop,
            ObservedLocalYield_raster)

        guess_total = guess_Production_raster.get_band(1).sum()
        check_total = observed_yield * lulc_raster.get_shape(
            )[0] * 0.0001 * lulc_raster.get_cell_area()
        assert(guess_total == np.float32(check_total))


class TestCalculateCostOfPerTonInputs(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        vars_dict = test_data.get_vars_dict()
        crop = 'corn'
        econ_table = vars_dict['economics_table_dict'][crop]
        lulc_raster = test_data.create_lulc_map2(test_data.aoi_dict)
        production_raster = lulc_raster.set_datatype(gdal.GDT_Float32) * 2.0

        CostPerTonInputTotal_raster = model._calc_cost_of_per_ton_inputs(
            vars_dict,
            crop,
            lulc_raster)

        print CostPerTonInputTotal_raster

        check = econ_table['cost_nitrogen_per_ton'] + econ_table[
            'cost_phosphorous_per_ton'] + econ_table['cost_potash_per_ton']

        assert(CostPerTonInputTotal_raster.get_band(
                1)[0, 0] == np.float32(check))


class TestCalculateCostOfPerHectareInputs(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        vars_dict = test_data.get_vars_dict()
        crop = 'corn'
        econ_table = vars_dict['economics_table_dict'][crop]
        lulc_raster = test_data.create_lulc_map2(test_data.aoi_dict)
        production_raster = lulc_raster.set_datatype(
            gdal.GDT_Float32).set_nodata(-1) * 2.0

        CostPerHectareInputTotal_raster = model._calc_cost_of_per_hectare_inputs(
            vars_dict,
            crop,
            lulc_raster)

        check = econ_table['cost_labor_per_ha'] + econ_table[
            'cost_machine_per_ha'] + econ_table[
            'cost_seed_per_ha'] + econ_table['cost_irrigation_per_ha']

        assert(CostPerHectareInputTotal_raster.get_band(
                1)[0, 0] == np.float32(check))


class TestCalcCropReturns(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        vars_dict = test_data.get_vars_dict()
        crop = 'corn'
        econ_table = vars_dict['economics_table_dict'][crop]
        lulc_raster = test_data.create_lulc_map2(test_data.aoi_dict)
        masked_lulc_float = model._get_masked_lulc_raster(
            vars_dict, crop, lulc_raster).set_datatype(
            gdal.GDT_Float32).set_nodata(-1)
        production_raster = lulc_raster.set_datatype(
            gdal.GDT_Float32).set_nodata(-1) * 2.0 * masked_lulc_float
        returns_raster = production_raster * 0.0

        returns_raster = model._calc_crop_returns(
            vars_dict,
            crop,
            lulc_raster,
            production_raster,
            returns_raster,
            econ_table)

        cost_per_ha = econ_table['cost_labor_per_ha'] + econ_table[
            'cost_machine_per_ha'] + econ_table[
            'cost_seed_per_ha'] + econ_table['cost_irrigation_per_ha']
        cost_per_ton = econ_table['cost_nitrogen_per_ton'] + econ_table[
            'cost_phosphorous_per_ton'] + econ_table['cost_potash_per_ton']
        cost = cost_per_ha + cost_per_ton
        revenue = econ_table['price_per_ton'] * 2.0
        check_returns = revenue - cost

        assert(returns_raster.get_band(
                1)[0, 0] == np.float32(check_returns))


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
            'do_yield_percentile': True,
            'output_dir': os.path.join(workspace_dir, 'output')
        }

    def test_run1(self):
        guess = model._create_results_table(self.vars_dict)
        pass


class TestCalcObservedYield(unittest.TestCase):
    def setUp(self):
        self.vars_dict = test_data.get_vars_dict()
        self.output_dir = self.vars_dict['output_dir']

    def test_run1(self):
        guess = model.calc_observed_yield(self.vars_dict)


    def tearDown(self):
        # shutil.rmtree(self.output_dir)
        pass

if __name__ == '__main__':
    unittest.main()
