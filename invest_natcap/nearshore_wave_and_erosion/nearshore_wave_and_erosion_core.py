"""Module that contains the core computational components for 
    the coastal protection model"""

import math
import sys
import os
import logging

import numpy as np
import scipy as sp
import h5py as h5

from osgeo import ogr
from osgeo import gdal
import logging

from invest_natcap import raster_utils
import nearshore_wave_and_erosion_core as core

logging.getLogger("raster_utils").setLevel(logging.WARNING)
logging.getLogger("raster_cython_utils").setLevel(logging.WARNING)
LOGGER = logging.getLogger('coastal_vulnerability_core')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    """Executes the coastal protection model 
    
        args - is a dictionary with at least the following entries:
        
        returns nothing"""
    logging.info('executing coastal_protection_core')
    logging.info('Detecting shore...')
    ## Can we compute the shore?
    #if ('aoi_raster_uri' in args) and ('landmass_raster_uri' in args):
    #    print('detecting shore...')
    #    args['coarse_shore_uri'] = os.path.join(\
    #        args['intermediate_dir'], 'coarse_shore.tif')
    #    detect_shore_uri( \
    #        args['coarse_landmass_uri'], args['coarse_aoi_uri'], \
    #        args['coarse_shore_uri'])

    transects_uri = compute_transects(args)


# Compute the shore transects
def compute_transects(args):
    LOGGER.debug('Computing transects...')
    print('arguments:')
    for key in args:
        print('entry', key, args[key])

    ## Extract shore
    #shore_raster_uri = args['coarse_shore_uri']

    #raster = gdal.Open(shore_raster_uri)
    #message = 'Cannot open file ' + shore_raster_uri
    #assert raster is not None, message
    #coarse_geotransform = raster.GetGeoTransform()
    #band = raster.GetRasterBand(1)
    #coarse_shore = band.ReadAsArray()
    #band = None
    #raster = None

    #tiles = np.where(coarse_shore > 0)
    #LOGGER.debug('found %i shore segments.' % shore_points[0].size)


    # Put a dot at the center of each cell in the finer landmass raster
    args['shore_uri'] = os.path.join( \
        os.path.split(args['landmass_raster_uri'])[0], 'shore.tif')
    raster_utils.new_raster_from_base_uri(args['landmass_raster_uri'], \
        args['shore_uri'], 'GTIFF', 0, gdal.GDT_Int32)
    shore_raster = gdal.Open(args['shore_uri'], gdal.GA_Update)
    shore_band = shore_raster.GetRasterBand(1)
    fine_shore = shore_band.ReadAsArray()

    raster = gdal.Open(args['landmass_raster_uri'], gdal.GA_Update)
    fine_geotransform = raster.GetGeoTransform()
    band = raster.GetRasterBand(1)
    landmass = band.ReadAsArray()
    band = None
    raster = None
    raster = gdal.Open(args['aoi_raster_uri'], gdal.GA_Update)
    band = raster.GetRasterBand(1)
    aoi = band.ReadAsArray()
    band = None
    raster = None

    row_count, col_count = landmass.shape

    i_side_fine = int(round(fine_geotransform[1]))
    j_side_fine = int(round(fine_geotransform[5]))
    i_side_coarse = int(math.copysign(args['transect_spacing'], i_side_fine))
    j_side_coarse = int(math.copysign(args['transect_spacing'], j_side_fine))

    i_start = int(round(fine_geotransform[3]))
    j_start = int(round(fine_geotransform[0]))
    i_end = int(round(i_start + i_side_fine * row_count))
    j_end = int(round(j_start + j_side_fine * col_count))
    

    print('iterations:', (len(range(i_start, i_end, i_side_coarse)), \
                          len(range(j_start, j_end, j_side_coarse))))

    i_offset = i_side_coarse/i_side_fine + 4
    j_offset = j_side_coarse/j_side_fine + 4
    mask = np.ones((i_offset, j_offset))
    tile_size = np.sum(mask)

    tiles = 0
    #for i in range(i_start, i_end, i_side_coarse):
    for i in range(i_start, i_start + 100 * i_side_coarse, i_side_coarse):
        LOGGER.debug(' Detecting shore along line ' + \
            str((i_end - i)/i_side_coarse))

        i_base = (i - i_start) / i_side_fine - 2

        for j in range(j_start, j_end, j_side_coarse):
#            print ' ', str(j),
            j_base = (j - j_start) / j_side_fine - 2

            data = aoi[i_base:i_base+i_offset, j_base:j_base+j_offset]
            # Avoid nodata on tile
            if np.sum(data) == tile_size:
#                print('Found potential shore')
                # Look for landmass cover on tile
                tile = landmass[i_base:i_base+i_offset, j_base:j_base+j_offset]
                land = np.sum(tile)
#                print('land = ', land, 'vs', tile_size)
                # If land and sea, we have a shore: detect it and store
                if land and land < tile_size:
                    shore_patch = detect_shore(tile, mask, 0, connectedness = 4)
                    shore_pts = np.where(shore_patch == 1)
                    if shore_pts[0].size:
#                        print (i_base, j_base), ' ',

                        # Estimate shore orientation
                        shore_orientations = \
                            compute_shore_orientation(shore_patch, \
                                shore_pts, i_base, j_base)
                        # Keep shore segments with valid orientations only
                        shore_pts = shore_orientations.keys()
                        # Pick transect position among valid shore points
                        transect = select_transect(shore_pts)
                        # Skip tile if no valid shore points
                        if not transect:
                            continue
                        # Compute transect orientation
                        transect_orientation = \
                            compute_transect_orientation(transect, \
                                shore_orientations[transect], landmass)
                        # Skip tile if can't compute valid orientation
                        if not transect_orientation:
                            continue
                        # Adjust transect position to bathymetry
                        transect_position = \
                            adjust_transect_position(transect_orientation, \
                                bathymetry)

                        #transect_profile = \
                        #    sample_transect_profile(transect_position, \
                        #        transect_orientation, bathymetry)

                        tiles += 1

    LOGGER.debug('found %i tiles.' % tiles)
    shore_band.WriteArray(fine_shore)
    shore_band = None
    shore_raster = None
        
    return
    # Extract landmass
    landmass_raster_uri = args['landmass_raster_uri']

    landmass_raster = gdal.Open(landmass_raster_uri)
    message = 'Cannot open file ' + landmass_raster_uri
    assert landmass_raster is not None, message
    landmass_band = landmass_raster.GetRasterBand(1)
    land = landmass_band.ReadAsArray()
    landmass_band = None
    landmass_raster = None

    # Extract bathymetry
    bathymetry_raster_uri = args['bathymetry_raster_uri']

    bathymetry_raster = gdal.Open(bathymetry_raster_uri)
    message = 'Cannot open file ' + bathymetry_raster_uri
    assert bathymetry_raster is not None, message
    bathymetry_band = bathymetry_raster.GetRasterBand(1)
    bathymetry = bathymetry_band.ReadAsArray()
    bathymetry_band = None
    bathymetry_raster = None

    
    # precompute directions
    SECTOR_COUNT = 16 
    rays_per_sector = 1
    d_max = args['max_profile_length'] * 1000 # convert in meters
    model_resolution = args['model_resolution'] # in meters already
    cell_size = args['cell_size']
    
    direction_count = SECTOR_COUNT * rays_per_sector
    direction_range = range(direction_count)
    direction_step = 2.0 * math.pi / direction_count
    directions_rad = [a * direction_step for a in direction_range]
    direction_vectors = fetch_vectors(directions_rad)
    unit_step_length = np.empty(direction_vectors.shape[0])
    
    # Perform a bunch of tests beforehand
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
    for p in zip(direction_vectors[0], direction_vectors[1]):
        result = cast_ray_fast(p, d_max/cell_size)

    # Identify valid transect directions
    valid_transect_count, valid_transects = \
        find_valid_transects(shore_points, land, direction_vectors)
 
    # Save valid transect directions
    output_uri = os.path.join(args['intermediate_dir'], 'valid_transects.tif')
    raster_utils.new_raster_from_base_uri( \
        args['shore_raster_uri'], output_uri, 'GTiff', 0., gdal.GDT_Float32)
    raster = gdal.Open(output_uri, gdal.GA_Update)
    band = raster.GetRasterBand(1)
    shore_array = band.ReadAsArray()
    for s in range(shore_points[0].size):
        shore_array[shore_points[0][s], shore_points[1][s]] = \
            np.sum(valid_transects[s] > -1).astype(np.int32)
    band.FlushCache()
    band.WriteArray(shore_array)
    band = None
    raster = None


    # Compute raw transect depths
    raw_depths = compute_raw_transect_depths(shore_points, \
        valid_transects, valid_transect_count, direction_vectors, bathymetry, \
        land, args['model_resolution'], args['max_land_profile_len'], \
        args['max_land_profile_height'], args['max_profile_length'])

    # Save raw transect depths
    raw_transect_depths_uri = \
        os.path.join(args['intermediate_dir'], 'raw_transect_depths.h5')
    f = h5.File(raw_transect_depths_uri, 'w')
    h5_dataset = f.create_dataset('raw_transect_depths', raw_depths.shape)
    h5_dataset[...] = raw_depths
    f.close()

    # Sample bathymetry along transects
    shore_profiles = sample_bathymetry_along_transects(bathymetry, \
        raw_depths, shore_points, direction_vectors)

    # Save bathymetry samples along transects

def compute_shore_orientation(shore, shore_pts, i_base, j_base):
    """Compute an estimate of the shore orientation. 
       Inputs:
           -shore: 2D numpy shore array (1 for shore, 0 otherwise)
           -shore_pts: shore ij coordinates in shore array coordinates

        Returns a dictionary of {(shore ij):(orientation vector ij)} pairs"""
    shore = np.copy(shore) # Creating a copy in-place
    max_i, max_j = shore.shape
    mask = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])

    updated_shore = shore.astype(int)

    # Compute orientations
    orientations = {}
    for coord in zip(shore_pts[0], shore_pts[1]):
        row, col = coord
        if not row or row >= max_i -1:
            updated_shore[row, col] = 0
            continue

        if not col or col >= max_j -1:
            updated_shore[row, col] = 0
            continue

        neighborhood = np.copy(shore[row-1:row+2, col-1:col+2])
        neighborhood[1, 1] = 0
        neighbor_count = np.sum(neighborhood)
 
        if neighbor_count != 2:
            updated_shore[row, col] = 0
            continue

        neighbors = np.where(neighborhood == 1)

        orientations[coord] = \
            (neighbors[0][1] - neighbors[0][0], \
            neighbors[1][1] - neighbors[1][0])

    # Compute average orientations
    shore = np.copy(updated_shore)
    average_orientations = {}
    for coord in orientations.keys():
        row, col = coord
        neighborhood = np.copy(shore[row-1:row+2, col-1:col+2])
        neighborhood[1, 1] = 0
        neighbor_count = np.sum(neighborhood)
             
        if neighbor_count != 2:
            del orientations[coord]
            continue

        neighbors = np.where(neighborhood == 1)
        neighbors = (neighbors[0] + row - 1, neighbors[1] + col - 1)

        first = (neighbors[0][0], neighbors[1][0])
        second = (neighbors[0][1], neighbors[1][1])
        if (first not in orientations) or (second not in orientations):
            del orientations[coord]
            continue

        average_orientation = \
            ((orientations[first][0] + orientations[second][0]) / 2,
            (orientations[first][1] + orientations[second][1]) / 2)
            
        average_orientations[coord] = average_orientation
    shore_orientation = {}
    for segment in orientations.keys():
        O = orientations[segment]
        A = average_orientations[segment]
        shore_orientation[(segment[0] + i_base, segment[1] + j_base)] = \
            (float(2 * O[0] + A[0]) / 3., float(2 * O[1] + A[1]) / 3.)

    return shore_orientation
 
def compute_transect_orientation(position, orientation, landmass):
    """Returns transect orientation towards the ocean."""
#    print('shore orientation', orientation)
    # orientation is perpendicular to the shore
    shore_orientation = np.copy(orientation)
    orientation = np.array([-orientation[1], orientation[0]]) # pi/2 rotation
    transect_orientation = np.copy(orientation)

    l = 0 if abs(orientation[0]) > abs(orientation[1]) else 1
    s = 1 if abs(orientation[0]) > abs(orientation[1]) else 0

    # Normalize orientation and extend to 3 pixels to minimize roundoff
    orientation[s] = round(3 * float(orientation[s]) / orientation[l])
    orientation[l] = 3.

    normalized_orientation = [orientation[0], orientation[1]]

    # If orientation points to water, return vector as is
    if not landmass[position[0] +orientation[0], position[1] +orientation[1]]:
        return orientation
    # Otherwise, check the opposite direction
    else:
        orientation *= -1

        # If the other direction does not work, maybe the vector is too long
        if landmass[position[0] +orientation[0], position[1] +orientation[1]]:
            # Reduce the vector length
            step = np.array([round(orientation[0]/3), round(orientation[1]/3)])

            # If orientation points to water, return vector as is
            if not landmass[position[0] + step[0], position[1] + step[1]]:
                return orientation
            # If not, check the other direction
            else:
                step *= -1
                # If it doesn't work, break.
                if landmass[position[0] +step[0], position[1] +step[1]]:
                    LOGGER.debug('invalid transect ' + str(position))
                    return None
                    #print('position', position)
                    #print('shore orientation', shore_orientation)
                    #print('transect orientation', transect_orientation)
                    #patch = np.copy(landmass[position[0]-5:position[0]+5, \
                    #    position[1]-5:position[1]+5]).astype(int)
                    #patch[5, 5] = 2
                    #patch[5 + normalized_orientation[0], \
                    #    5 + normalized_orientation[1]] += 5
                    #print('normalized orientation', normalized_orientation, \
                    #    (round(5 + normalized_orientation[0]), \
                    #        round(5 + normalized_orientation[1])))
                    #patch[5 + orientation[0], 5 + orientation[1]] += 3
                    #print('corrected orientation', orientation, \
                    #    (5 + orientation[0], 5 + orientation[1]))
                    #print(patch)
                    #assert False

                return orientation * -1


def select_transect(shore_pts):
    """Select transect postion among shore points"""
    if not len(shore_pts):
        return None
    
    # Return the transect with the smallest i first, and j second
    sorted_points = sorted(shore_pts, key = lambda p: p[1])
    sorted_points = sorted(sorted_points, key = lambda p: p[0])
    
#    print('sorted points', sorted_points)

    return sorted_points[0]

def compute_shore_location(bathymetry, transect_spacing, model_resolution):
    """Compute the location of the shore piecewise at much higher resolution
       than coastal vulnerability.
       
    """
    # Clip and resample bathymetry to the AOI
    #nearshore_wave_and_erosion.raster_from_shapefile_uri(shapefile_uri, aoi_uri, \
    #    cell_size, output_uri, field=None, all_touched=False, nodata = 0., \
    #    datatype = gdal.GDT_Float32)

def compute_raw_transect_depths(shore_points, valid_transects, \
    valid_transect_count, \
    direction_vectors, bathymetry, landmass, model_resolution, \
    max_land_profile_len, max_land_profile_height, \
    max_sea_profile_len):
    """ compute the transect endpoints that will be used to cut transects"""
    LOGGER.debug('Computing transect endpoints...')

    # Maximum transect extents
    max_land_len = max_land_profile_len / model_resolution
    max_sea_len = 1000 * max_sea_profile_len / model_resolution

    LOGGER.debug('Creating a %ix%i transect matrix' % \
        (valid_transect_count, max_land_len + max_sea_len))
    depths = np.ones((valid_transect_count, max_land_len + max_sea_len))*-20000

    # Repeat for each shore segment
    for segment in range(shore_points[0].size):
        transect = 0
        # For each valid transect
        while valid_transects[segment][transect] > -1:
            p_i = shore_points[0][segment]
            p_j = shore_points[1][segment]
            direction = valid_transects[segment][transect]
            d_i = direction_vectors[0][direction]
            d_j = direction_vectors[1][direction]

            depths[transect, max_sea_profile_len] = bathymetry[p_i, p_j]

            # Compute the landward part of the transect
            start_i = p_i - d_i
            start_j = p_j - d_j

            highest_point = max(0, bathymetry[int(start_i), int(start_j)])
            highest_index = 0

            # If no land behind the piece of land, stop there and report 0
            if not landmass[int(start_i), int(start_j)]:
                inland_steps = 0
            # Else, count from 1
            else:
                # Stop when maximum inland distance is reached
                for inland_steps in range(1, max_land_len + 1):
                    elevation = bathymetry[int(start_i), int(start_j)]
                    # Hit either nodata, or some bad data
                    if elevation <= -12000:
                        inland_steps -= 1
                        break
                    # Stop if shore is reached
                    if not landmass[int(start_i), int(start_j)]:
                        inland_steps -= 1
                        break
                    # We can store the depth at this point
                    depths[transect, max_land_len - inland_steps] = \
                        elevation
                    # Stop at maximum elevation
                    if elevation > 20:
                        break
                    # Keep track of highest point so far
                    if elevation >= highest_point:
                        highest_point = elevation
                        highest_index = inland_steps
                        
                    start_i -= d_i
                    start_j -= d_j
            # Adjust to highest point if necessary and put nodata after it
            if bathymetry[int(start_i), int(start_j)] < highest_point:
                inland_steps = highest_index
                depths[transect, max_land_len - inland_steps - 1] = \
                    -20000
            transect += 1

            # Compute the seaward part of the transect
            start_i = p_i
            start_j = p_j
            lowest_index = 0
            lowest_point = min(0, bathymetry[int(start_i), int(start_j)])
            lowest_index = 0

            # Stop when maximum offshore distance is reached
            for offshore_steps in range(max_sea_len):
                # Stop if shore is reached
                if landmass[int(start_i), int(start_j)]:
                    offshore_steps -= 1
                    break
                elevation = bathymetry[int(start_i), int(start_j)]
                # Hit either nodata, or some bad data
                if elevation <= -12000:
                    offshore_steps -= 1
                    break
                # We can store the depth at this point
                depths[transect, max_land_len + offshore_steps] = \
                    elevation
                # Keep track of lowest point so far
                if elevation <= lowest_point:
                    lowest_point = elevation
                    lowest_index = offshore_steps
                start_i -= d_i
                start_j -= d_j
            # Adjust to lowest point if necessary
            if bathymetry[int(start_i), int(start_j)] > lowest_point:
                offshore_steps = lowest_index
                depths[transect, max_land_len + offshore_steps] = \
                    elevation
            # If shore borders nodata, offshore_step is -1, set it to 0
            offshore_steps = max(0, offshore_steps)

            # Done for this transect, moving on to the next
            transect += 1

    return depths

def sample_bathymetry_along_transects(bathymetry, valid_transects, \
    shore_points, direction_vectors):
    """ Sample shore profile directly from the bathymetry layer."""
    pass

def find_valid_transects(shore_points, land, direction_vectors):
    """ Compute valid transect directions and store them in an array 
        where a row lists the index of valid sectors, with -1 as the
        list terminator."""
    LOGGER.debug('Counting valid transects...')

    # Precompute data about the angular sectors
    L = np.array(np.abs(direction_vectors[1]) > \
        np.abs(direction_vectors[0])).astype(np.int32)
    S = np.logical_not(L).astype(np.int32)
    I = np.array(range(L.size)).astype(np.int32)

    L_val = np.absolute(direction_vectors[(L,I)])
    directions = np.array([direction_vectors[0]/L_val,direction_vectors[1]/L_val])

    # Check for each shore point which sector is valid
    valid_transects = \
        np.ones((shore_points[0].size, direction_vectors[0].size)) * -1.
    valid_transect_count = 0
    for p in range(shore_points[0].size):
        point = (shore_points[0][p], shore_points[1][p])
        valid_sectors = 0
        for sector in range(L.size):
            i = round(point[0] + directions[0][sector])
            j = round(point[1] + directions[1][sector])
            if land[i, j] == 0:
                valid_transects[p, valid_sectors] = sector
                valid_sectors += 1
	valid_transect_count += valid_sectors

    LOGGER.debug('found %i valid transects.' % valid_transect_count)
    
    return (valid_transect_count, valid_transects)

def cast_ray_fast(direction, d_max):
    """ March from the origin towards a direction until either land or a
    maximum distance is met.
    
        Inputs:
        - origin: algorithm's starting point -- has to be on sea
        - direction: marching direction
        - d_max: maximum distance to traverse
        - raster: land mass raster
        
        Returns the distance to the origin."""
    # Rescale the stepping vector so that its largest coordinate is 1
    unit_step = direction / np.fabs(direction).max()
    # Compute the length of the normalized vector
    unit_step_length = np.sqrt(np.sum(unit_step**2))
    # Compute the number of steps to take
    # Use ceiling to make sure to include any cell that is within the range of
    # max_fetch
    step_count = int(math.ceil(d_max / unit_step_length))
    I = np.array([i*unit_step[0] for i in range(step_count+1)])
    J = np.array([j*unit_step[1] for j in range(step_count+1)])

    return ((I, J), unit_step_length)
 

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
    directions = np.empty((2, len(angles)))

    for a in range(len(angles)):
        pi = math.pi
        directions[0, a] = round(-math.cos(.5 * pi - angles[a]), 10)
        directions[1, a] = round(math.sin(.5 * pi - angles[a]), 10)
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
def detect_shore(land_sea_array, aoi_array, aoi_nodata, connectedness = 8):
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
        # Shore points are inland (>0), and detected using 8-connectedness
        if connectedness is 8:
            kernel = np.array([[-1, -1, -1],
                               [-1,  8, -1],
                               [-1, -1, -1]])
        else:
            kernel = np.array([[ 0, -1,  0],
                               [-1,  4, -1],
                               [ 0, -1,  0]])
        # Generate the nodata shore artifacts
        aoi_array = np.ones_like(land_sea_array)
        aoi_array[land_sea_array == nodata] = nodata
        aoi_borders = (sp.signal.convolve2d(aoi_array, \
                                                kernel, \
                                                mode='same') >0 ).astype('int')
        # Generate all the borders (including data artifacts)
        borders = (sp.signal.convolve2d(land_sea_array, \
                                     kernel, \
                                     mode='same') >0 ).astype('int')
        # Real shore = all borders - shore artifacts
        borders = ((borders - aoi_borders) >0 ).astype('int') * 1.

        shore_segment_count = np.sum(borders)
        if shore_segment_count == 0:
            LOGGER.warning('No shore segment detected')
        return borders



