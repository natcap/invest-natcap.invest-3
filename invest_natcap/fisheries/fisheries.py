'''This will be the entry point for the fisheries tier 1 model.'''

import logging
import os
import shutil
import csv

from osgeo import ogr
import numpy as np

import fisheries_io
from invest_natcap import raster_utils

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def execute(args):
    '''Main Function

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
    vars_dict = fisheries_io.fetch_verify_args(args)
    vars_dict = fisheries_io.initialize_vars(vars_dict)

    recru_func = set_recru_func(vars_dict)
    harvest_func = set_harvest_func(vars_dict)
    init_cond_func = set_init_cond_func(vars_dict, recru_func)
    cycle_func = set_cycle_func(vars_dict, recru_func, harvest_func)

    vars_dict = run_population_model(
        vars_dict, init_cond_func, cycle_func)

    fisheries_io.generate_outputs(vars_dict)


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
