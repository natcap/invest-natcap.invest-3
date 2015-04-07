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


def create_yield_func_output_folder(vars_dict, folder_name):
    '''
    Example Returns::

        vars_dict = {
            # ...

            'output_yield_func_dir': '/path/to/outputs/yield_func/',
            'output_production_maps_dir': '/path/to/outputs/yield_func/production/'
        }

    Output:
        .
        |-- [yield_func]
            |-- production

    '''
    if vars_dict['results_suffix']:
        folder_name = folder_name + '_' + vars_dict['results_suffix']
    output_yield_func_dir = os.path.join(vars_dict['output_dir'], folder_name)
    os.path.makedirs(output_yield_func_dir)
    vars_dict['output_yield_func_dir'] = output_yield_func_dir

    if vars_dict['create_crop_production_maps']:
        output_production_maps_dir = os.path.join(
            output_yield_func_dir, 'crop_production_maps')
        vars_dict['output_production_maps_dir'] = output_production_maps_dir

    return vars_dict


def calc_observed_yield(vars_dict):
    '''
    Creates yield maps from observed data and stores in the temporary yield
        folder

    Args:
        vars_dict (dict): descr

    Example Args::

        vars_dict = {
            # ...

            'lulc_map_uri': '/path/to/lulc_map_uri',
            'crop_lookup_dict': {
                'code': 'crop_name',
                ...
            },
            'observed_yields_maps_dict': {
                'crop': '/path/to/crop_climate_bin_map',
                ...
            },
            'economics_table_dict': {
                'crop': 2.3,
                ...
            },
        }
    '''
    vars_dict = create_yield_func_output_folder(
        vars_dict, "observed_yield")

    crop_production_dict = {}
    lulc_raster = Raster.from_file(vars_dict['lulc_map_uri'])
    aoi_vector = lulc_raster.get_aoi_as_vector()
    economics_table = vars_dict['economics_table_dict']
    if vars_dict['do_economic_returns']:
        revenue_raster = None  # ALL ZEROS

    for crop in vars_dict['observed_yields_maps_dict'].keys():
        global_crop_raster = Raster.from_file(
            vars_dict['observed_yields_maps_dict'][crop])

        reprojected_aoi = aoi_vector.reproject(
            global_crop_raster.get_projection())

        clipped_global_crop_raster = global_crop_raster.clip(
            reprojected_aoi.uri)

        reproj_crop_raster = clipped_global_crop_raster.reproject(
            lulc_raster.get_projection(), 'nearest')

        crop_raster = reproj_crop_raster.align_to(lulc_raster, 'nearest')

        reclass_table = {
            'crop': 1,
            'non-crop': 0
        }
        reclassed_lulc_raster = lulc_raster.reclass(reclass_table)

        crop_yield_per_ha_raster = reclassed_lulc_raster * crop_raster
        ha_per_cell = crop_yield_per_ha_raster.get_cell_area()
        crop_production_raster = crop_yield_per_ha_raster * ha_per_cell

        if vars_dict['create_crop_production_maps']:
            filename = crop + '_production_map.tif'
            dst_uri = os.path.join(vars_dict[
                'output_production_maps_dir'], filename)
            crop_production_raster.save_raster(dst_uri)

        total_production = crop_production_raster.get_band(1).sum()
        crop_production_dict[crop] = total_production

        if vars_dict['do_economic_returns']:
            revenue_raster += calc_crop_revenue(
                crop_production_raster,
                economics_table[crop])

        # Clean up rasters (del)
        del global_crop_raster
        del reprojected_aoi
        del clipped_global_crop_raster
        del reproj_crop_raster
        del crop_raster
        del reclassed_lulc_raster
        del crop_yield_per_ha_raster
        del crop_production_raster

    vars_dict['crop_production_dict'] = crop_production_dict

    # Economics map
    if vars_dict['do_economic_returns']:
        cost_per_ton_input_raster = 0
        if vars_dict['modeled_fertilizer_maps_dir']:
            cost_per_ton_input_raster = calc_cost_of_per_ton_inputs(
                vars_dict, lulc_raster)

        cost_per_hectare_input_raster = calc_cost_of_per_hectare_inputs()

        cost_raster = cost_per_hectare_input_raster + cost_per_ton_input_raster
        economic_returns_raster = revenue_raster - cost_raster

        economic_returns_map_uri = os.path.join(
            vars_dict['output_yield_func_dir'], 'economic_returns_map.tif')
        economic_returns_raster.save_raster(economic_returns_map_uri)

        del economic_returns_raster
        del cost_per_ton_input_raster
        del cost_per_hectare_input_raster
        del cost_raster
        del revenue_raster

    # Results Table
    create_results_table(vars_dict)

    return vars_dict


def calc_cost_of_per_ton_inputs(): pass
def calc_cost_of_per_hectare_inputs(): pass
def calc_crop_revenue(): pass


def calc_percentile_yield(vars_dict):
    '''
    Example Args::

        vars_dict = {
            ...

            '': '',
        }
    '''
    vars_dict = create_yield_func_output_folder(
        vars_dict, "climate_percentile_yield")
    pass


def calc_regression_yield(vars_dict):
    '''
    Example Args::

        vars_dict = {
            ...

            '': '',
        }
    '''
    vars_dict = create_yield_func_output_folder(
        vars_dict, "climate_regression_yield")
    pass


def calc_economic_returns(crop_production_raster, crop_economics_dict):
    '''
    '''

    # per ton
    price = crop_economics_dict['price']

    cost_nitrogen = crop_economics_dict['cost_nitrogen']
    cost_phosphorous = crop_economics_dict['cost_phosphorous']
    cost_potash = crop_economics_dict['cost_potash']

    # per hectare
    cost_labor = crop_economics_dict['cost_labor']
    cost_machine = crop_economics_dict['cost_machine']
    cost_seed = crop_economics_dict['cost_seed']
    cost_irrigation = crop_economics_dict['cost_irrigation']

    # 
    crop_returns_raster = crop_production_raster
    economic_returns_raster = economic_returns_raster_next


def create_results_table(vars_dict):
    '''
    Example Args::

        vars_dict = {
            ...

            'crop_production_dict': {
                'corn': 12.3,
                'soy': 13.4,
                ...
            },
            '': '',
        }
    '''
    pass
