import os
import sys
import unittest

import numpy as np
from osgeo import ogr
from invest_natcap.wave_energy import waveEnergy_biophysical
import invest_test_core

class TestWaveEnergyBiophysical(unittest.TestCase):
    def test_wave_energy_biophysical(self):
        args = {}
        args['workspace_dir'] = './data/wave_energy_data'
        args['wave_base_data_uri'] = args['workspace_dir'] + os.sep + 'samp_input/WaveData'
        args['analysis_area_uri'] = 'West Coast of North America and Hawaii'
        args['machine_perf_uri'] = args['workspace_dir'] + os.sep + 'samp_input/Machine_PelamisPerfCSV.csv'
        args['machine_param_uri'] = args['workspace_dir'] + os.sep + 'samp_input/Machine_PelamisParamCSV.csv'
        args['dem_uri'] = args['workspace_dir'] + os.sep + 'samp_input/global_dem'
#        args['aoi_uri'] = args['workspace_dir'] + os.sep + 'samp_input/AOI_WCVI.shp'
        waveEnergy_biophysical.execute(args)
        regression_dir = './data/wave_energy_regression_data'
        #assert that the output raster is equivalent to the regression test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/capwe_mwh.tif',
            regression_dir + '/capwe_mwh_regression.tif')
        
        #assert that the output raster is equivalent to the regression test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/wp_kw.tif',
            regression_dir + '/wp_kw_regression.tif')
        
        #Regression Check for WaveData_clipZ shapefile
        regression_wave_data_shape = ogr.Open(regression_dir
                                              + '/WaveData_clipZ_regression.shp')
        wave_data_shape = ogr.Open(args['workspace_dir'] 
                                   + '/Intermediate/WaveData_clipZ.shp')
        
        regression_layer = regression_wave_data_shape.GetLayer(0)
        layer = wave_data_shape.GetLayer(0)
        
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
            
        regression_wave_data_shape.Destroy()
        wave_data_shape.Destroy()

    def test_wave_energy_extrapolate_wave_data(self):
        wave_base_data_uri = './data/wave_energy_data/test_input/sampWaveDataTest.txt'
        if os.path.isfile(wave_base_data_uri):
            wave_data = waveEnergy_biophysical.extrapolate_wave_data(wave_base_data_uri)
            row = np.array([.25, 1.0, 2.0, 3.0, 4.0, 5.0])
            col = np.array([.125, .5, 1.0, 1.5, 2.0, 2.5])
            matrix1 = np.array([[0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 3.0, 0., 0.],
                                [0., 0., 0., 0., 24.0, 27.0],
                                [0., 0., 0., 0., 3.0, 219.0],
                                [0., 0., 0., 0., 0., 84.0],
                                [0., 0., 0., 0., 0., 12.0]])
            matrix2 = np.array([[0., 0., 0., 0., 0., 0.],
                                [0., 0., 0., 3.0, 0., 0.],
                                [0., 0., 0., 0., 24.0, 21.0],
                                [0., 0., 0., 0., 3.0, 219.0],
                                [0., 0., 0., 0., 0., 78.0],
                                [0., 0., 0., 0., 0., 12.0]])

            test_dict = {(580, 507): matrix1, (580, 508): matrix2}
            keys = [(580, 507), (580, 508)]
            for key in test_dict:
                if key in wave_data:
                    for i, ar in enumerate(test_dict[key]):
                        for index, val in enumerate(ar):
                            self.assertEqual(val, float(wave_data[key][i][index]))
                else:
                    self.assertEqual(0, 1, 'Keys do not match')
            for val, val2 in zip(row, wave_data[0]):
                self.assertEqual(val, val2)
            for val, val2 in zip(col, wave_data[1]):
                self.assertEqual(val, val2)
        else:
            print 'NOT A FILE'
