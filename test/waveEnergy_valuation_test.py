import os
import sys
import unittest

import numpy as np
from osgeo import ogr
from invest_natcap.wave_energy import waveEnergy_valuation
import invest_test_core

class TestWaveEnergyValuation(unittest.TestCase):
    def test_wave_energy_valuation_regression(self):
        """A regression test for valuation file to make sure that the output
        raster and output shapefile are what is expected.
        """
        args = {}
        args['workspace_dir'] = './data/wave_energy_data'
        args['wave_base_data_uri'] = args['workspace_dir'] + os.sep + 'samp_input/WaveData'
        args['land_gridPts_uri'] = args['workspace_dir'] + os.sep + 'samp_input/LandGridPts_WCVI_CSV.csv'
        args['machine_econ_uri'] = args['workspace_dir'] + os.sep + 'samp_input/Machine_PelamisEconCSV.csv'
        args['number_of_machines'] = 28
        args['projection_uri'] = args['workspace_dir'] + os.sep + 'test_input/WGS_1984_UTM_Zone_10N.prj'
        args['global_dem'] = args['workspace_dir'] + os.sep + 'samp_input/global_dem'
        args['wave_data_shape_path'] = args['workspace_dir'] + os.sep + 'Intermediate/WaveData_clipZ.shp'
        
        waveEnergy_valuation.execute(args)
        regression_dir = './data/wave_energy_regression_data'
        #assert that the output raster is equivalent to the regression
        #test
        invest_test_core.assertTwoDatasetEqualURI(self,
            args['workspace_dir'] + '/Output/npv_usd.tif',
            regression_dir + '/npv_usd_regression.tif')

        #Regression Check for LandPts_prj shapefile
        regression_landing_shape = ogr.Open(regression_dir + '/LandPts_prj_regression.shp')
        landing_shape = ogr.Open(args['workspace_dir'] + '/Output/LandPts_prj.shp')
        
        regression_layer = regression_landing_shape.GetLayer(0)
        layer = landing_shape.GetLayer(0)
        
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
            
        regression_landing_shape.Destroy()
        landing_shape.Destroy()
        
        #Regression Check for GridPt_prj shapefile
        regression_grid_shape = ogr.Open(regression_dir + '/GridPt_prj_regression.shp')
        grid_shape = ogr.Open(args['workspace_dir'] + '/Output/GridPt_prj.shp')
        
        regression_layer = regression_grid_shape.GetLayer(0)
        layer = grid_shape.GetLayer(0)
        
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
            
        regression_grid_shape.Destroy()
        grid_shape.Destroy()
