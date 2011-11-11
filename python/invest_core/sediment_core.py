"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import numpy as np
from osgeo import gdal, ogr
from dbfpy import dbf
import math
import invest_core
import logging

logger = logging.getLogger('carbon_core')

def biophysical(args):
    """Executes the basic sediment model

        args - is a dictionary with at least the following entries:
            
        returns nothing"""

    logger.info("do it up")

def valuation(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with the following entries:
        
        returns nothing"""

    logger.info('do it up')
