#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This is a script I use to develop the efficient drainage functionality in
    invest_natcap.routing.  It should be deleted if not in its own feature
    branch"""

import cProfile
import pstats
import os
import logging
import subprocess

from invest_natcap.routing import routing_utils
import routing_cython_core #pylint: disable=F0401
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routedem')


def main():
    """main entry"""
    #dem_uri = r"C:\Users\rpsharp\Dropbox_stanford\Dropbox" \
    #    r"\brian_packard_dem_nutrient_bug\dem"

    dem_uri = \
        'C:\\Users\\rpsharp\\Documents\\invest-natcap.invest-3\\test\\' \
        + 'invest-data\\Base_Data\\Freshwater\\dem'

    args = {
        'flow_direction_filename': 'flow_direction.tif',
        'flow_accumulation_filename': 'flow_accumulation.tif',
        'resolve_plateaus_filename': 'resolved_plateaus_dem.tif',
        'sink_filename': 'sinks.tif',
    }

    output_directory = 'C:/Users/rpsharp/Documents/routing_test/'
    raster_utils.create_directories([output_directory])
    file_suffix = ''

    LOGGER.info('resolve_plateaus')
    (prefix, suffix) = os.path.splitext(
        args['resolve_plateaus_filename'])
    dem_offset_uri = os.path.join(output_directory, prefix
                                  + file_suffix + suffix)
    routing_cython_core.resolve_flat_regions_for_drainage(dem_uri,
                                                          dem_offset_uri)
    dem_uri = dem_offset_uri

    LOGGER.info('calculating flow direction')
    (prefix, suffix) = os.path.splitext(args['flow_direction_filename'])
    flow_direction_uri = os.path.join(
        output_directory, prefix + file_suffix + suffix)
    routing_cython_core.flow_direction_inf(dem_uri, flow_direction_uri)

    LOGGER.info('calculating flow accumulation')
    (prefix, suffix) = (
        os.path.splitext(args['flow_accumulation_filename']))
    flow_accumulation_uri = os.path.join(
        output_directory, prefix + file_suffix + suffix)
    routing_utils.flow_accumulation(
        flow_direction_uri, dem_uri, flow_accumulation_uri)

    qgis_bin = r"C:\Program Files\QGIS Brighton\bin\qgis.bat"
    subprocess.Popen([qgis_bin, flow_accumulation_uri],
                     cwd=os.path.dirname(qgis_bin))

if __name__ == '__main__':
    cProfile.run('main()', 'stats')
    P_STATS = pstats.Stats('stats')
    P_STATS.sort_stats('time').print_stats(20)
    P_STATS.sort_stats('cumulative').print_stats(20)
    os.remove('stats')
