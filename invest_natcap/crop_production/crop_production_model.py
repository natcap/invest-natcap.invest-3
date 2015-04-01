'''
The Crop Production Model module contains functions for running the model
'''

import os
import logging

from raster import Raster
from vector import Vector
import pygeoprocessing.geoprocessing as pygeo

LOGGER = logging.getLogger('CROP_PRODUCTION')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def create_observed_yield_maps(vars_dict):
    '''
    Creates yield maps from observed data and stores in the temporary yield
        folder

    Args:
        vars_dict (dict): descr

    Example Args::

        vars_dict = {
            # ...

            'lulc_map_uri': 'path/to/lulc_map_uri',
            'crop_lookup_dict': {
                'code': 'crop_name',
                ...
            },
            'observed_yields_maps_dict': {
                'crop': 'path/to/crop_climate_bin_map',
                ...
            },
            'tmp_observed_dir': '/path/to/tmp_observed_dir',
        }

    Outputs:

    .
    |-- tmp
        |-- observed
            |-- yield
                |-- [crop]_yield_map (*.tif)
    '''
    lulc_raster = Raster.from_file(vars_dict['lulc_map_uri'])
    aoi_vector = lulc_raster.get_aoi_as_vector()
    for crop in vars_dict['observed_yields_maps_dict'].keys():
        global_crop_raster = Raster.from_file(
            vars_dict['observed_yields_maps_dict'][crop])

        reprojected_aoi = aoi_vector.reproject(
            global_crop_raster.get_projection())

        clipped_global_crop_raster = global_crop_raster.clip(
            reprojected_aoi.uri)

        reproj_crop_raster = clipped_global_crop_raster.reproject(
            lulc_raster.get_projection(), 'nearest')

        crop_raster = reproj_crop_raster.align_to(lulc_raster)

        reclass
    # For crop in observed_yields_maps_dict:
    #

    # For Each Crop, Clip Corresponding Observed Crop Yield Map over AOI and Reproject
    #   Save to temporary directory

    # Create Crop Production Maps by Multiplying Yield by Cell Size Area
    #   Output: Crop Production Maps

    # Find Total Production for Given Crop by Summing Cells in Crop Production Maps
    #   Output: Crop Production Dictionary?

    pass


def create_percentile_yield_maps(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }

    Example Returns::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    # Get List of Crops in LULC Crop Map

    # Create Raster of Climate Bin Indices

    # For Each Yield Column in Percentile Yield Table:

    # For Each Crop, Create Crop Yield Map over AOI
        # Output: Crop Yield Maps

    # Create Crop Production Maps by Multiplying Yield by Cell Size Area
        # Output: Crop Production Maps
        # If 'create_crop_production_maps' selected, save to output folder

    # Find Total Production for Given Crop by Summing Cells in Crop Production Maps
        # Output: Crop Production Dictionary?

    # Generate Yield Results

    pass


def create_regression_yield_maps(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }

    Example Returns::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    pass


def create_production_maps(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }

    Example Returns::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    pass


def create_economic_returns_map(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }

    Example Returns::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    pass


def create_results_table(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }

    Example Returns::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    pass
