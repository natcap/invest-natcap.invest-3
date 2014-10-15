import logging
import os
import shutil
import csv

from osgeo import ogr
import numpy as np

from invest_natcap import raster_utils

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


class ImproperStageParameter(Exception):
    '''This exception will occur if the stage-specific headings in the main
    parameter CSV are not included in the set of known parameters.'''
    pass


class ImproperAreaParameter(Exception):
    '''This exception will occur if the area-specific headings in the main
    parameter CSV are not included in the set of known parameters.'''
    pass


class MissingParameter(Exception):
    '''This is a broad exception which can be raised if the any of the
    parameters required for a specific model run type are missing. This
    can include recruitment parameters, vulnerability, exploitation fraction,
    maturity, weight, or duration.
    '''
    pass


def fetch_verify_args(args):
    '''Fetches input arguments from the user, verifies for correctness and
    completeness, and returns a dictionary of variables

    :param dictionary args: arguments from the user
    :return: vars_dict
    :rtype: dictionary
    '''
    pop_dict = _verify_population_csv(args)

    mig_dict = _verify_migration_tables(args)

    params_dict = _verify_single_params(args, pop_dict, mig_dict)

    vars_dict = dict(pop_dict.items() + mig_dict.items() + params_dict.items())

    return vars_dict


def _verify_population_csv(args):

    population_csv_uri = args['population_csv_uri']
    pop_dict = _parse_population_csv(population_csv_uri)

    # Check that required information exists


    pass


def _parse_population_csv(uri):
    pass


def _verify_migration_tables(args):

    mig_dict = {}

    # If Migration:
    migration_dir = args['migration_dir']
    mig_dict = _parse_migration_tables(migration_dir)

    # Check migration CSV files match areas.
    # Check columns approximately sum to one? (maybe throw warning rather than error)

    pass


def _parse_migration_tables(uri):
    # (Make use of Kathryn's listdir)
    pass


def _verify_single_params(args, pop_dict, mig_dict):
    # Check that path exists and user has read/write permissions along path
    workspace_dir = args['workspace_dir']

    # Check file extension? (maybe try / except would be better)
    # Check shapefile subregions match regions in population parameters file
    aoi_uri = args['aoi_uri']

    # Check positive number
    total_timesteps = args['total_timesteps']

    # If stage-based: Check that Duration vector exists in parameters file
    population_type = args['population_type']

    # If sex-specific: Check for male and female matrices in parameters file
    sexsp = args['sexsp']

    # Check for non-negative float
    total_init_recruits = args['total_init_recruits']

    # Check that corresponding parameters exist
    recruitment_type = args['recruitment_type']

    # If BH or Ricker and 'spawners by weight' selected: Check that Weight vector exists in parameters file
    spawn_units = args['spawn_units']

    # If BH or Ricker: Check positive number
    alpha = args['alpha']

    # Check positive float
    beta = args['beta']

    # If Fixed: Check non-negative number, check for sum approximately equal to one
    # Special Case: 1 sub-region --> vector equals 1
    total_recur_recruits = args['total_recur_recruits']

    # If Harvest: Check that Weight vector exists in population parameters file
    harvest_units = args['harvest_units']

    # If Harvest: Check float between [0,1]
    frac_post_process = args['frac_post_process']

    # If Harvest: Check non-negative float
    unit_price = args['unit_price']

    pass


def initialize_vars(vars_dict):
    '''Initializes variables
    '''

    pass


def generate_outputs(vars_dict):
    '''
    '''
    # Append Results to Shapefile
    # HTML results page
    # CSV results page
    pass


def listdir(path):
    '''A replacement for the standar os.listdir which, instead of returning
    only the filename, will include the entire path. This will use os as a
    base, then just lambda transform the whole list.

    Input:
        :param string path: the location container from which we want to
            gather all files

    Returns:
        :return: A list of full URIs contained within 'path'.
        :rtype: list
    '''
    file_names = os.listdir(path)
    uris = map(lambda x: os.path.join(path, x), file_names)

    return uris
