"""InVEST Wind Energy model file handler module"""
import os.path
import logging
import csv

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap.wind_energy import wind_energy_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_valuation')

def execute(args):
    """This is where the doc string lives"""

    # create output folders

    # handle suffix

    # handle opening of relevant files

    # handle any pre-processing that must be done

    # call on the core module
