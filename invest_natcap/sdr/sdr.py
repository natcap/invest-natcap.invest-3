"""InVEST Sediment Delivery Ratio (SDR) module"""

import os
import csv
import logging

from osgeo import gdal
from osgeo import ogr
import numpy

from invest_natcap import raster_utils
from invest_natcap.routing import routing_utils
import routing_cython_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('sdr')


def execute(args):
    pass
