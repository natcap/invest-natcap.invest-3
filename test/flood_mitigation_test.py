import unittest
import os
import time

from osgeo import gdal
from osgeo import ogr
import numpy

from invest_natcap import raster_utils
from invest_natcap.flood_mitigation import flood_mitigation
import invest_test_core
from invest_natcap.routing import routing_utils
import routing_cython_core

TEST_DATA = os.path.join('invest-data/test/data', 'flood_mitigation')
SAMP_INPUT = os.path.join(TEST_DATA, 'samp_input')
REGRESSION_DATA = os.path.join(TEST_DATA, 'regression')

class FloodMitigationTest(unittest.TestCase):
    def setUp(self):
        self.workspace = os.path.join(TEST_DATA, 'test_workspace')
        self.curve_numbers = os.path.join(SAMP_INPUT, 'curve_numbers.tif')
        self.curve_numbers_30m = os.path.join(SAMP_INPUT, 'curve_numbers_30m.tif')
        self.dem = os.path.join('invest-data/test/data', 'sediment_test_data', 'dem', 'hdr.adf')
        self.dem_small = os.path.join(SAMP_INPUT, 'dem_200m.tif')
        self.precip = os.path.join(SAMP_INPUT, 'precipitation.csv')
        self.landcover = os.path.join('invest-data/test/data', 'base_data', 'terrestrial', 'lulc_samp_cur')
        self.landcover_small = os.path.join(SAMP_INPUT, 'landuse_cur_200m.tif')
        self.mannings = os.path.join(SAMP_INPUT, 'mannings.csv')

        self.args = {
            'workspace': self.workspace,
            'curve_numbers': self.curve_numbers,
            'dem': self.dem,
            'cn_adjust': True,
            'cn_season': 'dry',
            'precipitation': self.precip,
            'num_intervals': 6,
            'time_interval': 120.0,  # 2 minutes
            'landuse': self.landcover,
            'mannings': self.mannings,
            'flow_threshold': 400
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

    def test_regression_dry_season_200m(self):
        self.args['dem'] = self.dem_small
        self.args['landuse'] = self.landcover_small
        flood_mitigation.execute(self.args)

    def test_regression_dry_season(self):
        """Regression test for the flood mitigation model."""
        self.args['curve_numbers'] = self.curve_numbers_30m
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

        precip_raster_uri = os.path.join(REGRESSION_DATA, 'rainfall_step2.tif')
        swrc_uri = os.path.join(REGRESSION_DATA, 'soil_water_retention.tif')
        storm_runoff_uri = os.path.join(self.workspace, 'storm_runoff.tif')
        flood_mitigation.storm_runoff(precip_raster_uri, swrc_uri,
            storm_runoff_uri)

        regression_storm_runoff = os.path.join(REGRESSION_DATA,
            'storm_runoff_step2.tif')
        invest_test_core.assertTwoDatasetEqualURI(self, storm_runoff_uri,
            regression_storm_runoff)

    def test_flood_water_discharge(self):
        storm_runoff = os.path.join(REGRESSION_DATA, 'storm_runoff_step2.tif')
        flood_water_discharge = os.path.join(self.workspace,
                'fw_discharge_nditer.tif')
        outflow_weights_uri = os.path.join(self.workspace, 'outflow_weights.tif')
        outflow_direction_uri = os.path.join(self.workspace, 'outflow_dir.tif')
        flow_direction_uri = os.path.join(self.workspace, 'flow_direction.tif')

        resampled_runoff_uri = os.path.join(self.workspace, 'runoff_resamp.tif')
        
        bounding_box = raster_utils.get_bounding_box(storm_runoff)
        raster_utils.resize_and_resample_dataset_uri(
                storm_runoff, bounding_box, 200, resampled_runoff_uri,
                gdal.GRA_Bilinear)

        routing_utils.flow_direction_inf(self.dem_small, flow_direction_uri)

        discharge_nodata = raster_utils.get_nodata_from_uri(flow_direction_uri)
        prev_discharge = os.path.join(self.workspace, 'prev_discharge.tif')
        raster_utils.new_raster_from_base_uri(flow_direction_uri, prev_discharge,
            'GTiff', discharge_nodata, gdal.GDT_Float32, fill_value=0.0)

        orig_time = time.time()
        flood_mitigation.flood_water_discharge(resampled_runoff_uri, flow_direction_uri,
            self.args['time_interval'], flood_water_discharge,
            outflow_weights_uri, outflow_direction_uri, prev_discharge)
        elapsed_time = time.time() - orig_time
        print('old runtime = %s' % elapsed_time)

        orig_time = time.time()
        cython_discharge_uri = os.path.join(self.workspace,
                'fw_discharge_cython.tif')
        flood_mitigation.flood_water_discharge(resampled_runoff_uri, flow_direction_uri,
            self.args['time_interval'], cython_discharge_uri,
            outflow_weights_uri, outflow_direction_uri, prev_discharge)
        elapsed_time = time.time() - orig_time
        print('cythonized runtime = %s' % elapsed_time)

        invest_test_core.assertTwoDatasetEqualURI(self, flood_water_discharge,
            cython_discharge_uri)

    def test_flood_water_discharge_convolution(self):
        import numpy
        from scipy import ndimage
        runoff = numpy.array([
            [25.51, 10.75, 0,     80],
            [2.52,  10.75, 10.75, 51.70],
            [22.82, 51.7,  51.7,  22.82],
            [22.82, 0,     10,    22.82]])

        outflow_weights = numpy.array([
            [0.875, 1, 1, -1],
            [0.11,  1, 1, 1],
            [0.2,   1, 1, 1],
            [1,     1, 1, 1]])

        outflow_direction = numpy.array([
            [0, 0, 2, 9],
            [7, 0, 2, 3],
            [7, 7, 2, 1],
            [0, 1, 1, 1]])

        # I can't seem to figure out how to have a kernel based off of both the
        # outflow weights and the outflow direction ... Is this problem even
        # possible to implement as a convolution?
        kernel = numpy.array([
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]])


        convolved = ndimage.convolve(runoff, kernel, mode='constant', cval=0.0)
        print numpy.divide(convolved, 120)

    def test_flood_inundation_depth_uri(self):
        """A test for comparing the original to the cythonized FID function."""

        flood_height_uri = os.path.join(REGRESSION_DATA, 'flood_height_2.tif')
        flood_height_resized_uri = os.path.join(REGRESSION_DATA,
            'flood_height_2_resized.tif')
        dem_uri = self.dem
        dem_resized_uri = os.path.join(self.workspace, 'dem_resized.tif')
        cn_uri = self.curve_numbers_30m

        channels_uri = os.path.join(self.workspace, 'channels.tif')
        flow_direction = os.path.join(self.workspace, 'flow_dir.tif')
        outflow_weights = os.path.join(self.workspace, 'outflow_weights.tif')
        outflow_direction = os.path.join(self.workspace, 'outflow_direction.tif')
        python_output_uri = os.path.join(self.workspace, 'fid_python.tif')
        cython_output_uri = os.path.join(self.workspace, 'fid_cython.tif')

        # resize the cn and flood height to the dem
        cn_resized_uri = os.path.join(self.workspace, 'cn_resized.tif')
        datatype = gdal.GDT_Float32
        nodata = raster_utils.get_nodata_from_uri(cn_uri)
        cell_size = raster_utils.get_cell_size_from_uri(dem_uri)
        raster_utils.vectorize_datasets([cn_uri, flood_height_uri, dem_uri],
                lambda x,y,z: x,
            cn_resized_uri, datatype, nodata, cell_size, 'intersection')

        nodata = raster_utils.get_nodata_from_uri(flood_height_uri)
        raster_utils.vectorize_datasets([flood_height_uri, cn_uri,  dem_uri],
                lambda x,y,z: x,
            flood_height_resized_uri, datatype, nodata, cell_size, 'intersection')

        nodata = raster_utils.get_nodata_from_uri(flood_height_uri)
        raster_utils.vectorize_datasets([cn_uri, flood_height_uri, dem_uri],
                lambda x,z,y: y,
            dem_resized_uri, datatype, nodata, cell_size, 'intersection')

        # Make the channels and the flow direction from the DEM.
        routing_utils.calculate_stream(dem_resized_uri, self.args['flow_threshold'],
            channels_uri)
        routing_utils.flow_direction_inf(dem_resized_uri, flow_direction)
        routing_cython_core.calculate_flow_graph(flow_direction,
            outflow_weights, outflow_direction)

        py_start_time = time.time()
        flood_mitigation.flood_inundation_depth(flood_height_resized_uri, dem_resized_uri,
            cn_resized_uri, channels_uri, outflow_direction, python_output_uri)
        py_duration = time.time() - py_start_time
        print 'Python runtime: %s' % py_duration

        cy_start_time = time.time()
        flood_mitigation.flood_inundation_depth(flood_height_resized_uri, dem_resized_uri,
            cn_resized_uri, channels_uri, outflow_direction, cython_output_uri)
        cy_duration = time.time() - cy_start_time
        print 'Cython runtime: %s' % cy_duration
        print 'Speedup: %s' % (py_duration / cy_duration)

        invest_test_core.assertTwoDatasetEqualURI(self, python_output_uri,
            cython_output_uri)


    def test_flood_inundation_depth(self):
        """Test for the flood inundation depth function."""

        channel_matrix = numpy.array([
            [0, 0, 0, 0, 1],
            [0, 0, 0, 1, 0],
            [1, 1, 0, 1, 0],
            [0, 1, 0, 1, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0]])

        dem_matrix = numpy.array([
            [3,   3, 13, 12, 9 ],
            [4,  13, 14, 8,  12],
            [2,  2,  12, 8,  12],
            [7,  3,  9,  6,  11],
            [9,  6,  4,  8,  12],
            [10, 10, 8, 10,  9]])

        # Just for fun, assume constant CN value
        cn_matrix = numpy.zeros(dem_matrix.shape)
        cn_matrix.fill(0.125)

        flood_height_matrix = numpy.array([
            [0, 0, 0, 0, 3],
            [0, 0, 0, 3, 0],
            [3, 3, 0, 3, 0],
            [0, 3, 0, 3, 0],
            [0, 0, 3, 0, 0],
            [0, 0, 0, 0, 0]], dtype=numpy.float)

        #  3 2 1
        #  4 p 0
        #  5 6 7
        outflow_direction_matrix = numpy.array([
            [0, 4, 4, 6, 5],
            [6, 6, 5, 6, 4],
            [4, 4, 4, 6, 5],
            [1, 2, 3, 5, 4],
            [1, 2, 3, 4, 3],
            [1, 1, 2, 3, 3]])


        # Call the numpy-only function for testing out the core algorithm,
        # without all the raster stuff implied in URIs.
        fid, distance, nearest_channel = flood_mitigation._calculate_fid(flood_height_matrix, dem_matrix,
            channel_matrix, cn_matrix, outflow_direction_matrix, 1)


        matrices = [
            ('fid', fid),
            ('distance', distance),
            ('nearest_channel', nearest_channel),
            ('channels', channel_matrix),
            ('flood height', flood_height_matrix),
            ('dem', dem_matrix),
            ('curve_nums', cn_matrix)
        ]

        for label, matrix in matrices:
            print label
            print matrix
            print ""

##        print fid
##        print channel_matrix
##        print dem_matrix
##        print cn_matrix
