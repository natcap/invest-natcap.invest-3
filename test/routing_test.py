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

LOGGER = logging.getLogger('routing_test')

class TestRasterUtils(unittest.TestCase):
    def test_smoke_routing(self):
        base_dir = 'data/test_out/routing_test'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        regression_uri = 'data/routing_regression/out.tif'
#        dem_uri = 'data/sediment_test_data/dem'
#        dem_uri = 'data/smooth_rasters/smoothleft.tif'
#        dem_uri = 'data/smooth_rasters/smoothright.tif'
        dem_uri = 'data/smooth_rasters/smoothbottom_right.tif'
#        dem_uri = 'data/smooth_rasters/random.tif'
        source_uri = dem_uri
        absorption_rate_uri = dem_uri
        loss_uri = os.path.join(base_dir, 'loss.tif')
        flux_uri = os.path.join(base_dir, 'flux.tif')
        aoi_uri = 'data/sediment_test_data/watersheds.shp'

        routing.route_flux(dem_uri, source_uri, absorption_rate_uri, loss_uri, flux_uri, base_dir, aoi_uri = aoi_uri)

#        invest_test_core.assertTwoDatasetEqualURI(self, output_uri, regression_uri)
        subprocess.Popen(['qgis', flux_uri])
