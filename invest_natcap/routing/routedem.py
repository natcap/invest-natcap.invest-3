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
    
    LOGGER.info('resolving filling pits')
    
    prefix, suffix = os.path.splitext(args['pit_filled_filename'])
    dem_pit_filled_uri =  os.path.join(output_directory, prefix + file_suffix + suffix)  
    routing_utils.fill_pits(dem_uri, dem_pit_filled_uri)
    dem_uri = dem_pit_filled_uri
    
    LOGGER.info('resolving plateaus')
    prefix, suffix = os.path.splitext(args['resolve_plateaus_filename'])
    dem_offset_uri = os.path.join(output_directory, prefix + file_suffix + suffix)    
    routing_cython_core.resolve_flat_regions_for_drainage(dem_uri, dem_offset_uri)
    dem_uri = dem_offset_uri
    

    #Calculate slope
    if args['calculate_slope']:
        LOGGER.info("Calculating slope")
        prefix, suffix = os.path.splitext(args['slope_filename'])
        slope_uri = os.path.join(output_directory, prefix + file_suffix + suffix)
        raster_utils.calculate_slope(dem_uri, slope_uri)

    #Calculate flow accumulation
    LOGGER.info("calculating flow direction")
    prefix, suffix = os.path.splitext(args['flow_direction_filename'])
    flow_direction_uri = os.path.join(
        output_directory, prefix + file_suffix + suffix)
    routing_cython_core.flow_direction_inf(dem_uri, flow_direction_uri)
    
    LOGGER.info("calculating flow accumulation")
    prefix, suffix = os.path.splitext(args['flow_accumulation_filename'])
    flow_accumulation_uri = os.path.join(
        output_directory, prefix + file_suffix + suffix)
    routing_utils.flow_accumulation(flow_direction_uri, dem_uri, flow_accumulation_uri)
    
    #classify streams from the flow accumulation raster
    LOGGER.info("Classifying streams from flow accumulation raster")
    
    if args['multiple_stream_thresholds']:
        lower_threshold = int(args['threshold_flow_accumulation'])
        upper_threshold = int(args['threshold_flow_accumulation_upper'])
        threshold_step = int(args['threshold_flow_accumulation_stepsize'])
        
        for threshold_amount in range(
            lower_threshold, upper_threshold+1, threshold_step):
            LOGGER.info("Calculating stream threshold at %s pixels" % (threshold_amount))
            v_stream_uri = os.path.join(output_directory, 'v_stream%s_%s.tif' % (file_suffix, str(threshold_amount)))
            
            routing_utils.stream_threshold(
                flow_accumulation_uri, threshold_amount, v_stream_uri)
    else:
        v_stream_uri = os.path.join(output_directory, 'v_stream%s.tif' % file_suffix)
        routing_utils.stream_threshold(flow_accumulation_uri,
        float(args['threshold_flow_accumulation']), v_stream_uri)

    if args['calculate_downstream_distance']:
        prefix, suffix = os.path.splitext(args['downstream_distance_filename'])
        distance_uri = os.path.join(
            output_directory, prefix + file_suffix + suffix)
        routing_utils.distance_to_stream(flow_direction_uri, v_stream_uri, distance_uri)