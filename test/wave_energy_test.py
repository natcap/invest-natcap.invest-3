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

from invest_natcap.wave_energy import wave_energy
import invest_test_core
from nose.plugins.skip import SkipTest

LOGGER = logging.getLogger('wave_energy_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestWaveEnergy(unittest.TestCase):

    def test_wave_energy_regression_no_options(self):
        """Regression test for the wave energy model without any optional
            inputs.
        """
        #raise SkipTest
        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy/no_options'
        
        #Set all arguments to be passed
        args = {}
        # Required
        args['workspace_dir'] = output_dir
        args['wave_base_data_uri'] = os.path.join(
                test_dir, 'samp_input/WaveData')
        args['analysis_area_uri'] = 'West Coast of North America and Hawaii'
        args['machine_perf_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisPerfCSV.csv')
        args['machine_param_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisParamCSV.csv')
        args['dem_uri'] = os.path.join(test_dir, 'samp_input/global_dem')
        # Optional
        #args['valuation_container'] = True
        #args['aoi_uri'] = os.path.join(test_dir, 'test_input/AOI_WCVI.shp')
        #args['land_gridPts_uri'] =  os.path.join(
        #        test_dir, 'samp_input/LandGridPts_WCVI_221.csv')
        #args['machine_econ_uri'] = os.path.join(
        #        test_dir, 'samp_input/Machine_PelamisEconCSV.csv') 
        #args['number_of_machines'] = 28 
        args['suffix'] = '' 
        
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        wave_energy.execute(args)
        
        regression_dir = './invest-data/test/data/wave_energy_regression_data/'
        
        # Path names for output rasters to test 
        regression_raster_uris = [
                os.path.join(regression_dir, 'wp_kw_no_aoi_regression.tif'),
                os.path.join(regression_dir, 'capwe_mwh_no_aoi_regression.tif'),
                os.path.join(regression_dir, 'wp_rc_no_aoi_regression.tif'),
                os.path.join(regression_dir, 'capwe_rc_no_aoi_regression.tif'),
        #        os.path.join(regression_dir, 'npv_usd_regression.tif'),
        #        os.path.join(regression_dir, 'npv_rc_regression.tif')
                ]
        raster_uris = [
                os.path.join(output_dir, 'output/wp_kw.tif'),
                os.path.join(output_dir, 'output/capwe_mwh.tif'),
                os.path.join(output_dir, 'output/wp_rc.tif'),
                os.path.join(output_dir, 'output/capwe_rc.tif'),
                #os.path.join(output_dir, 'output/npv_usd.tif'),
                #os.path.join(output_dir, 'output/npv_rc.tif')
                ]
        # Test that raster outputs are correct
        for reg_raster_uri, raster_uri in zip(
                regression_raster_uris, raster_uris):
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_raster_uri, raster_uri)
        
        # Path names for output shapefiles to test
        regression_shapes_uris = [
                os.path.join(
                    regression_dir, 'WEM_InputOutput_Pts_bio_no_aoi_regression.shp'),
                #os.path.join(
                #    regression_dir, 'WEM_InputOutput_Pts_val_regression.shp'),
                #os.path.join(regression_dir, 'LandPts_prj_regression.shp'),
                #os.path.join(regression_dir, 'GridPts_prj_regression.shp')
                ]
        shapes_uris = [
                os.path.join(output_dir,
                    'intermediate/WEM_InputOutput_Pts.shp'),
                #os.path.join(output_dir, 'output/LandPts_prj.shp'),
                #os.path.join(output_dir, 'output/GridPts_prj.shp')
                ]
        # Test that shapefile outputs are correct
        for reg_shapes_uri, shapes_uri in zip(
                regression_shapes_uris, shapes_uris):
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_shapes_uri, shapes_uri)

        # Path names for output dbf tables
        regression_dbf_uris = [
                os.path.join(regression_dir, 'wp_rc_no_aoi_regression.tif.vat.dbf'),
                os.path.join(regression_dir, 'capwe_rc_no_aoi_regression.tif.vat.dbf'),
                #os.path.join(regression_dir, 'npv_rc_regression.tif.vat.dbf')
                ]
        dbf_uris = [
                os.path.join(output_dir, 'output/wp_rc.tif.vat.dbf'),
                os.path.join(output_dir, 'output/capwe_rc.tif.vat.dbf'),
                #os.path.join(output_dir, 'output/npv_rc.tif.vat.dbf')
                ]

        # Regression check to make sure the dbf files with the attributes for the
        # percentile rasters are correct
        for reg_dbf_uri, dbf_uri in zip(regression_dbf_uris, dbf_uris):
            try:
                regression_table = dbf.Dbf(reg_dbf_uri)
                db_file = dbf.Dbf(dbf_uri)
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
    
    def test_wave_energy_regression_aoi(self):
        """Regression test for the wave energy model when using an AOI.
        """
        #raise SkipTest
        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy/aoi'
        
        #Set all arguments to be passed
        args = {}
        # Required
        args['workspace_dir'] = output_dir
        args['wave_base_data_uri'] = os.path.join(
                test_dir, 'samp_input/WaveData')
        args['analysis_area_uri'] = 'West Coast of North America and Hawaii'
        args['machine_perf_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisPerfCSV.csv')
        args['machine_param_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisParamCSV.csv')
        args['dem_uri'] = os.path.join(test_dir, 'samp_input/global_dem')
        # Optional
        #args['valuation_container'] = True
        args['aoi_uri'] = os.path.join(test_dir, 'test_input/AOI_WCVI.shp')
        #args['land_gridPts_uri'] =  os.path.join(
        #        test_dir, 'samp_input/LandGridPts_WCVI_221.csv')
        #args['machine_econ_uri'] = os.path.join(
        #        test_dir, 'samp_input/Machine_PelamisEconCSV.csv') 
        #args['number_of_machines'] = 28 
        args['suffix'] = '' 
        
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        wave_energy.execute(args)
        
        regression_dir = './invest-data/test/data/wave_energy_regression_data/'
        
        # Path names for output rasters to test 
        regression_raster_uris = [
                os.path.join(regression_dir, 'wp_kw_regression.tif'),
                os.path.join(regression_dir, 'capwe_mwh_regression.tif'),
                os.path.join(regression_dir, 'wp_rc_regression.tif'),
                os.path.join(regression_dir, 'capwe_rc_regression.tif'),
                #os.path.join(regression_dir, 'npv_usd_regression.tif'),
                #os.path.join(regression_dir, 'npv_rc_regression.tif')
                ]
        raster_uris = [
                os.path.join(output_dir, 'output/wp_kw.tif'),
                os.path.join(output_dir, 'output/capwe_mwh.tif'),
                os.path.join(output_dir, 'output/wp_rc.tif'),
                os.path.join(output_dir, 'output/capwe_rc.tif'),
                #os.path.join(output_dir, 'output/npv_usd.tif'),
                #os.path.join(output_dir, 'output/npv_rc.tif')
                ]
        # Test that raster outputs are correct
        for reg_raster_uri, raster_uri in zip(
                regression_raster_uris, raster_uris):
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_raster_uri, raster_uri)
        
        # Path names for output shapefiles to test
        regression_shapes_uris = [
                os.path.join(
                    regression_dir, 'WEM_InputOutput_Pts_bio_regression.shp'),
                #os.path.join(
                #    regression_dir, 'WEM_InputOutput_Pts_val_regression.shp'),
                #os.path.join(regression_dir, 'LandPts_prj_regression.shp'),
                #os.path.join(regression_dir, 'GridPts_prj_regression.shp')
                ]
        shapes_uris = [
                os.path.join(output_dir,
                    'intermediate/WEM_InputOutput_Pts.shp'),
                #os.path.join(output_dir, 'output/LandPts_prj.shp'),
                #os.path.join(output_dir, 'output/GridPts_prj.shp')
                ]
        # Test that shapefile outputs are correct
        for reg_shapes_uri, shapes_uri in zip(
                regression_shapes_uris, shapes_uris):
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_shapes_uri, shapes_uri)

        # Path names for output dbf tables
        regression_dbf_uris = [
                os.path.join(regression_dir, 'wp_rc_regression.tif.vat.dbf'),
                os.path.join(regression_dir, 'capwe_rc_regression.tif.vat.dbf'),
                #os.path.join(regression_dir, 'npv_rc_regression.tif.vat.dbf')
                ]
        dbf_uris = [
                os.path.join(output_dir, 'output/wp_rc.tif.vat.dbf'),
                os.path.join(output_dir, 'output/capwe_rc.tif.vat.dbf'),
                #os.path.join(output_dir, 'output/npv_rc.tif.vat.dbf')
                ]

        # Regression check to make sure the dbf files with the attributes for the
        # percentile rasters are correct
        for reg_dbf_uri, dbf_uri in zip(regression_dbf_uris, dbf_uris):
            try:
                regression_table = dbf.Dbf(reg_dbf_uri)
                db_file = dbf.Dbf(dbf_uri)
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
    
    def test_wave_energy_regression_aoi_val(self):
        """Regression test for the wave energy model when doing valuation and
            using an AOI.
        """
        #raise SkipTest
        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy/aoi_val'
        
        #Set all arguments to be passed
        args = {}
        # Required
        args['workspace_dir'] = output_dir
        args['wave_base_data_uri'] = os.path.join(
                test_dir, 'samp_input/WaveData')
        args['analysis_area_uri'] = 'West Coast of North America and Hawaii'
        args['machine_perf_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisPerfCSV.csv')
        args['machine_param_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisParamCSV.csv')
        args['dem_uri'] = os.path.join(test_dir, 'samp_input/global_dem')
        # Optional
        args['valuation_container'] = True
        args['aoi_uri'] = os.path.join(test_dir, 'test_input/AOI_WCVI.shp')
        args['land_gridPts_uri'] =  os.path.join(
                test_dir, 'samp_input/LandGridPts_WCVI_221.csv')
        args['machine_econ_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisEconCSV.csv') 
        args['number_of_machines'] = 28 
        args['suffix'] = '' 
        
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        wave_energy.execute(args)
        
        regression_dir = './invest-data/test/data/wave_energy_regression_data/'
        
        # Path names for output rasters to test 
        regression_raster_uris = [
                os.path.join(regression_dir, 'wp_kw_regression.tif'),
                os.path.join(regression_dir, 'capwe_mwh_regression.tif'),
                os.path.join(regression_dir, 'wp_rc_regression.tif'),
                os.path.join(regression_dir, 'capwe_rc_regression.tif'),
                os.path.join(regression_dir, 'npv_usd_regression.tif'),
                os.path.join(regression_dir, 'npv_rc_regression.tif')]
        raster_uris = [
                os.path.join(output_dir, 'output/wp_kw.tif'),
                os.path.join(output_dir, 'output/capwe_mwh.tif'),
                os.path.join(output_dir, 'output/wp_rc.tif'),
                os.path.join(output_dir, 'output/capwe_rc.tif'),
                os.path.join(output_dir, 'output/npv_usd.tif'),
                os.path.join(output_dir, 'output/npv_rc.tif')]
        # Test that raster outputs are correct
        for reg_raster_uri, raster_uri in zip(
                regression_raster_uris, raster_uris):
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_raster_uri, raster_uri)
        
        # Path names for output shapefiles to test
        regression_shapes_uris = [
                #os.path.join(
                #    regression_dir, 'WEM_InputOutput_Pts_bio_regression.shp'),
                os.path.join(
                    regression_dir, 'WEM_InputOutput_Pts_val_regression.shp'),
                os.path.join(regression_dir, 'LandPts_prj_regression.shp'),
                os.path.join(regression_dir, 'GridPts_prj_regression.shp')]
        shapes_uris = [
                os.path.join(output_dir,
                    'intermediate/WEM_InputOutput_Pts.shp'),
                os.path.join(output_dir, 'output/LandPts_prj.shp'),
                os.path.join(output_dir, 'output/GridPts_prj.shp')]
        # Test that shapefile outputs are correct
        for reg_shapes_uri, shapes_uri in zip(
                regression_shapes_uris, shapes_uris):
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_shapes_uri, shapes_uri)

        # Path names for output dbf tables
        regression_dbf_uris = [
                os.path.join(regression_dir, 'wp_rc_regression.tif.vat.dbf'),
                os.path.join(regression_dir, 'capwe_rc_regression.tif.vat.dbf'),
                os.path.join(regression_dir, 'npv_rc_regression.tif.vat.dbf')]
        dbf_uris = [
                os.path.join(output_dir, 'output/wp_rc.tif.vat.dbf'),
                os.path.join(output_dir, 'output/capwe_rc.tif.vat.dbf'),
                os.path.join(output_dir, 'output/npv_rc.tif.vat.dbf')]

        # Regression check to make sure the dbf files with the attributes for the
        # percentile rasters are correct
        for reg_dbf_uri, dbf_uri in zip(regression_dbf_uris, dbf_uris):
            try:
                regression_table = dbf.Dbf(reg_dbf_uri)
                db_file = dbf.Dbf(dbf_uri)
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
    
    def test_wave_energy_regression_suffix(self):
        """Regression test for the wave energy model when doing valuation,
            using an AOI, and a suffix.
        """
        #raise SkipTest
        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy/aoi_val'
        
        #Set all arguments to be passed
        args = {}
        # Required
        args['workspace_dir'] = output_dir
        args['wave_base_data_uri'] = os.path.join(
                test_dir, 'samp_input/WaveData')
        args['analysis_area_uri'] = 'West Coast of North America and Hawaii'
        args['machine_perf_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisPerfCSV.csv')
        args['machine_param_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisParamCSV.csv')
        args['dem_uri'] = os.path.join(test_dir, 'samp_input/global_dem')
        # Optional
        args['valuation_container'] = True
        args['aoi_uri'] = os.path.join(test_dir, 'test_input/AOI_WCVI.shp')
        args['land_gridPts_uri'] =  os.path.join(
                test_dir, 'samp_input/LandGridPts_WCVI_221.csv')
        args['machine_econ_uri'] = os.path.join(
                test_dir, 'samp_input/Machine_PelamisEconCSV.csv') 
        args['number_of_machines'] = 28 
        args['suffix'] = 'suffix' 
        
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        wave_energy.execute(args)
        
        regression_dir = './invest-data/test/data/wave_energy_regression_data/'
        
        # Path names for output rasters to test 
        regression_raster_uris = [
                os.path.join(regression_dir, 'wp_kw_regression.tif'),
                os.path.join(regression_dir, 'capwe_mwh_regression.tif'),
                os.path.join(regression_dir, 'wp_rc_regression.tif'),
                os.path.join(regression_dir, 'capwe_rc_regression.tif'),
                os.path.join(regression_dir, 'npv_usd_regression.tif'),
                os.path.join(regression_dir, 'npv_rc_regression.tif')]
        raster_uris = [
                os.path.join(output_dir, 'output/wp_kw_suffix.tif'),
                os.path.join(output_dir, 'output/capwe_mwh_suffix.tif'),
                os.path.join(output_dir, 'output/wp_rc_suffix.tif'),
                os.path.join(output_dir, 'output/capwe_rc_suffix.tif'),
                os.path.join(output_dir, 'output/npv_usd_suffix.tif'),
                os.path.join(output_dir, 'output/npv_rc_suffix.tif')]
        # Test that raster outputs are correct
        for reg_raster_uri, raster_uri in zip(
                regression_raster_uris, raster_uris):
            invest_test_core.assertTwoDatasetEqualURI(
                    self, reg_raster_uri, raster_uri)
        
        # Path names for output shapefiles to test
        regression_shapes_uris = [
                #os.path.join(
                #    regression_dir, 'WEM_InputOutput_Pts_bio_regression.shp'),
                os.path.join(
                    regression_dir, 'WEM_InputOutput_Pts_val_regression.shp'),
                os.path.join(regression_dir, 'LandPts_prj_regression.shp'),
                os.path.join(regression_dir, 'GridPts_prj_regression.shp')]
        shapes_uris = [
                os.path.join(output_dir,
                    'intermediate/WEM_InputOutput_Pts_suffix.shp'),
                os.path.join(output_dir, 'output/LandPts_prj_suffix.shp'),
                os.path.join(output_dir, 'output/GridPts_prj_suffix.shp')]
        # Test that shapefile outputs are correct
        for reg_shapes_uri, shapes_uri in zip(
                regression_shapes_uris, shapes_uris):
            invest_test_core.assertTwoShapesEqualURI(
                    self, reg_shapes_uri, shapes_uri)

        # Path names for output dbf tables
        regression_dbf_uris = [
                os.path.join(regression_dir, 'wp_rc_regression.tif.vat.dbf'),
                os.path.join(regression_dir, 'capwe_rc_regression.tif.vat.dbf'),
                os.path.join(regression_dir, 'npv_rc_regression.tif.vat.dbf')]
        dbf_uris = [
                os.path.join(output_dir, 'output/wp_rc_suffix.tif.vat.dbf'),
                os.path.join(output_dir, 'output/capwe_rc_suffix.tif.vat.dbf'),
                os.path.join(output_dir, 'output/npv_rc_suffix.tif.vat.dbf')]

        # Regression check to make sure the dbf files with the attributes for the
        # percentile rasters are correct
        for reg_dbf_uri, dbf_uri in zip(regression_dbf_uris, dbf_uris):
            try:
                regression_table = dbf.Dbf(reg_dbf_uri)
                db_file = dbf.Dbf(dbf_uri)
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
    
    def test_wave_energy_build_point_shapefile(self):
        """A regression test that uses known data and inputs to test
            the validity of the function build_point_shapefile"""
        #raise SkipTest
        output_dir = './invest-data/test/data/test_out/wave_energy_build_pt_shapefile'
        reg_shape_path = \
            './invest-data/test/data/wave_energy_regression_data/LandPts_prj_regression.shp'
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

        built_shape = wave_energy.build_point_shapefile(
                driver_name, layer_name, path, data, target_sr, coord_trans)
        built_shape = None
        reg_shape = None
        invest_test_core.assertTwoShapesEqualURI(self, path, reg_shape_path)
                
    def test_wave_energy_clip_shape(self):
        """A trivial test case that makes sure clip_shape returns the proper 
            shape after it has been clipped by a polygon shapefile.  
            Here the clipping polygon is the same size and form as the shape
            to be clipped so we would expect the output to be equal to the
            input"""

        #raise SkipTest
        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy_clip_shape'
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

        wave_energy.clip_shape(
                shape_to_clip_path, binding_shape_path, new_shape_path)

        invest_test_core.assertTwoShapesEqualURI(
                self, shape_to_clip_path, new_shape_path)

    def test_wave_energy_clip_shape_empty(self):
        """A trivial test case that makes sure clip_shape returns an empty
            shapefile if the binding polygon does not intersect with the other
            shape's features"""

        #raise SkipTest
        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy_clip_shape'
        shape_to_clip_path = os.path.join(
                test_dir, 'test_input/pointShapeTest.shp')
        binding_shape_path = os.path.join(test_dir, 'test_input/AOI_WCVI.shp')
        new_shape_path = os.path.join(output_dir, 'wave_energy_NoClip.shp')

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        wave_energy.clip_shape(
                shape_to_clip_path, binding_shape_path, new_shape_path)

        new_shape = ogr.Open(new_shape_path)
        layer = new_shape.GetLayer(0)

        self.assertEqual(layer.GetFeatureCount(), 0)

        layer = None
        new_shape = None

    def test_wave_energy_clip_shape_hand_calculated(self):
        """A non trivial test case that makes sure clip_shape returns the
            proper shape after it has been clipped by a polygon shapefile.
            Also check values of features based on known hand given results.
        """
        #raise SkipTest

        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy_clip_shape'
        shape_to_clip_path = os.path.join(
                test_dir, 'test_input/NAmerica_WestCoast_4m.shp')
        binding_shape_path = os.path.join(
                test_dir, 'test_input/threePointShape.shp')
        new_shape_path = os.path.join(
                output_dir, 'wave_energy_ClipAOI.shp')

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        wave_energy.clip_shape(
                shape_to_clip_path, binding_shape_path, new_shape_path)
        
        # It seems that the fields "FID" and "Shape" are not included for some 
        # reason when Looping through all the fields of the shapefile
        point_one_fields = [572, 490, -126.933144, 47.600162, 2.8, 11.1]
        point_two_fields = [573, 490, -126.866477, 47.600162, 2.8, 11.11]
        point_three_fields = [574, 490, -126.79981, 47.600162, 2.79, 11.11]
        point_field_array = [
                point_one_fields, point_two_fields, point_three_fields]

        new_shape = ogr.Open(new_shape_path)
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

            feat = None
            feat = layer.GetNextFeature()
            point_array_iderator = point_array_iderator + 1

        new_shape = None

    def test_wave_energy_captured_wave_energy_to_shape(self):
        """Test captured_wave_energy_to_shape using hand calculated and 
            generated values to pass into the function.
        """
        #raise SkipTest

        shape_path = './invest-data/test/data/wave_energy_data/test_input/pointShapeTest.shp'
        out_dir = \
            './invest-data/test/data/test_out/wave_energy/captured_wave_energy_to_shape'
        shape_copy_path = os.path.join(out_dir,'pointShapeTest_copy.shp')

        wave_shape = ogr.Open(shape_path)

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        if os.path.isfile(shape_copy_path):
            os.remove(shape_copy_path)

        wave_shape_driver = ogr.GetDriverByName('ESRI Shapefile')
        wave_shape_copy = wave_shape_driver.CopyDataSource(
                wave_shape, shape_copy_path)
        
        wave_shape_copy = None

        test_dict = {(572, 490):2302, (573, 490):1453, (574, 490):2103}
        ij_array = [[572, 490], [573, 490], [574, 490]]
        
        wave_energy.captured_wave_energy_to_shape(
            test_dict, shape_copy_path)

        wave_shape_copy = ogr.Open(shape_copy_path)
        layer = wave_shape_copy.GetLayer(0)
        #Need to reset the layer because the function call goes through the 
        #features in the layer and does not reset or close.
        feat = layer.GetNextFeature()
        comp_dict = {}
        while feat is not None:
            temp_array = []
            for fld in ('I', 'J', 'CAPWE_MWHY'):
                index = feat.GetFieldIndex(fld)
                field_val = feat.GetField(index)
                temp_array.append(field_val)
            comp_dict[(temp_array[0], temp_array[1])] = temp_array[2]

            feat = None
            feat = layer.GetNextFeature()

        self.assertEqual(len(test_dict), len(comp_dict), 
                         'The lengths of the dictionaries are not the same')

        for key, val in test_dict.iteritems():
            if key in comp_dict:
                self.assertEqual(val, comp_dict[key])
            else:
                self.assertEqual(0, 1, 
                                 'The key does not exist in the new feature')
        wave_shape = None
        wave_shape_copy = None

    def test_wave_energy_compute_wave_energy_capacity(self):
        """Test compute_wave_energy_capacity function using hand generated
            values and results."""

        #raise SkipTest
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

        we_sum = wave_energy.compute_wave_energy_capacity(
                    wave_data, interpZ, machine_param)

        #Loop that compares dictionaries we_sum and result checking key, 
        #sum values
        for key in result:
            if key in we_sum:
                self.assertAlmostEqual(
                        result[key], we_sum[key], 8,
                        'The values do not match for key ' + str(we_sum[key]))
            else:
                self.assertEqual(0, 1, 'The keys do not match')

    def test_wave_energy_wave_energy_interp(self):
        """Test wave_energy_interp by using hand calculations and hand
            calculated results based on the given inputs.
        """
        #raise SkipTest
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
        interpZ = wave_energy.wave_energy_interp(wave_data, machine_perf)

        self.assertEqual(
                result.shape, interpZ.shape, 'The shapes are not the same')

        for indexOut, ar in enumerate(result):
            for indexIn, val in enumerate(ar):
                self.assertAlmostEqual(val, interpZ[indexOut][indexIn], 5, 
                                       'Values do not match')
                
    def test_wave_energy_wave_power(self):
        """Test the wave_power function by hand calculating wave power with 
            known variables and creating shapefile with those variables and 
            comparing returned value against known results."""
        #raise SkipTest

        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy_wave_power'
        shape_path = os.path.join(
                test_dir, 'test_input/test_wave_power_shape.shp')
        shape_copy_path = os.path.join(output_dir, 'test_wave_power_shape.shp')
        
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
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
            feat = None
            feat = layer.GetNextFeature()
            i = i + 1

        layer = None
        shape_copy = None
        
        wave_energy.wave_power(shape_copy_path)
        
        shape_copy = ogr.Open(shape_copy_path)
        layer = shape_copy.GetLayer(0)
        layer.ResetReading()
        feat = layer.GetNextFeature()
        i = 0
        while feat is not None:
            wave_power_index = feat.GetFieldIndex('WE_kWM')
            wave_power = feat.GetField(wave_power_index)
            self.assertAlmostEqual(
                    wave_power, calculations_by_hand[i], 1, 
                    'Wave Power calculations do not match.')
            feat = None
            feat = layer.GetNextFeature()
            i = i + 1
        
        shape_copy = None
        shape = None
        
    def test_wave_energy_wave_power_regression(self):
        """A regresssion test for the wave_power function."""
        #raise SkipTest

        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy_wave_power'
        regression_dir = './invest-data/test/data/wave_energy_regression_data'
        shape_path = os.path.join(
                test_dir, 'test_input/test_wavepower_withfields.shp')
        shape_copy_path = os.path.join(
                output_dir, 'regression_test_wave_power_output.shp')
        regression_shape_path = os.path.join(
                regression_dir, 'wave_power_regression.shp')
        
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        if os.path.isfile(shape_copy_path):
            os.remove(shape_copy_path)

        shape = ogr.Open(shape_path)
        shape_reg = ogr.Open(regression_shape_path)
        shape_copy = ogr.GetDriverByName('ESRI Shapefile').\
                             CopyDataSource(shape, shape_copy_path)
        shape_copy = None
        shape_copy = wave_energy.wave_power(shape_copy_path)
        shape_copy = ogr.Open(shape_copy_path)

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
            self.assertEqual(
                    wave_power, wave_power_reg,
                    'The wave power values do not match.')
            feat = None
            feat_reg = None
            feat = layer.GetNextFeature()
            feat_reg = layer_reg.GetNextFeature()

        shape_copy = None
        shape = None
        shape_reg = None

    def test_wave_energy_get_points(self):
        """Test the get_points_geometries function by first creating a shapefile
            with assigned points and geometries. Pass shapefile to function
            and checked returned value against calculated ones."""
        #raise SkipTest
        shape_path = \
            './invest-data/test/data/wave_energy_data/test_input/test_wavepower_withfields.shp'
        out_dir = './invest-data/test/data/test_out/wave_energy/get_points_geometries'
        out_path = os.path.join(out_dir, 'points_geom.shp')
        
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        if os.path.isfile(out_path):
            os.remove(out_path)
        
        shape = ogr.Open(shape_path)
        layer = shape.GetLayer(0)
        calculated_points = [[-126.726911, 48.241337], [-126.580642, 48.240944],
                             [-126.726911, 48.098204], [-126.5771122, 48.015067],
                              [-126.427313, 48.091537]]
        drv = ogr.GetDriverByName('ESRI Shapefile')
        src = drv.CreateDataSource(out_path)
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
            feat = None
        
        lyr.ResetReading()
        shape = None
        src = None

        result_points = wave_energy.get_points_geometries(out_path)
        
        for index, value in enumerate(result_points):
            self.assertEqual(value[0], calculated_points[index][0],
                             'The X value of the points do not match.')
            self.assertEqual(value[1], calculated_points[index][1],
                             'The Y value of the points do not match.')
        
    def test_wave_energy_calc_dist(self):
        """Test the calculate_distance function by hand calculating the
            distances between known points and checking them against
            the functions returned results on the same set of points."""
        #raise SkipTest
        xy_1 = np.array([[250, 120], [300, 212], [125, 215], [1222, 988]])
        xy_2 = np.array([[156, 133], [198, 111]])
        calculated_dist_results = np.array(
                [52.77309921, 143.5444182, 87.66413178, 1348.222904])
        calculated_id_results = np.array([1, 1, 0, 1])
        dist_results, id_results = wave_energy.calculate_distance(
                xy_1, xy_2)
        calculated_dist_rounded = np.ma.round(calculated_dist_results, 3)
        dist_rounded = np.ma.round(dist_results, 3)
        mask_dist = calculated_dist_rounded == dist_rounded
        mask_id = calculated_id_results == id_results
        self.assertTrue(mask_dist.all(),
                        'Not all of the distances were equal.')
        self.assertTrue(mask_id.all(), 'Not all of the IDs matched.')
    
    def test_wave_energy_create_percentile_raster_regression(self):
        """A regression test for create_percentile_raster."""
        #raise SkipTest
        
        test_dir = './invest-data/test/data/wave_energy_data'
        output_dir = './invest-data/test/data/test_out/wave_energy/create_percentile_raster'
        regression_dir = './invest-data/test/data/wave_energy_regression_data'
        aoi_path = os.path.join(test_dir, 'samp_input/AOI_WCVI.shp')
        #The raster dataset input
        regression_dataset_uri = os.path.join(
                regression_dir, 'wp_kw_regression.tif')
        #The raster dataset and dbf file to test against
        regression_perc_uri = os.path.join(
                regression_dir, 'wp_rc_regression.tif')
        regression_table_uri = os.path.join(
                regression_dir, 'wp_rc_regression.tif.vat.dbf')
        #The resulting output raster location the function produces
        perc_path = os.path.join(output_dir, 'wp_percentile.tif')

        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        if os.path.isfile(perc_path):
            os.remove(perc_path)
    
        #regression_dataset = gdal.Open(regression_dataset_uri)
        units_short = ' (kW/m)'
        units_long = ' wave power per unit width of wave crest length (kW/m)'
        
        wave_energy.create_percentile_rasters(
                regression_dataset_uri, perc_path, units_short, units_long, 
                '1', [25,50,75,90], aoi_path)
        
        #Check the resulting raster against the regression raster
        invest_test_core.assertTwoDatasetEqualURI(
                self, regression_perc_uri, perc_path)
        
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
        #raise SkipTest
        
        values = np.arange(1,101)
        calc_percentiles = [25, 50, 75, 90]
        perc_list = [25,50,75,90]
        min_val = 0
        max_val = 105
        percentiles = wave_energy.get_percentiles(
                values, perc_list, min_val, max_val)
        self.assertTrue(calc_percentiles == percentiles)
        return
    
    def test_wave_energy_create_percentile_ranges(self):
        """A non-trivial test case that compares hand calculated
            percentile ranges with ranges returned from the function being
            tested."""
        
        #raise SkipTest
        units_short = ' (m/s)'
        units_long = ' the rate of time travel in meters per second (m/s)'
        percentiles = [4, 8, 12, 16]
        ranges = wave_energy.create_percentile_ranges(
                percentiles, units_short, units_long, '1')
        calc_ranges = [
                '1 - 4 the rate of time travel in meters per second (m/s)',
                '4 - 8 (m/s)', '8 - 12 (m/s)', '12 - 16 (m/s)',
                'Greater than 16 (m/s)']
        #Check that the returned ranges as Strings are correct
        self.assertTrue(ranges == calc_ranges)
        return
    
    def test_wave_energy_create_attribute_table(self):
        """A non-trivial test case that compares hand calculated
            attribute table values against the returned dbf's values
            from the function being tested."""
        #raise SkipTest
        
        output_dir = './invest-data/test/data/test_out/wave_energy_attribute_table'
        raster_uri = os.path.join(output_dir, 'test_attr_table.tif')
        dbf_uri = raster_uri + '.vat.dbf'
        #Add the Output directory onto the given workspace
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        if os.path.isfile(dbf_uri):
            os.remove(dbf_uri)
        #Make pre-calculated attribute table that should match the results
        #the function returns
        calc_ranges = [
                '1 - 4 the rate of time travel in meters per second (m/s)',
                '4 - 8 (m/s)', '8 - 12 (m/s)', '12 - 16 (m/s)', 
                'Greater than 16 (m/s)']
        
        calc_count = [24, 25, 25, 15, 11]
        calc_values = [1,2,3,4,5]
        wave_energy.create_attribute_table(
                raster_uri, calc_ranges, calc_count)
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
