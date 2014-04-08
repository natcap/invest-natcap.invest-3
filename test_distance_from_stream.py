import cProfile
import pstats

import time
import gdal
import numpy
from invest_natcap.routing import routing_utils
import routing_cython_core


dem_uri = 'test/invest-data/Base_Data/Freshwater/dem'
resolved_dem_uri = 'test_resolved_dem.tif'
flow_direction_uri = 'test_flow.tif'
flow_accumulation_uri = 'test_flux.tif'
flow_threshold = 1000
stream_uri = 'test_stream.tif'
distance_uri = 'test_distance_to_stream.tif'
routing_utils.resolve_flat_regions_for_drainage(
    dem_uri, resolved_dem_uri)

routing_utils.flow_direction_inf(resolved_dem_uri, flow_direction_uri)
routing_utils.flow_accumulation(
    flow_direction_uri, resolved_dem_uri, flow_accumulation_uri)
routing_utils.stream_threshold(
    flow_accumulation_uri, flow_threshold, stream_uri)
routing_utils.distance_to_stream(
    flow_direction_uri, stream_uri, distance_uri)
    