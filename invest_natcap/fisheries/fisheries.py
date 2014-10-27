'''This will be the entry point for the fisheries tier 1 model.'''

import logging

import fisheries_io as io
import fisheries_model as model

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def execute(args):
    '''Main Function

    The following parameters are passed into this function via an 'args'
        dictionary:

    **General Parameters**
    :param string workspace_dir: location into which all intermediate and
        output files should be placed.
    :param string aoi_uri: location of shapefile which will be used as
        subregions for calculation. Each region must conatin a 'name'
        attribute which will
    :param int timesteps:represents the number of time steps that
        the user desires the model to run.

    **Population Parameters**
    :param string population_type: specifies whether the model
        is age-specific or stage-specific. Options will be either "Age
        Specific" or "Stage Specific" and will change which equation is
        used in modeling growth.
    :param string sexsp: specifies whether or not the age and stage
        classes are distinguished by sex.
    :param string population_csv_uri: location of the population parameters
        csv. This will contain all age and stage specific parameters.
    :param string spawn_units:

    **Recruitment Parameters**
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

    **Migration Parameters**
    :param bool migr_cont: if true, model uses migration
    :param string migration_dir: if this parameter exists, it means
        migration is desired. This is  the location of the parameters
        folder containing files for migration. There should be one file for
        every age class which migrates.

    **Harvest Parameters**
    :param bool harv_cont: if true, model runs harvest computations
    :param string harvest_units: specifies how the user wants to get
        the harvest data. Options are either "Individuals" or "Weight", and
        will change the harvest equation used in core.
    :param float frac_post_process: represents the fraction of the animal
        remaining after processing of the whole carcass is complete.
        This will exist only if valuation is desired for the particular
        species.
    :param float unit_price: represents the price for a single unit of
        harvest. Exists only if valuation is desired.

    **Example Input**
    args = {
        'workspace_dir': 'path/to/workspace_dir',
        'aoi_uri': 'path/to/aoi_uri',
        'total_timesteps': 100,
        'population_type': 'Stage-Based',
        'sexsp': 'Yes',
        'population_csv_uri': 'path/to/csv_uri',
        'spawn_units': 'Weight',
        'total_init_recruits': 100.0,
        'recruitment_type': 'Ricker',
        'alpha': 32.4,
        'beta': 54.2,
        'total_recur_recruits': 92.1,
        'migr_cont': True,
        'migration_dir': 'path/to/mig_dir',
        'harv_cont': True,
        'harvest_units': 'Individuals',
        'frac_post_process': 0.5,
        'unit_price': 5.0
    }
    '''
    # Parse Inputs
    vars_dict = io.fetch_verify_args(args)

    # Setup Model
    vars_dict = model.initialize_vars(vars_dict)
    recru_func = model.set_recru_func(vars_dict)
    init_cond_func = model.set_init_cond_func(vars_dict)
    cycle_func = model.set_cycle_func(vars_dict, recru_func)
    harvest_func = model.set_harvest_func(vars_dict)

    # Run Model
    vars_dict = model.run_population_model(
        vars_dict, init_cond_func, cycle_func, harvest_func)

    # Generate Outputs
    io.generate_outputs(vars_dict)
