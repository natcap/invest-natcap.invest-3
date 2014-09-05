from __future__ import print_function

import unittest
import logging
import os
import math
import numpy as np
import random
import csv
import shutil
import json

from osgeo import gdal
from osgeo import ogr
from nose.plugins.skip import SkipTest

import invest_test_core
from invest_natcap import raster_utils
from invest_natcap.nearshore_wave_and_erosion \
    import nearshore_wave_and_erosion
from invest_natcap.nearshore_wave_and_erosion \
    import nearshore_wave_and_erosion_core


LOGGER = logging.getLogger('nearshore_wave_and_eroasion_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestNearshoreWaveAndErosionCore(unittest.TestCase):
    """Main testing class for the nearshore wave and erosion core model tests"""
    
    def setUp(self):
        """ Set up function
        """
        pass

    def add_intermediate_output_directories(self, args):
        # Add the Output directory onto the given workspace
        args['output_dir'] = \
            os.path.join(args['workspace_dir'], 'output')
        if not os.path.isdir(args['output_dir']):
            os.makedirs(args['output_dir'])
        # Add the intermediate directory as well
        args['intermediate_dir'] = \
            os.path.join(args['workspace_dir'], 'intermediate')
        if not os.path.isdir(args['intermediate_dir']):
            os.makedirs(args['intermediate_dir'])

    def test_find_valid_transects(self):
        """Test if number of valid transects is ok"""
        # Extract shore
        shore_raster_uri = '../../NearshoreWaveAndErosion/tests/shore.tif'
        assert os.path.isfile(shore_raster_uri)

        shore_raster = gdal.Open(shore_raster_uri)
        message = 'Cannot open file ' + shore_raster_uri
        assert shore_raster is not None, message
        shore_band = shore_raster.GetRasterBand(1)
        shore = shore_band.ReadAsArray()
        shore_band = None
        shore_raster = None

        shore_points = np.where(shore > 0)
        LOGGER.debug('found %i shore segments.' % shore_points[0].size)

        # Extract landmass
        landmass_raster_uri = '../../NearshoreWaveAndErosion/tests/landmass.tif'
        assert os.path.isfile(landmass_raster_uri)

        landmass_raster = gdal.Open(landmass_raster_uri)
        message = 'Cannot open file ' + landmass_raster_uri
        assert landmass_raster is not None, message
        landmass_band = landmass_raster.GetRasterBand(1)
        land = landmass_band.ReadAsArray()
        landmass_band = None
        landmass_raster = None

        # Load the args dictionary
        args_uri = '../../NearshoreWaveAndErosion/tests/nearshore_wave_and_erosion_test_archive.json'    

        with open(args_uri) as args_file:
            contents = json.load(args_file)
            args = contents['arguments']
            self.add_intermediate_output_directories(args)

        # precompute directions
        SECTOR_COUNT = 16 
        rays_per_sector = 1
        d_max = args['max_profile_length'] * 1000 # convert in meters
        model_resolution = args['model_resolution'] # in meters already
        cell_size = model_resolution
    
        direction_count = SECTOR_COUNT * rays_per_sector
        direction_range = range(direction_count)
        direction_step = 2.0 * math.pi / direction_count
        directions_rad = [a * direction_step for a in direction_range]
        direction_vectors = \
            nearshore_wave_and_erosion_core.fetch_vectors(directions_rad)
    
        # Perform a bunch of tests beforehand
        assert (np.amax(shore_points[0]) < land.shape[0]) and \
            (np.amax(shore_points[1]) < land.shape[1])
        assert not np.where(land[shore_points] < 0.)[0].size
        assert not np.where(land[shore_points] > 0)[0].size
    
        # Compute the ray paths in each direction to their full length (d_max).
        # We'll clip them for each point in two steps (raster boundaries & land)
        # The points returned by the cast function are relative to the origin (0,0)
        for p in zip(direction_vectors[0], direction_vectors[1]):
            result = \
                nearshore_wave_and_erosion_core.cast_ray_fast(p, d_max/cell_size)

        # Identify valid transect directions
        valid_transect_count, valid_transects = \
            nearshore_wave_and_erosion_core.find_valid_transects( \
                shore_points, land, direction_vectors)
 
        # Compare valid transect counts
        valid_sectors_uri = '../../NearshoreWaveAndErosion/tests/shore_valid_sectors.tif'
        assert os.path.isfile(valid_sectors_uri)

        # Load reference raster
        valid_sectors_raster = gdal.Open(valid_sectors_uri)
        band = valid_sectors_raster.GetRasterBand(1)
        reference_nodata = band.GetNoDataValue()
        reference_array = band.ReadAsArray()

        # Map valid transects onto array
        computed_array = np.ones_like(reference_array) * reference_nodata
        for s in range(shore_points[0].size):
            computed_array[shore_points[0][s], shore_points[1][s]] = \
                np.sum(valid_transects[s] > -1).astype(np.int32)

        # Assert if different
        difference = np.sum(np.absolute(reference_array - computed_array))
        message = 'Computed and reference arrays disagree ' + str(difference)
        assert difference == 0., message

    def test_compute_transects(self):
        """Compute transects algorithm"""
        shore_raster_uri = '../../NearshoreWaveAndErosion/tests/shore.tif'
        assert os.path.isfile(shore_raster_uri)

        landmass_raster_uri = '../../NearshoreWaveAndErosion/tests/landmass.tif'
        assert os.path.isfile(landmass_raster_uri)

        bathymetry_raster_uri = '../../NearshoreWaveAndErosion/tests/bathymetry.tif'
        assert os.path.isfile(bathymetry_raster_uri)

        args_uri = '../../NearshoreWaveAndErosion/tests/nearshore_wave_and_erosion_test_archive.json'    

        with open(args_uri) as args_file:
            contents = json.load(args_file)
            args = contents['arguments']
            args['landmass_raster_uri'] = landmass_raster_uri
            args['shore_raster_uri'] = shore_raster_uri
            args['bathymetry_raster_uri'] = bathymetry_raster_uri
            self.add_intermediate_output_directories(args)
        nearshore_wave_and_erosion_core.compute_transects(args)

    def tare_down(self):
        """ Clean up code."""
        # Do nothing for now 
        pass
