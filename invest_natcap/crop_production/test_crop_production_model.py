'''
python -m unittest test_crop_production_model
'''

import unittest
import os
import pprint

from numpy import testing
import numpy as np

import crop_production_model as model

workspace_dir = '../../test/invest-data/Crop_Production'
input_dir = '../../test/invest-data/Crop_Production/input'
pp = pprint.PrettyPrinter(indent=4)


class TestModelCalcYieldObserved(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run1(self):
        guess = model.calc_yield_observed(self.vars_dict)
        pass

    def test_run2(self):
        guess = model.calc_yield_observed(self.vars_dict)
        pass


class TestModelCalcYieldPercentile(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run1(self):
        guess = model.calc_yield_percentile(self.vars_dict)
        pass

    def test_run2(self):
        guess = model.calc_yield_percentile(self.vars_dict)
        pass


class TestModelCalcYieldModeled(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run1(self):
        guess = model.calc_yield_modeled(self.vars_dict)
        pass

    def test_run2(self):
        guess = model.calc_yield_modeled(self.vars_dict)
        pass


class TestModelCalcNutrition(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run1(self):
        guess = model.calc_nutrition(self.vars_dict)
        pass

    def test_run2(self):
        guess = model.calc_nutrition(self.vars_dict)
        pass


class TestModelEconomicReturns(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run1(self):
        guess = model.calc_economic_returns(self.vars_dict)
        pass

    def test_run2(self):
        guess = model.calc_economic_returns(self.vars_dict)
        pass


class TestModelClipRasterOverAOI(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run1(self):
        guess = model.clip_raster_over_aoi(self.vars_dict)
        pass

    def test_run2(self):
        guess = model.clip_raster_over_aoi(self.vars_dict)
        pass


class TestModelSumCellsInRaster(unittest.TestCase):
    def setUp(self):
        self.vars_dict = {

        }

    def test_run1(self):
        guess = model.sum_cells_in_raster(self.vars_dict)
        pass

    def test_run2(self):
        guess = model.sum_cells_in_raster(self.vars_dict)
        pass

if __name__ == '__main__':
    unittest.main()
