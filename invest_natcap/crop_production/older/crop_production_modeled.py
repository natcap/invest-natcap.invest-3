import logging
from osgeo import gdal, ogr, osr
from invest_natcap import raster_utils
import sys

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('invest_natcap.crop_production.older.modeled')

def execute(args):
    pass
