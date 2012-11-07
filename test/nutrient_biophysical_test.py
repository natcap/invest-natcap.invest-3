import unittest
import os
import shutil

import numpy as np
from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
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
            'accum_threshold': 1000,
            'folders': {
                'workspace': WORKSPACE,
                'intermediate': os.path.join(WORKSPACE, 'intermediate'),
                'output': os.path.join(WORKSPACE, 'output')
            }
        }

    def tearDown(self):
        shutil.rmtree(WORKSPACE)

    def test_smoke(self):
        """Smoke test for nutrient retention: biophysical"""
        nutrient_biophysical.execute(self.args)

        dest = '/tmp/Nutrient_workspace'
        try:
            shutil.rmtree(dest)
        except:
            pass
        shutil.copytree(WORKSPACE, dest)


class NutrientCoreTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(WORKSPACE)

    def tearDown(self):
        shutil.rmtree(WORKSPACE)

    def test_get_raster_stats_under_polygon(self):
        sample_raster = gdal.Open(os.path.join(NUTR_INPUT, 'wyield.tif'))
        shapefile = ogr.Open(os.path.join(NUTR_INPUT, 'watersheds.shp'))
        sample_layer = shapefile.GetLayer(0)
        sample_feature = sample_layer.GetFeature(1)
        output_path = os.path.join(WORKSPACE, 'test_stats_feature.tif')

        stats = nutrient_core.get_raster_stat_under_polygon(sample_raster,
            sample_feature, sample_layer, output_path)

        reg_stats = [732.85412597656, 2237.7661132812, 1133.0612776513, 236.55612231802]
        for test_stat, reg_stat in zip(stats, reg_stats):
            self.assertAlmostEqual(test_stat, reg_stat)

        reg_pixel_count = 93339
        num_pixels = nutrient_core.get_raster_stat_under_polygon(sample_raster,
            sample_feature, sample_layer, output_path, 'count')
        self.assertEqual(num_pixels, reg_pixel_count)

        num_pixels = nutrient_core.get_raster_stat_under_polygon(sample_raster,
            sample_feature, sample_layer, output_path, 'numpy_count')
        self.assertEqual(num_pixels, reg_pixel_count)

        with self.assertRaises(nutrient_core.OptionNotRecognized):
            null = nutrient_core.get_raster_stat_under_polygon(sample_raster,
                sample_feature, sample_layer, output_path, 'does_not_exist')
