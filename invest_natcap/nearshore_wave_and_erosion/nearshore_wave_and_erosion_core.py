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
from scipy import sparse
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
    block_size = transect_band.GetBlockSize()
    transects = \
        sp.sparse.lil_matrix((transect_band.YSize, transect_band.XSize))
#    transects = transect_band.ReadAsArray()
    
    print('past transects. size', \
        (transect_band.YSize, transect_band.XSize), \
        'blocksize', block_size)
#    sys.exit(0)

    # Store transect profiles to reconstruct shore profile
    args['shore_profile_uri'] = os.path.join( \
        os.path.split(args['landmass_raster_uri'])[0], 'shore_profile.tif')
    raster_utils.new_raster_from_base_uri(args['landmass_raster_uri'], \
        args['shore_profile_uri'], 'GTIFF', shore_nodata, gdal.GDT_Float64)
    shore_raster = gdal.Open(args['shore_profile_uri'], gdal.GA_Update)
    shore_band = shore_raster.GetRasterBand(1)
    shore = \
        sp.sparse.lil_matrix((shore_band.XSize, shore_band.YSize))
#    shore_profile = shore_band.ReadAsArray()

    print('past shore')

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
    i_max_fine = (i_end - i_start) / i_side_fine
    j_max_fine = (j_end - j_start) / j_side_fine
    
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

        # Adjust offset so it doesn't get outside raster bounds
        # TODO: Allow to use fractional tile size
        if (i_base + i_offset) >= row_count:
            continue

        for j in range(j_start, j_end, j_side_coarse):
 
            # Left coordinate of the current tile
            j_base = max((j - j_start) / j_side_fine - 2, 0)

            # Adjust offset so it doesn't get outside raster bounds
            # TODO: Allow to use fractional tile size
            if (j_base + j_offset) >= col_count:
                continue

            # Data under the tile
            #data = aoi[i_base:i_base+i_offset, j_base:j_base+j_offset]

            # Look for landmass cover on tile
            #tile = landmass[i_base:i_base+i_offset, :j_base+j_offset]
            tile = landmass_band.ReadAsArray(j_base, i_base, j_offset, i_offset)
            
            land = np.sum(tile)

            # If land and sea, we have a shore: detect it and store
            if land and land < tile_size:
                shore_patch = detect_shore(tile, mask, 0, connectedness = 4)
                shore_pts = np.where(shore_patch == 1)
                if shore_pts[0].size:

                    # Store shore position
                    transects[(shore_pts[0] + i_base, shore_pts[1] + j_base)] = -1

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
                    interpolated_depths = \
                        raw_depths if raw_depths.size > 5 else None
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

                    # Clip if transect hits land
                    (clipped_transect, (start, shore, end)) = \
                        clip_transect(smoothed_depths)

                    # Transect could be invalid, skip it
                    if clipped_transect is None:
                        continue
                   
                    # At this point, the transect is valid: 
                    # extract remaining information about it
                    transect_info.append( \
                        {'raw_positions': \
                            (raw_positions[0][start:end], \
                            raw_positions[1][start:end]), \
                        'depths':smoothed_depths[start:end], \
                        'clip_limits':(0, shore-start, end-start)})

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

    habitat_nodata = -99999

    print('transect_info size', len(transect_info))

    # Create a numpy array to store the habitat type
    field_count = args['maximum_field_count']
    transect_count = tiles

    # Creating HDF5 file that will store the transect data
    transect_data_uri = \
        os.path.join(args['intermediate_dir'], 'transect_data.h5')
    
    transect_data_file = h5.File(transect_data_uri, 'w')
    


    habitat_type_dataset = \
        transect_data_file.create_dataset('habitat_types', \
            (transect_count, max_transect_length), \
            compression = 'gzip', fillvalue = habitat_nodata)
    
    habitat_properties_dataset = \
        transect_data_file.create_dataset('habitat_properties', \
            (transect_count, field_count, max_transect_length), \
            compression = 'gzip', fillvalue = habitat_nodata)

    bathymetry_dataset = \
        transect_data_file.create_dataset('bathymetry', \
            (tiles, max_transect_length), \
            compression = 'gzip', fillvalue = habitat_nodata)
    
    positions_dataset = \
        transect_data_file.create_dataset('ij_positions', \
            (tiles, 2, max_transect_length), \
            compression = 'gzip', fillvalue = habitat_nodata)
    
    shore_dataset = \
        transect_data_file.create_dataset('shore_index', \
            (tiles, 1), \
            compression = 'gzip', fillvalue = habitat_nodata)

    climatic_forcing_dataset = \
        transect_data_file.create_dataset('climatic_forcing', \
            (tiles, 4), \
            compression = 'gzip', fillvalue = habitat_nodata)

    limits_group = transect_data_file.create_group('limits')

    indices_limit_dataset = \
        limits_group.create_dataset('indices', \
            (tiles, 2), \
            compression = 'gzip', fillvalue = habitat_nodata)

    coordinates_limits_dataset = \
        limits_group.create_dataset('ij_coordinates', \
            (tiles, 4), \
            compression = 'gzip', fillvalue = habitat_nodata)



    habitat_type_array = \
        np.ones(habitat_type_dataset.shape).astype(int) * habitat_nodata

    habitat_properties_array = \
        np.ones(habitat_properties_dataset.shape) * habitat_nodata

    bathymetry_array = \
        np.ones(bathymetry_dataset.shape) * habitat_nodata

    positions_array = \
        np.ones(positions_dataset.shape).astype(int) * habitat_nodata

    shore_array = \
        np.ones(shore_dataset.shape).astype(int) * habitat_nodata

    climatic_forcing_array = \
        np.ones(climatic_forcing_dataset.shape) * habitat_nodata

    indices_limit_array = \
        np.ones(indices_limit_dataset.shape).astype(int) * habitat_nodata

    coordinates_limits_array = \
        np.ones(coordinates_limits_dataset.shape) * habitat_nodata



    for transect in range(transect_count):
        (start, shore, end) = transect_info[transect]['clip_limits']

        bathymetry_array[transect, start:end] = \
            transect_info[transect]['depths'][start:end]

        positions_array[transect, 0, start:end] = \
            transect_info[transect]['raw_positions'][0][start:end]

        positions_array[transect, 1, start:end] = \
            transect_info[transect]['raw_positions'][1][start:end]

        indices_limit_array[transect] = [start, end]

        shore_array[transect] = shore

        coordinates_limits_array[transect] = [ \
            transect_info[transect]['raw_positions'][0][start], \
            transect_info[transect]['raw_positions'][1][start], \
            transect_info[transect]['raw_positions'][0][end-1], \
            transect_info[transect]['raw_positions'][1][end-1], \
            ]

        transect_info[transect] = None



    # HDF5 file container
    hdf5_files = {}

    # Iterate through shapefile types
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
            mask_dict = {}

            progress_step = tiles / 50
            for transect in range(tiles):
                if transect % progress_step == 0:
                    print '.',

                [start, end] = indices_limit_array[transect]

                shore = shore_array[transect]

                #raw_positions = transect_info[transect]['raw_positions']
                raw_positions = \
                    (positions_array[transect, 0, start:end], \
                    positions_array[transect, 1, start:end])
                
                # Load the habitat type buffer
                destination = habitat_type_array[transect,:end-start]

                #Load the habitats as sampled from the raster
                source = array[raw_positions]

                # Interpolate the data to the model resolution 
#                source = interpolate_transect(source, i_side_fine, \
#                    args['model_resolution'], kind = 'nearest')

                source = source[start:end,]

                # Apply the habitat constraints
#                source = \
#                    apply_habitat_constraints(source, args['habitat_information'])
#                sys.exit(0)
                
                # Compute the mask that will be used to update the values
                mask = destination < source

                mask_dict[transect] = mask

                # Update habitat_types with new type of higher priority
                destination[mask] = source[mask]

                # Transect values without nodata
                clipped_positions = \
                    (raw_positions[0][start:end], raw_positions[1][start:end])

                # Transect values to update
                masked_positions = \
                    (clipped_positions[0][mask], clipped_positions[1][mask])

                # If source nodata ended up in destination, find it
                source_nodata_mask = destination == source_nodata

                # Remove source nodata
                destination[source_nodata_mask] = habitat_nodata

                # Find where source nodata is in the raster
                source_nodata_coordinates = \
                    (raw_positions[0][source_nodata_mask], \
                    raw_positions[1][source_nodata_mask])

                # Update the values using source
                transects[masked_positions] = source[mask]
                # Update nodata appropriately
                transects[source_nodata_coordinates] = -2
                # Leave the transect ID on the transect's shore
                transects[(raw_positions[0][shore], \
                    raw_positions[1][shore])] = transect

            print('')

            # Clean up
            band = None
            raster = None
            array = None


            for field in args['shapefiles'][shp_type][shp_name]:

                # Skip the field 'type'
                if field.lower() == 'type':
                    continue

                # Get rid of the path and the extension
                basename = os.path.splitext( \
                    os.path.basename(args['shapefiles'][shp_type][shp_name][field]))[0]

                # Extract data from the current raster field
                field_id = args['field_index'][shp_type][field]
                uri = args['shapefiles'][shp_type][shp_name][field]
                raster = gdal.Open(uri)
                band = raster.GetRasterBand(1)
                array = band.ReadAsArray()

                LOGGER.info('Extracting transect information from ' + basename)
                
                progress_step = tiles / 50
                for transect in range(tiles):
                    if transect % progress_step == 0:
                        print '.',

                    [start, end] = indices_limit_array[transect]

                    shore = shore_array[transect]

                    raw_positions = \
                        (positions_array[transect, 0, start:end], \
                        positions_array[transect, 1, start:end])


                    source = array[raw_positions]

                    destination = \
                        habitat_properties_array[transect, field_id, start:end]

                    # Save transect to file
                    mask = mask_dict[transect]

                    destination[mask] = source[mask]

                    clipped_positions = \
                        (raw_positions[0][start:end], raw_positions[1][start:end])

                    masked_positions = \
                        (clipped_positions[0][mask], clipped_positions[1][mask])
                    
                    transects[masked_positions] = source[mask]
                print('')

                # Close the raster before proceeding to the next one
                band = None
                raster = None
                array = None

    # Both the habitat type and the habitat field data are complete, save them
    habitat_type_dataset[...] = habitat_type_array[...]
    habitat_properties_dataset[...] = habitat_properties_array[...]
    bathymetry_dataset[...] = bathymetry_array[...]
    positions_dataset[...] = positions_array[...]
    indices_limit_dataset[...] = indices_limit_array[...]
    coordinates_limits_dataset[...] = coordinates_limits_array[...]
    shore_dataset[...] = shore_array[...]

    # Add size and model resolution to the attributes
    habitat_type_dataset.attrs.create('transect_spacing', i_side_coarse)
    habitat_type_dataset.attrs.create('model_resolution', args['model_resolution'])
    

    # Store shore information gathered during the computation
    LOGGER.info('Storing transect information...')
    n_rows = transect_band.YSize
    n_cols = transect_band.XSize

    cols_per_block, rows_per_block = block_size[0], block_size[1]
    n_col_blocks = int(math.ceil(n_cols / float(cols_per_block)))
    n_row_blocks = int(math.ceil(n_rows / float(rows_per_block)))

    dataset_buffer = np.zeros((rows_per_block, cols_per_block))

    # Compute data for progress bar
    block_count = n_row_blocks * n_col_blocks
    progress_step = block_count / 50
    processed_blocks = 0

    for row_block_index in xrange(n_row_blocks):
        row_offset = row_block_index * rows_per_block
        row_block_width = n_rows - row_offset
        if row_block_width > rows_per_block:
            row_block_width = rows_per_block

        for col_block_index in xrange(n_col_blocks):
            col_offset = col_block_index * cols_per_block
            col_block_width = n_cols - col_offset
            if col_block_width > cols_per_block:
                col_block_width = cols_per_block

            # Show progress bar
            if processed_blocks % progress_step == 0:
                print '.',

            # Load data from the dataset
            transect_band.ReadAsArray(
                xoff=col_offset, yoff=row_offset, 
                win_xsize=col_block_width,
                win_ysize=row_block_width, 
                buf_obj=dataset_buffer[0:row_block_width,0:col_block_width])
                
            dataset_block = dataset_buffer[ \
                0:row_block_width, \
                0:col_block_width]
            
            # Load data from the sparse matrix
            matrix_block = transects[ \
                row_offset:row_offset+row_block_width, \
                col_offset:col_offset+col_block_width].todense()

            # Write sparse matrix contents over the dataset
            mask = np.where(matrix_block != 0)

            dataset_block[mask] = matrix_block[mask]

            transect_band.WriteArray(
                dataset_block[0:row_block_width, 0:col_block_width],
                xoff=col_offset, yoff=row_offset)

            processed_blocks += 1

    #Making sure the band and dataset is flushed and not in memory before
    #adding stats
    transect_band.FlushCache()
    transect_band = None
    transect_raster.FlushCache()
    gdal.Dataset.__swig_destroy__(transect_raster)
    transect_raster = None
    raster_utils.calculate_raster_stats_uri(args['transects_uri'])


    # We're done, we close the file
    #habitat_type_dataset = None
    #habitat_properties_dataset = None
    transect_data_file.close()
        
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
    # Transect has to have a minimum size
    if transect.size < 5:
         return (None, (None, None, None))

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



