'''This is #the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''
import math
import datetime
import logging
import os
import numpy as np

from osgeo import gdal, ogr
from invest_natcap import raster_utils

LOGGER = logging.getLogger('HRA_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
