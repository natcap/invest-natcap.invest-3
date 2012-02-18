import sys
import os
import unittest
import math
import csv
import osr
import logging

from osgeo import ogr
from osgeo import gdal
from osgeo.gdalconst import *
from invest_natcap.dbfpy import dbf
import numpy as np

from invest_natcap.wave_energy import wave_energy_core
from invest_natcap.wave_energy import wave_energy_biophysical
import invest_test_core

LOGGER = logging.getLogger('wave_energy_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaveEnergy(unittest.TestCase):

    def test_wave_energy_biophysical_regression(self):
        """Runs the biophysical part of the Wave Energy Model (WEM),
        and does regression tests against the raster outputs and shapefile
        output.
        """
        test_dir = './data/wave_energy_data'
        analysis_path = test_dir + os.sep + 'test_input/NAmerica_WestCoast_4m.shp'
        analysis_extract_path = test_dir + os.sep + 'test_input/WCNA_extract.shp'
        aoi_path = test_dir + os.sep + 'test_input/AOI_WCVI.shp'
        dem_path = test_dir + os.sep + 'samp_input/global_dem'
        wave_file_path = test_dir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.txt'
        machine_perf_path = test_dir + os.sep + 'samp_input/Machine_PelamisPerfCSV.csv'
        machine_param_path = test_dir + os.sep + 'samp_input/Machine_PelamisParamCSV.csv'
        #Set all arguments to be passed
        args = {}
        args['wave_base_data'] = wave_energy_biophysical.extrapolate_wave_data(wave_file_path)
        args['analysis_area'] = ogr.Open(analysis_path, 1)
        args['analysis_area_extract'] = ogr.Open(analysis_extract_path)
        args['aoi'] = ogr.Open(aoi_path)
        args['dem'] = gdal.Open(dem_path)
        args['workspace_dir'] = test_dir
        #Create a 2D array of the machine performance table and place the row
        #and column headers as the first two arrays in the list of arrays
        try:
            machine_perf_twoDArray = [[], []]
            machine_perf_file = open(machine_perf_path)
            reader = csv.reader(machine_perf_file)
            get_row = True
            for row in reader:
                if get_row:
                    machine_perf_twoDArray[0] = row[1:]
                    get_row = False
                else:
                    machine_perf_twoDArray[1].append(row.pop(0))
                    machine_perf_twoDArray.append(row)
            machine_perf_file.close()
            args['machine_perf'] = machine_perf_twoDArray
        except IOError, e:
            print 'File I/O error' + e

        #Create a dictionary whose keys are the 'NAMES' from the machine parameter table
        #and whose values are from the corresponding 'VALUES' field.
        try:
            machine_params = {}
            machine_param_file = open(machine_param_path)
            reader = csv.DictReader(machine_param_file)
            for row in reader:
                machine_params[row['NAME'].strip().lower()] = row['VALUE']
            machine_param_file.close()
            args['machine_param'] = machine_params
        except IOError, error:
            print 'File I/O error' + error

        wave_energy_core.biophysical(args)
        regression_dir = './data/wave_energy_regression_data/'
        #Check that output/intermediate files have been made
        wave_data_shape_path = args['workspace_dir'] + '/Intermediate/WEM_InputOutput_Pts.shp'
        regression_shape_path = regression_dir + '/WEM_InputOutput_Pts_bio_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, wave_data_shape_path, regression_shape_path)                        
        #Check that resulting rasters are correct
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/wp_kw.tif',
            regression_dir + 'wp_kw_regression.tif')
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/capwe_mwh.tif',
            regression_dir + 'capwe_mwh_regression.tif')

    def test_wave_energy_change_projection(self):
        """Test change_projection by comparing returned shapefiles projection
        features with hand calculated ones to make sure the change occurred.
        Also make sure that the features and field values are the same.
        """
        test_dir = './data/wave_energy_data'
        shape_to_reproject_path = test_dir + os.sep + 'test_input/NAmerica_WestCoast_4m.shp'
        projection = test_dir + os.sep + 'test_input/WGS_1984_UTM_Zone_10N.prj'
        output_path = test_dir + os.sep + 'test_output/waveEnergy_Clip_prj.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape_to_reproject = ogr.Open(shape_to_reproject_path)
        lyr = shape_to_reproject.GetLayer(0)

        prj_file = open(projection)
        prj_string = prj_file.read()
        spatial_prj = osr.SpatialReference()
        spatial_prj.ImportFromWkt(prj_string)

        new_shape = wave_energy_core.change_shape_projection(shape_to_reproject, spatial_prj, output_path)
        layer = new_shape.GetLayer(0)
        
        shape_projection = layer.GetSpatialRef()
        projcs = shape_projection.GetAttrValue('PROJCS')
        projcs_calc = spatial_prj.GetAttrValue('PROJCS')
        attribute_projection = shape_projection.GetAttrValue('PROJECTION')
        attribute_projection_calc = spatial_prj.GetAttrValue('PROJECTION')
        attribute_unit = shape_projection.GetAttrValue('UNIT')
        attribute_unit_calc = spatial_prj.GetAttrValue('UNIT')
        attribute_spheroid = shape_projection.GetAttrValue('SPHEROID')
        attribute_spheroid_calc = spatial_prj.GetAttrValue('SPHEROID')

        self.assertEqual(projcs, projcs_calc)
        self.assertEqual(attribute_projection, attribute_projection_calc)
        self.assertEqual(attribute_unit, attribute_unit_calc)
        self.assertEqual(attribute_spheroid, attribute_spheroid_calc)
        
        shape_to_reproject.Destroy()
        new_shape.Destroy()
        
        invest_test_core.assertTwoShapesEqualURI(self, shape_to_reproject_path, output_path)
        
    def test_wave_energy_build_point_shapefile(self):
        """A regression test that uses known data and inputs to test
        the validity of the function build_point_shapefile"""
        
        reg_shape_path = './data/wave_energy_regression_data/LandPts_prj_regression.shp'
        reg_shape = ogr.Open(reg_shape_path)
        driver_name = 'ESRI Shapefile'
        layer_name = 'landpoints'
        path = './data/wave_energy_data/test_output/test_build_pt.shp'
        data = {1:[45.661,-123.938],2:[45.496,-123.972]}

        #Add the Output directory onto the given workspace
        output_dir = './data/wave_energy_data' + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(path):
            os.remove(path)

        #Create a coordinate transformation for lat/long to meters
        srs_prj = osr.SpatialReference()
        #Using 'WGS84' as our well known lat/long projection
        srs_prj.SetWellKnownGeogCS("WGS84")
        source_sr = srs_prj
        target_sr = reg_shape.GetLayer(0).GetSpatialRef()
        coord_trans = osr.CoordinateTransformation(source_sr, target_sr)

        built_shape = wave_energy_core.build_point_shapefile(driver_name, layer_name,
                                                             path, data, target_sr, coord_trans)
        built_shape.Destroy()
        reg_shape.Destroy()
        invest_test_core.assertTwoShapesEqualURI(self, path, reg_shape_path)
                
    def test_wave_energy_clip_shape(self):
        """A trivial test case that makes sure clip_shape returns the proper shape
        after it has been clipped by a polygon shapefile.  Here the clipping polygon is
        the same size and form as the shape to be clipped so we would expect the output to be
        equal to the input"""

        test_dir = './data/wave_energy_data'
        shape_to_clip_path = test_dir + os.sep + 'test_input/NAmerica_WestCoast_4m.shp'
        binding_shape_path = test_dir + os.sep + 'test_input/WCNA_extract.shp'
        new_shape_path = test_dir + os.sep + 'test_output/waveEnergy_Clipz.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape_to_clip = ogr.Open(shape_to_clip_path)
        binding_shape = ogr.Open(binding_shape_path)

        new_shape = wave_energy_core.clip_shape(shape_to_clip, binding_shape, new_shape_path)

        new_shape.Destroy()
        shape_to_clip.Destroy()
        binding_shape.Destroy()

        invest_test_core.assertTwoShapesEqualURI(self, shape_to_clip_path, new_shape_path)

    def test_wave_energy_clip_shape_empty(self):
        """A trivial test case that makes sure clip_shape returns an empty
        shapefile if the binding polygon does not intersect with the other
        shape's features"""

        test_dir = './data/wave_energy_data'
        shape_to_clip_path = test_dir + os.sep + 'test_input/pointShapeTest.shp'
        binding_shape_path = test_dir + os.sep + 'test_input/AOI_WCVI.shp'
        new_shape_path = test_dir + os.sep + 'test_output/waveEnergy_NoClip.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape_to_clip = ogr.Open(shape_to_clip_path)
        binding_shape = ogr.Open(binding_shape_path)

        new_shape = wave_energy_core.clip_shape(shape_to_clip, binding_shape, new_shape_path)

        layer = new_shape.GetLayer(0)

        self.assertEqual(layer.GetFeatureCount(), 0)

        layer = None
        new_shape.Destroy()
        shape_to_clip.Destroy()
        binding_shape.Destroy()

    def test_wave_energy_clip_shape_hand_calculated(self):
        """A non trivial test case that makes sure clip_shape returns the proper shape
        after it has been clipped by a polygon shapefile. Also check values of features
        based on known hand given results.
        """

        test_dir = './data/wave_energy_data'
        shape_to_clip_path = test_dir + os.sep + 'test_input/NAmerica_WestCoast_4m.shp'
        binding_shape_path = test_dir + os.sep + 'test_input/threePointShape.shp'
        new_shape_path = test_dir + os.sep + 'test_output/waveEnergy_ClipAOI.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape_to_clip = ogr.Open(shape_to_clip_path)
        binding_shape = ogr.Open(binding_shape_path)

        new_shape = wave_energy_core.clip_shape(shape_to_clip, binding_shape, new_shape_path)
        #It seems that the fields "FID" and "Shape" are not included for some reason when
        #Looping through all the fields of the shapefile
        point_one_fields = [572, 490, -126.933144, 47.600162, 2.8, 11.1]
        point_two_fields = [573, 490, -126.866477, 47.600162, 2.8, 11.11]
        point_three_fields = [574, 490, -126.79981, 47.600162, 2.79, 11.11]
        point_field_array = [point_one_fields, point_two_fields, point_three_fields]

        layer = new_shape.GetLayer(0)
        feat_count_calc = 3
        feat_count = layer.GetFeatureCount()
        self.assertEqual(feat_count_calc, feat_count, 'The number of features are not correct')

        feat = layer.GetNextFeature()
        point_array_iderator = 0
        while feat is not None:
            layer_def = layer.GetLayerDefn()
            point_field = point_field_array[point_array_iderator]
            field_count = layer_def.GetFieldCount()
            fld_count_calc = 6
            self.assertEqual(field_count, fld_count_calc, 'The number of fields are not correct')
            for fld_index in range(field_count):
                field = feat.GetField(fld_index)
                field_calc = point_field[fld_index]
                self.assertEqual(field, field_calc,
                                 'The field values do not match' + str(field) + 
                                 '!=' + str(field_calc))

            feat.Destroy()
            feat = layer.GetNextFeature()
            point_array_iderator = point_array_iderator + 1

        new_shape.Destroy()
        shape_to_clip.Destroy()
        binding_shape.Destroy()

    def test_wave_energy_get_points_values(self):
        """Test get_points_values by using hand calculated results to
        check against returned values.
        """

        test_dir = './data/wave_energy_data'
        shape_path = test_dir + os.sep + 'test_input/pointShapeTest.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape_to_clip = ogr.Open(shape_path)
        value = 'HSAVG_M'
        points = [[-126.933144, 47.600162], [-126.866477, 47.600162], [-126.79981, 47.600162]]
        values = [2.8, 2.8, 2.79]
        shape_array = wave_energy_core.get_points_values(shape_to_clip, value)
        self.assertEqual(len(points), len(shape_array[0]), 'The number of points do not match')
        self.assertEqual(len(values), len(shape_array[1]), 'The number of values do not match')
        shape_points = shape_array[0]
        shape_values = shape_array[1]
        calc_dict = {}
        fun_dict = {}
        for index, var in enumerate(points):
            calc_dict[tuple(var)] = values[index]
        for index, var in enumerate(shape_points):
            fun_dict[tuple(var)] = shape_values[index]
        for key, val in calc_dict.iteritems():
            if key in fun_dict:
                self.assertEqual(val, fun_dict[key], 'The values do not match')
            else:
                self.assertEqual(0, 1, 'The keys do not match')

        shape_to_clip.Destroy()

    def test_wave_energy_captured_wave_energy_to_shape(self):
        """Test captured_wave_energy_to_shape using hand calculated and generated
        values to pass into the function.
        """

        test_dir = './data/wave_energy_data'
        shape_path = test_dir + os.sep + 'test_input/pointShapeTest.shp'
        wave_shape = ogr.Open(shape_path)

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        wave_shape_copy = ogr.GetDriverByName('Memory').CopyDataSource(wave_shape, '')

        test_dict = {(572, 490):2302, (573, 490):1453, (574, 490):2103}
        ij_array = [[572, 490], [573, 490], [574, 490]]
        
        wave_energy_core.captured_wave_energy_to_shape(test_dict, wave_shape_copy)

        layer = wave_shape_copy.GetLayer(0)
        #Need to reset the layer because the function call goes through the features in
        #the layer and does not reset or close.
        layer.ResetReading()
        feat = layer.GetNextFeature()
        comp_dict = {}
        while feat is not None:
            temp_array = []
            for fld in ('I', 'J', 'capWE_Sum'):
                index = feat.GetFieldIndex(fld)
                field_val = feat.GetField(index)
                temp_array.append(field_val)
            comp_dict[(temp_array[0], temp_array[1])] = temp_array[2]

            feat.Destroy()
            feat = layer.GetNextFeature()

        self.assertEqual(len(test_dict), len(comp_dict), 'The lengths of the dictionaries are not the same')

        for key, val in test_dict.iteritems():
            if key in comp_dict:
                self.assertEqual(val, comp_dict[key],
                                 'The values corresponding to the keys do not match' + str(val) 
                                 + ':' + str(comp_dict[key]))
            else:
                self.assertEqual(0, 1, 'The key does not exist in the new feature')
        wave_shape.Destroy()
        wave_shape_copy.Destroy()

    def test_wave_energy_compute_wave_energy_capacity(self):
        """Test compute_wave_energy_capacity function using hand generated
        values and results."""

        #A dictionary representing a mini version of what would be produced
        #from the wave watch text file
        wave_data = {0:[1, 2, 3, 4, 5], 1:[1, 2, 3, 4],
                    (520, 490):[[0, 10, 13, 9, 7],
                                [8, 15, 17, 13, 3],
                                [0, 3, 11, 9, 7],
                                [11, 17, 23, 19, 12]],
                    (521, 491):[[-1, 6.5, 13.3, 9, 7],
                                [-8, -5, 170, 13, 0],
                                [2, 3, 11.5, 9, 7.25],
                                [11, 17, 23, 19, 12]]
                    }
        #An interpolated object from machine performace and wave_data ranges
        interpZ = [[0, 0, 1, 3, 8], [0, 3, 5, 9, 7], [1, 4, 5, 3, 0], [0, 0, 0, 0, 0]]
        #A dictionary with CapMax TpMax and HsMax as limitations
        machine_param = {'capmax':20, 'tpmax':4, 'hsmax':3}
        #Hand calculated results for the two points
        result = {(520, 490):0.0762, (521, 491):0.22116}

        we_sum = wave_energy_core.compute_wave_energy_capacity(wave_data, interpZ, machine_param)

        #Loop that compares dictionaries we_sum and result checking key, sum values
        for key in result:
            if key in we_sum:
                self.assertAlmostEqual(result[key], we_sum[key], 8,
                                       'The values do not match for key ' + str(we_sum[key]))
            else:
                self.assertEqual(0, 1, 'The keys do not match')

    def test_wave_energy_wave_energy_interp(self):
        """Test wave_energy_interp by using hand calculations and hand
        calculated results based on the given inputs.
        """
        #Rows/Col
        wave_data = {0:[1, 2, 3, 4, 5, 6, 7, 8], 1:[.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]}
        #Machine performace table with first two arrays being rows/col
        machine_perf = [[2, 3, 4, 7], [1, 2, 3],
                       [0, 8, 20, 10],
                       [6, 18, 23, 13],
                       [0, 8, 20, 0]]
        result = [[0, 0, 8, 20, 16.6666667, 13.33333, 10, 10],
                  [0, 0, 8, 20, 16.66666667, 13.33333333, 10, 10],
                  [3, 3, 13, 21.5, 18.16666667, 14.83333333, 11.5, 11.5],
                  [6, 6, 18, 23, 19.66666667, 16.33333333, 13, 13],
                  [3, 3, 13, 21.5, 16.5, 11.5, 6.5, 6.5],
                  [0, 0, 8, 20, 13.33333333, 6.66666667, 0, 0],
                  [0, 0, 8, 20, 13.33333333, 6.66666667, 0, 0],
                  [0, 0, 8, 20, 13.33333333, 6.66666667, 0, 0]]
        result = np.array(result)
        interpZ = wave_energy_core.wave_energy_interp(wave_data, machine_perf)

        self.assertEqual(result.shape, interpZ.shape, 'The shapes are not the same')

        for indexOut, ar in enumerate(result):
            for indexIn, val in enumerate(ar):
                self.assertAlmostEqual(val, interpZ[indexOut][indexIn], 5, 'Values do not match')

    def test_wave_energy_clip_raster_from_polygon(self):
        """Test clip_raster_from_polygon by using hand calculations of
        what the clipped raster should have as values and shape.
        """
        test_dir = './data/wave_energy_data'
        shape_path = test_dir + os.sep + 'test_input/threePointShape.shp'
        raster_path = test_dir + os.sep + 'test_input/noAOIWP.tif'
        path = test_dir + os.sep + 'test_output/clip_raster_from_poly_wpClipped.tif'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape = ogr.Open(shape_path)
        raster = gdal.Open(raster_path)

        new_raster = wave_energy_core.clip_raster_from_polygon(shape, raster, path)

        new_band = new_raster.GetRasterBand(1)
        band = raster.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        test_matrix = [36.742653, 36.675091, 36.606201, 36.537350, 36.469341,
                      36.814983, 36.763050, 36.704857, 36.646111, 36.587391]
        matrix = band.ReadAsArray(0, 0, band.XSize, band.YSize)
        new_matrix = new_band.ReadAsArray(0, 0, new_band.XSize, new_band.YSize)
        temp_matrix = []
        for index, item in enumerate(new_matrix):
            for i, val in enumerate(item):
                if val != nodata:
                    temp_matrix.append(val)
                    self.assertEqual(val, matrix[index][i], 'Values are not the same')

        self.assertEqual(len(temp_matrix), 10, 'Number of pixels do not match')

        for i, val in enumerate(test_matrix):
            self.assertAlmostEqual(val, temp_matrix[i], 4)

        new_raster = None
        raster = None
        shape.Destroy()
        
    def test_wave_energy_clip_raster_from_polygon_regression(self):
        """A regression test for clip_raster_from_polygon function."""
        test_dir = './data/wave_energy_data'
        regression_dir = './data/wave_energy_regression_data'
        raster_input_path = test_dir + os.sep + 'test_input/clip_raster_from_poly_capwe.tif'
        copy_raster_input_path = test_dir + os.sep + 'test_output/clip_raster_from_poly_output.tif'
        regression_raster_path = regression_dir + os.sep + 'clip_raster_from_poly_regression.tif'
        clip_shape_path = test_dir + os.sep + 'test_input/clip_raster_from_poly_shape.shp'
        
        clip_shape = ogr.Open(clip_shape_path)
        raster_input = gdal.Open(raster_input_path)

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        
        copy_raster = wave_energy_core.clip_raster_from_polygon(clip_shape, raster_input, copy_raster_input_path)
        copy_raster.FlushCache()
        #Check that resulting rasters are correct
        invest_test_core.assertTwoDatasetEqualURI(self,
            regression_raster_path, copy_raster_input_path)
                
        copy_raster = None
        raster_input = None
        clip_shape.Destroy()
        
    def test_wave_energy_interp_points_over_raster(self):
        """Test interp_points_over_raster by hand creating a blank raster
        and hand calculate the interpolation over known points. Pass
        known points and values into function with raster and then check
        the interpolated raster with hand calculated points."""
        test_dir = './data/wave_energy_data'
        path = test_dir + os.sep + 'test_output/fourbyfourRaster_output.tif'
        #Create a blank raster of small dimensions.
        driver = gdal.GetDriverByName('GTIFF')
        raster = driver.Create(path, 4, 4, 1, gdal.GDT_Float32)
        raster.SetGeoTransform([-129, 1, 0, 48, 0, -1])
        raster.GetRasterBand(1).SetNoDataValue(0)
        raster.GetRasterBand(1).Fill(0)
        #Hard code points and values
        points = np.array([[-128, 47], [-128, 45], [-126, 47], [-126, 45]])
        values = np.array([10, 12, 14, 16])
        #Hand Calculate what interpolated values should be and set as matrix
        result = np.array([[  0., 0., 0., 0.],
                           [  0., 10., 12., 14.],
                           [  0., 11., 13., 15.],
                           [  0., 12., 14., 16.]])

        wave_energy_core.interp_points_over_raster(points, values, raster)
        band = raster.GetRasterBand(1)
        matrix = band.ReadAsArray()
        self.assertEqual(matrix.size, result.size, 'The sizes are not the same')
        for indexOut, ar in enumerate(result):
            for indexIn, val in enumerate(ar):
                self.assertAlmostEqual(val, matrix[indexOut][indexIn], 5,
                                       'The interpolated values are not equal.')

    def test_wave_energy_wave_power(self):
        """Test the wave_power function by hand calculating wave power with known
        variables and creating shapefile with those variables and comparing returned
        value against known results."""

        test_dir = './data/wave_energy_data'
        shape_path = test_dir + os.sep + 'test_input/test_wave_power_shape.shp'
        shape_copy_path = test_dir + os.sep + 'test_output/test_wave_power_shape.shp'
        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(shape_copy_path):
            os.remove(shape_copy_path)

        depth_list = [-500, -1000, -100, 1, -80]
        height_list = [2.5, 2.8, 2.3, 1.5, 2.04]
        period_list = [10.0, 12.0, 8.0, 5.0, 11.3]
        calculations_by_hand = [26.39331177, 39.729324, 17.87146248, 3.996030763, 20.10613825]
        shape = ogr.Open(shape_path)
        
        shape_copy = ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(shape, shape_copy_path)
        layer = shape_copy.GetLayer(0)
        for field in ['Depth_M', 'HSAVG_M', 'TPAVG_S']:
            fld_defn = ogr.FieldDefn(field, ogr.OFTReal)
            layer.CreateField(fld_defn)
        layer.ResetReading()
        feat = layer.GetNextFeature()
        i = 0
        while feat is not None:
            height_index = feat.GetFieldIndex('HSAVG_M')
            period_index = feat.GetFieldIndex('TPAVG_S')
            depth_index = feat.GetFieldIndex('Depth_M')
        
            feat.SetField(depth_index, depth_list[i])
            feat.SetField(height_index, height_list[i])
            feat.SetField(period_index, period_list[i])
        
            layer.SetFeature(feat)
            feat.Destroy()
            feat = layer.GetNextFeature()
            i = i + 1
        layer = None
        shape_copy = wave_energy_core.wave_power(shape_copy)
        
        layer = shape_copy.GetLayer(0)
        layer.ResetReading()
        feat = layer.GetNextFeature()
        i = 0
        while feat is not None:
            wave_power_index = feat.GetFieldIndex('wp_Kw')
            wave_power = feat.GetField(wave_power_index)
            self.assertAlmostEqual(wave_power, calculations_by_hand[i], 1,
                                   'Wave Power calculations do not match.')
            feat.Destroy()
            feat = layer.GetNextFeature()
            i = i + 1
        shape_copy.Destroy()
        shape.Destroy()
        
    def test_wave_energy_wave_power_regression(self):
        """A regresssion test for the wave_power function."""

        test_dir = './data/wave_energy_data'
        regression_dir = './data/wave_energy_regression_data'
        shape_path = test_dir + os.sep + 'test_input/test_wavepower_withfields.shp'
        shape_copy_path = test_dir + os.sep + 'test_output/regression_test_wave_power_output.shp'
        regression_shape_path = regression_dir + os.sep + 'wave_power_regression.shp'
        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(shape_copy_path):
            os.remove(shape_copy_path)

        shape = ogr.Open(shape_path)
        shape_reg = ogr.Open(regression_shape_path)
        shape_copy = ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(shape, shape_copy_path)
        shape_copy = wave_energy_core.wave_power(shape_copy)
        
        layer = shape_copy.GetLayer(0)
        layer_reg = shape_reg.GetLayer(0)
        layer.ResetReading()
        feat = layer.GetNextFeature()
        feat_reg = layer_reg.GetNextFeature()
        while feat is not None:
            wave_power_index = feat.GetFieldIndex('wp_Kw')
            wave_power_index_reg = feat_reg.GetFieldIndex('wp_Kw')
            wave_power = feat.GetField(wave_power_index)
            wave_power_reg = feat_reg.GetField(wave_power_index_reg)
            self.assertEqual(wave_power, wave_power_reg,
                             'The wave power values do not match.')
            feat.Destroy()
            feat_reg.Destroy()
            feat = layer.GetNextFeature()
            feat_reg = layer_reg.GetNextFeature()

        shape_copy.Destroy()
        shape.Destroy()
        shape_reg.Destroy()

    def test_wave_energy_get_points(self):
        """Test the get_points_geometries function by first creating a shapefile
        with assigned points and geometries. Pass shapefile to function
        and checked returned value against calculated ones."""
        test_dir = './data/wave_energy_data'
        shape_path = test_dir + os.sep + 'test_input/test_wavepower_withfields.shp'
        
        shape = ogr.Open(shape_path)
        layer = shape.GetLayer(0)
        calculated_points = [[-126.726911, 48.241337], [-126.580642, 48.240944],
                             [-126.726911, 48.098204], [-126.5771122, 48.015067],
                              [-126.427313, 48.091537]]
        drv = ogr.GetDriverByName('MEMORY')
        src = drv.CreateDataSource('')
        lyr = src.CreateLayer('geom', layer.GetSpatialRef(), ogr.wkbPoint)
        field_defn = ogr.FieldDefn('Id', ogr.OFTInteger)
        lyr.CreateField(field_defn)
        
        for index, value in enumerate(calculated_points):
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint_2D(value[0], value[1])            
            feat = ogr.Feature(lyr.GetLayerDefn())
            lyr.CreateFeature(feat)
            feat.SetGeometryDirectly(point)
            lyr.SetFeature(feat)
            feat.Destroy()
        
        lyr.ResetReading()
        result_points = wave_energy_core.get_points_geometries(src)
        
        for index, value in enumerate(result_points):
            self.assertEqual(value[0], calculated_points[index][0],
                             'The X value of the points do not match.')
            self.assertEqual(value[1], calculated_points[index][1],
                             'The Y value of the points do not match.')
        
    def test_wave_energy_calc_dist(self):
        """Test the calculate_distance function by hand calculating the
        distances between known points and checking them against the functions
        returned results on the same set of points."""
        xy_1 = np.array([[250, 120], [300, 212], [125, 215], [1222, 988]])
        xy_2 = np.array([[156, 133], [198, 111]])
        calculated_dist_results = np.array([52.77309921, 143.5444182, 87.66413178, 1348.222904])
        calculated_id_results = np.array([1, 1, 0, 1])
        dist_results, id_results = wave_energy_core.calculate_distance(xy_1, xy_2)
        calculated_dist_rounded = np.ma.round(calculated_dist_results, 3)
        dist_rounded = np.ma.round(dist_results, 3)
        mask_dist = calculated_dist_rounded == dist_rounded
        mask_id = calculated_id_results == id_results
        self.assertTrue(mask_dist.all(),
                        'Not all of the distances were equal to three decimal places.')
        self.assertTrue(mask_id.all(), 'Not all of the IDs matched.')
        
    def test_wave_energy_create_percentile_raster(self):
        test_dir = './data/wave_energy_data'
        perc_path = test_dir + os.sep + 'test_output/percentile_five_by_five.tif'
        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(perc_path):
            os.remove(perc_path)
        #make a dummy 5 x 5 raster
        raster_size = 10
        driver = gdal.GetDriverByName('GTiff')
        dataset = driver.Create(perc_path, raster_size, raster_size, 1, gdal.GDT_Int32)
    
        raster_data = np.reshape(np.arange(1,101),(10,10))
        dataset.GetRasterBand(1).WriteArray(raster_data, 0, 0)
        calculated_perc_list = [25,50,75,90]
        calc_value_array = [1,2,3,4,5]
        calc_count_array = [25, 25, 25, 15, 10]
        calc_val_range_array = ['1 - 25 the amount of mice per cat (mice/cat)',
                                '25 - 50 (mice/cat)',
                                '50 - 75 (mice/cat)',
                                '75 - 90 (mice/cat)',
                                'Greater than 90 (mice/cat)']
        calculated_output_raster = np.array([[1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,2,2,2,2,2],
                                            [2,2,2,2,2,2,2,2,2,2],
                                            [2,2,2,2,2,2,2,2,2,2],
                                            [3,3,3,3,3,3,3,3,3,3],
                                            [3,3,3,3,3,3,3,3,3,3],
                                            [3,3,3,3,3,4,4,4,4,4],
                                            [4,4,4,4,4,4,4,4,4,4],
                                            [5,5,5,5,5,5,5,5,5,5]])
        units_short = ' (mice/cat)'
        units_long = ' the amount of mice per cat (mice/cat)'
        percentile_raster = wave_energy_core.create_percentile_rasters(dataset, perc_path, units_short, units_long)
        perc_band = percentile_raster.GetRasterBand(1)
        perc_matrix = perc_band.ReadAsArray()
        LOGGER.debug('percentile matrix: %s', perc_matrix)
        LOGGER.debug('matrix: %s', calculated_output_raster)
        self.assertTrue((perc_matrix == calculated_output_raster).all())
        
        db_file = dbf.Dbf(perc_path+'.vat.dbf')
        value_array = []
        count_array = []
        val_range_array = []
        for rec in db_file:
            value_array.append(rec['VALUE'])
            count_array.append(rec['COUNT'])
            val_range_array.append(rec['VAL_RANGE'])
        
        for i in range(5):
            self.assertEqual(value_array[i], calc_value_array[i])
            self.assertEqual(count_array[i], calc_count_array[i])
            self.assertEqual(val_range_array[i], calc_val_range_array[i])      
        #hand calculate percentiles
        
        #hand calculate attribute table
#        dataset_attribute_table = dbf.Dbf(perc_path + ".vat.dbf", new=True)
#        dataset_attribute_table.addField(
#                     #integer field
#                     ("VALUE", "N", 9),
#                     ("COUNT", "N", 9),
#                     #character field, I think header names need to be short?
#                     ("DESCRIPTIO", "C", 254))
#    
#        #Add all the records
#        for id_value in range(6):
#            rec = dataset_attribute_table.newRecord()
#            rec["VALUE"] = id_value
#            rec["DESCRIPTIO"] = "The value of %s" % id_value
#            rec.store()
#        dataset_attribute_table.close()
        
        #assert percentile raster
        
        #assert table values and existence
    
    def test_wave_energy_get_percentiles(self):
        #hand make lists and check that correct percentiles are returned
        return
    
    def test_wave_energy_create_percentile_ranges(self):
        #Given a list make sure proper strings are being returned
        return
    
    def test_wave_energy_create_attribute_table(self):
        #make a dummy attribute table
        
        #make sure file exists
        
        #assert that dummy and returned tables are equal
        return
        
    def test_wave_energy_valuation_regression(self):
        """Runs the valuation part of the Wave Energy Model (WEM),
        and does regression tests against the raster outputs and shapefile
        output.
        """
        test_dir = './data/wave_energy_data'
        wave_data_shape_path = test_dir + os.sep + 'Intermediate/WEM_InputOutput_Pts.shp'
        number_of_machines = 28
        machine_econ_path = test_dir + os.sep + 'samp_input/Machine_PelamisEconCSV.csv'
        land_grid_path = test_dir + os.sep + 'samp_input/LandGridPts_WCVI_221.csv'
        dem_path = test_dir + os.sep + 'samp_input/global_dem'
        #Set all arguments to be passed
        args = {}
        args['workspace_dir'] = test_dir
        args['wave_data_shape'] = ogr.Open(wave_data_shape_path, 1)
        args['number_machines'] = number_of_machines
        args['global_dem'] = gdal.Open(dem_path)

        #Read machine economic parameters into a dictionary
        try:
            machine_econ = {}
            machine_econ_file = open(machine_econ_path)
            reader = csv.DictReader(machine_econ_file)
            LOGGER.debug('reader fieldnames : %s ', reader.fieldnames)
            #Read in the field names from the column headers
            name_key = reader.fieldnames[0]
            value_key = reader.fieldnames[1]
            for row in reader:
                #Convert name to lowercase
                name = row[name_key].strip().lower()
                LOGGER.debug('Name : %s and Value : % s', name, row[value_key])
                machine_econ[name] = row[value_key]
            machine_econ_file.close()
            args['machine_econ'] = machine_econ
        except IOError, error:
            print 'File I/O error' + error
        #Read landing and power grid connection points into a dictionary
        try:
            land_grid_pts = {}
            land_grid_pts_file = open(land_grid_path)
            reader = csv.DictReader(land_grid_pts_file)
            for row in reader:
                LOGGER.debug('Land Grid Row: %s', row)
                if row['ID'] in land_grid_pts:
                    land_grid_pts[row['ID'].strip()][row['TYPE']] = [row['LAT'],
                                                                     row['LONG']]
                else:
                    land_grid_pts[row['ID'].strip()] = {row['TYPE']:[row['LAT'],
                                                                     row['LONG']]}
            LOGGER.debug('New Land_Grid Dict : %s', land_grid_pts)
            land_grid_pts_file.close()
            args['land_gridPts'] = land_grid_pts
        except IOError, error:
            print 'File I/O error' + error

        wave_energy_core.valuation(args)
        
        regression_dir = './data/wave_energy_regression_data'
        regression_shape_path = regression_dir + '/WEM_InputOutput_Pts_val_regression.shp'
        shape_path = args['workspace_dir'] + '/Intermediate/WEM_InputOutput_Pts.shp'
        #Check that resulting wave data shapefile is correct
        invest_test_core.assertTwoShapesEqualURI(self, regression_shape_path, shape_path)
        #Check that resulting rasters are correct
        invest_test_core.assertTwoDatasetEqualURI(self, args['workspace_dir'] + '/Output/npv_usd.tif', 
                                                  regression_dir + '/npv_usd_regression.tif')
