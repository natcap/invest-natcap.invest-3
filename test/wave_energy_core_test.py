import sys
import os
import unittest
import math
import csv
import logging

from osgeo import osr
from osgeo import ogr
from osgeo import gdal
from osgeo.gdalconst import *
from invest_natcap.dbfpy import dbf
import numpy as np

from invest_natcap.wave_energy import wave_energy_core
from invest_natcap.wave_energy import wave_energy_biophysical
import invest_test_core
from nose.plugins.skip import SkipTest

LOGGER = logging.getLogger('wave_energy_core_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaveEnergy(unittest.TestCase):

    def test_wave_energy_biophysical_regression(self):
        """Runs the biophysical part of the Wave Energy Model (WEM),
        and does regression tests against the raster outputs and shapefile
        output.
        """
        raise SkipTest
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_biophysical_out'
        intermediate_dir = os.path.join(output_dir, 'Intermediate')
        out_dir = os.path.join(output_dir, 'Output')
        analysis_path = os.path.join(
                test_dir, 'test_input/NAmerica_WestCoast_4m.shp')
        analysis_extract_path = os.path.join(
                test_dir, 'test_input/WCNA_extract.shp')
        aoi_path = os.path.join(test_dir, 'test_input/AOI_WCVI.shp')
        dem_path = os.path.join(test_dir, 'samp_input/global_dem')
        wave_file_path = os.path.join(
                test_dir, 'samp_input/WaveData/NAmerica_WestCoast_4m.txt.bin')
        machine_perf_path = os.path.join(
                test_dir, 'samp_input/Machine_PelamisPerfCSV.csv')
        machine_param_path = os.path.join(
                test_dir, 'samp_input/Machine_PelamisParamCSV.csv')
        #Set all arguments to be passed
        args = {}
        args['wave_base_data'] = \
            wave_energy_biophysical.load_binary_wave_data(wave_file_path)
        args['analysis_area'] = ogr.Open(analysis_path, 1)
        args['analysis_area_extract'] = ogr.Open(analysis_extract_path)
        args['aoi'] = ogr.Open(aoi_path)
        args['dem'] = gdal.Open(dem_path)
        args['workspace_dir'] = output_dir
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        for file in [intermediate_dir, out_dir]:
            if not os.path.isdir(file):
                os.makedirs(file)
        
        #Create a dictionary that stores the wave periods and wave heights as
        #arrays. Also store the amount of energy the machine produces 
        #in a certain wave period/height state as a 2D array
        machine_perf_dict = {}
        machine_perf_file = open(machine_perf_path)
        reader = csv.reader(machine_perf_file)
        #Get the column header which is the first row in the file
        #and specifies the range of wave periods
        periods = reader.next()
        machine_perf_dict['periods'] = periods[1:]
        #Set the keys for storing wave height range and the machine performance
        #at each state
        machine_perf_dict['heights'] = []
        machine_perf_dict['bin_matrix'] = []
        for row in reader:
            #Build up the row header by taking the first element in each row
            #This is the range of heights
            machine_perf_dict['heights'].append(row.pop(0))
            machine_perf_dict['bin_matrix'].append(row)
        machine_perf_file.close()
        args['machine_perf'] = machine_perf_dict
        
        #Create a dictionary whose keys are the 'NAMES' from the machine 
        #parameter table and whose values are from the corresponding 
        #'VALUES' field.
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
        wave_data_shape_path = os.path.join(
                output_dir, 'Intermediate/WEM_InputOutput_Pts.shp')
        regression_shape_path = os.path.join(
                regression_dir, 'WEM_InputOutput_Pts_bio_regression.shp')
        invest_test_core.assertTwoShapesEqualURI(
                self, wave_data_shape_path, regression_shape_path)                        
        #Check that resulting rasters are correct
        invest_test_core.assertTwoDatasetEqualURI(self,
            os.path.join(output_dir, 'Output/wp_kw.tif'),
            os.path.join(regression_dir, 'wp_kw_regression.tif'))
        invest_test_core.assertTwoDatasetEqualURI(self,
            os.path.join(output_dir, 'Output/capwe_mwh.tif'),
            os.path.join(regression_dir, 'capwe_mwh_regression.tif'))
        invest_test_core.assertTwoDatasetEqualURI(self,
            os.path.join(output_dir, 'Output/wp_rc.tif'),
            os.path.join(regression_dir, 'wp_rc_regression.tif'))
        invest_test_core.assertTwoDatasetEqualURI(self,
            os.path.join(output_dir, 'Output/capwe_rc.tif'),
            os.path.join(regression_dir, 'capwe_rc_regression.tif'))

    def test_wave_energy_change_projection(self):
        """Test change_projection by comparing returned shapefiles projection
        features with hand calculated ones to make sure the change occurred.
        Also make sure that the features and field values are the same.
        """
        raise SkipTest
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_change_projection'
        regression_dir = './data/wave_energy_regression_data'
        shape_to_reproject_path = os.path.join(
                test_dir, 'test_input/NAmerica_WestCoast_4m.shp')
        projected_path = os.path.join(
                regression_dir, 'wave_energy_clip_prj.shp')
        output_path = os.path.join(output_dir, 'wave_energy_clip_prj.shp')

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        shape_to_reproject = ogr.Open(shape_to_reproject_path)

        prj_ds = ogr.Open(projected_path)
        prj_layer = prj_ds.GetLayer()
        spatial_prj = prj_layer.GetSpatialRef()

        new_shape = wave_energy_core.change_shape_projection(
                shape_to_reproject, spatial_prj, output_path)
       
        new_shape = None
        shape_to_reproject = None

        invest_test_core.assertTwoShapesEqualURI(
                self, projected_path, output_path)
        
    def test_wave_energy_build_point_shapefile(self):
        """A regression test that uses known data and inputs to test
        the validity of the function build_point_shapefile"""
        raise SkipTest
        output_dir = './data/test_out/wave_energy_core_build_pt_shapefile'
        reg_shape_path = \
            './data/wave_energy_regression_data/LandPts_prj_regression.shp'
        reg_shape = ogr.Open(reg_shape_path)
        driver_name = 'ESRI Shapefile'
        layer_name = 'landpoints'
        path = os.path.join(output_dir, 'test_build_pt.shp')
        data = {1:[48.921,-125.542],2:[49.139,-125.915]}

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        if os.path.isfile(path):
            os.remove(path)

        #Create a coordinate transformation for lat/long to meters
        srs_prj = osr.SpatialReference()
        #Using 'WGS84' as our well known lat/long projection
        srs_prj.SetWellKnownGeogCS("WGS84")
        source_sr = srs_prj
        target_sr = reg_shape.GetLayer(0).GetSpatialRef()
        coord_trans = osr.CoordinateTransformation(source_sr, target_sr)

        built_shape = wave_energy_core.build_point_shapefile(
                driver_name, layer_name, path, data, target_sr, coord_trans)
        built_shape = None
        reg_shape = None
        invest_test_core.assertTwoShapesEqualURI(self, path, reg_shape_path)
                
    def test_wave_energy_clip_shape(self):
        """A trivial test case that makes sure clip_shape returns the proper 
        shape after it has been clipped by a polygon shapefile.  
        Here the clipping polygon is the same size and form as the shape to be 
        clipped so we would expect the output to be equal to the input"""

        raise SkipTest
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_clip_shape'
        shape_to_clip_path = os.path.join(
                test_dir, 'test_input/NAmerica_WestCoast_4m.shp')
        binding_shape_path = os.path.join(
                test_dir, 'test_input/WCNA_extract.shp')
        new_shape_path = os.path.join(
                output_dir, 'wave_energy_clipz.shp')

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        if os.path.isfile(new_shape_path):
            os.remove(new_shape_path)
            
        shape_to_clip = ogr.Open(shape_to_clip_path)
        binding_shape = ogr.Open(binding_shape_path)

        new_shape = wave_energy_core.clip_shape(
                shape_to_clip, binding_shape, new_shape_path)

        new_shape.Destroy()
        shape_to_clip.Destroy()
        binding_shape.Destroy()

        invest_test_core.assertTwoShapesEqualURI(
                self, shape_to_clip_path, new_shape_path)

    def test_wave_energy_clip_shape_empty(self):
        """A trivial test case that makes sure clip_shape returns an empty
        shapefile if the binding polygon does not intersect with the other
        shape's features"""

        raise SkipTest
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_clip_shape'
        shape_to_clip_path = os.path.join(
                test_dir, 'test_input/pointShapeTest.shp')
        binding_shape_path = os.path.join(test_dir, 'test_input/AOI_WCVI.shp')
        new_shape_path = os.path.join(output_dir, 'wave_energy_NoClip.shp')

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        shape_to_clip = ogr.Open(shape_to_clip_path)
        binding_shape = ogr.Open(binding_shape_path)

        new_shape = wave_energy_core.clip_shape(
                shape_to_clip, binding_shape, new_shape_path)

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
        raise SkipTest

        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_clip_shape'
        shape_to_clip_path = os.path.join(
                test_dir, 'test_input/NAmerica_WestCoast_4m.shp')
        binding_shape_path = os.path.join(
                test_dir, 'test_input/threePointShape.shp')
        new_shape_path = os.path.join(
                output_dir, 'wave_energy_ClipAOI.shp')

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        shape_to_clip = ogr.Open(shape_to_clip_path)
        binding_shape = ogr.Open(binding_shape_path)

        new_shape = wave_energy_core.clip_shape(
                shape_to_clip, binding_shape, new_shape_path)
        #It seems that the fields "FID" and "Shape" are not included for some 
        #reason when
        #Looping through all the fields of the shapefile
        point_one_fields = [572, 490, -126.933144, 47.600162, 2.8, 11.1]
        point_two_fields = [573, 490, -126.866477, 47.600162, 2.8, 11.11]
        point_three_fields = [574, 490, -126.79981, 47.600162, 2.79, 11.11]
        point_field_array = [point_one_fields, point_two_fields, 
                             point_three_fields]

        layer = new_shape.GetLayer(0)
        feat_count_calc = 3
        feat_count = layer.GetFeatureCount()
        self.assertEqual(feat_count_calc, feat_count, 
                         'The number of features are not correct')

        feat = layer.GetNextFeature()
        point_array_iderator = 0
        while feat is not None:
            layer_def = layer.GetLayerDefn()
            point_field = point_field_array[point_array_iderator]
            field_count = layer_def.GetFieldCount()
            fld_count_calc = 6
            self.assertEqual(field_count, fld_count_calc, 
                             'The number of fields are not correct')
            for fld_index in range(field_count):
                field = feat.GetField(fld_index)
                field_calc = point_field[fld_index]
                self.assertEqual(field, field_calc, \
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
        raise SkipTest

        shape_path = './data/wave_energy_data/test_input/pointShapeTest.shp'

        shape_to_clip = ogr.Open(shape_path)
        value = 'HSAVG_M'
        points = [[-126.933144, 47.600162], [-126.866477, 47.600162], 
                  [-126.79981, 47.600162]]
        values = [2.8, 2.8, 2.79]
        shape_array = wave_energy_core.get_points_values(shape_to_clip, value)
        self.assertEqual(len(points), len(shape_array[0]), 
                         'The number of points do not match')
        self.assertEqual(len(values), len(shape_array[1]), 
                         'The number of values do not match')
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
        """Test captured_wave_energy_to_shape using hand calculated and 
        generated values to pass into the function.
        """
        raise SkipTest

        shape_path = './data/wave_energy_data/test_input/pointShapeTest.shp'
        wave_shape = ogr.Open(shape_path)

        wave_shape_copy = \
            ogr.GetDriverByName('Memory').CopyDataSource(wave_shape, '')

        test_dict = {(572, 490):2302, (573, 490):1453, (574, 490):2103}
        ij_array = [[572, 490], [573, 490], [574, 490]]
        
        wave_energy_core.captured_wave_energy_to_shape(
                test_dict, wave_shape_copy)

        layer = wave_shape_copy.GetLayer(0)
        #Need to reset the layer because the function call goes through the 
        #features in the layer and does not reset or close.
        layer.ResetReading()
        feat = layer.GetNextFeature()
        comp_dict = {}
        while feat is not None:
            temp_array = []
            for fld in ('I', 'J', 'CAPWE_MWHY'):
                index = feat.GetFieldIndex(fld)
                field_val = feat.GetField(index)
                temp_array.append(field_val)
            comp_dict[(temp_array[0], temp_array[1])] = temp_array[2]

            feat.Destroy()
            feat = layer.GetNextFeature()

        self.assertEqual(len(test_dict), len(comp_dict), 
                         'The lengths of the dictionaries are not the same')

        for key, val in test_dict.iteritems():
            if key in comp_dict:
                self.assertEqual(val, comp_dict[key])
            else:
                self.assertEqual(0, 1, 
                                 'The key does not exist in the new feature')
        wave_shape.Destroy()
        wave_shape_copy.Destroy()

    def test_wave_energy_compute_wave_energy_capacity(self):
        """Test compute_wave_energy_capacity function using hand generated
        values and results."""

        raise SkipTest
        #A dictionary representing a mini version of what would be produced
        #from the wave watch text file
        wave_data = {'periods':[1, 2, 3, 4, 5], 'heights':[1, 2, 3, 4],
                     'bin_matrix':{(520, 490):[[0, 2, 2.6, 1.8, 1.4],
                                               [1.6, 3, 3.4, 2.6, .6],
                                               [0, .6, 2.2, 1.8, 1.4],
                                               [2.2, 3.4, 4.6, 3.8, 2.4]],
                                   (521, 491):[[-.2, 1.3, 2.66, 1.8, 1.4],
                                               [-1.6, -1, 34, 2.6, 0],
                                               [.4, .6, 2.3, 1.8, 1.45],
                                               [2.2, 3.4, 4.6, 3.8, 2.4]]
                                   }
                    }
        #An interpolated object from machine performace and wave_data ranges
        interpZ = [[0, 0, 1, 3, 8], [0, 3, 5, 9, 7], 
                   [1, 4, 5, 3, 0], [0, 0, 0, 0, 0]]
        #A dictionary with CapMax TpMax and HsMax as limitations
        machine_param = {'capmax':20, 'tpmax':4, 'hsmax':3}
        #Hand calculated results for the two points
        result = {(520, 490):0.0762, (521, 491):0.22116}

        we_sum = wave_energy_core.compute_wave_energy_capacity(
                    wave_data, interpZ, machine_param)

        #Loop that compares dictionaries we_sum and result checking key, 
        #sum values
        for key in result:
            if key in we_sum:
                self.assertAlmostEqual(result[key], we_sum[key], 8, \
                        'The values do not match for key ' + str(we_sum[key]))
            else:
                self.assertEqual(0, 1, 'The keys do not match')

    def test_wave_energy_wave_energy_interp(self):
        """Test wave_energy_interp by using hand calculations and hand
        calculated results based on the given inputs.
        """
        raise SkipTest
        #Rows/Col
        wave_data = {'periods':[1, 2, 3, 4, 5, 6, 7, 8], 
                     'heights':[.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]}
        #Machine performace table with first two arrays being rows/col
        machine_perf = {'periods':[2, 3, 4, 7], 'heights': [1, 2, 3],
                        'bin_matrix':[[0, 8, 20, 10],
                                      [6, 18, 23, 13],
                                      [0, 8, 20, 0]]
                        }
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

        self.assertEqual(
                result.shape, interpZ.shape, 'The shapes are not the same')

        for indexOut, ar in enumerate(result):
            for indexIn, val in enumerate(ar):
                self.assertAlmostEqual(val, interpZ[indexOut][indexIn], 5, 
                                       'Values do not match')

    def test_wave_energy_clip_raster_from_polygon(self):
        """Test clip_raster_from_polygon by using hand calculations of
        what the clipped raster should have as values and shape.
        """
        raise SkipTest
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_clip_raster_from_poly'
        shape_path = os.path.join(test_dir, 'test_input/threePointShape.shp')
        raster_path = os.path.join(test_dir, 'test_input/noAOIWP.tif')
        path = os.path.join(output_dir, 'clip_raster_from_poly_wpClipped.tif')

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        shape = ogr.Open(shape_path)
        raster = gdal.Open(raster_path)

        new_raster = wave_energy_core.clip_raster_from_polygon(
                shape, raster, path)

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
                    self.assertEqual(val, matrix[index][i], 
                                     'Values are not the same')

        self.assertEqual(len(temp_matrix), 10, 'Number of pixels do not match')

        for i, val in enumerate(test_matrix):
            self.assertAlmostEqual(val, temp_matrix[i], 4)

        new_raster = None
        raster = None
        shape.Destroy()
        
    def test_wave_energy_clip_raster_from_polygon_regression(self):
        """A regression test for clip_raster_from_polygon function."""
        #raise SkipTest
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_clip_raster_from_poly'
        regression_dir = './data/wave_energy_regression_data'
        raster_input_path = os.path.join(
                test_dir, 'test_input/clip_raster_from_poly_capwe.tif')
        copy_raster_input_path = os.path.join(
                output_dir, 'clip_raster_from_poly_output.tif')
        regression_raster_path = os.path.join(
                regression_dir, 'clip_raster_from_poly_regression.tif')
        clip_shape_path = os.path.join(
                test_dir, 'test_input/clip_raster_from_poly_shape.shp')
        
        clip_shape = ogr.Open(clip_shape_path)
        raster_input = gdal.Open(raster_input_path)

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        
        copy_raster = wave_energy_core.clip_raster_from_polygon(
                clip_shape, raster_input, copy_raster_input_path)
        copy_raster.FlushCache()
        #Check that resulting rasters are correct
        copy_raster = None
        clip_shape = None
        raster_input = None

        invest_test_core.assertTwoDatasetEqualURI(self,
            regression_raster_path, copy_raster_input_path)
                

    def test_wave_energy_wave_power(self):
        """Test the wave_power function by hand calculating wave power with 
        known variables and creating shapefile with those variables and 
        comparing returned value against known results."""
        raise SkipTest

        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_wave_power'
        shape_path = test_dir + os.sep + 'test_input/test_wave_power_shape.shp'
        shape_copy_path = output_dir + os.sep + 'test_wave_power_shape.shp'
        
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(shape_copy_path):
            os.remove(shape_copy_path)

        depth_list = [-500, -1000, -100, 1, -80]
        height_list = [2.5, 2.8, 2.3, 1.5, 2.04]
        period_list = [10.0, 12.0, 8.0, 5.0, 11.3]
        calculations_by_hand = [26.39331177, 39.729324, 17.87146248, 
                                3.996030763, 20.10613825]
        shape = ogr.Open(shape_path)
        
        shape_copy = ogr.GetDriverByName('ESRI Shapefile').\
                             CopyDataSource(shape, shape_copy_path)
        layer = shape_copy.GetLayer(0)
        for field in ['DEPTH_M', 'HSAVG_M', 'TPAVG_S']:
            fld_defn = ogr.FieldDefn(field, ogr.OFTReal)
            layer.CreateField(fld_defn)
        layer.ResetReading()
        feat = layer.GetNextFeature()
        i = 0
        while feat is not None:
            height_index = feat.GetFieldIndex('HSAVG_M')
            period_index = feat.GetFieldIndex('TPAVG_S')
            depth_index = feat.GetFieldIndex('DEPTH_M')
        
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
            wave_power_index = feat.GetFieldIndex('WE_kWM')
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
        raise SkipTest

        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_wave_power'
        regression_dir = './data/wave_energy_regression_data'
        shape_path = \
            test_dir + os.sep + 'test_input/test_wavepower_withfields.shp'
        shape_copy_path = \
            output_dir + os.sep + 'regression_test_wave_power_output.shp'
        regression_shape_path = \
            regression_dir + os.sep + 'wave_power_regression.shp'
        
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(shape_copy_path):
            os.remove(shape_copy_path)

        shape = ogr.Open(shape_path)
        shape_reg = ogr.Open(regression_shape_path)
        shape_copy = ogr.GetDriverByName('ESRI Shapefile').\
                             CopyDataSource(shape, shape_copy_path)
        shape_copy = wave_energy_core.wave_power(shape_copy)
        
        layer = shape_copy.GetLayer(0)
        layer_reg = shape_reg.GetLayer(0)
        layer.ResetReading()
        feat = layer.GetNextFeature()
        feat_reg = layer_reg.GetNextFeature()
        while feat is not None:
            wave_power_index = feat.GetFieldIndex('WE_kWM')
            wave_power_index_reg = feat_reg.GetFieldIndex('WE_kWM')
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
        raise SkipTest
        shape_path = \
            './data/wave_energy_data/test_input/test_wavepower_withfields.shp'
        
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
        raise SkipTest
        xy_1 = np.array([[250, 120], [300, 212], [125, 215], [1222, 988]])
        xy_2 = np.array([[156, 133], [198, 111]])
        calculated_dist_results = np.array([52.77309921, 143.5444182, 
                                            87.66413178, 1348.222904])
        calculated_id_results = np.array([1, 1, 0, 1])
        dist_results, id_results = \
            wave_energy_core.calculate_distance(xy_1, xy_2)
        calculated_dist_rounded = np.ma.round(calculated_dist_results, 3)
        dist_rounded = np.ma.round(dist_results, 3)
        mask_dist = calculated_dist_rounded == dist_rounded
        mask_id = calculated_id_results == id_results
        self.assertTrue(mask_dist.all(),
                        'Not all of the distances were equal.')
        self.assertTrue(mask_id.all(), 'Not all of the IDs matched.')
        
    def test_wave_energy_create_percentile_raster(self):
        """A non-trivial test case that passes in a generated 10x10 raster
        with values from 1 - 100, along with the other necessary arguments.
        It then compares the resulting percentile raster against hand
        calculated results."""
        
        raise SkipTest
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_percentile_raster'
        #Output path for created raster
        perc_path = output_dir + os.sep + 'percentile_five_by_five.tif'
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(perc_path):
            os.remove(perc_path)
        #Make a dummy 10 x 10 raster
        raster_size = 10
        driver = gdal.GetDriverByName('GTiff')
        dataset = driver.Create(perc_path, raster_size, raster_size, 1, 
                                gdal.GDT_Int32)
        #Create a 10 x 10 2D numpy array with values ranging from 1 to 100
        raster_data = np.reshape(np.arange(1,101),(10,10))
        dataset.GetRasterBand(1).WriteArray(raster_data, 0, 0)
        calculated_perc_list = [25,50,75,90]
        calc_value_array = [1,2,3,4,5]
        calc_count_array = [24, 25, 25, 15, 11]
        calc_val_range_array = ['1 - 25 the amount of mice per cat (mice/cat)',
                                '25 - 50 (mice/cat)',
                                '50 - 75 (mice/cat)',
                                '75 - 90 (mice/cat)',
                                'Greater than 90 (mice/cat)']
        calculated_output_raster = np.array([[1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,2,2,2,2,2,2],
                                            [2,2,2,2,2,2,2,2,2,2],
                                            [2,2,2,2,2,2,2,2,2,3],
                                            [3,3,3,3,3,3,3,3,3,3],
                                            [3,3,3,3,3,3,3,3,3,3],
                                            [3,3,3,3,4,4,4,4,4,4],
                                            [4,4,4,4,4,4,4,4,4,5],
                                            [5,5,5,5,5,5,5,5,5,5]])
        units_short = ' (mice/cat)'
        units_long = ' the amount of mice per cat (mice/cat)'
        percentile_raster = \
            wave_energy_core.create_percentile_rasters(dataset, perc_path, 
                                                       units_short, units_long, 
                                                       '1', [25,50,75,90], 0)
        perc_band = percentile_raster.GetRasterBand(1)
        perc_matrix = perc_band.ReadAsArray()
        LOGGER.debug('percentile matrix: %s', perc_matrix)
        LOGGER.debug('matrix: %s', calculated_output_raster)
        #Assert that the resulting raster's data is what is expected
        self.assertTrue((perc_matrix == calculated_output_raster).all())
        #Verify the resulting dbf attribute table is what is expected
        try:
            db_file = dbf.Dbf(perc_path+'.vat.dbf')
            value_array = []
            count_array = []
            val_range_array = []
            for rec in db_file:
                value_array.append(rec['VALUE'])
                count_array.append(rec['COUNT'])
                val_range_array.append(rec['VAL_RANGE'])
            LOGGER.debug('ranges : %s : %s', val_range_array, 
                         calc_val_range_array)
            for i in range(5):
                self.assertEqual(value_array[i], calc_value_array[i])
                self.assertEqual(count_array[i], calc_count_array[i])
                self.assertEqual(val_range_array[i], calc_val_range_array[i])
            db_file.close()
        except IOError, error:
            self.assertTrue(False, 'The dbf file could not be opened')
    
    def test_wave_energy_create_percentile_raster_regression(self):
        """A regression test for create_percentile_raster."""
        raise SkipTest
        
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_percentile_raster'
        regression_dir = './data/wave_energy_regression_data'
        #The raster dataset input
        regression_dataset_uri = regression_dir + os.sep + 'wp_kw_regression.tif'
        #The raster dataset and dbf file to test against
        regression_perc_uri = regression_dir + os.sep + 'wp_rc_regression.tif'
        regression_table_uri = regression_dir + os.sep + 'wp_rc_regression.tif.vat.dbf'
        #The resulting output raster location the function produces
        perc_path = output_dir + os.sep + 'wp_percentile.tif'
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(perc_path):
            os.remove(perc_path)
    
        regression_dataset = gdal.Open(regression_dataset_uri)
        units_short = ' (kW/m)'
        units_long = ' wave power per unit width of wave crest length (kW/m)'
        percentile_raster = \
            wave_energy_core.create_percentile_rasters(regression_dataset, 
                                                       perc_path, units_short, 
                                                       units_long, '1',
                                                       [25,50,75,90], 0)
        percentile_raster = None
        regression_dataset = None
        #Check the resulting raster against the regression raster
        invest_test_core.assertTwoDatasetEqualURI(self,
            regression_perc_uri, perc_path)
        #Verify the dbf attribute tables are correct
        try:
            regression_table = dbf.Dbf(regression_table_uri)
            db_file = dbf.Dbf(perc_path+'.vat.dbf')
            value_array = []
            count_array = []
            val_range_array = []
            for rec, reg_rec in zip(db_file, regression_table):
                self.assertEqual(rec['VALUE'], reg_rec['VALUE'])
                self.assertEqual(rec['COUNT'], reg_rec['COUNT'])
                self.assertEqual(rec['VAL_RANGE'], reg_rec['VAL_RANGE'])
            db_file.close()
            regression_table.close()
        except IOError, error:
            self.assertTrue(False, 'The dbf file could not be opened')
        
    def test_wave_energy_get_percentiles(self):
        """A straight forward test that passes in a list of percentiles
        and a list of values.  The returned percentile marks are compared
        against hand calculated results."""
        raise SkipTest
        
        values = np.arange(1,101)
        calc_percentiles = [25, 50, 75, 90]
        perc_list = [25,50,75,90]
        percentiles = wave_energy_core.get_percentiles(values, perc_list)
        self.assertTrue(calc_percentiles == percentiles)
        return
    
    def test_wave_energy_create_percentile_ranges(self):
        """A non-trivial test case that compares hand calculated
        percentile ranges with ranges returned from the function being
        tested."""
        
        raise SkipTest
        units_short = ' (m/s)'
        units_long = ' the rate of time travel in meters per second (m/s)'
        percentiles = [4, 8, 12, 16]
        ranges = wave_energy_core.create_percentile_ranges(percentiles, units_short, units_long, '1')
        calc_ranges = ['1 - 4 the rate of time travel in meters per second (m/s)',
                       '4 - 8 (m/s)', '8 - 12 (m/s)', '12 - 16 (m/s)', 'Greater than 16 (m/s)']
        #Check that the returned ranges as Strings are correct
        self.assertTrue(ranges == calc_ranges)
        return
    
    def test_wave_energy_create_attribute_table(self):
        """A non-trivial test case that compares hand calculated
        attribute table values against the returned dbf's values
        from the function being tested."""
        raise SkipTest
        
        output_dir = './data/test_out/wave_energy_core_attribute_table'
        raster_uri = output_dir + os.sep + 'test_attr_table.tif'
        dbf_uri = raster_uri + '.vat.dbf'
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(dbf_uri):
            os.remove(dbf_uri)
        #Make pre-calculated attribute table that should match the results
        #the function returns
        calc_ranges = \
            ['1 - 4 the rate of time travel in meters per second (m/s)',
            '4 - 8 (m/s)', '8 - 12 (m/s)', '12 - 16 (m/s)', 
            'Greater than 16 (m/s)']
        calc_count = [24, 25, 25, 15, 11]
        calc_values = [1,2,3,4,5]
        wave_energy_core.create_attribute_table(raster_uri, calc_ranges, 
                                                calc_count)
        #Check that the dbf attribute table returned is correct and what
        #is expected
        try:
            db_file = dbf.Dbf(dbf_uri)
            value_array = []
            count_array = []
            val_range_array = []
            for rec in db_file:
                value_array.append(rec['VALUE'])
                count_array.append(rec['COUNT'])
                val_range_array.append(rec['VAL_RANGE'])
            LOGGER.debug('ranges : %s : %s', val_range_array, calc_ranges)
            for i in range(5):
                self.assertEqual(value_array[i], calc_values[i])
                self.assertEqual(count_array[i], calc_count[i])
                self.assertEqual(val_range_array[i], calc_ranges[i])
            db_file.close()
        except IOError, error:
            self.assertTrue(False, 'The dbf file could not be opened')
        
    def test_wave_energy_valuation_regression(self):
        """Runs the valuation part of the Wave Energy Model (WEM),
        and does regression tests against the raster outputs and shapefile
        output.
        """
        raise SkipTest
        test_dir = './data/wave_energy_data'
        output_dir = './data/test_out/wave_energy_core_valuation'
        intermediate_dir = output_dir + os.sep + 'Intermediate'
        out_dir = output_dir + os.sep + 'Output'
        wave_data_shape_path = \
            test_dir + os.sep + 'test_input/WEM_InputOutput_Pts_Bio.shp'
        wave_data_copy_path = \
            test_dir + os.sep + 'test_input/WEM_InputOutput_Bio_copy.shp'
        number_of_machines = 28
        machine_econ_path = \
            test_dir + os.sep + 'samp_input/Machine_PelamisEconCSV.csv'
        land_grid_path = \
            test_dir + os.sep + 'samp_input/LandGridPts_WCVI_221.csv'
        dem_path = test_dir + os.sep + 'samp_input/global_dem'
        
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(wave_data_copy_path):
            os.remove(wave_data_copy_path)
        for file in [intermediate_dir, out_dir]:
            if not os.path.isdir(file):
                os.mkdir(file)
                
        wave_data_shape = ogr.Open(wave_data_shape_path)
        wave_data_shape_copy = \
            ogr.GetDriverByName('ESRI Shapefile').\
                CopyDataSource(wave_data_shape, wave_data_copy_path)
        
        #Set all arguments to be passed
        args = {}
        args['workspace_dir'] = output_dir
        args['wave_data_shape'] = wave_data_shape_copy
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
            LOGGER.error('File I/O error' + error)
        
        #Read landing and power grid connection points into a dictionary
        try:
            land_grid_pts = {}
            land_grid_pts_file = open(land_grid_path)
            reader = csv.DictReader(land_grid_pts_file)
            for row in reader:
                LOGGER.debug('Land Grid Row: %s', row)
                if row['ID'] in land_grid_pts:
                    land_grid_pts[row['ID'].strip()][row['TYPE']] = \
                        [row['LAT'], row['LONG']]
                else:
                    land_grid_pts[row['ID'].strip()] = \
                        {row['TYPE']:[row['LAT'], row['LONG']]}
            LOGGER.debug('New Land_Grid Dict : %s', land_grid_pts)
            land_grid_pts_file.close()
            args['land_gridPts'] = land_grid_pts
        except IOError, error:
            LOGGER.error('File I/O error' + error) 

        wave_energy_core.valuation(args)
        
        regression_dir = './data/wave_energy_regression_data/'
        
        #Regression Check for NPV raster
        invest_test_core.assertTwoDatasetEqualURI(self,
            output_dir + os.sep + 'Output/npv_usd.tif',
            regression_dir + 'npv_usd_regression.tif')
        
        #Regression Check for NPV percentile raster
        invest_test_core.assertTwoDatasetEqualURI(self,
            output_dir + os.sep + 'Output/npv_rc.tif',
            regression_dir + 'npv_rc_regression.tif')
        
        #Regression Check for LandPts_prj shapefile
        landing_shape_path = output_dir + os.sep + 'Output/LandPts_prj.shp'
        regression_landing_shape_path = \
            regression_dir + 'LandPts_prj_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, landing_shape_path, 
                                                 regression_landing_shape_path)
        
        #Regression Check for GridPts_prj shapefile
        grid_shape_path = output_dir + os.sep + 'Output/GridPts_prj.shp'
        regression_grid_shape_path = \
            regression_dir + 'GridPts_prj_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, grid_shape_path, 
                                                 regression_grid_shape_path)
        
        #Regression Check for WEM_InputOutput_Pts shapefile
        regression_wave_data_shape_path = \
            regression_dir + 'WEM_InputOutput_Pts_val_regression.shp'
        invest_test_core.assertTwoShapesEqualURI(self, wave_data_copy_path, 
                                                 regression_wave_data_shape_path)

        try:
            regression_table = dbf.Dbf(regression_dir + os.sep + \
                                      'npv_rc_regression.tif.vat.dbf')
            db_file = dbf.Dbf(output_dir + os.sep + 'Output/npv_rc.tif.vat.dbf')
            value_array = []
            count_array = []
            val_range_array = []
            for rec, reg_rec in zip(db_file, regression_table):
                self.assertEqual(rec['VALUE'], reg_rec['VALUE'])
                self.assertEqual(rec['COUNT'], reg_rec['COUNT'])
                self.assertEqual(rec['VAL_RANGE'], reg_rec['VAL_RANGE'])
            db_file.close()
            regression_table.close()
        except IOError, error:
            self.assertTrue(False, 'The dbf file could not be opened')
