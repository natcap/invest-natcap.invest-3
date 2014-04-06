import cProfile
import pstats

import time
import gdal
import numpy
from invest_natcap.routing import routing_utils
import routing_cython_core


dem_uri = 'test/invest-data/Base_Data/Freshwater/dem'
flow_direction_uri = 'test_flow.tif'
flow_accumulation_uri = 'test_flux.tif'
flow_threshold = 1000
stream_uri = 'test_stream.tif'
routing_utils.flow_direction_inf(dem_uri, flow_direction_uri)
routing_utils.flow_accumulation(
    flow_direction_uri, dem_uri, flow_accumulation_uri)
routing_utils.stream_threshold(
    flow_accumulation_uri, flow_threshold, stream_uri)
    