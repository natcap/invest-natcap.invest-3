"""InVEST Biodiversity model core function  module"""

import invest_cython_core
from invest_natcap.invest_core import invest_core

from osgeo import gdal
from osgeo import org
import numpy as np
import scipy.ndimage as ndimage

import os.path
import logging

LOGGER = logging.getLogger('biodiversity_core')


def biophysical(args):
    """Execute the biophysical component of the pollination model.

        returns nothing."""

    LOGGER.debug('Starting biodiversity biophysical calculations')
    #Get raster properties: cellsize, width, height, cells = width * height, extent    
    #Create raster of habitat based on habitat field

    #Sum weight of threats

    #Check that threat count matches with sensitivity

    #If access_lyr: convert to raster, if value is null set to 1, else set to value

    #Process density layers / each threat

    #For all threats:
        #get weight, name, max_idst, decay
        #mulitply max_dist by 1000 (must be a conversion to meters
        #get proper density raster, depending on land cover
        
        #Adjust threat by distance:
            #Calculate neighborhood

        #Adjust threat by weight:
        
        #Adjust threat by protection / access

        #Adjust threat by sensitivity

    #Compute Degradation of all threats

    #Compute quality for all threats

    #Adjust quality by habitat status

    #Comput Rarity if user supplied baseline raster


    LOGGER.debug('Finished biodiversity biophysical calculations')

def raster_from_table_values(table, raster):
    return raster
