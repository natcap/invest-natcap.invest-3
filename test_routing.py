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
import tempfile

from invest_natcap.routing import routing_utils
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('test_routing')


def main():
    """main entry"""
    #dem_uri = r"C:\Users\rpsharp\Dropbox_stanford\Dropbox" \
    #    r"\brian_packard_dem_nutrient_bug\dem"

    dem_uri = (
        #r"E:\repositories\invest-natcap.invest-3\test\invest-data\Base_Data"
        #r"\Freshwater\erosivity")
        #'C:\\Users\\rsharp\\Documents\\invest-natcap.invest-3\\test\\' \
        #+ 'invest-data\\Base_Data\\Freshwater\\dem'
        'C:\\Users\\rpsharp\\Documents\\invest-natcap.invest-3\\test\\' \
        + 'invest-data\\Base_Data\\Freshwater\\dem')

    args = {
        'flow_direction_filename': 'flow_direction.tif',
        'flow_accumulation_filename': 'flow_accumulation.tif',
        'resolve_plateaus_filename': 'resolved_plateaus_dem.tif',
        'sink_filename': 'sinks.tif',
        'flat_mask_filename': 'flat_mask.tif',
        'labels_filename': 'labels.tif',
    }

    output_directory = 'C:/Users/rpsharp/Documents/routing_test/'

    tempfile.tempdir = output_directory
    raster_utils.create_directories([output_directory])
    file_suffix = ''

    LOGGER.info('calculating flow direction')
    (prefix, suffix) = (
        os.path.splitext(args['flow_direction_filename']))
    flow_direction_uri = os.path.join(
        output_directory, prefix + file_suffix + suffix)

    (prefix, suffix) = (
        os.path.splitext(args['flat_mask_filename']))
    flat_mask_uri = os.path.join(
        output_directory, prefix + file_suffix + suffix)

    (prefix, suffix) = (
        os.path.splitext(args['labels_filename']))
    labels_uri = os.path.join(
        output_directory, prefix + file_suffix + suffix)

    routing_utils.flow_direction_flat_drainage(
        dem_uri, flow_direction_uri, flat_mask_uri, labels_uri)

    LOGGER.info('calculating flow accumulation')
    (prefix, suffix) = (
        os.path.splitext(args['flow_accumulation_filename']))
    flow_accumulation_uri = os.path.join(
        output_directory, prefix + file_suffix + suffix)
    routing_utils.flow_accumulation(
        flow_direction_uri, dem_uri, flow_accumulation_uri)

    qgis_bin = r"C:\Program Files\QGIS Brighton\bin\qgis.bat"
    subprocess.Popen(
        [qgis_bin, dem_uri, labels_uri, flat_mask_uri, flow_direction_uri,
         flow_accumulation_uri],
        cwd=os.path.dirname(qgis_bin))

if __name__ == '__main__':
    cProfile.run('main()', 'stats')
    P_STATS = pstats.Stats('stats')
    P_STATS.sort_stats('time').print_stats(20)
    P_STATS.sort_stats('cumulative').print_stats(20)
    os.remove('stats')
