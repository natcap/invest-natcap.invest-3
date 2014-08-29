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

    transects_uri = compute_transects(args['shore_raster_uri'], \
        args['landmass_raster_uri'])


# Compute the shore transects
def compute_transects(args):
    print('arguments:')
    for key in args:
        print('entry', key, args[key])

    shore_raster_uri = args['shore_raster_uri']

    shore_raster = gdal.Open(shore_raster_uri)
    message = 'Cannot open file ' + shore_raster_uri
    assert shore_raster is not None, message
    shore_band = shore_raster.GetRasterBand(1)
    shore = shore_band.ReadAsArray()
    shore_band = None
    shore_raster = None

    shore_points = np.where(shore > 0)

    landmass_raster_uri = args['landmass_raster_uri']

    landmass_raster = gdal.Open(landmass_raster_uri)
    message = 'Cannot open file ' + landmass_raster_uri
    assert landmass_raster is not None, message
    landmass_band = landmass_raster.GetRasterBand(1)
    land = landmass_band.ReadAsArray()
    landmass_band = None
    landmass_raster = None

    bathymetry_raster_uri = args['bathymetry_raster_uri']

    bathymetry_raster = gdal.Open(bathymetry_raster_uri)
    message = 'Cannot open file ' + bathymetry_raster_uri
    assert bathymetry_raster is not None, message
    bathymetry_band = bathymetry_raster.GetRasterBand(1)
    bathymetry = bathymetry_band.ReadAsArray()
    bathymetry_band = None
    bathymetry_raster = None

    
    SECTOR_COUNT = 16 
    rays_per_sector = 1
    d_max = args['max_profile_length'] * 1000 # convert in meters
    model_resolution = args['model_resolution'] # in meters already
    cell_size = model_resolution
    
    # precompute directions
    direction_count = SECTOR_COUNT * rays_per_sector
    direction_range = range(direction_count)
    direction_step = 2.0 * math.pi / direction_count
    directions_rad = [a * direction_step for a in direction_range]
    direction_vectors = fetch_vectors(directions_rad)
    unit_step_length = np.empty(direction_vectors.shape[0])
    
    # Perform a bunch of tests to ensure the assumptions in the fetch algorithm
    # are valid
    # Check that bathy and landmass rasters are size-compatible
    message = 'landmass and bathymetry rasters are not the same size:' + \
    str(land.shape) + ' and ' + str(bathymetry.shape) + ' respectively.'
    assert land.shape == bathymetry.shape, message
    # Used to test if point fall within both land and bathy raster size limits
    (i_count, j_count) = land.shape
    # Check that shore points fall within the land raster limits
    message = 'some shore points fall outside the land raster'
    assert (np.amax(shore_points[0]) < i_count) and \
        (np.amax(shore_points[1]) < j_count), message
    # Check that shore points don't fall on nodata
    shore_points_on_nodata = np.where(land[shore_points] < 0.)[0].size
    message = 'There are ' + str(shore_points_on_nodata) + '/' + \
    str(shore_points[0].size) + \
    ' shore points on nodata areas in the land raster. There should be none.'
    assert not shore_points_on_nodata, message
    # Check that shore points don't fall on land
    shore_points_on_land = np.where(land[shore_points] > 0)[0].size
    if shore_points_on_land:
        points = np.where(land[shore_points] > 0)
        points = (shore_points[0][points[0]], shore_points[1][points[0]])
    message = 'There are ' + str(shore_points_on_land) + \
    ' shore points on land. There should be none.'
    assert not shore_points_on_land, message
    # Compute the ray paths in each direction to their full length (d_max).
    # We'll clip them for each point in two steps (raster boundaries & land)
    # The points returned by the cast function are relative to the origin (0,0)
    ray_path = {}
    valid_depths = 0 # used to determine if there are non-nodata depths
    #for d in direction_range:
    #    result = \
    #        cast_ray_fast(direction_vectors[d], MAX_FETCH/cell_size)
    #        ray_path[directions_rad[d]] = result[0]
    #        unit_step_length[d] = result[1]

def fetch_vectors(angles):
    """convert the angles passed as arguments to raster vector directions.
    
        Input:
            -angles: list of angles in radians
            
        Outputs:
            -directions: vector directions numpy array of size (len(angles), 2)
    """
    # Raster convention: Up is north, i.e. decreasing 'i' is towards north.
    # Wind convention: Wind is defined as blowing FROM and not TOWARDS. This
    #                  means that fetch rays are going where the winds are
    #                  blowing from:
    # top angle: cartesian convention (x axis: J, y axis: negative I)
    # parentheses: (oceanographic   
    #               convention)    Angle   direction   ray's I  ray's J
    #                                                  coord.   coord. 
    #              90                  0      north       -1        0
    #             (90)                90       east        0        1
    #               |                180      south        1        0
    #               |                270       west        0       -1
    #     0         |         180 
    #   (180)-------+-------->(0)  Cartesian to oceanographic
    #               |              angle transformation: a' = 180 - a  
    #               |              
    #               |              so that: [x, y] -> [I, J]
    #              270  
    #             (270)
    #            
    directions = np.empty((len(angles), 2))

    for a in range(len(angles)):
        pi = math.pi
        directions[a] = (round(math.cos(pi - angles[a]), 10),\
            round(math.sin(pi - angles[a]), 10))
    return directions


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



