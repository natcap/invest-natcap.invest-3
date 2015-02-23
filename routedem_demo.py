"""Example script of how to do flow direction, flow accumulation, stream
    thresholding and slope calculation with the InVEST RouteDEM toolkit."""

import os

from invest_natcap.routing import routing_utils
from invest_natcap import raster_utils

def main():
    dem_uri = (
        'C:/Users/rpsharp/Documents/invest-natcap.invest-3/test/invest-data/'
        'Base_Data/Freshwater/dem')
    output_directory = 'C:/Users/rpsharp/Documents/routedem_demo/'
    os.makedirs(output_directory)

    print 'calculating flow direction'
    flow_direction_uri = os.path.join(output_directory, 'flow_direction.tif')
    routing_utils.flow_direction_d_inf(dem_uri, flow_direction_uri)

    print 'calculating flow accumulation'
    flow_accumulation_uri = os.path.join(
        output_directory, 'flow_accumulation.tif')
    routing_utils.flow_accumulation(
        flow_direction_uri, dem_uri, flow_accumulation_uri)

    print 'calculating streams'
    stream_uri = os.path.join(output_directory, 'streams.tif')
    routing_utils.stream_threshold(
        flow_accumulation_uri, 1000, stream_uri)

    print 'calculating slope'
    slope_uri = os.path.join(output_directory, 'slope.tif.')
    raster_utils.calculate_slope(dem_uri, slope_uri)

if __name__ == '__main__':
    main()
