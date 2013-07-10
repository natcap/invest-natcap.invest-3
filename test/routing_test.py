"""URI level tests for the sediment biophysical module"""

import unittest
import os
import subprocess
import logging
import subprocess

from osgeo import gdal
from nose.plugins.skip import SkipTest
import numpy

from invest_natcap.routing import routing_utils
import invest_test_core
from invest_natcap import raster_utils
import routing_cython_core

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
        base_dir = 'invest-data/test/data/test_out/routing_test'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        dem_uri = 'invest-data/test/data/sediment_test_data/dem'

        flow_accumulation_uri = os.path.join(base_dir, 'flow_accumulation.tif')
        routing_utils.flow_accumulation(dem_uri, flow_accumulation_uri)

        flow_accumulation_regression_uri = 'invest-data/test/data/routing_regression/flow_accumulation.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, flow_accumulation_uri, flow_accumulation_regression_uri)

        source_uri = os.path.join(base_dir, 'source.tif')
        export_rate_uri = os.path.join(base_dir, 'export_rate.tif')

        make_constant_raster_from_base(dem_uri, 1.0, source_uri)
        make_constant_raster_from_base(dem_uri, 0.9, export_rate_uri)

        loss_uri = os.path.join(base_dir, 'loss.tif')
        flux_uri = os.path.join(base_dir, 'flux.tif')
        aoi_uri = 'invest-data/test/data/sediment_test_data/watersheds.shp'

        stream_uri = os.path.join(base_dir, 'stream.tif')
        stream_regression_uri = 'invest-data/test/data/routing_regression/stream.tif'
        routing_utils.stream_threshold(flow_accumulation_uri, 103.9, stream_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, stream_uri, stream_regression_uri)

        effect_uri = os.path.join(base_dir, 'effect.tif')
        effect_regression_uri = 'invest-data/test/data/routing_regression/effect.tif'

        flow_direction_uri = os.path.join(base_dir, 'flow_direction.tif')
        routing_cython_core.calculate_flow_direction(dem_uri, flow_direction_uri)

        flow_length_uri = os.path.join(base_dir, 'flow_length.tif')
        routing_utils.calculate_flow_length(flow_direction_uri, flow_length_uri)

        outflow_direction_uri = os.path.join(base_dir, 'outflow_directions.tif')
        outflow_weights_uri = os.path.join(base_dir, 'outflow_weights.tif')

        sink_cell_set, _ = routing_cython_core.calculate_flow_graph(
            flow_direction_uri, outflow_weights_uri, outflow_direction_uri)

        routing_cython_core.percent_to_sink(stream_uri, export_rate_uri, outflow_direction_uri, outflow_weights_uri, effect_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, effect_uri, effect_regression_uri)

        flux_regression_uri = 'invest-data/test/data/routing_regression/flux.tif'
        loss_regression_uri = 'invest-data/test/data/routing_regression/loss.tif'
        invest_test_core.assertTwoDatasetEqualURI(self, flux_uri, flux_regression_uri)
        invest_test_core.assertTwoDatasetEqualURI(self, loss_uri, loss_regression_uri)
