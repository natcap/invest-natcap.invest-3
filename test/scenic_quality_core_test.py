from __future__ import print_function

import unittest
import logging
import os
import sys
import subprocess
import math
import numpy as np
import random
import time
import csv
import glob
import shutil
import json

from osgeo import gdal
from osgeo import ogr
from nose.plugins.skip import SkipTest

import invest_test_core
from invest_natcap import raster_utils
from invest_natcap.scenic_quality \
    import scenic_quality as sq
from invest_natcap.scenic_quality \
    import scenic_quality_core as sqc


LOGGER = logging.getLogger('scenic_quality_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestScenicQuality(unittest.TestCase):
    """Main testing class for the scenic quality tests"""
    
    def setUp(self):
        pass

    def test_get_perimeter_cells(self):
        DEM_size = 9
        elevation = np.zeros((DEM_size, DEM_size))
        viewpoint = (DEM_size/2+2, DEM_size/2-2)
        radius = 3
	perimeter = sqc.get_perimeter_cells(elevation.shape, viewpoint, radius)
        #print('perimeter', perimeter)
        elevation[perimeter] = 1
        elevation[viewpoint[0], viewpoint[1]] = 2
        #print(elevation)

    def test_visibility_basic_array(self):
        DEM_size = 31
        elevation = np.zeros((DEM_size, DEM_size))
        nodata = -1
        viewpoint = (DEM_size/2, DEM_size/2)
        elevation[viewpoint[0]+1, viewpoint[1]+1] = 2.
        obs_elev = 1.0
        tgt_elev = 0.0
        max_dist = 5 
        cell_size = 5.0
        refraction_coeff = 0.13
        alg_version = 'cython' #'python'
        visibility = sqc.compute_viewshed(elevation, nodata, viewpoint, \
            obs_elev, tgt_elev, max_dist, cell_size, refraction_coeff, \
            alg_version)
        visibility[visibility > 0] = 1
        visibility[visibility < 0] = 0
        visibility[DEM_size/2, DEM_size/2] = 2
        print(visibility.astype(int))

    def test_cython_vs_python_on_default_1_pt_data(self):
        args_uri = "../../ScenicQuality/tests/default-1-pt/run_parameters_default-1-pt.json"
        with open(args_uri) as args_file:
            args = json.load(args_file)
        sq.execute(args)
        reference_uri = "../../ScenicQuality/tests/default-1-pt/python/output/vshed.tif"
        reference_raster = gdal.Open(reference_uri)
        message = "Cannot open " + reference_uri
        assert reference_raster is not None, message
        reference_band = reference_raster.GetRasterBand(1)
        reference_array = reference_band.ReadAsArray()
        computed_uri = "../../ScenicQuality/tests/default-1-pt/cython/output/vshed.tif"
        computed_raster = gdal.Open(computed_uri)
        message = "Cannot open " + computed_uri
        assert computed_raster is not None, message
        computed_band = computed_raster.GetRasterBand(1)
        computed_array = computed_band.ReadAsArray()
        message = "Computed viewshed " + computed_uri + \
            " doesn't correspond to " + reference_uri
        assert \
            np.sum(np.absolute(reference_array - computed_array)) == 0.0, message
	return

    def test_cython_vs_python_on_default_data_data(self):
        args_uri = "../../ScenicQuality/tests/default-data/run_parameters_default-data.json"
        with open(args_uri) as args_file:
            args = json.load(args_file)
        sq.execute(args)
        reference_uri = "../../ScenicQuality/tests/default-data/python/output/vshed.tif"
        reference_raster = gdal.Open(reference_uri)
        message = "Cannot open " + reference_uri
        assert reference_raster is not None, message
        reference_band = reference_raster.GetRasterBand(1)
        reference_array = reference_band.ReadAsArray()
        computed_uri = "../../ScenicQuality/tests/default-data/cython/output/vshed.tif"
        computed_raster = gdal.Open(computed_uri)
        message = "Cannot open " + computed_uri
        assert computed_raster is not None, message
        computed_band = computed_raster.GetRasterBand(1)
        computed_array = computed_band.ReadAsArray()
        message = "Computed viewshed " + computed_uri + \
            " doesn't correspond to " + reference_uri
        assert \
            np.sum(np.absolute(reference_array - computed_array)) == 0.0, message
	return

    def test_cython_vs_python_on_block_island(self):
        return
        args_uri = "../../ScenicQuality/tests/block-island/run_parameters_block-island.json"
        with open(args_uri) as args_file:
            args = json.load(args_file)
            for entry in args:
                print('entry', entry, args[entry], type(args[entry]))
        sq.execute(args)
        reference_uri = "../../ScenicQuality/tests/block-island/python/output/vshed.tif"
        reference_raster = gdal.Open(reference_uri)
        message = "Cannot open " + reference_uri
        assert reference_raster is not None, message
        reference_band = reference_raster.GetRasterBand(1)
        reference_array = reference_band.ReadAsArray()
        computed_uri = "../../ScenicQuality/tests/block-island/cython/output/vshed.tif"
        computed_raster = gdal.Open(computed_uri)
        message = "Cannot open " + computed_uri
        assert computed_raster is not None, message
        computed_band = computed_raster.GetRasterBand(1)
        computed_array = computed_band.ReadAsArray()
        message = "Computed viewshed " + computed_uri + \
            " doesn't correspond to " + reference_uri
        assert \
            np.sum(np.absolute(reference_array - computed_array)) == 0.0, message
	return

    def test_visibility_simple_obstacles(self):
        return
        obs_elev = 1.0
        tgt_elev = 0.0
        max_dist = -1.0
        coefficient = 1.0
        height = 0.0
        refraction_coeff = 0.13
        base_dem_uri = "../../AQ_Rob/Block_Island_fast_alg/SQ/bi_100meters/hdr.adf"
        base_dem_nodata = raster_utils.get_nodata_from_uri(base_dem_uri)
	raster = gdal.Open(base_dem_uri)
        band = raster.GetRasterBand(1)
        base_array = band.ReadAsArray()
        (rows, cols) = base_array.shape
        band = None
        raster = None
        cell_size = raster_utils.get_cell_size_from_uri(base_dem_uri)
        GT = raster_utils.get_geotransform_uri(base_dem_uri)
        iGT = gdal.InvGeoTransform(GT)[1]
        flat_dem_uri = "flat_dem.tif"

        structure_uri = "../../AQ_Rob/Block_Island_fast_alg/SQ/1_pt/e911_132.shp"
        shapefile = ogr.Open(structure_uri)
        assert shapefile is not None
        layer = shapefile.GetLayer(0)
        assert layer is not None
        feature = layer.GetFeature(0)
        field_count = feature.GetFieldCount()
        # Check for feature information (radius, coeff, height)
        for field in range(field_count):
            field_def = feature.GetFieldDefnRef(field)
            field_name = field_def.GetNameRef()
            if (field_name.upper() == 'RADIUS2') or \
                (field_name.upper() == 'RADIUS'):
                max_dist = abs(int(feature.GetField(field)))
                assert max_dist is not None, "max distance can't be None"
                max_dist = int(max_dist/cell_size)
            if field_name.lower() == 'coeff':
                coefficient = float(feature.GetField(field))
                assert coefficient is not None, "feature coeff can't be None"
            if field_name.lower() == 'offseta':
                obs_elev = float(feature.GetField(field))
                assert obs_elev is not None, "OFFSETA can't be None"
            if field_name.lower() == 'offsetb':
                tgt_elev = float(feature.GetField(field))
                assert tgt_elev is not None, "OFFSETB can't be None"
                
        geometry = feature.GetGeometryRef()
        assert geometry is not None
        message = 'geometry type is ' + str(geometry.GetGeometryName()) + \
        ' point is "POINT"'
        assert geometry.GetGeometryName() == 'POINT', message
        x = geometry.GetX()
        y = geometry.GetY()
        j = int((iGT[0] + x*iGT[1] + y*iGT[2]))
        i = int((iGT[3] + x*iGT[4] + y*iGT[5]))

        viewpoint = (i, j)

        print('x', x, 'y', y, 'i', i, 'j', j)
        print('RADIUS', max_dist, 'coefficient', coefficient, \
            'obs_elev', obs_elev, 'tgt_elev', tgt_elev)

        raster_utils.new_raster_from_base_uri( \
            base_dem_uri, flat_dem_uri, 'GTiff', 2., gdal.GDT_Float32, \
            fill_value = base_dem_nodata, n_rows = rows, n_cols = cols)

	raster = gdal.Open(flat_dem_uri, gdal.GA_Update)
        band = raster.GetRasterBand(1)
        array = band.ReadAsArray()

        alg_version = 'python'
        print('array_shape', base_array.shape)
        print('viewpoint', viewpoint)
        visibility = sqc.compute_viewshed(base_array, base_dem_nodata, \
            viewpoint, obs_elev, tgt_elev, max_dist, cell_size, \
            refraction_coeff, alg_version)
        visibility[viewpoint[0], viewpoint[1]] = 2
        #scenic_quality_core.viewshed(
        #    input_array, cell_size, array_shape, nodata, tmp_visibility_uri,
        #    (i,j), obs_elev, tgt_elev, max_dist, refr_coeff)
        band.WriteArray(visibility)
	print('file saved in', os.path.join(os.getcwd(), flat_dem_uri))

    def test_visibility_multiple_points(self):
        pass

    def tare_down(self):
        """ Clean up code."""
        # Do nothing for now 
        pass
