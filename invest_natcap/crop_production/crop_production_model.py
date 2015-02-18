'''
The Crop Production Model module contains functions for running the model
'''

import logging

from invest_natcap import raster_utils as ru

LOGGER = logging.getLogger('CROP_PRODUCTION')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def calc_yield_observed(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    pass


def calc_yield_percentile(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    pass


def calc_yield_modeled(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    pass


def calc_nutrition(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

        vars_dict = {
            ...

            '': '',

            ...
        }
    '''
    pass


def calc_economic_returns(vars_dict):
    '''
    About

    var_name (type): desc

    Example Args::

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
    '''
    # Option 1: use sum or mean in GDAL's raster stats
    # Option 2: extract numpy array using GDAL
    # Option 3: use Raster_Utils functionality memmap for large rasters

    pass


def element_wise_operation():
    '''
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
