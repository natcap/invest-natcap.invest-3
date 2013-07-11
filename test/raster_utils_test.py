"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess
import logging

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from nose.plugins.skip import SkipTest
import numpy as np
from invest_natcap import raster_utils
import invest_test_core

LOGGER = logging.getLogger('invest_core')

class TestRasterUtils(unittest.TestCase):
    def test_resample_dataset(self):
        base_dir = 'invest-data/test/data/test_out/resample_dataset'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        output_uri = os.path.join(base_dir, 'resampled.tif')
        base_uri = 'invest-data/test/data/sediment_test_data/dem'
        dataset = gdal.Open(base_uri)

        pixel_size = 1000.0

        raster_utils.resample_dataset(
            base_uri, pixel_size, output_uri, resample_method=gdal.GRA_Bilinear)

        #TODO: add regression test


    def test_reclassify_dataset(self):
        base_dir = 'invest-data/test/data/test_out/reclassify_dataset'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        output_uri = os.path.join(base_dir, 'reclassified.tif')
        base_uri = 'invest-data/test/data/base_data/terrestrial/lulc_samp_cur'
        dataset = gdal.Open(base_uri)
        value_map = {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.5}

        reclassified_ds = raster_utils.reclassify_dataset(
            dataset, value_map, output_uri, gdal.GDT_Float32, -1.0)

        regression_uri = 'invest-data/test/data/reclassify_regression/reclassified.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, regression_uri, output_uri)

        #If we turn on the exception flag, we should get an exception
        self.assertRaises(raster_utils.UndefinedValue,
            raster_utils.reclassify_dataset, dataset, value_map, output_uri, 
            gdal.GDT_Float32, -1.0, exception_flag = 'values_required')

    def test_aggregate_raster_values_uri(self):
        raster_uri = 'invest-data/test/data/base_data/terrestrial/lulc_samp_cur'
        shapefile_uri = os.path.join(
            'invest-data/test/data', 'hydropower_data', 'test_input', 'watersheds.shp')
        shapefile_field = 'ws_id'
        
        result_dict = raster_utils.aggregate_raster_values_uri(
            raster_uri, shapefile_uri, shapefile_field, ignore_nodata=True, 
            threshold_amount_lookup=None)

        #I did these by hand.  Better than nothing:
        self.assertEqual(result_dict.total[0], 2724523.0)
        self.assertEqual(result_dict.pixel_max[2], 95.0)
        self.assertEqual(result_dict.n_pixels[1], 93016.0)


    def test_gaussian_filter(self):
        base_dir = 'invest-data/test/data/test_out/gaussian_filter'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        output_uri = os.path.join(base_dir, 'gaussian_filter.tif')
        base_uri = 'invest-data/test/data/base_data/terrestrial/lulc_samp_cur'
        dataset = gdal.Open(base_uri)
        filtered_ds = raster_utils.gaussian_filter_dataset(dataset, 12.7, output_uri, -1.0)
        regression_uri = 'invest-data/test/data/gaussian_regression/gaussian_filter.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, regression_uri, output_uri)

    def test_get_rat_as_dictionary(self):
        path = 'invest-data/test/data/get_rat_as_dict/activity_transition_map.tif'
        ds = gdal.Open(path)
        LOGGER.debug("Get Rat As Dict Path: %s", path)
        LOGGER.debug("Get Rat As Dict DS: %s", ds)
        rat_dict = raster_utils.get_rat_as_dictionary(ds)

        unit_dict = {
            'Max Transition': ['agricultural_vegetation_managment', 
                               'fertilizer_management', 
                               'keep_native_vegetation', 
                               'increase_native_vegetation_assisted', 
                               'ditching', 
                               'pasture_management', 
                               'irrigation_management', 
                               'increase_native_vegetation_unassisted'], 
            'Value': [0, 1, 2, 3, 4, 5, 6, 7]}

        self.assertEqual(unit_dict, rat_dict)

    def test_unique_values(self):
        dataset = gdal.Open('invest-data/test/data/base_data/terrestrial/lulc_samp_cur')
        unique_vals = raster_utils.unique_raster_values(dataset)
        LOGGER.debug(unique_vals)

    def test_contour_raster(self):
        base_dir = 'invest-data/test/data/test_out/contour_raster'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dem_uri = 'invest-data/test/data/sediment_test_data/dem'
        dem_dataset = gdal.Open(dem_uri)
        output_uri = os.path.join(base_dir, 'contour_raster.tif')
        raster_utils.build_contour_raster(dem_dataset, 500, output_uri)
        regression_uri = 'invest-data/test/data/raster_utils_data/contour_raster.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, regression_uri, output_uri)

    def test_vectorize_points(self):
        base_dir = 'invest-data/test/data/test_out/raster_utils'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        shape_uri = os.path.join('invest-data/test/data', 'marine_water_quality_data', 'TideE_WGS1984_BCAlbers.shp')
        shape = ogr.Open(shape_uri)

        output_uri = os.path.join(base_dir, 'interp_points.tif')
        out_raster = raster_utils.create_raster_from_vector_extents(30, 30, gdal.GDT_Float32, -1, output_uri, shape)
        raster_utils.vectorize_points(shape, 'kh_km2_day', out_raster)
        out_raster = None
        regression_uri = 'invest-data/test/data/vectorize_points_regression_data/interp_points.tif'

        invest_test_core.assertTwoDatasetEqualURI(self, output_uri, regression_uri)

    def test_clip_datset(self):
        base_dir = 'invest-data/test/data/test_out/raster_utils'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        clip_regression_dataset = 'invest-data/test/data/clip_data/lulc_clipped.tif'
        dem_uri = 'invest-data/test/data/base_data/terrestrial/lulc_samp_fut'
        aoi_uri = 'invest-data/test/data/hydropower_data/test_input/watersheds.shp'
        dem = gdal.Open(dem_uri)
        aoi = ogr.Open(aoi_uri)
        
        clip_dataset = os.path.join(base_dir, 'lulc_clipped.tif')
        raster_utils.clip_dataset(dem, aoi, clip_dataset)
        invest_test_core.assertTwoDatasetEqualURI(self, clip_dataset, clip_regression_dataset)

    def test_calculate_slope(self):
        dem_points = {
            (0.0,0.0): 50,
            (0.0,1.0): 100,
            (1.0,0.0): 90,
            (1.0,1.0): 0,
            (0.5,0.5): 45}

        n = 100

        base_dir = 'invest-data/test/data/test_out/raster_utils'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dem_uri = 'invest-data/test/data/raster_slope_regression_data/raster_dem.tif'
        
        slope_uri = os.path.join(base_dir, 'raster_slope.tif')
        raster_utils.calculate_slope(dem_uri, slope_uri)

        slope_regression_uri = 'invest-data/test/data/raster_slope_regression_data/raster_slope.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, slope_uri, slope_regression_uri)

    def test_calculate_value_not_in_array(self):
        array = np.array([-1,2,5,-8,-9])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)

        array = np.array([-1,-1,-1])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)

        array = np.array([-1.1,-1.2,-1.2])
        value = raster_utils.calculate_value_not_in_array(array)
        print value
        self.assertFalse(value in array)

        ds = gdal.Open('invest-data/test/data/calculate_value_not_in_array_regression_data/HAB_03_kelp_influence_on_shore.tif')
        value = raster_utils.calculate_value_not_in_dataset(ds)
        _, _, array = raster_utils.extract_band_and_nodata(ds, get_array = True)
        self.assertFalse(value in array)


    def test_create_rat_with_no_rat(self):
        test_out = './invest-data/test/data/test_out/raster_utils/create_rat/'
        out_uri = os.path.join(test_out, 'test_RAT.tif')

        if not os.path.isdir(test_out):
            os.makedirs(test_out)
        
        dr = gdal.GetDriverByName('GTiff')
 
        ds = dr.Create(out_uri, 5, 5, 1, gdal.GDT_Int32)
        
        srs = osr.SpatialReference()
        srs.SetUTM(11,1)
        srs.SetWellKnownGeogCS('NAD27')
        ds.SetProjection(srs.ExportToWkt())
        ds.SetGeoTransform([444720, 30, 0, 3751320, 0 , -30])

        matrix = np.array([[1,2,3,4,5],
                           [5,4,3,2,1],
                           [3,2,4,5,1],
                           [2,1,3,4,5],
                           [4,5,1,2,3]])

        band = ds.GetRasterBand(1)
        band.SetNoDataValue(-1)
        band.WriteArray(matrix)
        band = None

        tmp_dict = {11:'farm', 23:'swamp', 13:'marsh', 22:'forest', 3:'river'}
        field_1 = 'DESC'
       
        known_results = np.array([[3, 'river'],
                                  [11, 'farm'],
                                  [13, 'marsh'],
                                  [22, 'forest'],
                                  [23, 'swamp']])

        ds_rat = raster_utils.create_rat(ds, tmp_dict, field_1)

        band = ds_rat.GetRasterBand(1)
        rat = band.GetDefaultRAT()
        col_count = rat.GetColumnCount()
        row_count = rat.GetRowCount()

        for row in range(row_count):
            for col in range(col_count):
                self.assertEqual(str(known_results[row][col]), rat.GetValueAsString(row, col))
        
        band = None
        rat = None
        ds = None
        ds_rat = None
        
    def test_get_raster_properties(self):
        """Test get_raster_properties against a known raster saved on disk"""
        data_dir = './invest-data/test/data/raster_utils_data'
        ds_uri = os.path.join(data_dir, 'get_raster_properties_ds.tif')

        ds = gdal.Open(ds_uri)

        result_dict = raster_utils.get_raster_properties(ds)

        expected_dict = {'width':30, 'height':-30, 'x_size':1125, 'y_size':991}

        self.assertEqual(result_dict, expected_dict)

    def test_get_raster_properties_unit_test(self):
        """Test get_raster_properties against a hand created raster with set 
            properties"""
        driver = gdal.GetDriverByName('MEM')
        ds_type = gdal.GDT_Int32
        dataset = driver.Create('', 112, 142, 1, ds_type)

        srs = osr.SpatialReference()
        srs.SetUTM(11, 1)
        srs.SetWellKnownGeogCS('NAD27')
        dataset.SetProjection(srs.ExportToWkt())
        dataset.SetGeoTransform([444720, 30, 0, 3751320, 0, -30])
        dataset.GetRasterBand(1).SetNoDataValue(-1)
        dataset.GetRasterBand(1).Fill(5)
        
        result_dict = raster_utils.get_raster_properties(dataset)

        expected_dict = {'width':30, 'height':-30, 'x_size':112, 'y_size':142}

        self.assertEqual(result_dict, expected_dict)

    def test_reproject_datasource(self):
        """A regression test using some of Nicks sample data that didn't work on
            his machine"""
        
        data_dir = './invest-data/test/data/raster_utils_data'
        barkclay_uri = os.path.join(data_dir, 'AOI_BarkClay.shp')
        lat_long_uri = os.path.join(data_dir, 'lat_long_file.shp')

        barkclay = ogr.Open(barkclay_uri)
        lat_long = ogr.Open(lat_long_uri)
        lat_long_srs = lat_long.GetLayer().GetSpatialRef()
        lat_long_wkt = lat_long_srs.ExportToWkt()

        out_dir = './invest-data/test/data/test_out/raster_utils/reproject_datasource'
        
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        out_uri = os.path.join(out_dir, 'reprojected_aoi_barkclay.shp')
        regression_uri = os.path.join(data_dir, 'reprojected_aoi_barkclay.shp')

        result_ds = raster_utils.reproject_datasource(
                barkclay, lat_long_wkt, out_uri)

        result_ds = None

        invest_test_core.assertTwoShapesEqualURI(
                self, out_uri, regression_uri)

    def test_reclassify_by_dictionary(self):
        landcover_uri = 'invest-data/test/data/pollination/samp_input/landuse_cur_200m.tif'
        out_uri = 'invest-data/test/data/test_out/raster_utils/reclassed_lulc.tif'
        sample_ds = gdal.Open(landcover_uri)

        reclass_rules = dict((n, n**2.0) for n in range(3, 60))

        # This call will check the default case, where reclassify_by_dictionary
        # uses the given nodata value as the value if a pixel value is not
        # found in the reclass_rules dictionary.
        raster_utils.reclassify_by_dictionary(sample_ds, reclass_rules,
            out_uri, 'GTiff', -1.0, gdal.GDT_Float32)
        reg_uri = 'invest-data/test/data/raster_utils_data/reclassed_lulc.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, out_uri, reg_uri)

        # This call checks the default_value functionality of the reclass
        # function.  In this case, we should expect to see all pixels that don't
        # have a default value to be reclassed as the user-defined default value
        # (which in this case is 0.0).
        out_uri = 'invest-data/test/data/test_out/raster_utils/reclass_default_lulc.tif'
        raster_utils.reclassify_by_dictionary(sample_ds, reclass_rules,
            out_uri, 'GTiff', -1.0, gdal.GDT_Float32, 0.0)
        reg_uri = 'invest-data/test/data/raster_utils_data/reclassed_lulc_default.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, out_uri, reg_uri)

    def test_resize_and_resample_dataset(self):
        raster_1 = 'invest-data/test/data/align_datasets_data/dem_30m_fill_clip.tif'

        bounding_box = raster_utils.get_bounding_box(raster_1)

        base_dir = 'invest-data/test/data/test_out/align_datasets'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        resized_raster = os.path.join(base_dir, 'resized.tif')

        width = abs(bounding_box[2]-bounding_box[0])
        height = abs(bounding_box[3]-bounding_box[1])

        bounding_box[0] -= width
        bounding_box[2] += width
        bounding_box[1] += height
        bounding_box[3] -= height

        regression_dir = 'invest-data/test/data/resize_resample_regression'

        raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 17, resized_raster, "nearest")
        invest_test_core.assertTwoDatasetEqualURI(self, resized_raster, os.path.join(regression_dir, os.path.basename(resized_raster)))

        bounding_box = raster_utils.get_bounding_box(raster_1)
        pixel_size = raster_utils.pixel_size(gdal.Open(raster_1))
        bounding_box[0] += 13.5*pixel_size
        bounding_box[1] -= 1.5*pixel_size
        bounding_box[2] -= width/4.0
        bounding_box[3] += height/4.0

        reduced_raster = os.path.join(base_dir, 'reduced.tif')
        #call through each interpolation scheme to make sure it works
        for interpolation_type in ["nearest", "bilinear", "cubic", "cubic_spline", "lanczos"]:
            reduced_raster = os.path.join(base_dir, 'reduced'+interpolation_type+'.tif')
            raster_utils.resize_and_resample_dataset(raster_1, bounding_box, 278, reduced_raster, interpolation_type)
            invest_test_core.assertTwoDatasetEqualURI(self, reduced_raster, os.path.join(regression_dir, os.path.basename(reduced_raster)))



    def test_assert_datasets_in_same_projection(self):
        raster_1 = 'invest-data/test/data/align_datasets_data/H[eelgrass]_S[finfishaquaculturecomm]_Risk.tif'
        raster_2 = 'invest-data/test/data/align_datasets_data/H[eelgrass]_S[shellfishaquaculturecomm]_Risk.tif'

        #These are in the same projection, so no exception expected
        raster_utils.assert_datasets_in_same_projection([raster_1, raster_2])
        
        raster_3 = 'invest-data/test/data/clip_data/global_clipped.tif'
        #Raster 3 is unprojected, so I expect an unprojected error
        self.assertRaises(raster_utils.DatasetUnprojected,raster_utils.assert_datasets_in_same_projection,[raster_3])

        raster_4 = 'invest-data/test/data/align_datasets_data/dem_30m_fill_clip.tif'
        #raster 1 and 4 are projected but in different projections..
        self.assertRaises(raster_utils.DifferentProjections,raster_utils.assert_datasets_in_same_projection,[raster_1, raster_4])

    def test_align_dataset_list(self):
        base_data = 'invest-data/test/data/base_data'
        precip = os.path.join(base_data, 'Freshwater', 'precip')
        lulc_samp_cur = os.path.join(base_data, 'terrestrial', 'lulc_samp_cur')

        out_dir = 'invest-data/test/data/test_out/align_terrestrial/'
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        precip_out = os.path.join(out_dir, os.path.basename(precip)+'.align.tif')
        lulc_samp_cur_out = os.path.join(out_dir, os.path.basename(lulc_samp_cur)+'.align.tif')

        pixel_size=60.0
        raster_utils.align_dataset_list([precip, lulc_samp_cur], [precip_out, lulc_samp_cur_out], ["nearest", "nearest"], pixel_size, "intersection", 1)

        lulc_samp_cur_regression = 'invest-data/test/data/align_regression/lulc_samp_cur.align.tif'
        precip_regression = 'invest-data/test/data/align_regression/precip.align.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, precip_out, precip_regression)
        invest_test_core.assertTwoDatasetEqualURI(self, lulc_samp_cur_out, lulc_samp_cur_regression)

        aoi_uri = os.path.join('invest-data/test/data', 'hydropower_data', 'test_input', 'watersheds.shp')
        precip_aoi_out = os.path.join(out_dir, os.path.basename(precip)+'.aoi_align.tif')
        lulc_samp_cur_aoi_out = os.path.join(out_dir, os.path.basename(lulc_samp_cur)+'.aoi_align.tif')
        raster_utils.align_dataset_list([precip, lulc_samp_cur], [precip_aoi_out, lulc_samp_cur_aoi_out], ["nearest", "nearest"], pixel_size, "intersection", 1, aoi_uri=aoi_uri)

        lulc_samp_cur_aoi_regression = 'invest-data/test/data/align_regression/lulc_samp_cur.aoi_align.tif'
        precip_aoi_regression = 'invest-data/test/data/align_regression/precip.aoi_align.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, precip_aoi_out, precip_aoi_regression)
        invest_test_core.assertTwoDatasetEqualURI(self, lulc_samp_cur_aoi_out, lulc_samp_cur_aoi_regression)

    def test_vectorize_datasets(self):
        base_dir = 'invest-data/test/data/test_out/vectorize_datasets'
        regression_dir = 'invest-data/test/data/vectorize_datasets_regression'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dataset_uri_list = ['invest-data/test/data/vectorize_datasets_data/H[eelgrass]_S[ShellfishAquacultureComm].tif',
                            'invest-data/test/data/vectorize_datasets_data/ShellfishAquacultureComm_buff.tif',
                            'invest-data/test/data/vectorize_datasets_data/eelgrass_connectivity_rating.tif',
                            'invest-data/test/data/vectorize_datasets_data/eelgrass_shellfishaquaculturecomm_change_in_area.tif',
                            'invest-data/test/data/vectorize_datasets_data/shellfishaquaculturecomm_new_stresscrit.tif']

        def vector_op(*pixel_list):
            return sum(pixel_list)

        datatype_out = gdal.GDT_Float32
        nodata_out = -100.0
        pixel_size_out = 55.5
        bounding_box_mode = "union"
        dataset_to_align_index = 0

        aoi_uri = None
        dataset_noaoi_union_out_uri = os.path.join(base_dir, 'vectorized_union_datasets_noaoi.tif')
        raster_utils.vectorize_datasets(
            dataset_uri_list, vector_op, dataset_noaoi_union_out_uri, datatype_out, nodata_out,
            pixel_size_out, bounding_box_mode, resample_method_list=["nearest", "bilinear", "cubic", "cubic_spline", "lanczos"], 
            dataset_to_align_index=dataset_to_align_index, aoi_uri=aoi_uri)
        dataset_noaoi_union_regression_uri = os.path.join(regression_dir, 'vectorized_union_datasets_noaoi.tif')
        invest_test_core.assertTwoDatasetEqualURI(self, dataset_noaoi_union_out_uri, dataset_noaoi_union_regression_uri)

        dataset_union_out_uri = os.path.join(base_dir, 'vectorized_union_datasets.tif')
        aoi_uri = 'invest-data/test/data/vectorize_datasets_data/aoi_test.shp'
        raster_utils.vectorize_datasets(
            dataset_uri_list, vector_op, dataset_union_out_uri, datatype_out, nodata_out,
            pixel_size_out, bounding_box_mode, resample_method_list=None,
            dataset_to_align_index=dataset_to_align_index, aoi_uri=aoi_uri)
        dataset_union_regression_uri = os.path.join(regression_dir, 'vectorized_union_datasets.tif')
        invest_test_core.assertTwoDatasetEqualURI(self, dataset_union_out_uri, dataset_union_regression_uri)


        bounding_box_mode = "intersection"
        dataset_intersection_out_uri = os.path.join(base_dir, 'vectorized_intersection_datasets.tif')
        raster_utils.vectorize_datasets(
            dataset_uri_list, vector_op, dataset_intersection_out_uri, datatype_out, nodata_out,
            pixel_size_out, bounding_box_mode, resample_method_list=None,
            dataset_to_align_index=dataset_to_align_index, aoi_uri=aoi_uri)
        dataset_intersection_regression_uri = os.path.join(regression_dir, 'vectorized_intersection_datasets.tif')
        invest_test_core.assertTwoDatasetEqualURI(self, dataset_intersection_out_uri, dataset_intersection_regression_uri)
    
    def test_dictionary_to_point_shapefile(self):
        """A regression test for making a point shapefile from a dictionary.
            This test uses a file path for an output."""

        #raise SkipTest

        regression_dir = './invest-data/test/data/wind_energy_regression_data/valuation/'

        expected_uri = os.path.join(regression_dir, 'dict_to_shape.shp')

        out_dir = './invest-data/test/data/test_out/raster_utils/dict_to_point_shape/'

        out_uri = os.path.join(out_dir, 'dict_to_shape.shp')

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        if os.path.isfile(out_uri):
            os.remove(out_uri)

        expected_dict = {}

        expected_dict[1] = {'lati':97, 'long':43, 'type':'grid'}
        expected_dict[2] = {'lati':96, 'long':44, 'type':'land'}

        raster_utils.dictionary_to_point_shapefile(
                expected_dict, 'tester', out_uri)

        invest_test_core.assertTwoShapesEqualURI(
                self, expected_uri, out_uri)
    
    def test_dictionary_to_point_shapefile_2(self):
        """A regression test for making a point shapefile from a dictionary.
            This test uses a directory path for an output."""

        #raise SkipTest

        regression_dir = './invest-data/test/data/wind_energy_regression_data/valuation/'

        expected_uri = os.path.join(regression_dir, 'dict_to_shape.shp')

        out_dir = './invest-data/test/data/test_out/raster_utils/dict_to_point_shape/pt_shape'

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        expected_dict = {}

        expected_dict[1] = {'lati':97, 'long':43, 'type':'grid'}
        expected_dict[2] = {'lati':96, 'long':44, 'type':'land'}

        raster_utils.dictionary_to_point_shapefile(
                expected_dict, 'tester', out_dir)

        invest_test_core.assertTwoShapesEqualURI(
                self, expected_uri, out_dir)
    
    def test_experimental_reproject_dataset(self):
        """A regression test using some data that Martin and Nic were having
            trouble reprojecting"""
       
        #raise SkipTest

        data_dir = './invest-data/test/data/raster_utils_data'
        barkclay_uri = os.path.join(data_dir, 'AOI_BarkClay.shp')
        clipped_pop_uri = os.path.join(data_dir, 'clipped_pop.tif')

        barkclay = ogr.Open(barkclay_uri)
        barkclay_layer = barkclay.GetLayer()
        out_wkt = barkclay_layer.GetSpatialRef().ExportToWkt()

        out_dir = './invest-data/test/data/test_out/raster_utils/exp_reproject_dataset'
        
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        pixel_spacing = 731.58

        out_uri = os.path.join(out_dir, 'reprojected_pop.tif')
        regression_uri = os.path.join(data_dir, 'projected_pop.tif')

        raster_utils._experimental_reproject_dataset_uri(
                clipped_pop_uri, pixel_spacing, out_wkt, out_uri)

        invest_test_core.assertTwoDatasetEqualURI(
                self, out_uri, regression_uri)
