'''
python -m unittest test_crop_production_model
'''

import unittest
import os
import pprint
import shutil

import gdal
import numpy as np

import invest_natcap.crop_production.crop_production_model as model
from invest_natcap.crop_production.vector import Vector
import test_data

current_dir = os.path.dirname(os.path.realpath(__file__))
workspace_dir = os.path.join(
    current_dir, '../invest-data/test/data/crop_production/')
input_dir = os.path.join(
    current_dir, '../invest-data/test/data/crop_production/input/')
pp = pprint.PrettyPrinter(indent=4)


# Function 1
class TestCreateYieldFuncOutputFolder(unittest.TestCase):
    def setUp(self):
        corn_observed = test_data.create_global_raster_factory(
            gdal.GDT_Float32, test_data.NODATA_FLOAT
            ).horizontal_ramp(1.0, 10.0)

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
            gdal.GDT_Float32, test_data.NODATA_FLOAT).uniform(observed_yield)

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
        observed_yield_over_aoi_raster = lulc_raster.ones().set_datatype_and_nodata(
            gdal.GDT_Float32, test_data.NODATA_FLOAT) * observed_yield
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
        observed_yield_over_aoi_raster = lulc_raster.ones().set_datatype_and_nodata(
            gdal.GDT_Float32, test_data.NODATA_FLOAT) * observed_yield
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
        production_raster = lulc_raster.set_datatype_and_nodata(
            gdal.GDT_Float32, test_data.NODATA_FLOAT) * 2.0

        CostPerTonInputTotal_raster = model._calc_cost_of_per_ton_inputs(
            vars_dict,
            crop,
            lulc_raster)

        # print CostPerTonInputTotal_raster

        check = econ_table['cost_nitrogen_per_kg'] + econ_table[
            'cost_phosphorous_per_kg'] + econ_table['cost_potash_per_kg']

        assert(float(CostPerTonInputTotal_raster.get_band(
                1)[0, 0]) == check)


class TestCalculateCostOfPerHectareInputs(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        vars_dict = test_data.get_vars_dict()
        crop = 'corn'
        econ_table = vars_dict['economics_table_dict'][crop]
        lulc_raster = test_data.create_lulc_map2(test_data.aoi_dict)
        production_raster = lulc_raster.set_datatype_and_nodata(
            gdal.GDT_Float32, test_data.NODATA_FLOAT) * 2.0

        CostPerHectareInputTotal_raster = model._calc_cost_of_per_hectare_inputs(
            vars_dict,
            crop,
            lulc_raster)

        check = econ_table['cost_labor_per_ha'] + econ_table[
            'cost_machine_per_ha'] + econ_table[
            'cost_seed_per_ha'] + econ_table['cost_irrigation_per_ha']

        assert(float(CostPerHectareInputTotal_raster.get_band(
                1)[0, 0]) == check)


class TestCalcCropReturns(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        vars_dict = test_data.get_vars_dict()
        crop = 'corn'
        econ_table = vars_dict['economics_table_dict'][crop]
        lulc_raster = test_data.create_lulc_map2(test_data.aoi_dict)
        masked_lulc_float = model._get_masked_lulc_raster(
            vars_dict, crop, lulc_raster).set_datatype_and_nodata(
            gdal.GDT_Float32, test_data.NODATA_FLOAT)
        production_raster_inter = lulc_raster.set_datatype_and_nodata(
            gdal.GDT_Float32, test_data.NODATA_FLOAT)
        production_raster = production_raster_inter * masked_lulc_float * 2.0
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
        cost_per_ton = econ_table['cost_nitrogen_per_kg'] + econ_table[
            'cost_phosphorous_per_kg'] + econ_table['cost_potash_per_kg']
        cost = cost_per_ha + cost_per_ton
        revenue = econ_table['price_per_tonne'] * 2.0
        check_returns = revenue - cost

        assert(returns_raster.get_band(
                1)[0, 0] == np.float32(check_returns))


class TestCalcNutrition(unittest.TestCase):
    def setUp(self):
        pass

    def test_run1(self):
        vars_dict = test_data.get_vars_dict()
        vars_dict['crop_production_dict'] = {
            'corn': 1.0,
            'soy': 2.0,
            'rice': 3.0
        }
        guess = model._calc_nutrition(vars_dict)
        assert('soy' in  guess['crop_total_nutrition_dict'].keys())


class TestCalcObservedYield(unittest.TestCase):
    def setUp(self):
        self.vars_dict = test_data.get_vars_dict()
        self.output_dir = self.vars_dict['output_dir']

    def test_run1(self):
        # pp.pprint(self.vars_dict)
        guess = model.calc_observed_yield(self.vars_dict)
        # pp.pprint(guess)
        assert('total_cost' in guess['economics_table_dict']['corn'].keys())


# Function 2
class TestCalcPercentileYield(unittest.TestCase):
    def setUp(self):
        self.vars_dict = test_data.get_vars_dict()
        self.output_dir = self.vars_dict['output_dir']

    def test_run1(self):
        # pp.pprint(self.vars_dict)
        guess = model.calc_percentile_yield(self.vars_dict)
        assert('total_cost' in guess['economics_table_dict']['corn'].keys())

# Function 3
class TestCalcRegressionYield(unittest.TestCase):
    def setUp(self):
        self.vars_dict = test_data.get_vars_dict()
        self.output_dir = self.vars_dict['output_dir']

    def test_run1(self):
        # pp.pprint(self.vars_dict)
        guess = model.calc_regression_yield(self.vars_dict)
        assert('total_cost' in guess['economics_table_dict']['corn'].keys())


if __name__ == '__main__':
    unittest.main()
