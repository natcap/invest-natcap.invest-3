"""Module that contains the core computational components for 
    the coastal protection model"""

import math
import sys
import os
import logging

import numpy as np
import scipy as sp

from osgeo import ogr
from osgeo import gdal

from invest_natcap import raster_utils

def execute(args):
    """Executes the coastal protection model 
    
        args - is a dictionary with at least the following entries:
        
        returns nothing"""
    logging.info('executing coastal_protection_core')
    logging.info('Detecting shore...')
    # Can we compute the shore?
    if ('aoi_raster_uri' in args) and ('landmass_raster_uri' in args):
        print('detecting shore...')
        args['shore_raster_uri'] = os.path.join(\
            args['intermediate_dir'], 'shore.tif')
        detect_shore_uri( \
            args['landmass_raster_uri'], args['aoi_raster_uri'], \
            args['shore_raster_uri'])


# TODO: improve this docstring!
def detect_shore_uri(landmass_raster_uri, aoi_raster_uri, output_uri):
    """ Extract the boundary between land and sea from a raster.
    
        - raster: numpy array with sea, land and nodata values.
        
        returns a numpy array the same size as the input raster with the shore
        encoded as ones, and zeros everywhere else."""
    landmass_raster = gdal.Open(landmass_raster_uri)
    land_sea_array = landmass_raster.GetRasterBand(1).ReadAsArray()
    landmass_raster = None
    aoi_raster = gdal.Open(aoi_raster_uri)
    aoi_array = aoi_raster.GetRasterBand(1).ReadAsArray()
    aoi_nodata = aoi_raster.GetRasterBand(1).GetNoDataValue()
    aoi_raster = None
    
    shore_array = detect_shore(land_sea_array, aoi_array, aoi_nodata)

    raster_utils.new_raster_from_base_uri( \
        aoi_raster_uri, output_uri, 'GTiff', 0., gdal.GDT_Float32)
    raster = gdal.Open(output_uri, gdal.GA_Update)
    band = raster.GetRasterBand(1)
    band.FlushCache()
    band.WriteArray(shore_array)

# improve this docstring!
def detect_shore(land_sea_array, aoi_array, aoi_nodata):
    """ Extract the boundary between land and sea from a raster.
    
        - raster: numpy array with sea, land and nodata values.
        
        returns a numpy array the same size as the input raster with the shore
        encoded as ones, and zeros everywhere else."""
    # Rich's super-short solution, which uses convolution.
    nodata = -1 
    land_sea_array[aoi_array == aoi_nodata] = nodata
    # Don't bother computing anything if there is only land or only sea
    land_size = np.where(land_sea_array > 0)[0].size

    if land_size == 0:
        LOGGER.warning('There is no shore to detect: land area = 0')
        return np.zeros_like(land_sea_array)
    elif land_size == land_sea_array.size:
        LOGGER.warning('There is no shore to detect: sea area = 0')
        return np.zeros_like(land_sea_array)
    else:
        kernel = np.array([[ 0, -1,  0],
                           [-1,  4, -1],
                           [ 0, -1,  0]])
        # Generate the nodata shore artifacts
        aoi_array = np.ones_like(land_sea_array)
        aoi_array[land_sea_array == nodata] = nodata
        aoi_borders = (sp.signal.convolve2d(aoi_array, \
                                                kernel, \
                                                mode='same') <0 ).astype('int')
        # Generate all the borders (including data artifacts)
        borders = (sp.signal.convolve2d(land_sea_array, \
                                     kernel, \
                                     mode='same') <0 ).astype('int')
        # Real shore = all borders - shore artifacts
        borders = ((borders - aoi_borders) >0 ).astype('int') * 1.

        shore_segment_count = np.sum(borders)
        if shore_segment_count == 0:
            LOGGER.warning('No shore segment detected')
        return borders



