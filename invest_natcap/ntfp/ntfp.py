"""InVEST NTFP module at the "uri" level"""

import os
import math
import logging
import shutil

from osgeo import gdal
from osgeo import ogr

import pygeoprocessing.geoprocessing

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('ntfp')

def execute(args):
    LOGGER.info(args)
    