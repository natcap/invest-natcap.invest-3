import unittest
import os
import shutil

import numpy as np
from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
from invest_natcap.nutrient import nutrient_biophysical
from invest_natcap.nutrient import nutrient_valuation
from invest_natcap.nutrient import nutrient_core

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

class NutrientValuationTest(unittest.TestCase):
    def setUp(self):
        self.args = {
            'workspace_dir': WORKSPACE,
            'watersheds': os.path.join(VAL_INPUT, 'watersheds.shp'),
            'valuation_table': os.path.join(VAL_INPUT, 'valuation_table.csv')
        }

    def test_smoke(self):
        nutrient_valuation.execute(self.args)

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

        sample_feature_shapefile = nutrient_core.split_datasource(shapefile)[1]

        # Test to get default GDAL raster stats.
        stats = nutrient_core.get_raster_stat_under_polygon(sample_raster,
            sample_feature_shapefile, output_path)

        reg_stats = [732.85412597656, 2237.7661132812, 1133.0612776513, 236.55612231802]
        for test_stat, reg_stat in zip(stats, reg_stats):
            self.assertAlmostEqual(test_stat, reg_stat)

        # Test for calculating the number of pixels under the shape using GDAL
        # and math.
        reg_pixel_count = 93339
        num_pixels = nutrient_core.get_raster_stat_under_polygon(sample_raster,
            sample_feature_shapefile, output_path, 'count')
        self.assertEqual(num_pixels, reg_pixel_count)

        # Test for calculating the number of pixels under the shape using numpy.
        num_pixels = nutrient_core.get_raster_stat_under_polygon(sample_raster,
            sample_feature_shapefile, output_path, 'numpy_count')
        self.assertEqual(num_pixels, reg_pixel_count)

        # Verify that the correct exception is raised when an invalid option is
        # passed.
        with self.assertRaises(nutrient_core.OptionNotRecognized):
            null = nutrient_core.get_raster_stat_under_polygon(sample_raster,
                sample_feature_shapefile, output_path, 'does_not_exist')

        # Verify that a user-defined function works as well when passed in to
        # the op argument.
        def test_op(mask_raster):
            """A simple function to assert that the expected return value is
            returned."""
            return 9.43
        user_def_output = nutrient_core.get_raster_stat_under_polygon(sample_raster,
            sample_feature_shapefile, output_path, 'op', test_op)
        self.assertEqual(user_def_output, 9.43)

        # Verify that if the user specifies the 'op' stat type but does not
        # provide a function, that a TypeError is raised.
        with self.assertRaises(TypeError):
            null = nutrient_core.get_raster_stat_under_polygon(sample_raster,
                sample_feature_shapefile, output_path, 'op')

        # Verify that if the original shapefile is used, that the output list
        # has three entries and all are what we expect.
        stats_list = nutrient_core.get_raster_stat_under_polygon(sample_raster,
            shapefile, output_path, 'op', test_op)
        self.assertEqual(stats_list, [test_op('')] * 3)

    def test_split_datasource(self):
        shapefile = ogr.Open(os.path.join(NUTR_INPUT, 'watersheds.shp'))

        # Get the memory-bound version of these shapefiles
        shapes_in_mem = nutrient_core.split_datasource(shapefile)

        # Get the number of features across all layers.
        feature_count = sum([l.GetFeatureCount() for l in shapefile])

        features_to_test = []
        for layer in shapefile:
            for shape in layer:
                features_to_test.append(shape)
            layer.ResetReading()

        uris = [r + str(i) for (i, r) in
                enumerate([WORKSPACE + '/shapefiles'] * feature_count)]
        shapes_on_disk = nutrient_core.split_datasource(shapefile, uris)

        for shapes_list_to_test in [shapes_in_mem, shapes_on_disk]:
            self.assertEqual(feature_count, len(shapes_list_to_test))
            for reg_feature, split_shapefile in zip(features_to_test, shapes_list_to_test):
                reg_geom = reg_feature.GetGeometryRef()

                # Assert split_shapefile only has one layer
                self.assertEqual(split_shapefile.GetLayerCount(), 1)

                # Assert that there's only one feature in the layer
                self.assertEqual(split_shapefile.GetLayer(0).GetFeatureCount(), 1)

                # Assert the geometry equality of the two features.
                # Do this by calculating the intersection of the two features and
                # then asserting that the area is what we expect from the original
                # shape.
                split_feature = split_shapefile.GetLayer(0).GetFeature(0)
                split_geom = split_feature.GetGeometryRef()
                split_geom_dict = split_geom.ExportToJson()

                intersection = reg_geom.Intersection(split_geom)
                difference_area = intersection.GetArea()
                reg_area = reg_geom.GetArea()
                self.assertEqual(difference_area, reg_area)

    def test_watershed_value(self):
        value = nutrient_core.watershed_value(24, 500, 3, 0.05)

        self.assertAlmostEqual(value, 34312.9251701)

    def test_valuation(self):
        pass
