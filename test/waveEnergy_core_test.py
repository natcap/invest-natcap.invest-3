import sys
import os
import unittest
import math
import csv
import osr

from osgeo import ogr
from osgeo import gdal
from osgeo.gdalconst import *
from invest_natcap.dbfpy import dbf
import numpy as np

from invest_natcap.wave_energy import waveEnergy_core
from invest_natcap.wave_energy import waveEnergy_biophysical
import invest_test_core

class TestWaveEnergy(unittest.TestCase):

    def test_wave_energy_biophysical_regression(self):
        """Runs the biophysical part of the Wave Energy Model (WEM).
    
        args['wave_base_data'] - a dictionary of seastate bin data.
        args['analysis_area'] - a point geometry shapefile representing the relevant WW3 points
        args['analysis_area_extract'] - a polygon geometry shapefile encompassing the broader range
                                        of interest.
        args['AOI'] - a polygon geometry shapefile outlining a more specific area of interest.
        args['machine_perf'] - a 2D array representing the machine performance table.
        args['machine_param'] - a dictionary which holds the machine parameter values.
        args['dem'] - a GIS raster file of the global elevation model
        args['workspace_dir'] - the workspace path
        args['wave_data_dir'] - the wave data path, used for retreiving other relevant files.
            
        """
        test_dir = './data/test_data/wave_Energy'
        analysis_path = test_dir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.shp'
        analysis_extract_path = test_dir + os.sep + 'samp_input/WaveData/WCNA_extract.shp'
        aoi_path = test_dir + os.sep + 'samp_input/AOI_WCVI.shp'
        dem_path = test_dir + os.sep + 'samp_input/global_dem'
        wave_file_path = test_dir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.txt'
        machine_perf_path = './data/test_data/wave_Energy/samp_input/Machine_PelamisPerfCSV.csv'
        machine_param_path = './data/test_data/wave_Energy/samp_input/Machine_PelamisParamCSV.csv'
        #Set all arguments to be passed
        args = {}
        args['wave_base_data'] = waveEnergy_biophysical.extrapolate_wave_data(wave_file_path)
        args['analysis_area'] = ogr.Open(analysis_path, 1)
        args['analysis_area_extract'] = ogr.Open(analysis_extract_path)
        args['aoi'] = ogr.Open(aoi_path)
        args['dem'] = gdal.Open(dem_path)
        args['workspace_dir'] = './data/test_data/wave_Energy'
        args['wave_data_dir'] = './data/test_data/wave_Energy/samp_input/WaveData'
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
        #and whose corresponding values are dictionaries whose keys are the column headers of
        #the machine parameter table with corresponding values
        try:
            machine_params = {}
            machine_param_file = open(machine_param_path)
            reader = csv.DictReader(machine_param_file)
            for row in reader:
                machine_params[row['NAME'].strip()] = row
            machine_param_file.close()
            args['machine_param'] = machine_params
        except IOError, e:
            print 'File I/O error' + e

        waveEnergy_core.biophysical(args)
        
        #Check that output/intermediate files have been made
        regression_shape = ogr.Open(args['workspace_dir'] + '/regression_tests/WaveData_clipZ_regression.shp')
        shape = ogr.Open(args['workspace_dir'] + '/Intermediate/WaveData_clipZ.shp')
        
        regression_layer = regression_shape.GetLayer(0)
        layer = shape.GetLayer(0)
        
        regression_feat_count = regression_layer.GetFeatureCount()
        feat_count = layer.GetFeatureCount()
        self.assertEqual(regression_feat_count, feat_count)
        
        layer_def = layer.GetLayerDefn()
        reg_layer_def = regression_layer.GetLayerDefn()
        field_count = layer_def.GetFieldCount()
        reg_field_count = reg_layer_def.GetFieldCount()
        self.assertEqual(field_count, reg_field_count, 'The shapes DO NOT have the same number of fields')
        
        reg_feat = regression_layer.GetNextFeature()
        feat = layer.GetNextFeature()
        while reg_feat is not None:            
            for fld_index in range(field_count):
                field = feat.GetField(fld_index)
                reg_field = reg_feat.GetField(fld_index)
                self.assertEqual(field, reg_field, 'The field values DO NOT match')
            feat.Destroy()
            reg_feat.Destroy()
            feat = layer.GetNextFeature()
            reg_feat = regression_layer.GetNextFeature()
                
        #Check that resulting rasters are correct
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/wp_kw.tif',
            args['workspace_dir'] + '/regression_tests/wp_kw_regression.tif')
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/capwe_mwh.tif',
            args['workspace_dir'] + '/regression_tests/capwe_mwh_regression.tif')

    def test_waveEnergy_changeProjection(self):
        test_dir = './data/test_data/wave_Energy'
        shape_to_reproject_path = test_dir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.shp'
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

        new_shape = waveEnergy_core.change_shape_projection(shape_to_reproject, projection, output_path)
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
        
        feat_count = lyr.GetFeatureCount()
        feat_count_projected = layer.GetFeatureCount()
        self.assertEqual(feat_count, feat_count_projected, 'The layers DO NOT have the same number of features')

        feat = lyr.GetNextFeature()
        feat_projected = layer.GetNextFeature()
        while feat is not None:
            layer_def = lyr.GetLayerDefn()
            layer_def_projected = layer.GetLayerDefn()

            field_count = layer_def.GetFieldCount()
            field_count_projected = layer_def_projected.GetFieldCount()
            self.assertEqual(field_count, field_count_projected, 'The shapes DO NOT have the same number of fields')

            for fld_index in range(field_count):
                field = feat.GetField(fld_index)
                field_projected = feat_projected.GetField(fld_index)
                self.assertEqual(field, field_projected, 'The field values DO NOT match')

            feat.Destroy()
            feat_projected.Destroy()
            feat = lyr.GetNextFeature()
            feat_projected = layer.GetNextFeature()
        
        shape_to_reproject.Destroy()
        new_shape.Destroy()
        
    def test_waveEnergy_clipShape(self):
        """A trivial test case that makes sure clip_shape returns the proper shape
        after it has been clipped by a polygon shapefile.  Here the clipping polygon is
        the same size and form as the shape to be clipped so we would expect the output to be
        equal to the input"""
        filesystemencoding = sys.getfilesystemencoding()

        test_dir = './data/test_data/wave_Energy'
        shape_to_clip_path = test_dir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.shp'
        binding_shape_path = test_dir + os.sep + 'samp_input/WaveData/WCNA_extract.shp'
        new_shape_path = test_dir + os.sep + 'test_output/waveEnergy_Clipz.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape_to_clip = ogr.Open(shape_to_clip_path.encode(filesystemencoding))
        binding_shape = ogr.Open(binding_shape_path.encode(filesystemencoding))

        new_shape = waveEnergy_core.clip_shape(shape_to_clip, binding_shape, new_shape_path)

        layer_count = shape_to_clip.GetLayerCount()
        layer_count_new = new_shape.GetLayerCount()
        self.assertEqual(layer_count, layer_count_new, 'The shapes DO NOT have the same number of layers')

        for layer_num in range(layer_count):
            layer = shape_to_clip.GetLayer(layer_num)
            layer.ResetReading()
            layer_new = new_shape.GetLayer(layer_num)

            feat_count = layer.GetFeatureCount()
            feat_count_new = layer_new.GetFeatureCount()
            self.assertEqual(feat_count, feat_count_new, 'The layers DO NOT have the same number of features')

            feat = layer.GetNextFeature()
            feat_new = layer_new.GetNextFeature()
            while feat is not None:
                layer_def = layer.GetLayerDefn()
                layer_def_new = layer_new.GetLayerDefn()

                field_count = layer_def.GetFieldCount()
                field_count_new = layer_def_new.GetFieldCount()
                self.assertEqual(field_count, field_count_new, 'The shapes DO NOT have the same number of fields')

                for fld_index in range(field_count):
                    field = feat.GetField(fld_index)
                    field_new = feat_new.GetField(fld_index)
                    self.assertEqual(field, field_new, 'The field values DO NOT match')

                feat.Destroy()
                feat_new.Destroy()
                feat = layer.GetNextFeature()
                feat_new = layer_new.GetNextFeature()

        new_shape.Destroy()
        shape_to_clip.Destroy()
        binding_shape.Destroy()

#        if os.path.isdir(output_dir):
#            textFileList = os.listdir(output_dir)
#            for file in textFileList:
#                os.remove(output_dir + file)
#            os.rmdir(output_dir)

    def test_waveEnergy_clipShapeZero(self):
        """A trivial test case that makes sure clip_shape returns the proper shape
        after it has been clipped by a polygon shapefile.  Here the clipping polygon is
        the same size and form as the shape to be clipped so we would expect the output to be
        equal to the input"""
        filesystemencoding = sys.getfilesystemencoding()

        test_dir = './data/test_data/wave_Energy'
        shape_to_clip_path = test_dir + os.sep + 'test_input/pointShapeTest.shp'
        binding_shape_path = test_dir + os.sep + 'samp_input/AOI_WCVI.shp'
        new_shape_path = test_dir + os.sep + 'test_output/waveEnergy_NoClip.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape_to_clip = ogr.Open(shape_to_clip_path.encode(filesystemencoding))
        binding_shape = ogr.Open(binding_shape_path.encode(filesystemencoding))

        new_shape = waveEnergy_core.clip_shape(shape_to_clip, binding_shape, new_shape_path)

        layer = new_shape.GetLayer(0)

        self.assertEqual(layer.GetFeatureCount(), 0)

        layer = None
        new_shape.Destroy()
        shape_to_clip.Destroy()
        binding_shape.Destroy()

    def test_waveEnergy_clipShapeProj(self):
        """A non trivial test case that makes sure clip_shape returns the proper shape
        after it has been clipped by a polygon shapefile."""
        filesystemencoding = sys.getfilesystemencoding()

        test_dir = './data/test_data/wave_Energy'
        shape_to_clip_path = test_dir + os.sep + 'samp_input/WaveData/NAmerica_WestCoast_4m.shp'
        binding_shape_path = test_dir + os.sep + 'test_input/threePointShape.shp'
        new_shape_path = test_dir + os.sep + 'test_output/waveEnergy_ClipAOI.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
#        elif os.path.isfile(output_dir + 'timber.shp'):
#            os.remove(output_dir + 'timber.shp')

        shape_to_clip = ogr.Open(shape_to_clip_path.encode(filesystemencoding))
        binding_shape = ogr.Open(binding_shape_path.encode(filesystemencoding))

        new_shape = waveEnergy_core.clip_shape(shape_to_clip, binding_shape, new_shape_path)

#        point_one_fields = [6025, 'Point', 572, 490, -126.933144, 47.600162, 2.8, 11.1]
#        point_two_fields = [6064, 'Point', 573, 490, -126.866477, 47.600162, 2.8, 11.11]
#        point_three_fields = [6101, 'Point', 574, 490, -126.79981, 47.600162, 2.79, 11.11]
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
                self.assertEqual(field, field_calc, 'The field values do not match' + str(field) + '!=' + str(field_calc))

            feat.Destroy()
            feat = layer.GetNextFeature()
            point_array_iderator = point_array_iderator + 1

        new_shape.Destroy()
        shape_to_clip.Destroy()
        binding_shape.Destroy()

#    def test_waveEnergy_shapeToDict(self):
#        """Test pointShapeToDict to make sure that it works properly for different geometries"""
#        filesystemencoding = sys.getfilesystemencoding()
#        
#        
#        test_dir = './data/test_data/wave_Energy'
#        shapePath = test_dir + os.sep + 'test_input/pointShapeTest.shp'
#        
#        #Add the Output directory onto the given workspace
#        output_dir = test_dir + os.sep + 'test_output/'
#        if not os.path.isdir(output_dir):
#            os.mkdir(output_dir)
##        elif os.path.isfile(output_dir + 'timber.shp'):
##            os.remove(output_dir + 'timber.shp')
#
#        shape_to_clip = ogr.Open(shapePath.encode(filesystemencoding))
#        key = ['LONG', 'LATI']
#        valueArray = ['LONG', 'LATI', 'HSAVG_M', 'TPAVG_S']
#        value = 'HSAVG_M'
#        xrange = [-126.933144, -126.866477, -126.79981]
#        yrange = [47.600162]
#        matrix = [[2.8, 2.8, 2.79]]
#        shapeArray = waveEnergy_core.pointShapeToDict(shape_to_clip, key, valueArray, value)
#        self.assertEqual(len(xrange), len(shapeArray[0]), 'xranges do not have same number of elements')
#        self.assertEqual(len(yrange), len(shapeArray[1]), 'yranges do not have same number of elements')
#        self.assertEqual(len(matrix), len(shapeArray[2]), 'matrices do not have same number of elements')
#        shapeMatrix = shapeArray[2]
#        for index, var in enumerate(matrix):
#            for innerIndex, num in enumerate(var):
#                self.assertEqual(num, shapeMatrix[index][innerIndex], 'The values of the matrices do not match')
#        
#        shape_to_clip.Destroy()

    def test_waveEnergy_getPointsValues(self):
        """Test getPointsValues to make sure that it works properly for different geometries"""
        filesystemencoding = sys.getfilesystemencoding()


        test_dir = './data/test_data/wave_Energy'
        shapePath = test_dir + os.sep + 'test_input/pointShapeTest.shp'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
#        elif os.path.isfile(output_dir + 'timber.shp'):
#            os.remove(output_dir + 'timber.shp')

        shape_to_clip = ogr.Open(shapePath.encode(filesystemencoding))
        key = ['LONG', 'LATI']
        value_array = ['LONG', 'LATI', 'HSAVG_M', 'TPAVG_S']
        value = 'HSAVG_M'
        points = [[-126.933144, 47.600162], [-126.866477, 47.600162], [-126.79981, 47.600162]]
        values = [2.8, 2.8, 2.79]
        shape_array = waveEnergy_core.get_points_values(shape_to_clip, key, value_array, value)
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

    def test_waveEnergy_capturedWaveEnergyToShape(self):
        """Test captured_wave_energy_to_shape to make sure that it works properly for different geometries"""
        filesystemencoding = sys.getfilesystemencoding()


        test_dir = './data/test_data/wave_Energy'
        shape_path = test_dir + os.sep + 'test_input/pointShapeTest.shp'
        new_path = str(test_dir + os.sep + 'test_output/pointShapeSum.shp')
        wave_shape = ogr.Open(shape_path.encode(filesystemencoding), 1)

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
#        elif os.path.isfile(output_dir + 'timber.shp'):
#            os.remove(output_dir + 'timber.shp')

        wave_shape_copy = ogr.GetDriverByName('Memory').CopyDataSource(wave_shape, '')
#        wave_shape_copy.Destroy()
#        wave_shape_copy = ogr.Open(new_path.encode(filesystemencoding), 1)

        test_dict = {(572, 490):2302, (573, 490):1453, (574, 490):2103}
        ij_array = [[572, 490], [573, 490], [574, 490]]
        waveEnergy_core.captured_wave_energy_to_shape(test_dict, wave_shape_copy)

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
                self.assertEqual(val, comp_dict[key], 'The values corresponding to the keys do not match' + str(val) + ':' + str(comp_dict[key]))
            else:
                self.assertEqual(0, 1, 'The key does not exist in the new feature')


        wave_shape.Destroy()
        wave_shape_copy.Destroy()


    def test_waveEnergy_computeWaveEnergyCapacity(self):
        """Test computWaveEnergyCapacity function to make sure it works properly"""

#        wave_data = 'A dictionary with key (I,J) and value 2D array'
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
#        interpZ = 'An interpolated object from machine performace and wave_data ranges'
        interpZ = [[0, 0, 1, 3, 8], [0, 3, 5, 9, 7], [1, 4, 5, 3, 0], [0, 0, 0, 0, 0]]
#        machine_param = 'A dictionary with CapMax TpMax and HsMax'
        machine_param = {'CapMax':{'VALUE':20}, 'TpMax':{'VALUE':4}, 'HsMax':{'VALUE':3}}
        result = {(520, 490):0.0762, (521, 491):0.22116}

        we_sum = waveEnergy_core.compute_wave_energy_capacity(wave_data, interpZ, machine_param)

        """Loop that compares dictionaries we_sum and result checking key, sum values"""
        for key in result:
            if key in we_sum:
                self.assertAlmostEqual(result[key], we_sum[key], 8, 'The values do not match for key ' + str(we_sum[key]))
            else:
                self.assertEqual(0, 1, 'The keys do not match')

    def test_waveEnergy_waveEnergyInterp(self):
        wave_data = {0:[1, 2, 3, 4, 5, 6, 7, 8], 1:[.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]}
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
        interpZ = waveEnergy_core.wave_energy_interp(wave_data, machine_perf)

        self.assertEqual(result.shape, interpZ.shape, 'The shapes are not the same')

        for indexOut, ar in enumerate(result):
            for indexIn, val in enumerate(ar):
                self.assertAlmostEqual(val, interpZ[indexOut][indexIn], 5, 'Values do not match')

    def test_waveEnergy_clipRasterFromPolygon(self):
        filesystemencoding = sys.getfilesystemencoding()

        test_dir = './data/test_data/wave_Energy'
        shape_path = test_dir + os.sep + 'test_input/threePointShape.shp'
        raster_path = test_dir + os.sep + 'test_input/noAOIWP.tif'
        path = test_dir + os.sep + 'test_output/wpClipped.tif'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape = ogr.Open(shape_path)
        raster = gdal.Open(raster_path)

        new_raster = waveEnergy_core.clip_raster_from_polygon(shape, raster, path)

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
        
    def test_waveEnergy_clipRasterFromPolygon_DEM(self):
        filesystemencoding = sys.getfilesystemencoding()

        test_dir = './data/test_data/wave_Energy'
        shape_path = test_dir + os.sep + 'samp_input/AOI_WCVI.shp'
        raster_path = test_dir + os.sep + 'samp_input/global_dem'
        path = test_dir + os.sep + 'test_output/clipped_dem.tif'

        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        shape = ogr.Open(shape_path)
        raster = gdal.Open(raster_path)

        new_raster = waveEnergy_core.clip_raster_from_polygon(shape, raster, path)

        new_raster = None

    def test_waveEnergy_interpPointsOverRaster(self):
        test_dir = './data/test_data/wave_Energy'
        path = test_dir + os.sep + 'test_output/fourbyfourRaster.tif'
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

        waveEnergy_core.interp_points_over_raster(points, values, raster)
        band = raster.GetRasterBand(1)
        matrix = band.ReadAsArray()
        self.assertEqual(matrix.size, result.size, 'The sizes are not the same')
        for indexOut, ar in enumerate(result):
            for indexIn, val in enumerate(ar):
                self.assertAlmostEqual(val, matrix[indexOut][indexIn], 5)

    def test_waveEnergy_wavePower(self):
        """Test wave_power to make sure desired outputs are met"""

        test_dir = './data/test_data/wave_Energy'
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
        shape_copy = waveEnergy_core.wave_power(shape_copy)
        
        layer = shape_copy.GetLayer(0)
        layer.ResetReading()
        feat = layer.GetNextFeature()
        i = 0
        while feat is not None:
            wave_power_index = feat.GetFieldIndex('wp_Kw')
            wave_power = feat.GetField(wave_power_index)
            self.assertAlmostEqual(wave_power, calculations_by_hand[i], 1)
            feat.Destroy()
            feat = layer.GetNextFeature()
            i = i + 1
        shape_copy.Destroy()
        shape.Destroy()
        
    def test_waveEnergy_wavePower_regression(self):
        """Test wave_power to make sure desired outputs are met"""

        test_dir = './data/test_data/wave_Energy'
        shape_path = test_dir + os.sep + 'test_input/test_wavepower_withfields.shp'
        shape_copy_path = test_dir + os.sep + 'test_output/test_wave_power_regression.shp'
        regression_shape_path = test_dir + os.sep + 'regression_tests/test_wave_power_shape.shp'
        #Add the Output directory onto the given workspace
        output_dir = test_dir + os.sep + 'test_output/'
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if os.path.isfile(shape_copy_path):
            os.remove(shape_copy_path)

        shape = ogr.Open(shape_path)
        shape_reg = ogr.Open(regression_shape_path)
        shape_copy = ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(shape, shape_copy_path)
        shape_copy = waveEnergy_core.wave_power(shape_copy)
        
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
            self.assertEqual(wave_power, wave_power_reg)
            feat.Destroy()
            feat_reg.Destroy()
            feat = layer.GetNextFeature()
            feat_reg = layer_reg.GetNextFeature()

        shape_copy.Destroy()
        shape.Destroy()
        shape_reg.Destroy()

    def test_waveEnergy_getPoints(self):
        test_dir = './data/test_data/wave_Energy'
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
        result_points = waveEnergy_core.get_points_geometries(src)
        
        for index, value in enumerate(result_points):
            self.assertEqual(value[0], calculated_points[index][0])
            self.assertEqual(value[1], calculated_points[index][1])
        
    def test_waveEnergy_calcDist(self):
        xy_1 = np.array([[250, 120], [300, 212], [125, 215], [1222, 988]])
        xy_2 = np.array([[156, 133], [198, 111]])
        calculated_dist_results = np.array([52.77309921, 143.5444182, 87.66413178, 1348.222904])
        calculated_id_results = np.array([1, 1, 0, 1])
        dist_results, id_results = waveEnergy_core.calculate_distance(xy_1, xy_2)
        calculated_dist_rounded = np.ma.round(calculated_dist_results, 3)
        dist_rounded = np.ma.round(dist_results, 3)
        mask_dist = calculated_dist_rounded == dist_rounded
        mask_id = calculated_id_results == id_results
        self.assertTrue(mask_dist.all())
        self.assertTrue(mask_id.all())
