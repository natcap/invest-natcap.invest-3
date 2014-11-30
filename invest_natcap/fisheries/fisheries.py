'''
The Fisheries module contains the high-level code for excuting the fisheries
model
'''

import logging
import pprint as pp

import fisheries_io as io
import fisheries_model as model

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def execute(args, create_outputs=True):
    '''
    Entry point into the Fisheries Model

    Args:
        workspace_dir (string): location into which all intermediate
            and output files should be placed.

        aoi_uri (string): location of shapefile which will be used as
            subregions for calculation. Each region must conatin a 'name'
            attribute which will

        timesteps (int): represents the number of time steps that
            the user desires the model to run.

        population_type (string): specifies whether the model
            is age-specific or stage-specific. Options will be either "Age
            Specific" or "Stage Specific" and will change which equation is
            used in modeling growth.

        sexsp (string): specifies whether or not the age and stage
            classes are distinguished by sex.

        harvest_units (string): specifies how the user wants to get
            the harvest data. Options are either "Individuals" or "Weight", and
            will change the harvest equation used in core. (Required if
            args['val_cont'] is True)

        do_batch (boolean): specifies whether program will perform a
            single model run or a batch (set) of model runs.

        population_csv_uri (string): location of the population
            parameters csv. This will contain all age and stage specific
            parameters. (Required if args['do_batch'] is False)

        population_csv_dir (string): location of the directory that
            contains the Population Parameters CSV files for batch processing
            (Required if args['do_batch'] is True)

        spawn_units (string): (description)

        total_init_recruits (float): represents the initial number of
            recruits that will be used in calculation of population on a per
            area basis.

        recruitment_type (string): (description)

        alpha (float): must exist within args for BH or Ricker.
            Parameter that will be used in calculation of recruitment.

        beta (float): must exist within args for BH or Ricker.
            Parameter that will be used in calculation of recruitment.

        total_recur_recruits (float): must exist within args for Fixed.
            Parameter that will be used in calculation of recruitment.

        migr_cont (bool): if true, model uses migration

        migration_dir (string): if this parameter exists, it means
            migration is desired. This is  the location of the parameters
            folder containing files for migration. There should be one file for
            every age class which migrates. (Required if args['migr_cont'] is
            True)

        val_cont (bool): if true, model runs valuation computations

        frac_post_process (float): represents the fraction of the
            species remaining after processing of the whole carcass is complete.
            This will exist only if valuation is desired for the particular
            species. (Required if args['val_cont'] is True)

        unit_price (float): represents the price for a single unit of
            harvest. Exists only if valuation is desired. (Required if
            args['val_cont'] is True)

    Example Args Dictionary::

        args = {
            'workspace_dir': 'path/to/workspace_dir/',
            'aoi_uri': 'path/to/aoi_uri',
            'total_timesteps': 100,
            'population_type': 'Stage-Based',
            'sexsp': 'Yes',
            'harvest_units': 'Individuals',
            'do_batch': False,
            'population_csv_uri': 'path/to/csv_uri',
            'population_csv_dir': ''
            'spawn_units': 'Weight',
            'total_init_recruits': 100000.0,
            'recruitment_type': 'Ricker',
            'alpha': 32.4,
            'beta': 54.2,
            'total_recur_recruits': 92.1,
            'migr_cont': True,
            'migration_dir': 'path/to/mig_dir/',
            'val_cont': True,
            'frac_post_process': 0.5,
            'unit_price': 5.0,
        }
    '''

    # Parse Inputs
    model_list = io.fetch_args(args, create_outputs=create_outputs)

    # Run Models
    vars_all_models = []
    for model_args_dict in model_list:

        # Setup Model
        model_vars_dict = model.initialize_vars(model_args_dict)

        recru_func = model.set_recru_func(model_vars_dict)
        init_cond_func = model.set_init_cond_func(model_vars_dict)
        cycle_func = model.set_cycle_func(model_vars_dict, recru_func)
        harvest_func = model.set_harvest_func(model_vars_dict)

        # Run Model
        model_vars_dict = model.run_population_model(
            model_vars_dict, init_cond_func, cycle_func, harvest_func)

        vars_all_models.append(model_vars_dict)

        if create_outputs:
            # Create Outputs
            io.create_outputs(model_vars_dict)

    return vars_all_models
