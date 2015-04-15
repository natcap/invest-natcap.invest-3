'''
The Crop Production Model module contains functions for running the model
'''

import os
import logging
import pprint
import gdal

from raster import Raster, RasterFactory
from vector import Vector
import pygeoprocessing.geoprocessing as pygeo

LOGGER = logging.getLogger('CROP_PRODUCTION')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

pp = pprint.PrettyPrinter(indent=4)


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
                'crop': {
                    'price': <float>,
                    ...
                }
                ...
            },
        }
    '''
    # pp.pprint(vars_dict)
    vars_dict = _create_yield_func_output_folder(
        vars_dict, "observed_yield")

    crop_production_dict = {}
    lulc_raster = Raster.from_file(vars_dict['lulc_map_uri'])
    aoi_vector = Vector.from_shapely(
        lulc_raster.get_aoi(), lulc_raster.get_projection())
    economics_table = vars_dict['economics_table_dict']

    # setup useful base rasters
    base_raster_float = lulc_raster.set_datatype(gdal.GDT_Float32)
    base_raster_float_neg1 = base_raster_float.set_nodata(-1)
    base_raster_zeros_float_neg1 = base_raster_float_neg1.zeros()

    if vars_dict['do_economic_returns']:
        returns_raster = base_raster_zeros_float_neg1.copy()
        # print returns_raster
        return

    for crop in vars_dict['observed_yields_maps_dict'].keys():
        # Check that crop is in LULC map, if not, skip

        # Wrangle Data...
        observed_yield_over_aoi_raster = _get_observed_yield_from_dataset(
            vars_dict,
            crop,
            aoi_vector)

        ObservedLocalYield_raster = _get_yield_given_lulc(
            vars_dict,
            lulc_raster,
            observed_yield_over_aoi_raster)

        # Operations as Noted in User's Guide...
        Production_raster = _calculate_production_for_crop(
            vars_dict,
            crop,
            ObservedLocalYield_raster)

        vars_dict['crop_production_dict'][crop] = Production_raster.get_band(1).sum()

        if vars_dict['do_economic_returns']:
            returns_raster += _calc_crop_returns(
                vars_dict,
                crop,
                Production_raster,
                returns_raster,
                economics_table[crop])

        # Clean Up Rasters...
        del observed_yield_over_aoi_raster
        del ObservedLocalYield_raster
        del Production_raster

    # Results Table
    _create_results_table(vars_dict)

    if all([vars_dict['do_economic_returns'], vars_dict['create_crop_production_maps']]):
        output_observed_yield_dir = vars_dict['output_yield_func_dir']
        returns_uri = os.path.join(
            output_observed_yield_dir, 'economic_returns_map.tif')
        returns_raster.save_raster(returns_uri)

    return vars_dict


def _create_yield_func_output_folder(vars_dict, folder_name):
    '''
    Example Returns::

        vars_dict = {
            # ...

            'output_yield_func_dir': '/path/to/outputs/yield_func/',
            'output_production_maps_dir': '/path/to/outputs/yield_func/production/'
        }

    Output:
        .
        |-- [yield_func]_[results_suffix]
            |-- production

    '''
    if vars_dict['results_suffix']:
        folder_name = folder_name + '_' + vars_dict['results_suffix']
    output_yield_func_dir = os.path.join(vars_dict['output_dir'], folder_name)
    if not os.path.exists(output_yield_func_dir):
        os.makedirs(output_yield_func_dir)
    vars_dict['output_yield_func_dir'] = output_yield_func_dir

    if vars_dict['create_crop_production_maps']:
        output_production_maps_dir = os.path.join(
            output_yield_func_dir, 'crop_production_maps')
        if not os.path.exists(output_production_maps_dir):
            os.makedirs(output_production_maps_dir)
        vars_dict['output_production_maps_dir'] = output_production_maps_dir

    return vars_dict


def _get_observed_yield_from_dataset(vars_dict, crop, aoi_vector, base_raster_float):
    '''
    '''
    crop_observed_yield_raster = Raster.from_file(
        vars_dict['observed_yields_maps_dict'][crop])

    reproj_aoi_vector = aoi_vector.reproject(
        crop_observed_yield_raster.get_projection())

    clipped_crop_raster = crop_observed_yield_raster.clip(
        reproj_aoi_vector.uri)

    if clipped_crop_raster.get_shape() == (1, 1):
        observed_yield_val = float(clipped_crop_raster.get_band(1).data[0, 0])
        aligned_crop_raster = base_raster_float.ones() * observed_yield_val
    else:
        # this reprojection could result in very long computation times
        reproj_crop_raster = clipped_crop_raster.reproject(
            lulc_raster.get_projection(), 'nearest', lulc_raster.get_affine().a)

        aligned_crop_raster = reproj_crop_raster.align_to(
            base_raster_float, 'nearest')

    return aligned_crop_raster


def _get_yield_given_lulc(vars_dict, crop, lulc_raster, observed_yield_over_aoi_raster):
    crop_lookup_dict = vars_dict['crop_lookup_dict']
    inv_crop_lookup_dict = {v: k for k, v in crop_lookup_dict.items()}

    reclass_table = {}
    for key in vars_dict['observed_yields_maps_dict'].keys():
        reclass_table[inv_crop_lookup_dict[key]] = 0
    reclass_table[inv_crop_lookup_dict[crop]] = 1

    reclassed_lulc_raster = lulc_raster.reclass(reclass_table)
    masked_lulc_raster = reclassed_lulc_raster.set_datatype(
        gdal.GDT_Float32).set_nodata(
        observed_yield_over_aoi_raster.get_nodata(1))
    return masked_lulc_raster * observed_yield_over_aoi_raster


def _calculate_production_for_crop(vars_dict, crop, ObservedLocalYield_raster):
    '''
    '''
    ha_per_m2 = 0.0001
    ha_per_cell = ObservedLocalYield_raster.get_cell_area() * ha_per_m2  # or pass units into raster method?

    Production_raster = ObservedLocalYield_raster * ha_per_cell

    if vars_dict['create_crop_production_maps']:
        filename = crop + '_production_map.tif'
        dst_uri = os.path.join(vars_dict[
            'output_production_maps_dir'], filename)
        Production_raster.save_raster(dst_uri)

    return Production_raster


def _calc_crop_returns(vars_dict, crop, production_raster, returns_raster, economics_table):
    '''
    Cost_crop = CostPerTonInputTotal_crop + CostPerHectareInputTotal_crop
    Revenue_crop = Production_crop * Price_crop
    Returns_crop = Revenue_crop - Cost_crop
    '''
    cost_per_ton_input_raster = 0
    if vars_dict['modeled_fertilizer_maps_dir']:
        cost_per_ton_input_raster = _calc_cost_of_per_ton_inputs(
            vars_dict, lulc_raster, production_raster)

    cost_per_hectare_input_raster = _calc_cost_of_per_hectare_inputs()

    cost_raster = cost_per_hectare_input_raster + cost_per_ton_input_raster

    price = vars_dict['economics_table_dict'][crop]['price_per_ton']
    revenue_raster = production_raster * price
    returns_raster = revenue_raster - cost_raster

    return returns_raster


def _calc_cost_of_per_ton_inputs(vars_dict, lulc_raster, production_raster):
    '''
    sum_across_fert(FertAppRate_fert * LULCCropCellArea * CostPerTon_fert)
    '''
    CostPerTonInputTotal_raster = revenue_raster.set_datatype(gdal.GDT_Float32) * 0
    try:
        cost_nitrogen_per_ton = economics_table_crop['cost_nitrogen_per_ton']
        Nitrogen_raster = Raster.from_file(fert_maps_dict['nitrogen'])
        NitrogenCost_raster = Nitrogen_raster * cost_nitrogen_per_ton
        CostPerTonInputTotal_raster += NitrogenCost_raster
    except:
        pass
    try:
        cost_phosphorous_per_ton = economics_table_crop['cost_phosphorous_per_ton']
        PhosphorousCost_raster = Phosphorous_raster * cost_phosphorous_per_ton
        CostPerTonInputTotal_raster += PhosphorousCost_raster
    except:
        pass
    try:
        cost_potash_per_ton = economics_table_crop['cost_potash_per_ton']
        Potash_raster = Raster.from_file(fert_maps_dict['potash'])
        PotashCost_raster = Potash_raster * cost_potash_per_ton
        CostPerTonInputTotal_raster += PotashCost_raster
    except:
        pass

    return CostPerTonInputTotal_raster


def _calc_cost_of_per_hectare_inputs():
    '''

    '''
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


def _create_results_table(vars_dict):
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
