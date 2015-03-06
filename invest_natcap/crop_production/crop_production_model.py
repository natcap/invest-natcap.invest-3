'''
The Crop Production Model module contains functions for running the model
'''

import logging

import pygeoprocessing.geoprocessing as ru

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
            'observed_yields_maps_dict': {
                'crop': 'path/to/crop_climate_bin_map',
                ...
            },
            'tmp_observed_dir': '/path/to/tmp_observed_yield_dir',
        }
    '''
    # Get List of Crops in LULC Crop Map

    # For Each Crop, Clip Corresponding Observed Crop Yield Map over AOI and Reproject
    #   Save to tmp_climate_percentile_yield_intermediate_dir

    # Create Crop Production Maps by Multiplying Yield by Cell Size Area
    #   Output: Crop Production Maps
    #   If 'create_crop_production_maps' selected, save to output folder

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


# Raster Utils Wrapper for High-level Functions
def clip_raster_over_aoi():
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
    # Check that datasets are in same projection
    ru.assert_datasets_in_same_projection()

    # Reproject AOI onto Raster, find bounding box
    ru.reproject_dataset_uri()

    # Clip raster around bounding box
    ru.clip_dataset_uri()

    # Reproject Clipped Raster onto AOI
    ru.reproject_dataset_uri()

    ru.align_dataset_list()

    # Save/return clipped raster
    pass


def sum_cells_in_raster():
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
    # Option 1: use sum or mean in GDAL's raster stats
    # Option 2: extract numpy array using GDAL
    # Option 3: use Raster_Utils functionality memmap for large rasters

    pass


def element_wise_operation():
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
    ru.vectorize_datasets(
        dataset_uri_list,
        dataset_pixel_op,
        dataset_out_uri,
        datatype_out,
        nodata_out,
        pixel_size_out,
        bounding_box_mode)
    pass
