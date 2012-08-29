"""InVEST Wind_Energy model core function  module"""
import math
import os.path
import logging

from osgeo import gdal
import numpy as np
import scipy.ndimage as ndimage

from invest_natcap import raster_utils
LOGGER = logging.getLogger('wind_energy_core')

def biophysical(args):
    """This is where the doc string lives
    
        args[workspace_dir] - uri for workspace directory
        args[bathymetry] - a GDAL raster of elevation values
        args[aoi] - an OGR polygon shapefile of the area of interest


        returns - 
    """

    # fill in skeleton below

def valuation(args):
    """This is where the doc string lives"""

    # fill in skeleton below
