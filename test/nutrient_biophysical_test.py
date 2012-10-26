import unittest
import os
import timeit

import numpy as np
from osgeo import gdal

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
            'accum_threshold': 1000
        }

    def test_smoke(self):
        """Smoke test for nutrient retention: biophysical"""
        nutrient_biophysical.execute(self.args)

class NutrientCoreTest(unittest.TestCase):
    def test_get_mean_pixel_value(self):
        """Test for the mean pixel value of a matrix given a nodata value."""
        array = np.array([ 1, 2, 4, 2, 1, 6, 3.4, 2, 2, 2 ])
        mean = nutrient_core.get_mean_pixel_value(array, 2)

        self.assertEqual(mean, 3.08)

#    def test_compare_raster_mean(self):
#        """Compare the wall-clock running times of mean on numpy + gdal."""
#        # This demonstrates that the gdal approach runs 1.737 times faster than
#        # the numpy approach (5.007s vs. 8.7002s)
#
#        ds = gdal.Open(os.path.join(NUTR_INPUT, 'dem'))
#        nodata = ds.GetRasterBand(1).GetNoDataValue()
#        print ''
#        def do_numpy():
#            array = ds.GetRasterBand(1).ReadAsArray()
#            mean = nutrient_core.get_mean_pixel_value(array, nodata)
#
#        numpy_time = 'numpy ' + str(timeit.timeit(do_numpy, number=1000))
#
#        def do_gdal():
#            mean = nutrient_core.get_mean_raster_value(ds)
#
#        gdal_time = 'gdal ' + str(timeit.timeit(do_gdal, number=1000))
#
#        print numpy_time
#        print gdal_time

