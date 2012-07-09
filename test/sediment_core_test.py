import unittest
import logging
import os
import subprocess

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy as np

from invest_natcap.sediment import sediment_biophysical
import invest_cython_core
import invest_test_core
from invest_natcap.sediment import sediment_core
from invest_natcap import raster_utils


LOGGER = logging.getLogger('sediment_biophysical_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestSedimentBiophysicalCore(unittest.TestCase):
    """Main testing class for the biophysical sediment tests"""
    def test_sediment_ls_factor(self):
        dem_points = {
            (0.0,0.0): 50,
            (0.0,1.0): 100,
            (1.0,0.0): 90,
            (1.0,1.0): 0,
            (0.5,0.5): 45}

        n = 100

        base_dir = 'data/test_out/sediment_biophysical_core'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dem_uri = os.path.join(base_dir,'dem_ls.tif')
        dem = invest_test_core.make_sample_dem(n,n,dem_points, 5.0, -1, dem_uri)

        flow_uri = os.path.join(base_dir,'flow_ls.tif')
        flow_dataset = raster_utils.new_raster_from_base(dem, flow_uri, 'GTiff',
                                                         -1, gdal.GDT_Float32)
        invest_cython_core.flow_direction_inf(dem, [0, 0, n, n], flow_dataset)

        flow_accumulation_uri = os.path.join(base_dir, 'ls_flow_accumulation.tif')
        flow_accumulation_dataset = raster_utils.flow_accumulation_dinf(flow_dataset, dem, 
                                                                        flow_accumulation_uri)

        slope_uri = os.path.join(base_dir,'raster_slope.tif')
        slope_dataset = raster_utils.calculate_slope(dem_dataset, slope_uri)

        ls_uri = os.path.join(base_dir, 'ls.tif')
        ls_dataset = sediment_core.calculate_ls_factor(flow_accumulation_dataset,
                                                       slope_dataset,
                                                       flow_dataset,
                                                       ls_uri)
        subprocess.Popen(["qgis", ls_uri, dem_uri, flow_uri, flow_accumulation_uri])
