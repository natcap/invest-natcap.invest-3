"""Module that contains the core computational components for 
    the coastal protection model"""

import math
import sys
import os
import logging

import numpy as np
import scipy as sp
from scipy import interpolate
from scipy import ndimage
import h5py as h5

from osgeo import ogr
from osgeo import gdal

import cProfile, pstats

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
    logging.info('Computing transects...')

    #transects_uri = compute_transects(args)
    #p = 
    p = cProfile.Profile()
    transects_uri = p.runctx('compute_transects(args)', globals(), locals())
    print('transects_uri', transects_uri)
    s = pstats.Stats(p)
    s.sort_stats('time').print_stats(20)


# Compute the shore transects
def compute_transects(args):
    LOGGER.debug('Computing transects...')
    #print('arguments:')
    #for key in args:
    #    print('entry', key, args[key])

    # Store shore and transect information
    shore_nodata = -20000.0
    args['transects_uri'] = os.path.join( \
        os.path.split(args['landmass_raster_uri'])[0], 'transects.tif')
    raster_utils.new_raster_from_base_uri(args['landmass_raster_uri'], \
        args['transects_uri'], 'GTIFF', shore_nodata, gdal.GDT_Float64)
    transect_raster = gdal.Open(args['transects_uri'], gdal.GA_Update)
    transect_band = transect_raster.GetRasterBand(1)
#    transects = transect_band.ReadAsArray()
    
    print('past transects')

#    # Store transect profiles to reconstruct shore profile
#    args['shore_profile_uri'] = os.path.join( \
#        os.path.split(args['landmass_raster_uri'])[0], 'shore_profile.tif')
#    raster_utils.new_raster_from_base_uri(args['landmass_raster_uri'], \
#        args['shore_profile_uri'], 'GTIFF', shore_nodata, gdal.GDT_Float64)
#    shore_raster = gdal.Open(args['shore_profile_uri'], gdal.GA_Update)
#    shore_band = shore_raster.GetRasterBand(1)
#    shore_profile = shore_band.ReadAsArray()
#
#    print('past shore')

    # Landmass
    landmass_raster = gdal.Open(args['landmass_raster_uri'])
    message = 'Cannot open file ' + args['landmass_raster_uri']
    assert landmass_raster is not None, message
    fine_geotransform = landmass_raster.GetGeoTransform()
    landmass_band = landmass_raster.GetRasterBand(1)
    landmass = landmass_band.ReadAsArray()
    
    print('past landmass')

    # AOI
    aoi_raster = gdal.Open(args['aoi_raster_uri'])
    message = 'Cannot open file ' + args['aoi_raster_uri']
    assert aoi_raster is not None, message
    aoi_band = aoi_raster.GetRasterBand(1)
    
    print('past AOI')

    # Bathymetry
    raster = gdal.Open(args['bathymetry_raster_uri'])
    message = 'Cannot open file ' + args['bathymetry_raster_uri']
    assert raster is not None, message
    band = raster.GetRasterBand(1)
    bathymetry = band.ReadAsArray()
    band = None
    raster = None

    row_count = landmass_band.YSize 
    col_count = landmass_band.XSize

    print('past bathymetry')

   # Get the fine and coarse raster cell sizes, making sure the signs are consistent
    i_side_fine = int(round(fine_geotransform[1]))
    j_side_fine = int(round(fine_geotransform[5]))
    i_side_coarse = int(math.copysign(args['transect_spacing'], i_side_fine))
    j_side_coarse = int(math.copysign(args['transect_spacing'], j_side_fine))

    # Start and stop coordinates in meters
    i_start = int(round(fine_geotransform[3]))
    j_start = int(round(fine_geotransform[0]))
    i_end = int(round(i_start + i_side_fine * row_count))
    j_end = int(round(j_start + j_side_fine * col_count))
    
    # Size of a tile. The + 4 at the end ensure the tiles overlap, 
    # leaving no gap in the shoreline
    i_offset = i_side_coarse/i_side_fine + 4
    j_offset = j_side_coarse/j_side_fine + 4
    mask = np.ones((i_offset, j_offset))
    tile_size = np.sum(mask)

    tiles = 0 # Number of valid tiles

    # Caching transect information for faster raster information processing:
    # Each entry is a dictionary with the following information:
    #   'raw_positions': numpy array
    #   'clip_limits': tuple (first, last)
    transect_info = []
    max_transect_length = 0

    # Going through the bathymetry raster tile-by-tile.
    for i in range(i_start, i_end, i_side_coarse):
        LOGGER.debug(' Detecting shore along line ' + \
            str((i_end - i)/i_side_coarse))

        # Top of the current tile
        i_base = max((i - i_start) / i_side_fine - 2, 0)

        for j in range(j_start, j_end, j_side_coarse):
            # Left coordinate of the current tile
            j_base = max((j - j_start) / j_side_fine - 2, 0)

            # Data under the tile
            #data = aoi[i_base:i_base+i_offset, j_base:j_base+j_offset]
            data = aoi_band.ReadAsArray(i_base, j_base, i_offset, j_offset)

            # Avoid nodata on tile
            if np.sum(data) == tile_size:

                # Look for landmass cover on tile
                #tile = landmass[i_base:i_base+i_offset, :j_base+j_offset]
                tile = landmass_band.ReadAsArray(i_base, j_base, i_offset, j_offset)
                land = np.sum(tile)

                # If land and sea, we have a shore: detect it and store
                if land and land < tile_size:
                    shore_patch = detect_shore(tile, mask, 0, connectedness = 4)
                    shore_pts = np.where(shore_patch == 1)
                    if shore_pts[0].size:

                        # Store shore position
#                        transects[(shore_pts[0] + i_base, shore_pts[1] + j_base)] = -1

                        # Estimate shore orientation
                        shore_orientations = \
                            compute_shore_orientation(shore_patch, \
                                shore_pts, i_base, j_base)
                          
                        # Skip if no shore orientation
                        if not shore_orientations:
                            continue

                        # Pick transect position among valid shore points
                        assert len(shore_pts) == 2, str((i, j)) + ' ' + str(shore_pts)
                        transect_position = select_transect(shore_orientations.keys())
                        
                        # Skip tile if no valid shore points
                        if not transect_position:
                            continue

                        # Store every transect position at this point 
                        # so we know what transects are discarded later on
                        #transects[transect_position] = 50

                        # Compute transect orientation
                        transect_orientation = \
                            compute_transect_orientation(transect_position, \
                                shore_orientations[transect_position],landmass)

                        # Skip tile if can't compute valid orientation
                        if transect_orientation is None:
                            continue

                        # Compute raw transect depths
                        raw_depths, raw_positions = \
                            compute_raw_transect_depths(transect_position, \
                            transect_orientation, bathymetry, \
                            landmass, i_side_fine, \
                            args['max_land_profile_len'], \
                            args['max_land_profile_height'], \
                            args['max_profile_length'])

                        # Interpolate transect to the model resolution
                        interpolated_depths = raw_depths
#                        interpolated_depths = \
#                            interpolate_transect(raw_depths, i_side_fine, \
#                                args['model_resolution'])

                        # Not enough values for interpolation
                        if interpolated_depths is None:
                            continue

                        # Smooth transect
                        smoothed_depths = \
                            smooth_transect(interpolated_depths, \
                                args['smoothing_percentage'])

                        # Clip transect
#                        print('size before', smoothed_depths.size)
                        (clipped_transect, (start, shore, end)) = \
                            clip_transect(smoothed_depths)
#                        print('size after', clipped_transect.size)

                        # Transect could be invalid, skip it
                        if clipped_transect is None:
                            continue
                       
                        # At this point, the transect is valid: 
                        # extract remaining information about it
                        transect_info.append( \
                            {'raw_positions':raw_positions, \
                            'clip_limits':(start, shore, end)})

                        # Update the logest transect length if necessary
                        if (end - start) > max_transect_length:
                            max_transect_length = end - start
                        
                        # Store transect information
#                        transects[transect_position] = tiles
                        #position1 = \
                        #    (transect_position + \
                        #        transect_orientation).astype(int)
                        #position3 = \
                        #    (transect_position + \
                        #        transect_orientation * 3).astype(int)
                        #transects[position1[0], position1[1]] = 6
                        #transects[position3[0], position3[1]] = 8
                        #transects[raw_positions] = 100 + tiles #raw_depths
#                        transects[(raw_positions[0][start:end], raw_positions[1][start:end])] = \
#                            tiles #raw_depths

                        ## Will reconstruct the shore from this information
                        #shore_profile[raw_positions] = raw_depths
                        
                        tiles += 1

    # Cleanup
    landmass = None
    aoi_band = None
    aoi_raster = None
    landmass_band = None
    landmass_raster = None

    

    LOGGER.debug('found %i tiles.' % tiles)

    print('transect_info size', len(transect_info))

    # Create a numpy array to store the habitat type
    field_count = args['maximum_field_count']
    transect_count = tiles

    habitat_type_array = np.ones((tiles, max_transect_length)) * -99999.0
    habitat_properties_array = \
        np.ones((tiles, field_count, max_transect_length)) * -99999.0

    # Creating HDF5 file that will store the transect data
    habitat_type_uri = \
        os.path.join(args['intermediate_dir'], 'habitat_type.h5')
    habitat_properties_uri = \
        os.path.join(args['intermediate_dir'], 'habitat_properties.h5')

    habitat_type_file = h5.File(habitat_type_uri, 'w')
    habitat_type_dataset = \
        habitat_type_file.create_dataset('habitat_types', \
            habitat_type_array.shape, compression = 'gzip', \
            fillvalue = -99999.0)

    habitat_properties_file = h5.File(habitat_properties_uri, 'w')
    habitat_properties_dataset = \
        habitat_properties_file.create_dataset('habitat_properties', \
            habitat_properties_array.shape, compression = 'gzip', \
            fillvalue = -99999.0)


    # HDF5 file container
    hdf5_files = {}

    # Iterate through shapefile types
    transect_range = range(2)

    for shp_type in args['shapefiles']:

        hdf5_files[shp_type] = []

        for shp_name in args['shapefiles'][shp_type]:

            # Get rid of the path and the extension
            basename = os.path.splitext(os.path.basename( \
                args['shapefiles'][shp_type][shp_name]['type']))[0]

            # Extract the type for this shapefile
            type_shapefile_uri = args['shapefiles'][shp_type][shp_name]['type']

            source_nodata = raster_utils.get_nodata_from_uri(type_shapefile_uri)
            raster = gdal.Open(type_shapefile_uri)
            band = raster.GetRasterBand(1)
            array = band.ReadAsArray()

            LOGGER.info('Extracting priority information from ' + basename)
            
            mask = None
            progress_step = tiles / 50
            for transect in range(tiles):
                if transect % progress_step == 0:
                    print '.',

                raw_positions = transect_info[transect]['raw_positions']
#                print('raw_positions', raw_positions[0].size)
                
                source = array[raw_positions]

                start = transect_info[transect]['clip_limits'][0]
                shore = transect_info[transect]['clip_limits'][1]
                end = transect_info[transect]['clip_limits'][2]

                destination = habitat_type_array[transect,:end-start]

#                source = interpolate_transect(source, i_side_fine, \
#                    args['model_resolution'], kind = 'nearest')
                source = source[start:end,]

#                source = \
#                    apply_habitat_constraints(source, args['habitat_information'])
#                sys.exit(0)
                
                # Compute the mask that will be used to update the values
                mask = destination < source
#                print('mask size', np.sum(mask.astype(int)))
                #if transect in transect_range:
                #    print('transect', transect)
                #    print('start, shore, end', (start, shore, end))
                #    print('source', source)
                #    print('mask', mask)
                #    print('destination', destination)

                # Save transect to file
                destination[mask] = source[mask]

                #if transect in transect_range:
                #    print('new destination', destination)
                #    print ''

                clipped_positions = \
                    (raw_positions[0][start:end], raw_positions[1][start:end])
#                print('clipped_positions', clipped_positions[0].size)

                masked_positions = \
                    (clipped_positions[0][mask], clipped_positions[1][mask])
#                print('masked_positions', masked_positions[0].size)

                nodata_mask = destination == source_nodata

                nodata_positions = (raw_positions[0][nodata_mask], \
                    raw_positions[1][nodata_mask])

                
#                transects[masked_positions] = source[mask]
#                transects[nodata_positions] = 0
#                transects[(raw_positions[0][shore], \
#                    raw_positions[1][shore])] = transect

#                print('')
#                sys.exit(0)
            print('')

            # Clean up
            band = None
            raster = None
            array = None


#            for field in args['shapefiles'][shp_type][shp_name]:
#
#                # Skip the field 'type'
#                if field.lower() == 'type':
#                    continue
#
#                # Get rid of the path and the extension
#                basename = os.path.splitext( \
#                    os.path.basename(args['shapefiles'][shp_type][shp_name][field]))[0]
#
#                # Extract data from the current raster field
#                field_id = args['field_index'][shp_type][field]
#                uri = args['shapefiles'][shp_type][shp_name][field]
#                raster = gdal.Open(uri)
#                band = raster.GetRasterBand(1)
#                array = band.ReadAsArray()
#
#                LOGGER.info('Extracting transect information from ' + basename)
#                
#                progress_step = tiles / 50
#                for transect in range(tiles):
#                    if transect % progress_step == 0:
#                        print '.',
#
#                    raw_positions = transect_info[transect]['raw_positions']
##                    print('raw_positions', raw_positions[0].size)
#                    
#                    source = array[raw_positions]
#
#                    start = transect_info[transect]['clip_limits'][0]
#                    shore = transect_info[transect]['clip_limits'][1]
#                    end = transect_info[transect]['clip_limits'][2]
#
#                    destination = habitat_properties_array[transect, field_id,:end-start]
#
##                    source = interpolate_transect(source, i_side_fine, \
##                        args['model_resolution'], kind = 'nearest')
#                    source = source[start:end,]
#                    
##                    if transect in transect_range:
##                        print('transect', transect)
##                        print('start, shore, end', (start, shore, end))
##                        print('source', source)
##                        print('mask', mask)
##                        print('destination', destination)
#
#                    # Save transect to file
##                    destination[mask] = source[mask]
#
##                    if transect in transect_range:
##                        print('new destination', destination)
##                        print ''
#
#                    clipped_positions = \
#                        (raw_positions[0][start:end], raw_positions[1][start:end])
##                    print('clipped_positions', clipped_positions[0].size)
#
#                    masked_positions = \
#                        (clipped_positions[0][mask], clipped_positions[1][mask])
##                    print('masked_positions', masked_positions[0].size)
#                    
##                    transects[masked_positions] = source[mask]
##                    print('')
#                print('')
#
#                # Close the raster before proceeding to the next one
#                band = None
#                raster = None
#                array = None

    # Both the habitat type and the habitat field data are complete, save them
    habitat_type_dataset[...] = habitat_type_array[...]
    habitat_properties_dataset[...] = habitat_properties_array[...]

    # Add size and model resolution to the attributes
    habitat_type_dataset.attrs.create('transect_spacing', i_side_coarse)
    habitat_type_dataset.attrs.create('model_resolution', args['model_resolution'])
    habitat_properties_dataset.attrs.create('transect_spacing', i_side_coarse)
    habitat_properties_dataset.attrs.create('model_resolution', args['model_resolution'])
    

    # Store shore information gathered during the computation
#    transect_band.WriteArray(transects)
    transect_band = None
    transect_raster = None
    raster_utils.calculate_raster_stats_uri(args['transects_uri'])


    # We're done, we close the file
    #habitat_type_dataset = None
    #habitat_properties_dataset = None
    habitat_type_file.close()
    habitat_properties_file.close()
        
    return

def apply_habitat_constraints(habitat, constraints):
    print('transect size', habitat.size)

    habitat_types = np.unique(habitat).astype(int)
    
    print('habitat types', habitat_types)

    for habitat_type in habitat_types:
        print('habitat_type', habitat_type)
        if (habitat_type >= 0) and (habitat_type < len(constraints)):
            print('constraints', constraints[habitat_type])

    return habitat


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
 
def select_transect(shore_pts):
    """Select transect postion among shore points"""
    if not len(shore_pts):
        return None
    
    # Return the transect with the smallest i first, and j second
    sorted_points = sorted(shore_pts, key = lambda p: p[1])
    sorted_points = sorted(sorted_points, key = lambda p: p[0])
    
    return sorted_points[0]

def compute_transect_orientation(position, orientation, landmass):
    """Returns transect orientation towards the ocean."""
    # orientation is perpendicular to the shore
    orientation = np.array([-orientation[1], orientation[0]]) # pi/2 rotation

    # Compute the long (l) and the short (s) axes indices
    l = 0 if abs(orientation[0]) > abs(orientation[1]) else 1
    s = 1 if abs(orientation[0]) > abs(orientation[1]) else 0

    # Normalize orientation and extend to 3 pixels to minimize roundoff
    orientation[s] = round(3 * float(orientation[s]) / orientation[l])
    orientation[l] = 3.

    # Orientation points to water: return rescaled vector
    if not landmass[position[0] +orientation[0], position[1] +orientation[1]]:
        return orientation / 3.

    # Otherwise, check the opposite direction
    else:
        orientation *= -1.
        
        # Other direction works, return rescaled orientation
        if not landmass[position[0] +orientation[0], position[1] +orientation[1]]:
            return orientation / 3.
        
        # Other direction does not work: possible overshoot, shorten vector
        else:
            # Reduce the vector length
            step = np.array([round(orientation[0]/3.), round(orientation[1]/3.)])

            # Orientation points to water: return vector as is
            if not landmass[position[0] + step[0], position[1] + step[1]]:
                return orientation
        
            # Orientation points to land: check the other direction
            else:
                step *= -1 # step in the other direction
        
                # Orientation doesn't work, return invalid transect.
                if landmass[position[0] +step[0], position[1] +step[1]]:
                    return None
        
                # Other direction worked, return orientation
                return orientation * -1


def compute_raw_transect_depths(shore_point, \
    direction_vector, bathymetry, landmass, model_resolution, \
    max_land_profile_len, max_land_profile_height, \
    max_sea_profile_len):
    """ compute the transect endpoints that will be used to cut transects"""
    # Maximum transect extents
    max_land_len = max_land_profile_len / model_resolution
    max_sea_len = 1000 * max_sea_profile_len / model_resolution

    # Limits on maximum coordinates
    bathymetry_shape = bathymetry.shape

    depths = np.ones((max_land_len + max_sea_len + 1))*-20000

    I = np.ones(depths.size) * -1
    J = np.ones(depths.size) * -1

    p_i = shore_point[0]
    p_j = shore_point[1]
    d_i = direction_vector[0]
    d_j = direction_vector[1]

    initial_elevation = bathymetry[p_i, p_j]
    depths[max_land_len] = 0

    I[max_land_len] = p_i
    J[max_land_len] = p_j


    # Compute the landward part of the transect (go backward)
    start_i = p_i - d_i
    start_j = p_j - d_j

    # If no land behind the piece of land, stop there and report 0
    if not landmass[int(round(start_i)), int(round(start_j))]:
        inland_steps = 0
    # Else, count from 1
    else:
        # Stop when maximum inland distance is reached
        for inland_steps in range(1, max_land_len):
            elevation = bathymetry[int(round(start_i)), int(round(start_j))]
            # Hit either nodata, or some bad data
            if elevation <= -12000:
                inland_steps -= 1
                break
            # Stop if shore is reached
            if not landmass[int(round(start_i)), int(round(start_j))]:
                inland_steps -= 1
                break
            # Stop at maximum elevation
            if elevation > 20:
                break
            # We can store the depth at this point
            depths[max_land_len - inland_steps] = elevation
            I[max_land_len - inland_steps] = start_i
            J[max_land_len - inland_steps] = start_j

            # Move backward (inland)
            start_i -= d_i
            start_j -= d_j

            # Stop if outside raster limits
            if (start_i < 0) or (start_j < 0) or \
                (start_i >= bathymetry_shape[0]) or (start_j >= bathymetry_shape[1]):
                break

    # Compute the seaward part of the transect
    start_i = p_i + d_i
    start_j = p_j + d_j

    # Stop when maximum offshore distance is reached
    offshore_steps = 0
    for offshore_steps in range(1, max_sea_len):
        # Stop if shore is reached
        if landmass[int(round(start_i)), int(round(start_j))]:
            offshore_steps -= 1
            break
        elevation = bathymetry[int(round(start_i)), int(round(start_j))]
        # Hit either nodata, or some bad data
        if elevation <= -12000:
            offshore_steps -= 1
            break
        # We can store the depth at this point
        depths[max_land_len + offshore_steps] = elevation
        I[max_land_len + offshore_steps] = start_i
        J[max_land_len + offshore_steps] = start_j

        # Move forward (offshore)
        start_i += d_i
        start_j += d_j

        # Stop if outside raster limits
        if (start_i < 0) or (start_j < 0) or \
            (start_i >= bathymetry_shape[0]) or (start_j >= bathymetry_shape[1]):
            break

    # If shore borders nodata, offshore_step is -1, set it to 0
    offshore_steps = max(0, offshore_steps)


    return (depths[I >= 0], (I[I >= 0].astype(int), J[J >= 0].astype(int)))


def interpolate_transect(depths, old_resolution, new_resolution, kind = 'linear'):
    """Interpolate transect at a higher resolution"""
    # Minimum entries required for interpolation
    if depths.size < 3:
        return None

    assert new_resolution < old_resolution, 'New resolution should be finer.'
    x = np.arange(0, depths.size) * old_resolution
    f = interpolate.interp1d(x, depths, kind)
    x_new = \
        np.arange(0, (depths.size-1) * old_resolution / new_resolution) * \
            new_resolution
    interpolated = f(x_new)

    return interpolated


def smooth_transect(transect, window_size_pct):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_size_pct: the dimension of the smoothing window in percent (0.0 to 100.0);

    output:
        the smoothed signal
    """

    if transect.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if (window_size_pct < 0.0) or (window_size_pct > 100.00):
        raise ValueError, "Window size percentage should be between 0.0 and 100.0"

    # Compute window length from window size percentage
    window_length = transect.size * window_size_pct / 100.0

    # Adjust window length to be an odd number
    window_length += int(int(window_length/2) * 2 == window_length)

 
    if window_length<3:
        return transect

    # Add reflected copies at each end of the signal
    s=np.r_[2*transect[0]-transect[window_length-1::-1], transect, \
        2*transect[-1]-transect[-1:-window_length:-1]]

    w=np.ones(window_length,'d')

    y=np.convolve(w/w.sum(),s,mode='same')


    return y[window_length:-window_length+1] 

def clip_transect(transect):
    """Clip transect using maximum and minimum heights"""
    # Return if transect size is 1
    if transect.size == 1:
        return (transect, (0, 0, 1))

    # Return if transect is full of zeros, otherwise break
    uniques = np.unique(transect)
    if uniques.size == 1:
        assert uniques[0] == 0.0
        return (transect, (0, 0, transect.size))

    # If higher point is negative: can't do anything
    if transect[0] < 0:
        return (None, (None, None, None))

    # Go along the transect to find the shore
    shore = 1
    while transect[shore] > 0:
        shore += 1
        # End of transect: can't find the shore (first segment in water)
        if shore == transect.size:
            return (None, (None, None, None))

    # Find water extent
    water_extent = 1
#    print('transect size', transect.size)
#    print('shore', shore)
    while transect[shore - 1 + water_extent] <= 0:
        # Stop if reached the end of the transect
        if shore + water_extent == transect.size:
            break
        # Else, proceed to the next pixel
        water_extent += 1

    # Compute the extremes on the valid portion only
    highest_point = np.argmax(transect[:shore])
    lowest_point = shore + np.argmin(transect[shore:shore + water_extent])
#    print('highest, lowest', (highest_point, lowest_point))

    assert highest_point < lowest_point

    return (transect[highest_point:lowest_point+1], (highest_point, shore, lowest_point+1))


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
#        if shore_segment_count == 0:
#            LOGGER.warning('No shore segment detected')
        return borders



