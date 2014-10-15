'''This will be the entry point for the fisheries tier 1 model.'''

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


def execute(args):
    '''This function will prepare files to be passed to the fisheries core
    module.

    Inputs:
        :param string workspace_dir: location into which all intermediate and
            output files should be placed.
        :param string aoi_uri: location of shapefile which will be used as
            subregions for calculation. Each region must conatin a 'name'
            attribute which will
        :param int timesteps:represents the number of time steps that
            the user desires the model to run.
        :param string population_type: specifies whether the model
            is age-specific or stage-specific. Options will be either "Age
            Specific" or "Stage Specific" and will change which equation is
            used in modeling growth.
        :param string sexsp: specifies whether or not the age and stage
            classes are distinguished by sex.
        :param string population_csv_uri: location of the population parameters
            csv. This will contain all age and stage specific parameters.
        :param string spawn_units:
        :param float total_init_recruits: represents the initial number of
            recruits that will be used in calculation of population on a per
            area basis.
        :param string recruitment_type:
        :param float alpha: must exist within args for BH or Ricker.
            Parameter that will be used in calculation of recruitment.
        :param float beta: must exist within args for BH or Ricker.
            Parameter that will be used in calculation of recruitment.
        :param float total_recur_recruits: must exist within args for Fixed.
            Parameter that will be used in calculation of recruitment.
        :param string migration_dir: if this parameter exists, it means
            migration is desired. This is  the location of the parameters
            folder containing files for migration. There should be one file for
            every age class which migrates.
        :param string harvest_units: specifies how the user wants to get
            the harvest data. Options are either "Individuals" or "Weight", and
            will change the harvest equation used in core.
        :param float frac_post_process: represents the fraction of the animal
            remaining after processing of the whole carcass is complete.
            This will exist only if valuation is desired for the particular
            species.
        :param float unit_price: represents the price for a single unit of
            harvest. Exists only if valuation is desired.
    '''
    vars_dict = fetch_verify_args(args)
    vars_dict = initialize_vars(vars_dict)

    recru_func = set_recru_func(vars_dict)
    harvest_func = set_harvest_func(vars_dict)
    init_cond_func = set_init_cond_func(vars_dict, recru_func)
    cycle_func = set_cycle_func(vars_dict, recru_func, harvest_func)

    vars_dict = run_population_model(
        vars_dict, init_cond_func, cycle_func)

    generate_outputs(vars_dict)


def fetch_verify_args(args):
    '''Fetches input arguments from the user, verifies for correctness and
    completeness, and returns a dictionary of variables

    :param dictionary args: arguments from the user
    :return: vars_dict
    :rtype: dictionary
    '''
    # Verify Population CSV
        # Parse Population CSV
    # Verify Migration Tables
        # (Make use of Kathryn's listdir)
        # Parse Migration Tables

    vars_dict = {}

    # Check that path exists and user has read/write permissions along path
    workspace_dir = args['workspace_dir']

    # Check shapefile subregions match regions in population parameters file
    aoi_uri = args['aoi_uri']

    # Check positive number
    total_timesteps = args['total_timesteps']

    # Check for Duration vector exists in parameters file if stage-based
    population_type = args['population_type']

    # Check for male and female matrices in parameters file if sex-specific
    sexsp = args['sexsp']

    # Check that required information exists
    population_csv_uri = args['population_csv_uri']

    # Check for Weight vector in parameters file if weight selected
    spawn_units = args['spawn_units']

    # Check for non-negative float
    total_init_recruits = args['total_init_recruits']

    # Check that corresponding parameters exist
    recruitment_type = args['recruitment_type']

    # Check positive float
    alpha = args['alpha']

    # Check positive float
    beta = args['beta']

    # Check non-negative number
    total_recur_recruits = args['total_recur_recruits']

    # Check migration CSV files match areas.
    # Check columns approximately sum to one?
    migration_dir = args['migration_dir']

    # Check that Weight vector exists in parameters file
    harvest_units = args['harvest_units']

    # Check float between [0,1]
    frac_post_process = args['frac_post_process']

    # Check non-negative float
    unit_price = args['unit_price']

    ##################################################################

    # Inputs - may want this to be a dictionary
    model_type, t, a, s, x, VulnFish, exploitFrac, SurvFrac, use_weight,\
        rec_eq_str, Fec, fixed, alpha, beta, sexsp, Weight = get_inputs(args)
    N_all, Matu, Mig, Surv, Harv, Val = initialize_matrices(
        t, a, s, x, exploitFrac, VulnFish, SurvFrac, Weight)

    pass


def initialize_vars(vars_dict):
    '''Initializes variables
    '''

    pass


def set_recru_func(vars_dict):
    '''
    Creates optimized recruitment function

    rec_eq_str, Matu, Weight, Fec, fixed, alpha, beta, sexsp
    '''
    def create_Spawners(Matu, Weight):
        return lambda N_prev: (N_prev * Matu * Weight)

    def create_BH(alpha, beta, sexsp, Matu, Weight):
        spawners = create_Spawners(Matu, Weight)
        return lambda N_prev: ((alpha * spawners(
            N_prev) / (beta + spawners(N_prev)))) / sexsp

    def create_Ricker(alpha, beta, sexsp, Matu, Weight):
        spawners = create_Spawners(Matu, Weight)
        return lambda N_prev: (alpha * spawners(
            N_prev) * (np.e ** (-beta * spawners(N_prev)))) / sexsp

    def create_Fecundity(Fec, sexsp, Matu):
        return lambda N_prev: (N_prev * Matu * Fec) / sexsp

    def create_Fixed(fixed, sexsp):
        return lambda N_prev: fixed / sexsp

    pass


def set_harvest_func(vars_dict):
    '''
    '''
    # Calculate Harvest
    # Calculate Valuation
    pass


def set_init_cond_func(vars_dict, recru_func):
    '''
    '''
    pass


def set_cycle_func(vars_dict, recru_func, harvest_func):
    '''
    '''
    pass


def run_population_model(vars_dict, init_cond_func, cycle_func):
    '''
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
