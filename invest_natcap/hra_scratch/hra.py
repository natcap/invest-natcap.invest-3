'''This will be the preperatory module for HRA. It will take all unprocessed
and pre-processed data from the UI and pass it to the hra_core module.'''

import os
import shutil
import logging
import fnmatch
import numpy as np
import math

from osgeo import gdal, ogr, osr
from scipy import ndimage
from invest_natcap.habitat_risk_assessment import hra_core
from invest_natcap.habitat_risk_assessment import hra_preprocessor
from invest_natcap import raster_utils

LOGGER = logging.getLogger('HRA')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

