import unittest
import os
import shutil

import numpy as np
from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
from invest_natcap.nutrient import nutrient

BASE_DATA = os.path.join('data', 'base_data', 'terrestrial')
NUTR_INPUT = os.path.join('data', 'nutrient', 'input')
VAL_INPUT = os.path.join('data', 'nutrient', 'valuation_input')

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
            'biophysical_table_uri': \
                os.path.join(NUTR_INPUT, 'biophysical_models.csv'),
            'water_purification_threshold_table_uri': \
                os.path.join(NUTR_INPUT, 'water_purification_threshold.csv'),
            'water_purification_valuation_table_uri': \
                os.path.join(NUTR_INPUT, 'water_purification_valuation.csv'),
                

            'nutrient_type': 'nitrogen',
            'accum_threshold': 1000,
            'folders': {
                'workspace': WORKSPACE,
                'intermediate': os.path.join(WORKSPACE, 'intermediate'),
                'output': os.path.join(WORKSPACE, 'output')
            }
        }

    def test_smoke(self):
        """Smoke test for nutrient retention: biophysical"""
        self.args['calc_p'] = False
        self.args['calc_n'] = False
        self.assertRaises(ValueError, nutrient.execute, self.args)

        self.args['calc_n'] = True
        self.args['calc_p'] = True
        nutrient.execute(self.args)
