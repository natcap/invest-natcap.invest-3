import unittest
import os

from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
from invest_natcap.flood_mitigation import flood_mitigation
import invest_test_core

TEST_DATA = os.path.join('data', 'flood_mitigation')
SAMP_INPUT = os.path.join(TEST_DATA, 'samp_input')
REGRESSION_DATA = os.path.join(TEST_DATA, 'regression')

class FloodMitigationTest(unittest.TestCase):
    def setUp(self):
        self.workspace = os.path.join(TEST_DATA, 'test_workspace')
        self.curve_numbers = os.path.join(SAMP_INPUT, 'curve_numbers.tif')
        self.dem = os.path.join('data', 'sediment_test_data', 'dem', 'hdr.adf')
        self.precip = os.path.join(SAMP_INPUT, 'precipitation.csv')

        self.args = {
            'workspace': self.workspace,
            'curve_numbers': self.curve_numbers,
            'dem': self.dem,
            'cn_adjust': True,
            'cn_season': 'dry'
        }

        try:
            os.makedirs(self.workspace)
        except OSError:
            # If folder already exists.
            pass

    def test_cn_dry_adjustment(self):
        """Check the dry seasion adjustment for curve numbers."""
        dry_season_cn = os.path.join(self.workspace, 'dry_season_cn.tif')
        flood_mitigation.adjust_cn_for_season(self.curve_numbers,
            'dry', dry_season_cn)

        regression_cn_raster = os.path.join(REGRESSION_DATA,
            'dry_season_cn.tif')
        invest_test_core.assertTwoDatasetEqualURI(self, regression_cn_raster,
            dry_season_cn)

    def test_cn_wet_adjustment(self):
        """Check the wet season adjustment for curve numbers."""
        wet_season_cn = os.path.join(self.workspace, 'wet_season_cn.tif')
        flood_mitigation.adjust_cn_for_season(self.curve_numbers,
            'wet', wet_season_cn)

        regression_cn_raster = os.path.join(REGRESSION_DATA,
            'wet_season_cn.tif')
        invest_test_core.assertTwoDatasetEqualURI(self, regression_cn_raster,
            wet_season_cn)

    def test_season_adjustment_bad_season(self):
        """Verify that an exception is raised when a bad season is used."""
        season_cn = os.path.join(self.workspace, 'season_cn.tif')
        self.assertRaises(flood_mitigation.InvalidSeason,
            flood_mitigation.adjust_cn_for_season, self.curve_numbers,
            'winter', season_cn)

    def test_cn_slope_adjustment(self):
        """Check the slope adjustment for curve numbers."""

        # Until we think it's necessary to actually save away a regression slope
        # raster, I'll just calculate it on the fly for this test.  It's only
        # a couple seconds.
        slope_uri = os.path.join(self.workspace, 'slope.tif')
        slope_cn = raster_utils.calculate_slope(self.dem, slope_uri)

        slope_cn = os.path.join(self.workspace, 'slope_cn.tif')
        flood_mitigation.adjust_cn_for_slope(self.curve_numbers, slope_uri,
            slope_cn)

        regression_slope_cn = os.path.join(REGRESSION_DATA, 'slope_cn.tif')
        invest_test_core.assertTwoDatasetEqualURI(self, regression_slope_cn,
            slope_cn)

    def test_swrc_raster(self):
        """Check the SWRC raster."""
        swrc_uri = os.path.join(self.workspace, 'soil_water_retention.tif')
        flood_mitigation.soil_water_retention_capacity(self.curve_numbers,
            swrc_uri)

        regression_swrc_uri = os.path.join(REGRESSION_DATA,
            'soil_water_retention.tif')
        invest_test_core.assertTwoDatasetEqualURI(self, regression_swrc_uri,
            swrc_uri)

    def test_regression_dry_season(self):
        """Regression test for the flood mitigation model."""
        flood_mitigation.execute(self.args)

    def test_regression_wet_season(self):
        self.args['cn_season'] = 'wet'
        """Regression test for the flood mitigation model."""
        flood_mitigation.execute(self.args)

    def test_regression_no_season(self):
        self.args['cn_adjust'] = False
        """Regression test for the flood mitigation model."""
        flood_mitigation.execute(self.args)

    def test_convert_precip_to_points(self):
        points_uri = os.path.join(self.workspace, 'precip_points')
        flood_mitigation.convert_precip_to_points(self.precip, points_uri)

        regression_points = os.path.join(REGRESSION_DATA, 'precip_points')
        invest_test_core.assertTwoShapesEqualURI(self, points_uri,
            regression_points)

    def test_storm_runoff(self):
        """Regression test for the storm runoff function."""

        # make a sample raster to live at precip_points_uri
        precip_raster_uri = os.path.join(self.workspace, 'precip_2.tif')
        precip_nodata = raster_utils.get_nodata_from_uri(self.dem)
        raster_utils.new_raster_from_base_uri(self.dem, precip_raster_uri,
            'GTiff', precip_nodata, gdal.GDT_Float32, precip_nodata)

        precip_points_uri = os.path.join(REGRESSION_DATA, 'precip_points',
            'precip_points.shp')
        precip_points_reproject = os.path.join(self.workspace,
            'precip_points_reproject.shp')
        dem_raster = gdal.Open(self.dem)
        dem_wkt = dem_raster.GetProjection()
        raster_utils.reproject_datasource_uri(precip_points_uri,
            dem_wkt, precip_points_reproject)

        raster_utils.vectorize_points_uri(precip_points_reproject, 2, precip_raster_uri)
