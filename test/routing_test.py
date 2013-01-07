"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess
import logging
import subprocess

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy

from invest_natcap.routing import routing
import invest_test_core
from invest_natcap import raster_utils

LOGGER = logging.getLogger('routing_test')

def make_constant_raster_from_base(base_dataset_uri, constant_value, out_uri):
    base_dataset = gdal.Open(base_dataset_uri)
    out_dataset = raster_utils.new_raster_from_base(
        base_dataset, out_uri, 'GTiff', constant_value-1,
        gdal.GDT_Float32)
    out_band, _ = raster_utils.extract_band_and_nodata(out_dataset)
    out_band.Fill(constant_value)


class TestRasterUtils(unittest.TestCase):
    def test_smoke_routing(self):
        base_dir = 'data/test_out/routing_test'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        regression_uri = 'data/routing_regression/out.tif'
#        dem_uri = 'data/sediment_test_data/dem'
        dem_uri = 'data/smooth_rasters/smoothleft.tif'
        dem_uri = 'data/smooth_rasters/smoothright.tif'
#        dem_uri = 'data/smooth_rasters/smoothbottom_right.tif'
#        dem_uri = 'data/smooth_rasters/smoothtop_left.tif'
#        dem_uri = 'data/smooth_rasters/random.tif'
        source_uri = os.path.join(base_dir, 'source.tif')
        absorption_rate_uri = os.path.join(base_dir, 'absorption.tif')


        make_constant_raster_from_base(dem_uri, 1.0, source_uri)
        make_constant_raster_from_base(dem_uri, 0.0, absorption_rate_uri)

        loss_uri = os.path.join(base_dir, 'loss.tif')
        flux_uri = os.path.join(base_dir, 'flux.tif')
        aoi_uri = 'data/sediment_test_data/watersheds.shp'

        routing.route_flux(dem_uri, source_uri, absorption_rate_uri, loss_uri, flux_uri, base_dir, aoi_uri = aoi_uri)

#        invest_test_core.assertTwoDatasetEqualURI(self, output_uri, regression_uri)
        subprocess.Popen(['qgis', flux_uri, 'count.tif', dem_uri, os.path.join(base_dir,'outflow_directions.tif'),
                          os.path.join(base_dir,'outflow_weights.tif'), os.path.join(base_dir,'flow_direction.tif')])
