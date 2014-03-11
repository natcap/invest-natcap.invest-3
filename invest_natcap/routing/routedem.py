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

def execute(*args):
    pass