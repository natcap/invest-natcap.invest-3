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
    def test_potential_sediment(self):
        dem_points = {
            (0.0,0.0): 50,
            (0.0,1.0): 100,
            (1.0,0.0): 90,
            (1.0,1.0): 0,
            (0.5,0.5): 45}

        n = 100
        noise = 0.5

        base_dir = 'data/test_out/sediment_biophysical_core'

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dem_uri = os.path.join(base_dir,'dem_ls.tif')
        dem_dataset = invest_test_core.make_sample_dem(n,n,dem_points, noise, -1, dem_uri)

        flow_uri = os.path.join(base_dir,'flow_ls.tif')
        flow_dataset = raster_utils.new_raster_from_base(dem_dataset, flow_uri, 'GTiff',
                                                         -1, gdal.GDT_Float32)
        invest_cython_core.flow_direction_inf(dem_dataset, [0, 0, n, n], flow_dataset)

        flow_accumulation_uri = os.path.join(base_dir, 'ls_flow_accumulation.tif')
        flow_accumulation_dataset = raster_utils.flow_accumulation_dinf(flow_dataset, dem_dataset, 
                                                                        flow_accumulation_uri)

        slope_uri = os.path.join(base_dir,'raster_slope.tif')
        slope_dataset = raster_utils.calculate_slope(dem_dataset, slope_uri)

        ls_uri = os.path.join(base_dir, 'ls.tif')
        ls_dataset = sediment_core.calculate_ls_factor(flow_accumulation_dataset,
                                                       slope_dataset,
                                                       flow_dataset,
                                                       ls_uri)

        c_p_points = {
            (0.0,0.0): 0.5,
            (0.0,1.0): 0.9,
            (1.0,0.0): 0.25,
            (1.0,1.0): 0.1,
            (0.5,0.5): 0.7}

        c_uri = os.path.join(base_dir,'c.tif')
        c_dataset = invest_test_core.make_sample_dem(n,n,c_p_points, noise, -1, c_uri)
        p_uri = os.path.join(base_dir,'p.tif')
        p_dataset = invest_test_core.make_sample_dem(n,n,c_p_points, noise, -1, p_uri)

        sedret_eff_uri = os.path.join(base_dir, 'sed_ret.tif')
        sedret_eff_dataset = invest_test_core.make_sample_dem(n, n, c_p_points, 0.0, -1, sedret_eff_uri)

        erosivity_points = {
            (0.0,0.0): 0.15,
            (0.0,1.0): 0.3,
            (1.0,0.0): 0.2,
            (1.0,1.0): 0.1,
            (0.5,0.5): 0.21}

        erosivity_uri = os.path.join(base_dir,'erosivity.tif')
        erosivity_dataset = invest_test_core.make_sample_dem(n,n, erosivity_points, 
                                                             noise, -1, erosivity_uri)


        erodibility_points = {
            (0.0,0.0): 2240,
            (0.0,1.0): 1999,
            (1.0,0.0): 1200,
            (1.0,1.0): 1500,
            (0.5,0.5): 1000}

        erodibility_uri = os.path.join(base_dir,'erodibility.tif')
        erodibility_dataset = invest_test_core.make_sample_dem(n,n, erodibility_points, 
                                                             noise, -1, erodibility_uri)

        potential_soil_loss_uri = os.path.join(base_dir,'soil_loss.tif')

        stream_uri = os.path.join(base_dir, 'streams.tif')
        stream_dataset = raster_utils.stream_threshold(flow_accumulation_dataset, 80, stream_uri)

        potential_sediment_export_dataset = \
            sediment_core.calculate_potential_soil_loss(ls_dataset, \
                erosivity_dataset, erodibility_dataset, c_dataset, p_dataset,\
                stream_dataset, potential_soil_loss_uri)
        


        effective_retention_uri = os.path.join(base_dir, 'effective_retention.tif')
        effective_retention_dataset = \
            sediment_core.effective_retention(flow_dataset, \
                sedret_eff_dataset, stream_dataset, effective_retention_uri)

        pixel_export_uri = os.path.join(base_dir, 'pixel_export.tif')
        sediment_core.calculate_pixel_export(potential_sediment_export_dataset,
                                             effective_retention_dataset, pixel_export_uri)
                                             

        subprocess.Popen(["qgis", ls_uri, dem_uri, flow_uri, flow_accumulation_uri, c_uri, 
                          p_uri, erosivity_uri, erodibility_uri, potential_soil_loss_uri,
                          effective_retention_uri, pixel_export_uri])
