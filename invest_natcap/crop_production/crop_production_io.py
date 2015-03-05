'''
The Crop Production IO module contains functions for handling inputs and
outputs
'''

import logging
import os
import pprint as pp

from invest_natcap import raster_utils as ru

LOGGER = logging.getLogger('CROP_PRODUCTION')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


class MissingParameter(StandardError):
    '''
    An exception class that may be raised when a necessary parameter is not
    provided by the user.
    '''
    def __init__(self, msg):
        self.msg = msg


# Fetch and Verify Arguments
def fetch_args(args, create_outputs=True):
    '''
    Fetches input arguments from the user, verifies for correctness and
    completeness, and returns a list of variables dictionaries

    Args:
        args (dictionary): arguments from the user

    Returns:
        vars_dict (dictionary): dictionary of variables to be used in the model

    Example Returns::

        vars_dict = {
            # ... original args ...

            # Workspace
            'intermediate_dir': 'path/to/intermediate_dir',
            'output_dir': 'path/to/output_dir',

            # Crop Lookup Table
            'crop_lookup_dict': {
                'code': 'crop_name',
                ...
            },

            # From spatial_dataset_dir
            'observed_yield_maps_dir': 'path/to/observed_yield_maps_dir/',
            'observed_yields_maps_dict': {
                'crop': 'path/to/crop_yield_map',
                ...
            },
            'climate_bin_maps_dir': 'path/to/climate_bin_maps_dir/',
            'climate_bin_maps_dict': {
                'crop': 'path/to/crop_climate_bin_map',
                ...
            },
            'percentile_table_uri': 'path/to/percentile_table_uri',
            'percentile_table_dict': {
                'crop': {
                    <climate_bin>: {
                        'yield_25th': <float>,
                        'yield_50th': <float>,
                        'yield_75th': <float>,
                        'yield_95th': <float>,
                        ...
                    },
                }
                ...
            },
            'modeled_yield_table_uri': 'path/to/modeled_yield_table_uri',
            'modeled_yield_table_dict': {
                'crop': {
                    'climate_bin': {
                        'yield_ceiling': '<float>',
                        'yield_ceiling_rf': '<float>',
                        'b_nut': '<float>',
                        'b_K2O': '<float>',
                        'c_N': '<float>',
                        'c_P2O5': '<float>',
                        'c_K2O': '<float>',
                    },
                },
                ...
            },

            # For Modeled Yield
            'modeled_fertilizer_maps_dict': {
                'nitrogen': 'path/to/nitrogen_fertilizer_map',
                'phosphorous': 'path/to/phosphorous_fertilizer_map',
                'potash': 'path/to/potash_fertilizer_map'
            },

            # For Nutrition
            'nutrition_table_dict': {
                'crop': {
                    'percent_refuse': <float>,
                    'protein': <float>,
                    'lipid': <float>,
                    'energy': <float>,
                    'ca': <float>,
                    'fe': <float>,
                    'mg': <float>,
                    'ph': <float>,
                    ...
                },
                ...
            },

            # For Economic Returns
            'economics_table_dict': {
                'crop': {
                    'price': <float>,
                    'cost_nitrogen': <float>,
                    'cost_phosphorous': <float>,
                    'cost_potash': <float>,
                    'cost_labor': <float>,
                    'cost_mach': <float>,
                    'cost_seed': <float>,
                    'cost_irrigation': <float>
                }
            },
        }

    '''
    vars_dict = dict(args.items())

    vars_dict = read_crop_lookup_table(vars_dict)
    vars_dict = fetch_spatial_dataset(vars_dict)

    if vars_dict['do_yield_regression_model']:
        vars_dict = fetch_modeled_fertilizer_maps(vars_dict)

    if vars_dict['do_nutrition']:
        vars_dict = read_nutrition_table(vars_dict)

    if vars_dict['do_economics']:
        vars_dict = read_economics_table(vars_dict)

    pass


def read_crop_lookup_table(vars_dict):
    '''
    Reads in the Crop Lookup Table and returns a dictionary

    Args:
        crop_lookup_table_uri (str): descr

    Returns:
        vars_dict (dict): descr

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'crop_lookup_dict': {
                'code': 'crop_name',
                ...
            }
        }
    '''
    input_dict = ru.get_lookup_from_csv(
        vars_dict['crop_lookup_table_uri'], 'code')

    crop_lookup_dict = {}
    for i in input_dict:
        crop_lookup_dict[i] = input_dict[i]['crop']

    # assert codes are non-negative integers?
    keys = crop_lookup_dict.keys()
    assert(all(map(lambda x: (type(x) is int), keys)))
    assert(all(map(lambda x: (x >= 0), keys)))

    vars_dict['crop_lookup_dict'] = crop_lookup_dict
    return vars_dict


def fetch_spatial_dataset(vars_dict):
    '''
    Fetches necessary variables from provided spatial dataset folder

    Args:
        vars_dict (dict): arguments and derived variables

    Returns:
        vars_dict (dict): same dictionary with additional variables as shown
            in the Example Returns

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'observed_yield_maps_dir': 'path/to/observed_yield_maps_dir/',
            'observed_yields_maps_dict': {
                'crop': 'path/to/crop_yield_map',
                ...
            },
            'climate_bin_maps_dir': 'path/to/climate_bin_maps_dir/',
            'climate_bin_maps_dict': {
                'crop': 'path/to/crop_climate_bin_map',
                ...
            },
            'percentile_table_uri': 'path/to/percentile_table_uri',
            'percentile_table_dict': {
                'crop': {
                    <climate_bin>: {
                        'yield_25th': <float>,
                        'yield_50th': <float>,
                        'yield_75th': <float>,
                        'yield_95th': <float>,
                        ...
                    },
                }
                ...
            },
            'modeled_yield_table_uri': 'path/to/modeled_yield_table_uri',
            'modeled_yield_table_dict': {
                'crop': {
                    'climate_bin': {
                        'yield_ceiling': '<float>',
                        'yield_ceiling_rf': '<float>',
                        'b_nut': '<float>',
                        'b_K2O': '<float>',
                        'c_N': '<float>',
                        'c_P2O5': '<float>',
                        'c_K2O': '<float>',
                    },
                },
                ...
            },
        }
    '''
    # Dictionary in case folder structure changes during development
    spatial_dataset_dict = {
        'observed_yield_maps_dir': 'observed_yield/',
        'climate_bin_maps_dir': 'climate_bin_maps/',
        'percentile_table_uri': 'climate_percentile_yield/percentile_yield_table.csv',
        'modeled_yield_table_uri': 'climate_regression_yield/percentile_model_yield_table.csv'
    }

    if vars_dict['do_yield_observed']:
        vars_dict['observed_yield_maps_dir'] = os.path.join(
            vars_dict['spatial_dataset_dir'],
            spatial_dataset_dict['observed_yield_maps_dir'])

        vars_dict = fetch_observed_yield_maps(vars_dict)

    if vars_dict['do_yield_percentile'] or vars_dict['do_yield_regression_model']:
        vars_dict['climate_bin_maps_dir'] = os.path.join(
            vars_dict['spatial_dataset_dir'],
            spatial_dataset_dict['climate_bin_maps_dir'])

        vars_dict = fetch_climate_bin_maps(vars_dict)

    if vars_dict['do_yield_percentile']:
        vars_dict['percentile_table_uri'] = os.path.join(
            vars_dict['spatial_dataset_dir'],
            spatial_dataset_dict['percentile_table_uri'])

        vars_dict = read_percentile_yield_table(vars_dict)

    if vars_dict['do_yield_regression_model']:
        vars_dict['modeled_yield_table_uri'] = os.path.join(
            vars_dict['spatial_dataset_dir'],
            spatial_dataset_dict['modeled_yield_table_uri'])

        vars_dict = read_regression_model_yield_table(vars_dict)

    return vars_dict


def fetch_observed_yield_maps(vars_dict):
    '''
    Fetches a dictionary of URIs to observed yield maps with crop names as keys

    Args:
        observed_yield_maps_dir (str): descr

    Returns:
        observed_yields_maps_dict (dict): descr

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'observed_yield_maps_dir': 'path/to/observed_yield_maps_dir/',
            'observed_yields_maps_dict': {
                'crop': 'path/to/crop_yield_map',
                ...
            },
        }
    '''
    map_uris = _listdir(vars_dict['observed_yield_maps_dir'])

    observed_yields_maps_dict = {}
    for map_uri in map_uris:
        # could check here to make sure file is raster

        basename = os.path.basename(map_uri)
        cropname = basename.split('_')[0]
        if cropname != '':
            observed_yields_maps_dict[cropname] = map_uri

    vars_dict['observed_yields_maps_dict'] = observed_yields_maps_dict

    return vars_dict


def fetch_climate_bin_maps(vars_dict):
    '''
    Fetches a dictionary of URIs to climate bin maps with crop names as keys

    Args:
        climate_bin_maps_dir (str): descr

    Returns:
        climate_bin_maps_dict (dict): descr

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'climate_bin_maps_dir': 'path/to/climate_bin_maps_dir/',
            'climate_bin_maps_dict': {
                'crop': 'path/to/crop_climate_bin_map',
                ...
            },
        }
    '''
    map_uris = _listdir(vars_dict['climate_bin_maps_dir'])

    climate_bin_maps_dict = {}
    for map_uri in map_uris:
        # could check here to make sure file is raster

        basename = os.path.basename(map_uri)
        cropname = basename.split('_')[0]
        if cropname != '':
            climate_bin_maps_dict[cropname] = map_uri

    vars_dict['climate_bin_maps_dict'] = climate_bin_maps_dict

    return vars_dict


# NOT IMPLEMENTED YET
def read_percentile_yield_table(vars_dict):
    '''
    Reads in the Percentile Yield Table and returns a dictionary

    Args:
        percentile_table_uri (str): descr

    Returns:
        percentile_table_dict (dict): descr

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'percentile_table_uri': 'path/to/percentile_table_uri',
            'percentile_table_dict': {
                'crop': {
                    <climate_bin>: {
                        'yield_25th': <float>,
                        'yield_50th': <float>,
                        'yield_75th': <float>,
                        'yield_95th': <float>,
                        ...
                    },
                }
                ...
            },
        }
    '''
    # Add information to user here in the case of raised exception
    assert(os.path.exists(vars_dict['percentile_table_uri']))

    # Need this to sort by crop, then climate bin
    input_dict = get_nested_lookup_from_csv(
        vars_dict['percentile_table_uri'], 'crop', 'climate_bin')

    # Add Assertion Statements?

    vars_dict['percentile_table_dict'] = input_dict
    return vars_dict


# NOT IMPLEMENTED YET
def read_regression_model_yield_table(vars_dict):
    '''
    (desc)

    Args:

    Returns:

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'modeled_yield_table_uri': 'path/to/modeled_yield_table_uri',
            'modeled_yield_table_dict': {
                'crop': {
                    'climate_bin': {
                        'yield_ceiling': '<float>',
                        'yield_ceiling_rf': '<float>',
                        'b_nut': '<float>',
                        'b_K2O': '<float>',
                        'c_N': '<float>',
                        'c_P2O5': '<float>',
                        'c_K2O': '<float>',
                    },
                },
                ...
            },
        }
    '''

    pass


def fetch_modeled_fertilizer_maps(vars_dict):
    '''
    Fetches a dictionary of URIs to fertilizer maps with fertilizer names as
        keys.

    Args:
        modeled_fertilizer_maps_dir (str): descr

    Returns:
        modeled_fertilizer_maps_dict (dict): descr

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'modeled_fertilizer_maps_dict': {
                'nitrogen': 'path/to/nitrogen_fertilizer_map',
                'phosphorous': 'path/to/phosphorous_fertilizer_map',
                'potash': 'path/to/potash_fertilizer_map'
            },
        }
    '''
    map_uris = _listdir(vars_dict['modeled_fertilizer_maps_dir'])

    modeled_fertilizer_maps_dict = {}
    for map_uri in map_uris:
        # could check here to make sure file is raster

        basename = os.path.basename(map_uri)
        fertilizer_name = basename.split('_')[0]
        if fertilizer_name in ['nitrogen', 'phosphorous', 'potash']:
            modeled_fertilizer_maps_dict[fertilizer_name] = map_uri

    # Assert that the dictionary contains maps for all three fertilizers?

    vars_dict['modeled_fertilizer_maps_dict'] = modeled_fertilizer_maps_dict

    return vars_dict


def read_nutrition_table(vars_dict):
    '''
    Reads in the Nutrition Table and returns a dictionary

    Args:
        nutrition_table_uri (str): descr

    Returns:
        nutrition_table_dict (dict): descr

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'nutrition_table_dict': {
                'crop': {
                    'percent_refuse': <float>,
                    'protein': <float>,
                    'lipid': <float>,
                    'energy': <float>,
                    'ca': <float>,
                    'fe': <float>,
                    'mg': <float>,
                    'ph': <float>,
                    ...
                },
                ...
            },
        }
    '''
    input_dict = ru.get_lookup_from_csv(
        vars_dict['nutrition_table_uri'], 'crop')

    # Add Assertion Statements?

    vars_dict['nutrition_table_dict'] = input_dict
    return vars_dict


def read_economics_table(vars_dict):
    '''
    Reads in the Economics Table and returns a dictionary

    Args:
        economics_table_uri (str): descr

    Returns:
        economics_table_dict (dict): descr

    Example Returns::

        vars_dict = {
            # ... previous vars ...

            'economics_table_dict': {
                'crop': {
                    'price': <float>,
                    'cost_nitrogen': <float>,
                    'cost_phosphorous': <float>,
                    'cost_potash': <float>,
                    'cost_labor': <float>,
                    'cost_mach': <float>,
                    'cost_seed': <float>,
                    'cost_irrigation': <float>
                }
            },
        }
    '''
    input_dict = ru.get_lookup_from_csv(
        vars_dict['economics_table_uri'], 'crop')

    # Add Assertion Statements?

    vars_dict['economics_table_dict'] = input_dict
    return vars_dict


# Helper function
def _listdir(path):
    '''
    A replacement for the standard os.listdir which, instead of returning
    only the filename, will include the entire path. This will use os as a
    base, then just lambda transform the whole list.

    Args:
        path (string): the location container from which we want to
            gather all files

    Returns:
        uris (list): A list of full URIs contained within 'path'
    '''
    file_names = os.listdir(path)
    uris = map(lambda x: os.path.join(path, x), file_names)

    return uris


# Create Outputs
def create_outputs(vars_dict):
    '''
    '''
    pass

