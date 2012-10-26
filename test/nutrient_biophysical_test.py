import unittest
import os

import numpy as np

from invest_natcap.nutrient import nutrient_biophysical
from invest_natcap.nutrient import nutrient_core

BASE_DATA = os.path.join('data', 'base_data', 'terrestrial')
NUTR_INPUT = os.path.join('data', 'nutrient', 'input')

WORKSPACE = os.path.join('data', 'test_out', 'nutrient')

class NutrientBiophysicalTest(unittest.TestCase):
    """Test class for test functions of the Nutrient retention model
    (biophysical component)."""
    def setUp(self):
        self.args = {
            'workspace_dir': WORKSPACE,
            'dem_uri': \
                os.path.join(NUTR_INPUT, 'dem'),
            'pixel_yield_uri': \
                os.path.join(NUTR_INPUT, 'wyield.tif'),
            'landuse_uri': \
                os.path.join(NUTR_INPUT, 'landuse_90'),
            'watersheds_uri': \
                os.path.join(NUTR_INPUT, 'watersheds.shp'),
            'subwatersheds_uri': \
                os.path.join(NUTR_INPUT, 'subwatersheds.shp'),
            'bio_table_uri': \
                os.path.join(NUTR_INPUT, 'biophysical_models.csv'),
            'threshold_table_uri': \
                os.path.join(NUTR_INPUT, 'water_purification_threshold.csv'),
            'nutrient_type': 'nitrogen',
            'accum_threshold': 1000
        }

    def test_smoke(self):
        """Smoke test for nutrient retention: biophysical"""
        nutrient_biophysical.execute(self.args)

class NutrientCoreTest(unittest.TestCase):
    def test_get_mean_pixel_value(self):
        array = np.array([ 1, 2, 4, 2, 1, 6, 3.4, 2, 2, 2 ])
        print nutrient_core.get_mean_pixel_value(array, 2)
