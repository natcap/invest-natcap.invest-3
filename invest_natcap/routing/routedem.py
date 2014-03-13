"""RouteDEM entry point for exposing the invest_natcap's routing package 
    to a UI."""

import os
import csv
import logging

from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
from invest_natcap.routing import routing_utils
import routing_cython_core
from invest_natcap.sediment import sediment_core


logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routedem')

def execute(args):

    output_directory = args['workspace_dir']
    LOGGER.info('creating directory %s', output_directory)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    file_suffix = ''
    dem_uri = args['dem_uri']
    if args['resolve_plateaus']:
        LOGGER.info('resolving plateaus')
        prefix, suffix = os.path.splitext(args['resolve_plateaus_filename'])
        dem_offset_uri = os.path.join(output_directory, prefix + file_suffix + suffix)    
        routing_cython_core.resolve_flat_regions_for_drainage(args['dem_uri'], dem_offset_uri)
        dem_uri = dem_offset_uri
    
    #Calculate slope
    LOGGER.info("Calculating slope")
    slope_uri = os.path.join(output_directory, 'slope%s.tif' % file_suffix)
    raster_utils.calculate_slope(dem_uri, slope_uri)

    #Calculate flow accumulation
    LOGGER.info("calculating flow direction")
    flow_direction_uri = os.path.join(output_directory, 'flow_direction%s.tif' % file_suffix)
    routing_cython_core.flow_direction_inf(dem_uri, flow_direction_uri)
    
    LOGGER.info("calculating flow accumulation")
    flow_accumulation_uri = os.path.join(output_directory, 'flow_accumulation%s.tif' % file_suffix)
    routing_utils.flow_accumulation(flow_direction_uri, dem_uri, flow_accumulation_uri)
    
    #classify streams from the flow accumulation raster
    LOGGER.info("Classifying streams from flow accumulation raster")
    v_stream_uri = os.path.join(output_directory, 'v_stream%s.tif' % file_suffix)

    routing_utils.stream_threshold(flow_accumulation_uri,
        float(args['threshold_flow_accumulation']), v_stream_uri)
