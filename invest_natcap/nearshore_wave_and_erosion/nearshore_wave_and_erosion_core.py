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
import h5py

from osgeo import ogr
from osgeo import gdal

import cProfile, pstats

from invest_natcap import raster_utils
import nearshore_wave_and_erosion_core as core

from NearshoreWaveFunctions_3p0 import*

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

    # Profile generator
    transect_data_uri = compute_transects(args)
#    transect_data_uri = \
#        os.path.join(args['intermediate_dir'], 'transect_data.h5')

    # Stop there if the user only wants to run the profile generator 
    if args['modules_to_run'] == 'Profile generator only':
        return

    # Nearshore wave and erosion model
    biophysical_data_uri = \
        compute_nearshore_and_wave_erosion(transect_data_uri, args)
#    biophysical_data_uri = \
#        os.path.join(args['intermediate_dir'], 'output.h5')

    # Reconstruct 2D shore maps from biophysical data 
    reconstruct_2D_shore_map(args, transect_data_uri, biophysical_data_uri)

    # Debug purposes
#    p = cProfile.Profile()
#    transects_uri = p.runctx('compute_transects(args)', globals(), locals())
#    transects_uri = p.runctx('compute_transects(args)', globals(), locals())
#    s = pstats.Stats(p)
#    s.sort_stats('time').print_stats(20)


# Compute the shore transects
def compute_transects(args):
    LOGGER.debug('Computing transects...')

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
    
#    print('past transects. size', \
#        (transect_band.YSize, transect_band.XSize), \
#        'blocksize', block_size)

    # Store transect profiles to reconstruct shore profile
    args['shore_profile_uri'] = os.path.join( \
        os.path.split(args['landmass_raster_uri'])[0], 'shore_profile.tif')
    raster_utils.new_raster_from_base_uri(args['landmass_raster_uri'], \
        args['shore_profile_uri'], 'GTIFF', shore_nodata, gdal.GDT_Float64)
    shore_raster = gdal.Open(args['shore_profile_uri'], gdal.GA_Update)
    shore_band = shore_raster.GetRasterBand(1)
    shore = \
        sp.sparse.lil_matrix((shore_band.XSize, shore_band.YSize))

    # Landmass
    landmass = raster_utils.load_memory_mapped_array( \
        args['landmass_raster_uri'], raster_utils.temporary_filename())
    
    landmass_raster = gdal.Open(args['landmass_raster_uri'])
    message = 'Cannot open file ' + args['landmass_raster_uri']
    assert landmass_raster is not None, message
    fine_geotransform = landmass_raster.GetGeoTransform()
    landmass_band = landmass_raster.GetRasterBand(1)

    # AOI
    aoi_raster = gdal.Open(args['aoi_raster_uri'])
    message = 'Cannot open file ' + args['aoi_raster_uri']
    assert aoi_raster is not None, message
    aoi_band = aoi_raster.GetRasterBand(1)
    
    # Bathymetry
    bathymetry = raster_utils.load_memory_mapped_array( \
        args['bathymetry_raster_uri'], raster_utils.temporary_filename())

    raster = gdal.Open(args['bathymetry_raster_uri'])
    message = 'Cannot open file ' + args['bathymetry_raster_uri']
    assert raster is not None, message
    band = raster.GetRasterBand(1)
    band = None
    raster = None

    row_count = landmass_band.YSize 
    col_count = landmass_band.XSize

   # Get the fine and coarse raster cell sizes, ensure consistent signs
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
    
    # Size of a tile. The + 6 at the end ensure the tiles overlap, 
    # leaving no gap in the shoreline, and allows a buffer big enough for
    # computing shore orientation
    i_offset = i_side_coarse/i_side_fine + 6
    j_offset = j_side_coarse/j_side_fine + 6
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
        i_base = max((i - i_start) / i_side_fine - 3, 0)

        # Adjust offset so it doesn't get outside raster bounds
        # TODO: Allow to use fractional tile size
        if (i_base + i_offset) >= row_count:
            continue

        for j in range(j_start, j_end, j_side_coarse):
 
            # Left coordinate of the current tile
            j_base = max((j - j_start) / j_side_fine - 3, 0)

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

                    # The index positions might be outside of valid bathymetry
                    if raw_depths is None:
                        continue

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

                    # Update the longest transect length if necessary
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
    bathymetry = None
    landmass = None
    aoi_band = None
    aoi_raster = None
    landmass_band = None
    landmass_raster = None

    transect_count = tiles

#    transect_count = 50
#    tiles = 50
    
    args['tiles'] = tiles
    args['max_transect_length'] = max_transect_length

    LOGGER.debug('found %i tiles.' % tiles)

    habitat_nodata = -99999

    # Create a numpy array to store the habitat type
    habitat_field_count = args['habitat_field_count']
    soil_field_count = args['soil_field_count']
    climatic_forcing_field_count = args['climatic_forcing_field_count']
    tidal_forcing_field_count = args['tidal_forcing_field_count']

    # Creating HDF5 file that will store the transect data
    transect_data_uri = \
        os.path.join(args['intermediate_dir'], 'transect_data.h5')
    
    LOGGER.debug('Creating HDF5 file %s.' % transect_data_uri)

    transect_data_file = h5py.File(transect_data_uri, 'w')
    

    climatic_forcing_dataset = \
        transect_data_file.create_dataset('climatic_forcing', \
            (transect_count, climatic_forcing_field_count), \
            compression = 'gzip', fillvalue = 0)

    soil_type_dataset = \
        transect_data_file.create_dataset('soil_type', \
            (transect_count, max_transect_length), \
            compression = 'gzip', fillvalue = 0, \
            dtype = 'i4')

    soil_properties_dataset = \
        transect_data_file.create_dataset('soil_properties', \
            (transect_count, soil_field_count, max_transect_length), \
            compression = 'gzip', fillvalue = habitat_nodata)

    bathymetry_dataset = \
        transect_data_file.create_dataset('bathymetry', \
            (tiles, max_transect_length), \
            compression = 'gzip', fillvalue = habitat_nodata)
    
    positions_dataset = \
        transect_data_file.create_dataset('ij_positions', \
            (tiles, 2, max_transect_length), \
            compression = 'gzip', fillvalue = habitat_nodata, \
            dtype = 'i4')
    
    shore_dataset = \
        transect_data_file.create_dataset('shore_index', \
            (tiles, 1), \
            compression = 'gzip', fillvalue = habitat_nodata, \
            dtype = 'i4')

    limits_group = transect_data_file.create_group('limits')

    indices_limit_dataset = \
        limits_group.create_dataset('indices', \
            (tiles, 2), \
            compression = 'gzip', fillvalue = habitat_nodata, \
            dtype = 'i4')

    coordinates_limits_dataset = \
        limits_group.create_dataset('ij_coordinates', \
            (tiles, 4), \
            compression = 'gzip', fillvalue = habitat_nodata, \
            dtype = 'i4')

    mask_dataset = transect_data_file.create_dataset('mask', \
            (args['tiles'], args['max_transect_length']), \
            compression = 'gzip', fillvalue = False, dtype = 'b')

    # TODO: Break this up so we don't use so much memory
    # On a second thought, this might be the best option: the model
    # can run optimally with enough memory, or use the HD otherwise...
    LOGGER.debug('Creating arrays')

    climatic_forcing_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'float32', \
            mode='w+', shape=climatic_forcing_dataset.shape)
#        np.ones(climatic_forcing_dataset.shape) * habitat_nodata

    print('2')

    soil_type_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'float32', \
            mode='w+', shape=soil_type_dataset.shape)
#        np.ones(soil_type_dataset.shape).astype(int) * habitat_nodata

    print('3')

    soil_properties_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'float32', \
            mode='w+', shape=soil_properties_dataset.shape)
#        np.ones(soil_properties_dataset.shape) * habitat_nodata

    print('6')

    bathymetry_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'float32', \
            mode='w+', shape=bathymetry_dataset.shape)
#        np.ones(bathymetry_dataset.shape) * habitat_nodata

    print('7')

    positions_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'int32', \
            mode='w+', shape=positions_dataset.shape)
#        np.ones(positions_dataset.shape).astype(int) * habitat_nodata

    print('8')

    shore_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'float32', \
            mode='w+', shape=shore_dataset.shape)
#        np.ones(shore_dataset.shape).astype(int) * habitat_nodata

    print('9')

    indices_limit_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'int32', \
            mode='w+', shape=indices_limit_dataset.shape)
#        np.ones(indices_limit_dataset.shape).astype(int) * habitat_nodata

    print('10')

    coordinates_limits_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'int32', \
            mode='w+', shape=coordinates_limits_dataset.shape)
#        np.ones(coordinates_limits_dataset.shape) * habitat_nodata


    args['climatic_forcing_array'] = climatic_forcing_array
    args['soil_type_array'] = soil_type_array
    args['soil_properties_array'] = soil_properties_array
    args['bathymetry_array'] = bathymetry_array
    args['positions_array'] = positions_array
    args['shore_array'] = shore_array
    args['indices_limit_array'] = indices_limit_array
    args['coordinates_limits_array'] = coordinates_limits_array


    LOGGER.debug('Storing transect_info data')

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

    bathymetry_dataset[...] = bathymetry_array[...]
    positions_dataset[...] = positions_array[...]
    indices_limit_dataset[...] = indices_limit_array[...]
    shore_dataset[...] = shore_array[...]
    coordinates_limits_dataset[...] = coordinates_limits_array[...]


#    for category in args['shapefiles']:
#        print('')
#        print 'HDF5 category', category,
#        
#        for filename in args['shapefiles'][category]:
#            print('filename', filename, 'fields:', \
#                args['shapefiles'][category][filename].keys())


    # HDF5 file container
    args['hdf5_files'] = {}
    args['habitat_nodata'] = habitat_nodata


    combine_natural_habitats(args, transect_data_file)
    combine_soil_types(args, transect_data_file)
    store_climatic_forcing(args)
    store_tidal_information(args, transect_data_file)

    # Both the habitat type and the habitat field data are complete, save them
    climatic_forcing_dataset[...] = climatic_forcing_array[...]
    soil_type_dataset[...] = soil_type_array[...]
    soil_properties_dataset[...] = soil_properties_array[...]
    habitat_type_dataset[...] = habitat_type_array[...]
    habitat_properties_dataset[...] = habitat_properties_array[...]

    # Add size and model resolution to the attributes
    habitat_type_dataset.attrs.create('transect_spacing', i_side_coarse)
    habitat_type_dataset.attrs.create('model_resolution', args['model_resolution'])
    habitat_type_dataset.attrs.create('bathymetry_resolution', i_side_fine)
    

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

    return transect_data_uri
    




# ----------------------------------------------
# Nearshore wave and erosion model
# ----------------------------------------------
def compute_nearshore_and_wave_erosion(transect_data_uri, args):
    LOGGER.debug('Computing nearshore wave and erosion...')

    print('Loading HDF5 files...')

    assert os.path.isfile(transect_data_uri)

    f = h5py.File(transect_data_uri) # Open the HDF5 file

    # Average spatial resolution of all transects
    transect_spacing = f['habitat_type'].attrs['transect_spacing']
    # Distance between transect samples
    model_resolution = f['habitat_type'].attrs['model_resolution']

    print('average space between transects:', transect_spacing, 'm')
    print('model resolution:', model_resolution, 'm')

    # ------------------------------------------------
    # Define file contents
    # ------------------------------------------------
    # Values on the transects are that of the closest shapefile point feature

    #--Climatic forcing
    # 5 Fields: Surge, WindSpeed, WavePeriod, WaveHeight
    # Matrix format: transect_count x 5 x max_transect_length  
    climatic_forcing_dataset = f['climatic_forcing']

    #--Soil type
    #mud=0, sand=1, gravel=2, unknown=-1
    # Matrix size: transect_count x max_transect_length
    soil_types_dataset = f['soil_type']

    #--Soil properties:
    # 0-mud: DryDensty, ErosionCst
    # 1-sand: SedSize, DuneHeight, BermHeight, BermLength, ForshrSlop
    # 2-gravel: same as sand
    # Matrix size: transect_count x 5 x max_transect_length
    soil_properties_dataset = f['soil_properties']

    #--Habitat types:  !! This is different from the sheet and the content of the file. 2 is seagrass, not reef!!
    #   <0 = no habitats
    #   0 = kelp #   1 = eelgrass #   2 = underwater structure/oyster reef
    #   3 = coral reef #   4 = levee #   5 = beach #   6 = seawall
    #   7 = marsh #   8 = mangrove #   9 = terrestrial structure
    # Matrix size: transect_count x max_transect_length
    habitat_types_dataset = f['habitat_type']

    #--Habitat properties for each habitat type:
    #   <0: no data
    #   0: StemHeight=0, StemDiam=1, StemDensty=2, StemDrag=3, Type=4
    #   1: same as 1
    #   2: ShoreDist=2, Height=3, BaseWidth=4, CrestWidth=5
    #   3: FricCoverd=1, FricUncov=2, SLRKeepUp=3, DegrUncov=4
    #   4: Type=1, Height=2, SideSlope=3, OvertopLim=4
    #   5: SedSize=1, ForshrSlop=2, BermLength=3, BermHeight=4, DuneHeight=5
    #   6: same as 5
    #   7: SurfRough=1, SurRedFact=2, StemHeight=3, StemDiam=4, StemDensty=5, StemDrag=6
    #   8: a lot...
    #   9: Type=1, TransParam=2, Height=3habitat_properties_dataset = f['habitat_properties']
    habitat_properties_dataset = f['habitat_properties']

    #--Bathymetry in meters
    # Matrix size: transect_count x max_transect_length
    bathymetry_dataset = f['bathymetry']
    # row, column (I, J resp.) position of each transect point in the raster matrix when extracted as a numpy array
    # Matrix size: transect_count x 2 (1st index is I, 2nd is J) x max_transect_length

    #--Index of the datapoint that corresponds to the shore pixel
    positions_dataset = f['ij_positions']
    # Matrix size: transect_count x max_transect_length

    # Name of the "subdirectory" that contains the indices and coordinate limits described below
    shore_dataset = f['shore_index']

    # First and last indices of the valid transect points (that are not nodata)
    limit_group = f['limits']
    # First index should be 0, and second is the last index before a nodata point.
    # Matrix size: transect_count x 2 (start, end) x max_transect_length
    indices_limit_dataset = limit_group['indices']

    #--Coordinates of the first transect point (index 0, start point) and the last valid transect point (end point)
    coordinates_limits_dataset = limit_group['ij_coordinates']

    # ------------------------------------------------
    # Extract content
    # ------------------------------------------------

    #-- Climatic forcing
    #transect_count, forcing, transect_length = climatic_forcing_dataset.shape
    Ho=8;To=12;Uo=0;Surge=0; #Default inputs for now

    # 5 Fields: Surge, WindSpeed, WavePeriod, WaveHeight
    # Matrix format: transect_count x 5 x max_transect_length

    #   transect_count: number of transects
    #   max_transect_length: maximum possible length of a transect in pixels
    #   max_habitat_field_count: maximum number of fields for habitats
    #   max_soil_field_count: maximum number of fields for soil types
    transect_count, habitat_fields, transect_length = habitat_properties_dataset.shape
    transect_count, soil_fields, transect_length = soil_properties_dataset.shape

    # Creating the numpy arrays that will store all the information for a single transect
    hab_types = numpy.array(transect_length)
    hab_properties = numpy.array((habitat_fields, transect_length))
    bathymetry = numpy.array(transect_length)
    positions = numpy.array((transect_length, 2))
    soil_types = numpy.array(transect_length)
    soil_properties = numpy.array((soil_fields, transect_length))
    indices_limit = numpy.array((transect_length, 2))
    coordinates_limits = numpy.array((transect_length, 4))

#    print('Number of transects', transect_count)
#    print('Maximum number of habitat fields', habitat_fields)
#    print('Maximum number of soil fields', soil_fields)
#    print('Maximum transect length', transect_length)

    # Open field indices file, so that we can access a specific field by name
    field_indices_uri = os.path.join(args['intermediate_dir'], 'field_indices')
    field_indices = json.load(open(field_indices_uri)) # Open field indices info

    # Field indices
#    print('')
#    print('')

    for habitat_type in field_indices:
        habitat = field_indices[habitat_type]
#        print('habitat', habitat)
        #print('habitat ' + str(habitat_type) + ' has ' + \
        #      str(len(habitat['fields'])) + ' fields:')

        #for field in habitat['fields']:
        #    print('field ' + str(field) + ' is ' + str(habitat['fields'][field]))
#        print('')


    #--------------------------------------------------------------
    #Run the loop
    #--------------------------------------------------------------

    nodata = -99999.0

    #Initialize matrices
    Depth=numpy.zeros((transect_count,transect_length))+nodata
    Wave =numpy.zeros((transect_count,transect_length))+nodata
    WaterLevel=numpy.zeros((transect_count,transect_length))+nodata
    WaterLevel_NoVegetation=numpy.zeros((transect_count,transect_length))+nodata
    VeloBottom=numpy.zeros((transect_count,transect_length))+nodata
    Undertow=numpy.zeros((transect_count,transect_length))+nodata
    SedTrsprt=numpy.zeros((transect_count,transect_length))+nodata


    #Read data for each transect, one at a time
    for transect in range(2000, 2500): #transect_count):
#        print('')
        print('Computing nearshore waves and erosion on transect', transect) #transect_count - transect)

        # Extract first and last index of the valid portion of the current transect
        start = indices_limit_dataset[transect,0]   # First index is the most landward point
        end = indices_limit_dataset[transect,1] # Second index is the most seaward point
        # Note: For bad data, the most landard point could be in the ocean or the most
        #   seaward point could be on land!!!
        Length=end-start;Start=start;End=end;
#        print('index limits (start, end):', (Start, End))
        
        # Extracting the valid portion (Start:End) of habitat properties
        hab_properties = habitat_properties_dataset[transect,:,Start:End]
        # The resulting matrix is of shape transect_count x 5 x max_transect_length
        # The middle index (1) is the maximum number of habitat fields:
#        print('maximum habitat property fields:', hab_properties.shape[1])
        
        unique_types = numpy.unique(hab_types)  # Compute the unique habitats

        #Bathymetry
        bathymetry = bathymetry_dataset[transect,Start:End]
        max_depth = numpy.amax(bathymetry)
        min_depth = numpy.amin(bathymetry)
        Shore=Indexed(bathymetry,0) #locate zero
        MinDepth=Indexed(bathymetry,min_depth)
#        print('bathymetry (min, max)', (min_depth, max_depth))

        if min_depth>-1 or abs(MinDepth-Shore)<2: #If min depth is too small and there aren't enough points, we don't run
                H=num.zeros(len(bathymetry))
        else: #Run the model
            #------Read habitat
            seagrass = 2
            
            # Load the habitat types along the valid portion (Start:End) of the current transect
            hab_types = habitat_types_dataset[transect,Start:End]
            habitat_types = numpy.unique(hab_types)#Different types of habitats
            habitat_types = habitat_types[habitat_types>=0]#Remove 'nodata' where theres no habitat
            
            positions = positions_dataset[transect,Start:End]
            start = [positions[0][0]]
            start.append(positions[0][1])
            end = [positions[-1][0]]
            end.append(positions[-1][1])
            coordinates_limits = coordinates_limits_dataset[transect,:]
#            print('coord limits:', \
#                  (coordinates_limits[0], coordinates_limits[1]), \
#                  (coordinates_limits[2], coordinates_limits[3]))
        
            #--Collect vegetation properties 
            #Zero the phys. char
            RootDiam=numpy.zeros(Length);    RootHeight=numpy.zeros(Length);
            RootDens=numpy.zeros(Length);    RootCd=numpy.zeros(Length);
            TrunkDiam=numpy.zeros(Length);    TrunkHeight=numpy.zeros(Length);
            TrunkDens=numpy.zeros(Length);    TrunkCd=numpy.zeros(Length);
            CanopDiam=numpy.zeros(Length);    CanopHeight=numpy.zeros(Length);
            CanopDens=numpy.zeros(Length);    CanopCd=numpy.zeros(Length)
        
            if habitat_types.size: #If there is a habitat in the profile
                seagrass=2
                HabType=[];#Collect the names of the different habitats
                if seagrass in habitat_types:
                    HabType.append('Seagrass')
                    seagrass_location = numpy.where(hab_types == seagrass)
                
                    #Seagrass physical parameters - 'field_indices' dictionary
                    if seagrass_location[0].size:
                        Sg_diameter_id = field_indices[str(seagrass)]['fields']['stemdiam']
                        Sg_diameters = hab_properties[Sg_diameter_id][seagrass_location]
                        mean_stem_diameter = numpy.average(Sg_diameters)
#                        print('   Seagrass detected. Mean stem diameter: ' + \
#                            str(mean_stem_diameter) + ' m')
                
                        Sg_height_id = field_indices[str(seagrass)]['fields']['stemheight']
                        Sg_height = hab_properties[Sg_height_id][seagrass_location]
                        mean_stem_height = numpy.average(Sg_height)
#                        print('                                    Mean stem height: ' + \
#                            str(mean_stem_height) + ' m')
                        
                        Sg_density_id = field_indices[str(seagrass)]['fields']['stemdensty']
                        Sg_density = hab_properties[Sg_density_id][seagrass_location]
                        mean_stem_density = numpy.average(Sg_density)
#                        print('                                    Mean stem density: ' + \
#                              str(mean_stem_density) + ' #/m^2')
                        
                        Sg_drag_id = field_indices[str(seagrass)]['fields']['stemdrag']
                        Sg_drag = hab_properties[Sg_drag_id][seagrass_location]
                        mean_stem_drag = numpy.average(Sg_drag)
#                        print('                                    Mean stem drag: ' + \
#                            str(mean_stem_drag) )
                        
                        RootDiam[seagrass_location]=Sg_diameters
                        RootHeight[seagrass_location]=Sg_height
                        RootDens[seagrass_location]=Sg_density
                        RootCd[seagrass_location]=Sg_drag
                        
#                print('unique habitat types:', HabType)
                    
            #Collect reef properties
            
            #Collect Oyster Reef properties
            Oyster={}
            
            #Soil types and properties   
            soil_types = soil_types_dataset[transect,Start:End]
            soil_properties = soil_properties_dataset[transect,:,Start:End]
#            print('maximum soil property fields:', soil_properties.shape[1])
#            print('soil types', numpy.unique(soil_types)) #, soil_types)
            
            #Prepare to run the model
            dx=20;
            import CPf_SignalSmooth as SignalSmooth
            smoothing_pct=10.0
            smoothing_pct=smoothing_pct/100;
            
            #Resample the input data
            Xold=range(0,dx*len(bathymetry),dx)
            Xnew=range(0,Xold[-1]+1)
            length=len(Xnew)
            from scipy import interpolate
            fintp=interpolate.interp1d(Xold,bathymetry, kind='linear')
            bath=fintp(Xnew)
            bath_sm=SignalSmooth.smooth(bath,len(bath)*smoothing_pct,'hanning') 
            shore=Indexed(bath_sm,0) #Locate zero in the new vector
            
            fintp=interpolate.interp1d(Xold,RootDiam, kind='nearest')
            RtDiam=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,RootHeight, kind='nearest')
            RtHeight=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,RootDens, kind='nearest')
            RtDens=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,RootCd, kind='nearest')
            RtCd=fintp(Xnew)
            
            fintp=interpolate.interp1d(Xold,TrunkDiam, kind='nearest')
            TkDiam=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,TrunkHeight, kind='nearest')
            TkHeight=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,TrunkDens, kind='nearest')
            TkDens=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,TrunkCd, kind='nearest')
            TkCd=fintp(Xnew)
        
            fintp=interpolate.interp1d(Xold,CanopDiam, kind='nearest')
            CpDiam=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,CanopHeight, kind='nearest')
            CpHeight=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,CanopDens, kind='nearest')
            CpDens=fintp(Xnew)
            fintp=interpolate.interp1d(Xold,CanopCd, kind='nearest')
            CpCd=fintp(Xnew)
        
            hab_types[hab_types==nodata]=-1
            fintp=interpolate.interp1d(Xold,hab_types, kind='nearest')
            Sr=fintp(Xnew)
            
            #Check to see if we need to flip the data
            flip=0
            if bath_sm[0]>bath_sm[-1]:
                bath_sm=bath_sm[::-1];        flip=1
                RtDiam=RtDiam[::-1];        RtHeight=RtHeight[::-1]
                RtDens=RtDens[::-1];        RtCd=RtCd[::-1]
                TkDiam=TkDiam[::-1];        TkHeight=TkHeight[::-1]
                TkDens=TkDens[::-1];        TkCd=TkCd[::-1]
                CpDiam=CpDiam[::-1];        CpHeight=CpHeight[::-1]
                CpDens=CpDens[::-1];        CpCd=CpCd[::-1]
                Sr=Sr[::-1]
                
            #Store hab char. into dic
            PlantsPhysChar={};Roots={};Trunks={};Canops={}
            Roots["RootDiam"]=RtDiam;    Roots["RootHeight"]=RtHeight
            Roots["RootDens"]=RtDens;    Roots["RootCd"]=RtCd
            Trunks["TrunkDiam"]=TkDiam;    Trunks["TrunkHeight"]=TkHeight
            Trunks["TrunkDens"]=TkDens;    Trunks["TrunkCd"]=TkCd
            Canops["CanopDiam"]=CpDiam;    Canops["CanopHeight"]=CpHeight
            Canops["CanopDens"]=CpDens;    Canops["CanopCd"]=CpCd
            #Final dictionary
            PlantsPhysChar['Roots']=Roots.copy()
            PlantsPhysChar['Trunks']=Trunks.copy()
            PlantsPhysChar['Canops']=Canops.copy()
            PlantsPhysChar['Oyster']=Oyster.copy()
            
            #Define friction coeff
            #   0 = kelp #   1 = eelgrass #   2 = underwater structure/oyster reef
            #   3 = coral reef #   4 = levee #   5 = beach #   6 = seawall
            #   7 = marsh #   8 = mangrove #   9 = terrestrial structure
            Cf=numpy.zeros(length)+.01
            if flip==1:
                Cf=Cf[::-1]
                
            #Compute Wave Height        
            Xnew=num.array(Xnew)
            H,Eta,Etanv,Ubot,Ur,Kt,Ic,Hm,other=WaveRegenWindCD(Xnew,bath_sm,Surge,Ho,To,Uo,Cf,Sr,PlantsPhysChar)
        
            #Compute maximum wave height
            k,C,Cg=Fast_k(To,-bath_sm)
            Hmx=0.1*(2.0*pi/k)*tanh((-bath_sm+Surge)*k);#Max wave height - Miche criterion
        
            #Wave Breaking information
            temp,temp,xb,hb,Hb,temp,temp=Runup_ErCoral(Xnew,-bath_sm,H,Ho,H*0,H*0,To,.2,1.0/10,Sr)
            loc,Hb=FindBreaker(Xnew,-bath_sm,H,To,Sr)
            Transport=nanmean(Ic[loc:-1])
            
            #Flip the vectors back
            if flip==1:
                H=H[::-1];Eta=Eta[::-1];Etanv=Etanv[::-1];
                Ubot=Ubot[::-1];Ur=Ur[::-1];Ic=Ic[::-1]
                h=bath_sm[::-1];X=Xnew[::-1]
                
            #Interpolate back to dx and save in matrix
            lx=len(Xold)
            fintp=interpolate.interp1d(X,h, kind='linear')
            h_save=fintp(Xold)
            Depth[transect,0:lx]=h_save
            
            fintp=interpolate.interp1d(X,H, kind='linear')
            H_save=fintp(Xold)
            Wave[transect,0:lx]=H_save

            fintp=interpolate.interp1d(X,Eta, kind='linear')
            Eta_save=fintp(Xold)
            WaterLevel[transect,0:lx]=Eta_save

            fintp=interpolate.interp1d(X,Etanv, kind='linear')
            Etanv_save=fintp(Xold)
            WaterLevel_NoVegetation[transect,0:lx]=Etanv_save

            fintp=interpolate.interp1d(X,Ubot, kind='linear')
            Ubot_save=fintp(Xold)
            VeloBottom[transect,0:lx]=Ubot_save

            fintp=interpolate.interp1d(X,Ur, kind='linear')
            Ur_save=fintp(Xold)
            Undertow[transect,0:lx]=Ur_save

            fintp=interpolate.interp1d(X,Ic, kind='linear')
            Ic_save=fintp(Xold)
            SedTrsprt[transect,0:lx]=Ic_save
            
            #Compute beach erosion
            Beach=-1;Struct=-1
            if Beach==1:
                g=9.81;rho=1024.0;Gam=0.78;
                TD=Dur;Lo=g*To**2.0/(2.0*pi);
                Co=g*To/(2.0*pi);#deep water phase speed with period
                
                Rs0,Rs1,xb,hb,Hb,Etapr,Hpr=Runup_ErCoral(Xnew,-bath_sm,H,Ho,Eta,Eta,To,A,m,Sr)
                #Quick Estimate
                TS=(320.0*(Hb**(3.0/2)/(g**.5*A**3.0))/(1.0+hb/(BermH_P+DuneH_P)+(m*xb)/hb))/3600.0;#erosion response time scale ).
                BetaKD=2.0*pi*(TS/TD)
                expr="num.exp(-2.0*x/BetaKD)-num.cos(2.0*x)+(1.0/BetaKD)*num.sin(2.0*x)" # solve this numerically
                fn=eval("lambda x: "+expr)
                z=FindRootKD(fn,pi,pi/2,BetaKD) # find zero in function,initial guess from K&D
                Ro,Rinfo,m0=Erosion_Quick(Ho,To,Surge[-1]+Rs0,BermH_P,DuneH_P,BermW_P,Dur,m,A,z) #Quick estimate
                
                #Erosion using waves
                TS=(320.0*(Hb**(3.0/2)/(g**.5*A**3.0))/(1.0+hb/(BermH_P+DuneH_P)+(m*xb)/hb))/3600.0;#erosion response time scale ).
                BetaKD=2.0*pi*(TS/TD)
                z=FindRootKD(fn,pi,pi/2,BetaKD) # find zero in function,initial guess from K&D
                R,Rinf,mo=ErosionFunction(A,m,xb,hb,Hb,Surge1[-1]+Rs0,BermH_P,DuneH_P,BermW_P,Dur,z)
                
                #Present
                Rsp0,Rsp1,xb1,hb1,Hb1,Etapr1,Hpr1=Runup_ErCoral(X1,-Z1,Hp,Ho,Eta0,Etap,To,A,m,Sr1)
                TS=(320.0*(Hb1**(3.0/2)/(g**.5*A**3.0))/(1.0+hb1/(BermH_P+DuneH_P)+(m*xb1)/hb1))/3600.0;#erosion response time scale ).
                BetaKD=2.0*pi*(TS/TD)
                z=FindRootKD(fn,pi,pi/2,BetaKD) # find zero in function,initial guess from K&D
                R1,Rinf1,m1=ErosionFunction(A,m,xb1,hb1,Hb1,Surge1[-1]+Rsp1,BermH_P,DuneH_P,BermW_P,Dur,z)
        
                Ro=round(Ro,2);R=round(R,2);R1=round(R1,2);
                
            #Compute mud scour
            if Beach==0:
                if Mgloc1.any(): #If there is any mangroves present at the site
                    temp1=Mgloc1[0];
                else:
                    temp1=-1
                
                Mudy1=[];#Location of the muddy bed
                if (temp1)>=0 or (temp2)>=0:
                    MudBeg=min(temp1,temp2)
                    Mudy1=arange(MudBeg,Xend1)
                    
                MErodeVol1=-1; #No mud erosion        
                if len(Mudy1)>0:#Calculate mud erosion if there's a muddy bed
                    Ubp=array(Ubp);
                    Retreat1,Trms1,Tc1,Tw1,Te=MudErosion(Ubp[Mudy1]*0,Ubp[Mudy1],-Z1[Mudy1],To,me,Cm)
                    ErodeLoc=find(Trms1>Te[0]); # indices where erosion rate greater than Threshold
                    MErodeLen1=len(ErodeLoc) # erosion rate greater than threshold at each location shoreward of the shoreline (pre-management)
                    if any(ErodeLoc)>0:
                        MErodeVol1=trapz(Retreat1[ErodeLoc]/100.0,Mudy1[ErodeLoc],1.) # volume of mud eroded shoreward of the shoreline (m^3/m)
                    else:
                        MErodeVol1=0
                    MErodeVol1=round(MErodeVol1,2)
                    gp.addmessage('MudScour_Present='+str(MErodeVol1)+' m^3/m')
        
            if Struct==1:
                #Current conditions
                Qp=150;htoe=round(-Z1[-1]+Etap[-1],1);Hwp=htoe
                while Qp>10:
                    Hwp=Hwp+.1;
                    temp,Qp,msg=SeawallOvertop(Hp[-1],To,htoe,Hwp)
                Fp=ForceSeawall(Hp[-1],To,-Z1[-1])
                Fp=round(Fp,2);Hwp=round(Hwp,2)
                gp.addmessage('Wall_Present='+str(Hwp)+' m; Force on wall='+str(Fp)+' kN/m')
        

    # Saving data in HDF5
    biophysical_data_uri = \
        os.path.join(args['intermediate_dir'], 'output.h5')

    f = h5py.File(biophysical_data_uri, 'w') # Create new HDF5 file

    # Creating the placeholders that will hold the matrices
    Depth_dataset = \
        f.create_dataset("Depth", Depth.shape, \
            compression = 'gzip', fillvalue = nodata)
    Wave_dataset = \
        f.create_dataset("Wave", Wave.shape, \
            compression = 'gzip', fillvalue = nodata)
    WaterLevel_dataset = \
        f.create_dataset("WaterLevel", WaterLevel.shape, \
            compression = 'gzip', fillvalue = nodata)
    WaterLevel_NoVegetation_dataset = \
        f.create_dataset("WaterLevel_NoVegetation", WaterLevel_NoVegetation.shape, \
            compression = 'gzip', fillvalue = nodata)
    VeloBottom_dataset = \
        f.create_dataset("VeloBottom", VeloBottom.shape, \
            compression = 'gzip', fillvalue = nodata)
    Undertow_dataset = \
        f.create_dataset("Undertow", Undertow.shape, \
            compression = 'gzip', fillvalue = nodata)
    SedTrsprt_dataset = \
        f.create_dataset("SedTrsprt", SedTrsprt.shape, \
            compression = 'gzip', fillvalue = nodata)

    # Saving the matrices on file
    Depth_dataset[...] = Depth[...]
    Wave_dataset[...] = Wave[...]
    WaterLevel_dataset[...] = WaterLevel[...]
    WaterLevel_NoVegetation_dataset[...] = WaterLevel_NoVegetation[...]
    VeloBottom_dataset[...] = VeloBottom[...]
    Undertow_dataset[...] = Undertow[...]
    SedTrsprt_dataset[...] = SedTrsprt[...]

    # Close your file at the end, or it could be invalid.
    f.close()

    return biophysical_data_uri


def reconstruct_2D_shore_map(args, transect_data_uri, biophysical_data_uri):
    LOGGER.debug('Reconstructing 2D shore maps...')
    
    transect_data = h5py.File(transect_data_uri)
    biophysical_data = h5py.File(biophysical_data_uri)

    limit_group = transect_data['limits']
    indices_limit_dataset = limit_group['indices']


    coordinates_dataset = transect_data['ij_positions']
    wave_dataset = biophysical_data['Wave']

    # Shapes should agree
    assert coordinates_dataset.shape[0] == wave_dataset.shape[0]
    assert coordinates_dataset.shape[2] == wave_dataset.shape[1]

    (transect_count, max_transect_length) = wave_dataset.shape

    
#    print('(transect_count, max_transect_length)', (transect_count, max_transect_length))

   
    wave_coordinates = np.zeros(coordinates_dataset.shape[1])
    wave_array = np.zeros(wave_dataset.shape[1])


    # Find transect intersections
    transect_footprint = set() # Stores (i, j) coord. pairs of occupied cells
    intersection = {} # Stores intersections for each transect
    intersected_transects = {} # Stores intersection information

    intersection_count = 0
    intersecting_transect_count = 0

    for transect in range(transect_count):
#        print('transect', transect_count - transect)

        # Extract and clean the transect from nan values
        start = indices_limit_dataset[transect,0]
        end = indices_limit_dataset[transect,1]

        wave_array = wave_dataset[transect,start:end]
        
        # Invalid wave data is not supposed to show up.
        invalid_data_count = np.where(wave_array == -99999.)[0].size
        if invalid_data_count:
            continue
        
        coordinates_array = coordinates_dataset[transect,start:end]

        # Clip the reansect at the first occurence of NaN
        first_nan = np.where(np.isnan(wave_array))[0]
        if first_nan.size:
            end = first_nan[0]

        # Loop throught the sample points to compute transect intersections
        for index in range(start,end):

            coord = (coordinates_array[0][index], coordinates_array[1][index])

            # If intersection: store it
            if coord in transect_footprint:
                intersection_count += 1

                # Already an intersection: append to existing list
                if coord in intersection:
                    intersection[coord].append(wave_array[index])
                    
                    if transect in intersected_transects:
                        intersected_transects[transect].append( \
                            (coord, index, wave_array[index]))
                    else:
                        intersected_transects[transect] = \
                            [(coord, index, wave_array[index])]                        
                        intersecting_transect_count += 1

                # Otherwise, create a new list
                else: 
                    intersection[coord] = [wave_array[index]]
                    intersected_transects[transect] = \
                        [(coord, index, wave_array[index])]
                    intersecting_transect_count += 1

            # No intersection here, update footprint
            else:
                transect_footprint.add(coord)

    print('Detected ' + str(intersection_count) + ' intersections in ' + \
        str(intersecting_transect_count) + ' transects.')


    # Adjust the intersecting transects so they all agree with each other
    for i in intersection:
        # Compute the mean value at the intersection
        intersection[i] = \
            sum(intersection[i]) / len(intersection[i])


    # Build mask to remove transect portions that are too far 
    # from the area we're interested in
    transect_mask = raster_utils.load_memory_mapped_array( \
        args['bathymetry_raster_uri'], raster_utils.temporary_filename())

#    bathymetry = gdal.Open(args['bathymetry_raster_uri'])
#    band = bathymetry.GetRasterBand(1)
#    transect_mask = band.ReadAsArray()

    min_bathy = -10   # Minimum interpolation depth
    max_bathy = 1  # Maximum interpolation depth

    transect_mask[transect_mask <= min_bathy] = min_bathy - 1
    transect_mask[transect_mask >= max_bathy] = min_bathy - 1

    transect_mask = transect_mask != min_bathy - 1


    # Build the interpolation structures
    X = []
    Y = []
    Z = []

    transect_footprint.clear() # used to remove coordinate duplicates

    for transect in intersected_transects:

        print('intersected transect', transect)

        current_transect = intersected_transects[transect]

        start = indices_limit_dataset[transect,0]
        end = indices_limit_dataset[transect,1]

        # Clip the reansect at the first occurence of NaN
        wave_array = wave_dataset[transect,start:end]
        first_nan = np.where(np.isnan(wave_array))[0]
        if first_nan.size:
            end = first_nan[0]

        # Interpolate delta_y: add key values for x and y
        # First value is 0 (no correction)
        delta_y = [0.]  # y
        x = [start] # x


        # Special case for first entry
        coord, index, value = current_transect[0]
        
        if index == 0:
            delta_y = [intersection[coord] - value]  # y

        for i in range(1, len(current_transect)):

            # Fill in subsequent values using intersection data
            coord, index, value = current_transect[i]

#            print('    ', i, index, value)

            delta_y.append(intersection[coord] - value)
            assert not math.isnan(delta_y[-1]), 'detected nan: ' + str(i)
            x.append(index)

        # Append last value if necessary
        if x[-1] != end-1:
            delta_y.append(0.)
            x.append(end-1)

        assert len(delta_y) == len(x), 'Arrays x and delta_y disagree in size (' + \
            str(len(x)) + ' vs ' + str(len(delta_y)) + ')'

        if len(delta_y) == 1:
            continue

        delta_y = np.array(delta_y)
        x = np.array(x)

        if np.isnan(delta_y).any():
            print('current_transect', current_transect)
            print('wave_dataset[transect,start:end]', wave_dataset[transect,start:end])
            print('delta_y', delta_y)
            print('any', np.isnan(delta_y).any(), \
                'count', np.sum(np.isnan(delta_y).any()))
            assert not np.isnan(delta_y).any()

        # Run the interpolation:
        f = interpolate.interp1d(x, delta_y, 'linear')

        interpolation_range = range(start, end)
        interpolated_delta_y = f(interpolation_range)

        if np.isnan(interpolated_delta_y).any():
            print('current_transect', current_transect)
            print('wave_dataset[transect,start:end]', wave_dataset[transect,start:end])
            print('x', x)
            print('delta_y', delta_y)
            print('interpolation_range', interpolation_range)
            print('interpolated_delta_y', interpolated_delta_y)
            print('any', np.isnan(interpolated_delta_y).any(), \
                'count', np.sum(np.isnan(interpolated_delta_y).any()))
            assert not np.isnan(interpolated_delta_y).any()

        # Compute new transect values:
        corrected_transect_values = \
            interpolated_delta_y + wave_dataset[transect,start:end]

#        print('wave_dataset[transect,start:end]', wave_dataset[transect,start:end])


        if np.isnan(corrected_transect_values).any():
            print('current_transect', current_transect)
            print('wave_dataset[transect,start:end]', wave_dataset[transect,start:end])
            print('delta_y', delta_y)
            print('interpolated_delta_y', interpolated_delta_y)
            print('corrected_transect_values', corrected_transect_values)
            print('any', np.isnan(corrected_transect_values).any(), \
                'count', np.sum(np.isnan(corrected_transect_values).any()))
            assert not np.isnan(corrected_transect_values).any()

        # Put the values in structures for 2d interpolation:
        coordinates = coordinates_dataset[transect,:]
        coordinates = (coordinates[0][start:end], coordinates[1][start:end])

#        print('start, end', start, end)
#        print('X size', X.size, 'X coordinates size', coordinates[0].size)
#        print('corrected_transect_values', corrected_transect_values.size)


        # Remove coordinate duplicates
        for index in range(coordinates[0].size):
            coord = (coordinates[0][index], coordinates[1][index])

            # Check if the point is not too far off
            if transect_mask[coord]:

                # Check if it's a new point
                if coord not in transect_footprint:
                    X.append(coordinates[0][index])
                    Y.append(coordinates[1][index])
                    assert not math.isnan(corrected_transect_values[index])
                    Z.append(corrected_transect_values[index])

                    transect_footprint.add(coord)

    X = np.array(X)
    Y = np.array(Y)
    Z = np.array(Z)

    # Now, we're ready to invoke the interpolation function
    # TODO: Fix that...
    print('Building the interpolation function for', X.size, 'points...')
    assert not np.isnan(Z).any()
    F = interpolate.interp2d(X, Y, Z, kind='linear')

    # Build the array of points onto which the function will interpolate:
    # For now, all the points with bathymetry between 1 and 10 meters:
    interp_I, interp_J = np.where(transect_mask)

    interp_I = np.unique(interp_I)
    interp_J = np.unique(interp_J)

    # Compute the actual interpolation
    print('Interpolating for', interp_I.size * interp_J.size, 'points...')
    surface = F(interp_I, interp_J)

    print('surface size:', surface.size, 'uniques', np.unique(surface).size, np.unique(surface))

    # Save the values in a raster
    wave_interpolation_uri = os.path.join(args['intermediate_dir'], \
        'wave_interpolation.tif')
    
    print('Saving data to', wave_interpolation_uri)

    bathymetry_nodata = \
        raster_utils.get_nodata_from_uri(args['bathymetry_raster_uri'])
    
    raster_utils.new_raster_from_base_uri(args['bathymetry_raster_uri'], \
        wave_interpolation_uri, 'GTIFF', bathymetry_nodata, gdal.GDT_Float64)

    wave_array = raster_utils.load_memory_mapped_array( \
        wave_interpolation_uri, raster_utils.temporary_filename())

#    wave_raster = gdal.Open(wave_interpolation_uri, gdal.GA_Update)
#    wave_band = wave_raster.GetRasterBand(1)
#    wave_array = wave_band.ReadAsArray()

    II, JJ = np.meshgrid(interp_I, interp_J)

    wave_array[(II, JJ)] = surface

    wave_array[~transect_mask] = bathymetry_nodata

    wave_array[([0], [0])] = 1.

#    wave_band.WriteArray(wave_array)

    wave_array = None
#    wave_band = None
#    wave_raster.FlushCache()
#    gdal.Dataset.__swig_destroy__(wave_raster)
#    wave_raster = None

    raster_utils.calculate_raster_stats_uri(wave_interpolation_uri)



def store_tidal_information(args, transect_data_file):

    LOGGER.info('Processing tidal information...')

    hdf5_files = args['hdf5_files']
    habitat_nodata = args['habitat_nodata']
    
    limit_group = transect_data_file['limits']
    indices_limit_dataset = limit_group['indices']
    positions_dataset = transect_data_file['ij_positions']


    # Create new category
    category = 'tidal information'


    tidal_forcing_dataset = \
        transect_data_file.create_dataset('tidal forcing', \
            (args['tiles'], args['tidal_forcing_field_count']), \
            compression = 'gzip', fillvalue = 0, \
            dtype = 'i4')


    tidal_forcing_array = \
        np.memmap(raster_utils.temporary_filename(), dtype = 'float32', \
            mode='w+', shape=tidal_forcing_dataset.shape)

    args['tidal_forcing_array'] = tidal_forcing_array
    


    hdf5_files[category] = []

    filenames = args['shapefiles'][category].keys()

    assert len(filenames) == 1, 'Detected more than one climatic forcing file'

    shp_name = filenames[0]

    for field in args['shapefiles'][category][shp_name]:

        # Retreive the index for this field
        field_id = args['field_index'][category]['fields'][field.lower()]

        # Extract the type for this shapefile
        tidal_file_uri = args['shapefiles'][category][shp_name][field]

        raster = gdal.Open(tidal_file_uri)
        band = raster.GetRasterBand(1)

        source_nodata = raster_utils.get_nodata_from_uri(tidal_file_uri)

#        array = raster_utils.load_memory_mapped_array( \
#            tidal_file_uri, raster_utils.temporary_filename())

        raster = gdal.Open(tidal_file_uri)
        band = raster.GetRasterBand(1)
        # Remove once source agrees with tidal_forcing in the assert
        array = band.ReadAsArray()

        tiles = args['tiles']
 
        progress_step = tiles / 50
        for transect in range(tiles):
            if transect % progress_step == 0:
                print '.',

#            indices_limit_array = args['indices_limit_array']
#            positions_array = args['positions_array']
#            tidal_forcing_array = args['tidal_forcing_array']

            [start, end] = indices_limit_dataset[transect]

            if end < 0:
                continue

            # The climatic data is taken as much offshore as possible
            positions = \
                (positions_dataset[transect, 0, start:end], \
                positions_dataset[transect, 1, start:end])
            
            print('start, end', start, end)
#            print 'positions',
            tidal_forcing = []
            for position in range(end-start):
#                print('position', position)
#                print '(' + str(positions[0][position]) + ', ' + \
#                    positions[1][position] + ')',
                tidal_forcing.append(
                    band.ReadAsArray(positions[1][position], \
                        positions[0][position], 1, 1)
                    )
#            print('')

#            tidal_forcing = np.array(tidal_forcing)

            source = array[positions]

            source = source[source != habitat_nodata]

            print('tidal_forcing', tidal_forcing)
#            print('positions', zip(positions[0], positions[1]))
            print('source', source)
            assert np.sum(np.absolute(source - tidal_forcing)) < 1e-15

            if source.size:
                tidal_value = np.average(source)
            else:
#                LOGGER.warning('No ' + field + ' information for transect ' + str(transect))
                tidal_value = habitat_nodata

            # Copy directly to destination
#            tidal_forcing_array[transect, field_id] = tidal_value
            tidal_forcing_dataset[transect, field_id] = tidal_value


        # Closing the raster and band before reuse
        band = None
        raster = None

#    tidal_forcing_dataset[...] = tidal_forcing_array[...]



def store_climatic_forcing(args):

    LOGGER.info('Processing climatic forcing...')
    
    hdf5_files = args['hdf5_files']
    habitat_nodata = args['habitat_nodata']

    # Create 'climatic forcing' category
    category = 'climatic forcing'

    hdf5_files[category] = []

    filenames = args['shapefiles'][category].keys()

    assert len(filenames) == 1, 'Detected more than one climatic forcing file'

    shp_name = filenames[0]

    
    for field in args['shapefiles'][category][shp_name]:

        # Retreive the index for this field
        field_id = args['field_index'][category]['fields'][field.lower()]

        # Extract the type for this shapefile
        file_uri = args['shapefiles'][category][shp_name][field]

        source_nodata = raster_utils.get_nodata_from_uri(file_uri)

        array = raster_utils.load_memory_mapped_array( \
            file_uri, raster_utils.temporary_filename())

#        raster = gdal.Open(file_uri)
#        band = raster.GetRasterBand(1)
#        array = band.ReadAsArray()

        tiles = args['tiles']

        indices_limit_array = args['indices_limit_array']
        positions_array = args['positions_array']
        climatic_forcing_array = args['climatic_forcing_array']


        progress_step = tiles / 50
        for transect in range(tiles):
            if transect % progress_step == 0:
                print '.',

            [_, end] = indices_limit_array[transect]

            # The climatic data is taken as much offshore as possible
            position = \
                (positions_array[transect, 0, end-1], \
                positions_array[transect, 1, end-1])
            
            # Copy directly to destination
            climatic_forcing_array[transect, field_id] = array[position]
        
        print('')



def combine_soil_types(args, transect_data_file):

    LOGGER.info('Processing soil types...')

    hdf5_files = args['hdf5_files']
    habitat_nodata = args['habitat_nodata']
    
    # soil types
    soil_types = { \
        'mud':0, \
        'sand':1, \
        'gravel':2 \
    }


    # List of habitats that must absolutely have mud under them
    mud_only_habitat_names = ['marsh', 'mangrove']

    # Mapping habitat names <=> habitat IDs
    habitat_name_to_ID = dict(zip( \
        [habitat[0] for habitat in args['habitat_information']], \
        range(len(args['habitat_information'])))
    )

    # IDs of habitats that must have mud under them
    mud_only_habitat_ids = \
        [habitat_name_to_ID[name] for name in mud_only_habitat_names]
    
    # Create 'soil types' category
    category = 'soil type'

    hdf5_files[category] = []
    mask_dataset = transect_data_file['mask']

    filenames = args['shapefiles'][category].keys()

    assert len(filenames) == 1, 'Detected more than one soil type file'

    shp_name = filenames[0]     

    mask = None
    mask_dict = {}

    # Assert if field 'type' doesn't exist
    field_names_lowercase = \
        [field_name.lower() for field_name in \
            args['shapefiles'][category][shp_name].keys()]

    assert 'type' in field_names_lowercase

    type_key = None
    for key in args['shapefiles'][category][shp_name].keys():
        if key.lower() == 'type':
            type_key = key
            break

    # Get rid of the path and the extension
    basename = os.path.splitext(os.path.basename( \
        args['shapefiles'][category][shp_name][type_key]))[0]

    # Extract the type for this shapefile
    type_shapefile_uri = args['shapefiles'][category][shp_name][type_key]

    source_nodata = raster_utils.get_nodata_from_uri(type_shapefile_uri)
    array = raster_utils.load_memory_mapped_array( \
        type_shapefile_uri, raster_utils.temporary_filename())

#    raster = gdal.Open(type_shapefile_uri)
#    band = raster.GetRasterBand(1)
#    array = band.ReadAsArray()

#    LOGGER.info('Extracting priority information from ' + shp_name)
    
    tiles = args['tiles']

    indices_limit_array = args['indices_limit_array']
    shore_array = args['shore_array']
    positions_array = args['positions_array']
    soil_type_array = args['soil_type_array']
    soil_properties_array = args['soil_properties_array']


    progress_step = tiles / 50
    for transect in range(tiles):
        if transect % progress_step == 0:
            print '.',

        [start, end] = indices_limit_array[transect]

        #raw_positions = transect_info[transect]['raw_positions']
        raw_positions = \
            (positions_array[transect, 0, start:end], \
            positions_array[transect, 1, start:end])
        
        #Load the habitats as sampled from the raster
        source = array[raw_positions]

        # Interpolate the data to the model resolution 
#                source = interpolate_transect(source, i_side_fine, \
#                    args['model_resolution'], kind = 'nearest')


        source = source[start:end,]

        # Load the soil type buffer
        destination = soil_type_array[transect,start:end]

        # Overriding source_nodata so it doesn't interfere with habitat_nodata
        source[source == source_nodata] = habitat_nodata

        # Apply the habitat constraints
#                source = \
#                    apply_habitat_constraints(source, args['habitat_information'])
#                sys.exit(0)
        
        # Copy soil type directly to destination
        destination = source

        # Apply the soil type constraints
        for mud_only_habitat in mud_only_habitat_ids:
            replace_with_mud = np.where(destination == mud_only_habitat)

            if replace_with_mud[0].size:
                destination[replace_with_mud] = soil_types['mud']
    
    print('')

    # Clean up
#    band = None
#    raster = None
    array = None

    for field in args['shapefiles'][category][shp_name]:

        # Skip the field 'type'
        if field.lower() == 'type':
            continue

        # Retreive the index for this field
        field_id = args['field_index'][category]['fields'][field.lower()]

        # Get rid of the path and the extension
        basename = os.path.splitext( \
            os.path.basename(args['shapefiles'][category][shp_name][field]))[0]

        # Extract data from the current raster field
        field_id = args['field_index'][category]['fields'][field.lower()]

        uri = args['shapefiles'][category][shp_name][field]
        array = raster_utils.load_memory_mapped_array( \
            uri, raster_utils.temporary_filename())

#        raster = gdal.Open(uri)
#        band = raster.GetRasterBand(1)
#        array = band.ReadAsArray()

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

            # Interpolate the data to the model resolution 
#                source = interpolate_transect(source, i_side_fine, \
#                    args['model_resolution'], kind = 'nearest')

            source = source[start:end,]

            destination = \
                soil_properties_array[transect, field_id, start:end]

            destination = source

            
        print('')

        # Close the raster before proceeding to the next one
#        band = None
#        raster = None
        array = None



def combine_natural_habitats(args, transect_data_file):

    LOGGER.info('Processing natural habitats...')

    hdf5_files = args['hdf5_files']
    habitat_nodata = args['habitat_nodata']

    limit_group = transect_data_file['limits']
    indices_limit_dataset = limit_group['indices']
    positions_dataset = transect_data_file['ij_positions']
    shore_dataset = transect_data_file['shore_index']

    
    category = 'natural habitats'


    habitat_type_dataset = \
        transect_data_file.create_dataset('habitat_type', \
            (args['tiles'], args['max_transect_length']), \
            compression = 'gzip', fillvalue = 0, \
            dtype = 'i4')
    
    habitat_properties_dataset = \
        transect_data_file.create_dataset('habitat_properties', \
            (args['tiles'], args['habitat_field_count'], args['max_transect_length']), \
            compression = 'gzip', fillvalue = habitat_nodata)


    # Create hdf5 category for natural habitats
    hdf5_files[category] = []
    mask_dataset = transect_data_file['mask']

    for shp_name in args['shapefiles'][category]:

        LOGGER.info('Extracting information from ' + shp_name)
        
        # Find habitat_id that will be used to search field position in field_index:
        habitat_type = args['shapefile types'][category][shp_name]
        habitat_id = None
        for habitat in args['field_index']['natural habitats']:
            if args['field_index']['natural habitats'][habitat]['name'] == \
                habitat_type:
                habitat_id = int(habitat)
                break

        assert habitat is not None

        # Build the list of field names in lower case 
        field_names_lowercase = \
            [field_name.lower() for field_name in \
                args['shapefiles'][category][shp_name].keys()]

        # Assert if field 'type' doesn't exist
        assert 'type' in field_names_lowercase

        # Store the key 'type' in its original case
        type_key = None
        for key in args['shapefiles'][category][shp_name].keys():
            if key.lower() == 'type':
                type_key = key
                break

        # Extract the habitat type for this shapefile
        type_shapefile_uri = args['shapefiles'][category][shp_name][type_key]

        shapefile_nodata = raster_utils.get_nodata_from_uri(type_shapefile_uri)

        raster = gdal.Open(type_shapefile_uri)
        band = raster.GetRasterBand(1)

        tiles = args['tiles']

        progress_step = tiles / 50
        for transect in range(tiles):
            if transect % progress_step == 0:
                print '.',

            [start, end] = indices_limit_dataset[transect]

            #raw_positions = transect_info[transect]['raw_positions']
            raw_positions = \
                (positions_dataset[transect, 0, start:end], \
                positions_dataset[transect, 1, start:end])

            #Load the habitats as sampled from the raster
            habitat_type = np.ones(end-start) * -1
            for position in range(end-start):
                habitat_type[position] = \
                    band.ReadAsArray(int(raw_positions[1][position]), \
                        int(raw_positions[0][position]), 1, 1)[0]

            # Load the habitat type buffer
            destination = habitat_type_dataset[transect,start:end]


            # Overriding shapefile_nodata so it doesn't interfere with habitat_nodata
            habitat_type[habitat_type == shapefile_nodata] = habitat_nodata


            # Apply the habitat constraints
#                habitat_type = \
#                    apply_habitat_constraints(habitat_type, args['habitat_information'])
#                sys.exit(0)
            
            # Compute the mask that will be used to update the values
            mask = destination < habitat_type
            mask_dataset[transect, start:end] = mask

            # Update habitat_types with new type of higher priority
            destination[mask] = habitat_type[mask]

            # Remove nodata
            clipped_positions = \
                (raw_positions[0][start:end], raw_positions[1][start:end])

            # Positions to update
            masked_positions = \
                (clipped_positions[0][mask], clipped_positions[1][mask])

            if category in args['valid_habitat_types']:
                # Update the values using habitat_type
                transects[masked_positions] = habitat_type[mask]
                # Leave the transect ID on the transect's shore
                shore = shore_dataset[transect]
                transects[(raw_positions[0][shore], \
                    raw_positions[1][shore])] = transect
        
        print('')

        # Clean up
        band = None
        raster = None

        # Go through each property for the current habitat
        for field in args['shapefiles'][category][shp_name]:

            # Skip the field 'type'
            if field.lower() == 'type':
                continue

            # Get rid of the path and the extension
            basename = os.path.splitext( \
                os.path.basename(args['shapefiles'][category][shp_name][field]))[0]

            # Extract data from the current raster field
            field_id = args['field_index']['natural habitats'][habitat_id]['fields'][field.lower()]

            uri = args['shapefiles'][category][shp_name][field]
            raster = gdal.Open(uri)
            band = raster.GetRasterBand(1)

#            LOGGER.info('Extracting transect information from ' + basename)
            
            # Process 
            progress_step = tiles / 50
            for transect in range(tiles):
                if transect % progress_step == 0:
                    print '.',

                [start, end] = indices_limit_dataset[transect]

                raw_positions = \
                    (positions_dataset[transect, 0, start:end], \
                    positions_dataset[transect, 1, start:end])


                #Load the habitats as sampled from the raster
                habitat_property = (np.ones(end-start) * -1).astype('float32')
                for position in range(end-start):
                    habitat_property[position] = \
                        band.ReadAsArray(int(raw_positions[1][position]), \
                            int(raw_positions[0][position]), 1, 1)

                habitat_property = habitat_property[start:end,]

                destination = \
                    habitat_properties_dataset[transect, field_id, start:end]

                # Save transect to file
                mask = mask_dataset[transect, start:end]

                destination[mask] = habitat_property[mask]

                clipped_positions = \
                    (raw_positions[0][start:end], raw_positions[1][start:end])

                masked_positions = \
                    (clipped_positions[0][mask], clipped_positions[1][mask])
                
            print('')

            # Close the raster before proceeding to the next one
            band = None
            raster = None

    print('---------------- Stopping here ---------------- ')
    sys.exit(0)

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
    
    # Shore point outside bathymetry
    if (p_i < 0) or (p_i >= bathymetry_shape[0]):
        return (None, None)

    p_j = shore_point[1]

    # Shore point outside bathymetry
    if (p_j < 0) or (p_j >= bathymetry_shape[0]):
        return (None, None)

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



