'''
The Crop Production module contains the high-level code for excuting the Crop
Production model
'''

import logging
import pprint as pp

import crop_production_io as io
import crop_production_model as model

LOGGER = logging.getLogger('CROP_PRODUCTION')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def execute(args, create_outputs=True):
    '''
    Entry point into the Crop Production Model

    :param str args['workspace_dir']: location into which all intermediate
        and output files should be placed.

    :param str args['results_suffix']: a string to append to output filenames

    :param str args['lulc_map_uri']: a GDAL-supported raster representing a
        crop management scenario.

    :param str args['crop_lookup_table_uri']: filepath to a CSV table used to
        convert the crop code provided in the Crop Map to the crop name that
        can be used for searching through inputs and formatting outputs.

    :param str args['spatial_dataset_dir']: the provided folder should contain
        a set of folders and data specified in the 'Running the Model' section
        of the model's User Guide.

    :param boolean args['create_crop_production_maps']: If True, a set of crop
        production maps is saved within the folder of each yield function.

    :param boolean args['do_yield_observed']: if True, calculates yield based
        on observed yields within region and creates associated outputs.

    :param boolean args['do_yield_percentile']: if True, calculates yield based
        on climate-specific distribution of observed yields and creates
        associated outputs

    :param boolean args['do_yield_modeled']: if True, calculates yield based on
        yield regression model with climate-specific parameters and creates
        associated outputs

    :param str args['modeled_fertilizer_maps_dir']: filepath to folder that
        should contain a set of GDAL-supported rasters representing the amount
        of Nitrogen (N), Phosphorous (P2O5), and Potash (K2O) applied to each
        area of land (kg/ha).

    :param str args['modeled_irrigation_map_uri']: filepath to a GDAL-supported
        raster representing whether irrigation occurs or not. A zero value
        indicates that no irrigation occurs.  A one value indicates that
        irrigation occurs.  If any other values are provided, irrigation is
        assumed to occur within that cell area.

    :param boolean args['do_nutrition']: if true, calculates nutrition from
        crop production and creates associated outputs.

    :param str args['nutrition_table_uri']: filepath to a CSV table containing
        information about the nutrient contents of each crop.

    :param boolean args['do_economic_returns']: if true, calculates economic
        returns from crop production and creates associated outputs.

    :param str args['economics_table_uri']: filepath to a CSV table containing
        information related to market price of a given crop and the expenses
        involved with producing that crop.

    Example Args::

        args = {
            'workspace_dir': 'path/to/workspace_dir/',
            'results_suffix': 'scenario_name',
            'lulc_map_uri': 'path/to/lulc_map_uri',
            'crop_lookup_table_uri': 'path/to/crop_lookup_table_uri',
            'spatial_dataset_dir': 'path/to/spatial_dataset_dir/',
            'create_crop_production_maps': True,
            'do_yield_observed': True,
            'do_yield_percentile': True,
            'do_yield_modeled': True,
            'modeled_fertilizer_maps_dir': 'path/to/modeled_fertilizer_maps_dir/',
            'modeled_irrigation_map_uri': 'path/to/modeled_irrigation_map_uri/',
            'do_nutrition': True,
            'nutrition_table_uri': 'path/to/nutrition_table_uri',
            'do_economic_returns': True,
            'economics_table_uri': 'path/to/economics_table_uri',
        }

    '''
    args['create_outputs'] = create_outputs

    if all(args['do_yield_observed'],
           args['do_yield_observed'],
           args['do_yield_observed']) is False:
        LOGGER.error('No Yield Function Selected.  Cannot Run Model.')
        return

    # Parse Inputs
    vars_dict = io.fetch_args(args)

    # Setup Temporary Folder
    vars_dict = io.setup_tmp(vars_dict)

    # Run Model ...
    observed_vars_dict = {}
    percentile_vars_dict = {}
    modeled_vars_dict = {}

    # Observed Yield Function
    if vars_dict['do_yield_observed']:
        # Calculate Yield
        observed_vars_dict = model.calc_yield_observed(vars_dict)

        # Calculate Nutrition
        if vars_dict['do_nutrition']:
            observed_vars_dict = model.calc_nutrition(vars_dict)

        # Calculate Economic Returns
        if vars_dict['do_economic_returns']:
            observed_vars_dict = model.calc_economic_returns(vars_dict)

        # Create Outputs
        if create_outputs:
            io.create_outputs()

    # Percentile Yield Function
    if vars_dict['do_yield_percentile']:
        # Calculate Yield
        percentile_vars_dict = model.calc_yield_percentile(vars_dict)

        # Calculate Nutrition
        if vars_dict['do_nutrition']:
            percentile_vars_dict = model.calc_nutrition(vars_dict)

        # Calculate Economic Returns
        if vars_dict['do_economic_returns']:
            percentile_vars_dict = model.calc_economic_returns(vars_dict)

        # Create Outputs
        if create_outputs:
            io.create_outputs()

    # Modeled Yield Function
    if vars_dict['do_yield_modeled']:
        # Calculate Yield
        modeled_vars_dict = model.calc_yield_modeled(vars_dict)

        # Calculate Nutrition
        if vars_dict['do_nutrition']:
            modeled_vars_dict = model.calc_nutrition(vars_dict)

        # Calculate Economic Returns
        if vars_dict['do_economic_returns']:
            modeled_vars_dict = model.calc_economic_returns(
                vars_dict)

        # Create Outputs
        if create_outputs:
            io.create_outputs()

    return observed_vars_dict, percentile_vars_dict, modeled_vars_dict
