'''
The Crop Production Model module contains functions for running the model
'''

import os
import logging
import pprint

import gdal
import numpy as np

import crop_production_io as io
from raster import Raster, RasterFactory
from vector import Vector
import pygeoprocessing.geoprocessing as pygeo

LOGGER = logging.getLogger('CROP_PRODUCTION')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

pp = pprint.PrettyPrinter(indent=4)


def calc_observed_yield(vars_dict):
    '''
    Creates yield maps from observed yield data

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
    vars_dict['crop_production_dict'] = {}
    vars_dict = _create_yield_func_output_folder(
        vars_dict, "observed_yield")

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

    for crop in vars_dict['observed_yields_maps_dict'].keys():
        # Check that crop is in LULC map, if not, skip

        # Wrangle Data...
        observed_yield_over_aoi_raster = _get_observed_yield_from_dataset(
            vars_dict,
            crop,
            aoi_vector,
            base_raster_float_neg1)

        ObservedLocalYield_raster = _get_yield_given_lulc(
            vars_dict,
            crop,
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
                lulc_raster,
                Production_raster,
                returns_raster,
                economics_table[crop])

        # print "\n%s returns raster" % crop
        # print returns_raster

        # Clean Up Rasters...
        del observed_yield_over_aoi_raster
        del ObservedLocalYield_raster
        del Production_raster

    # print "Final returns raster"
    # print returns_raster

    vars_dict = _calc_nutrition(vars_dict)

    # Results Table
    io.create_results_table(vars_dict)

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

    clipped_crop_raster_unkwn_nodata = crop_observed_yield_raster.clip(
        reproj_aoi_vector.uri)
    clipped_crop_raster = clipped_crop_raster_unkwn_nodata.set_nodata(-1)

    if clipped_crop_raster.get_shape() == (1, 1):
        observed_yield_val = float(clipped_crop_raster.get_band(1).data[0, 0])
        aligned_crop_raster = base_raster_float.ones() * observed_yield_val
    else:
        # this reprojection could result in very long computation times
        reproj_crop_raster = clipped_crop_raster.reproject(
            base_raster_float.get_projection(),
            'nearest',
            base_raster_float.get_affine().a)

        aligned_crop_raster = reproj_crop_raster.align_to(
            base_raster_float, 'nearest')

    return aligned_crop_raster


def _get_yield_given_lulc(vars_dict, crop, lulc_raster, observed_yield_over_aoi_raster):
    masked_lulc_raster = _get_masked_lulc_raster(vars_dict, crop, lulc_raster)
    masked_lulc_raster = masked_lulc_raster.set_datatype(
        gdal.GDT_Float32).set_nodata(
        observed_yield_over_aoi_raster.get_nodata(1))
    return masked_lulc_raster * observed_yield_over_aoi_raster


def _get_masked_lulc_raster(vars_dict, crop, lulc_raster):
    crop_lookup_dict = vars_dict['crop_lookup_dict']
    inv_crop_lookup_dict = {v: k for k, v in crop_lookup_dict.items()}

    reclass_table = {}
    for key in vars_dict['observed_yields_maps_dict'].keys():
        reclass_table[inv_crop_lookup_dict[key]] = 0
    reclass_table[inv_crop_lookup_dict[crop]] = 1

    return lulc_raster.reclass(reclass_table)


def _calculate_production_for_crop(vars_dict, crop, yield_raster, percentile=None):
    '''
    '''
    ha_per_m2 = 0.0001
    ha_per_cell = yield_raster.get_cell_area() * ha_per_m2  # or pass units into raster method?

    Production_raster = yield_raster * ha_per_cell

    if vars_dict['create_crop_production_maps'] and percentile is None:
        filename = crop + '_production_map.tif'
        dst_uri = os.path.join(vars_dict[
            'output_production_maps_dir'], filename)
        Production_raster.save_raster(dst_uri)

    elif vars_dict['create_crop_production_maps']:
        filename = crop + '_production_map_' + percentile + '.tif'
        dst_uri = os.path.join(vars_dict[
            'output_production_maps_dir'], filename)
        Production_raster.save_raster(dst_uri)

    return Production_raster


def _calc_crop_returns(vars_dict, crop, lulc_raster, production_raster, returns_raster, economics_table):
    '''
    Cost_crop = CostPerTonInputTotal_crop + CostPerHectareInputTotal_crop
    Revenue_crop = Production_crop * Price_crop
    Returns_crop = Revenue_crop - Cost_crop
    '''
    cost_per_ton_input_raster = 0
    cost_per_hectare_input_raster = _calc_cost_of_per_hectare_inputs(
        vars_dict, crop, lulc_raster)

    if vars_dict['modeled_fertilizer_maps_dir']:
        cost_per_ton_input_raster = _calc_cost_of_per_ton_inputs(
            vars_dict, crop, lulc_raster)

        cost_raster = cost_per_hectare_input_raster + cost_per_ton_input_raster
    else:
        cost_raster = cost_per_hectare_input_raster

    price = vars_dict['economics_table_dict'][crop]['price_per_ton']
    revenue_raster = production_raster * price

    # print "\n%s production raster" % crop
    # print production_raster
    # print "\n%s cost raster" % crop
    # print cost_raster
    # print "\n%s revenue raster" % crop
    # print revenue_raster

    returns_raster = revenue_raster - cost_raster

    vars_dict['economics_table_dict'][crop][
        'total_cost'] = cost_raster.get_band(1).data.sum()
    vars_dict['economics_table_dict'][crop][
        'total_revenue'] = revenue_raster.get_band(1).data.sum()
    vars_dict['economics_table_dict'][crop][
        'total_returns'] = returns_raster.get_band(1).data.sum()

    return returns_raster


def _calc_cost_of_per_ton_inputs(vars_dict, crop, lulc_raster):
    '''
    sum_across_fert(FertAppRate_fert * LULCCropCellArea * CostPerTon_fert)
    '''

    economics_table_crop = vars_dict['economics_table_dict'][crop]
    fert_maps_dict = vars_dict['modeled_fertilizer_maps_dict']

    masked_lulc_raster = _get_masked_lulc_raster(vars_dict, crop, lulc_raster)
    masked_lulc_raster_float = masked_lulc_raster.set_datatype(
        gdal.GDT_Float32).set_nodata(-1)

    CostPerTonInputTotal_raster = masked_lulc_raster_float.zeros()

    try:
        cost_nitrogen_per_ton = economics_table_crop['cost_nitrogen_per_ton']
        Nitrogen_raster = Raster.from_file(fert_maps_dict['nitrogen'])
        NitrogenCost_raster = Nitrogen_raster * cost_nitrogen_per_ton
        CostPerTonInputTotal_raster += NitrogenCost_raster.set_nodata(-1)
    except:
        pass
    try:
        cost_phosphorous_per_ton = economics_table_crop[
            'cost_phosphorous_per_ton']
        Phosphorous_raster = Raster.from_file(fert_maps_dict['nitrogen'])
        PhosphorousCost_raster = Phosphorous_raster * cost_phosphorous_per_ton
        CostPerTonInputTotal_raster += PhosphorousCost_raster.set_nodata(-1)
    except:
        pass
    try:
        cost_potash_per_ton = economics_table_crop['cost_potash_per_ton']
        Potash_raster = Raster.from_file(fert_maps_dict['potash'])
        PotashCost_raster = Potash_raster * cost_potash_per_ton
        CostPerTonInputTotal_raster += PotashCost_raster.set_nodata(-1)
    except:
        pass

    return CostPerTonInputTotal_raster * masked_lulc_raster_float


def _calc_cost_of_per_hectare_inputs(vars_dict, crop, lulc_raster):
    '''
    CostPerHectareInputTotal_crop = Mask_raster * CostPerHectare_input * ha_per_cell
    '''
    economics_table_crop = vars_dict['economics_table_dict'][crop]
    masked_lulc_raster = _get_masked_lulc_raster(vars_dict, crop, lulc_raster)
    masked_lulc_raster_float = masked_lulc_raster.set_datatype(
        gdal.GDT_Float32).set_nodata(-1)
    CostPerHectareInputTotal_raster = masked_lulc_raster_float * 0
    ha_per_m2 = 0.0001
    ha_per_cell = masked_lulc_raster.get_cell_area() * ha_per_m2
    try:
        cost_labor_per_ha = economics_table_crop['cost_labor_per_ha']
        CostLabor_raster = masked_lulc_raster_float * cost_labor_per_ha * ha_per_cell
        CostPerHectareInputTotal_raster += CostLabor_raster
    except:
        pass
    try:
        cost_machine_per_ha = economics_table_crop['cost_machine_per_ha']
        CostMachine_raster = masked_lulc_raster_float * cost_machine_per_ha * ha_per_cell
        CostPerHectareInputTotal_raster += CostMachine_raster
    except:
        pass
    try:
        cost_seed_per_ha = economics_table_crop['cost_seed_per_ha']
        CostSeed_raster = masked_lulc_raster_float * cost_seed_per_ha
        CostPerHectareInputTotal_raster += CostSeed_raster
    except:
        pass
    try:
        cost_irrigation_per_ha = economics_table_crop['cost_irrigation_per_ha']
        CostIrrigation_raster = masked_lulc_raster_float * cost_irrigation_per_ha * ha_per_cell
        CostPerHectareInputTotal_raster += CostIrrigation_raster
    except:
        pass

    return CostPerHectareInputTotal_raster


def calc_percentile_yield(vars_dict):
    '''
    Creates production maps based on a percentile yield table

    Example Args::

        vars_dict = {
            'percentile_yield_dict': {
                ''
            },
            '': ''
        }
    '''
    # pp.pprint(vars_dict['percentile_yield_dict'])

    vars_dict['crop_production_dict'] = {}
    vars_dict = _create_yield_func_output_folder(
        vars_dict, "climate_percentile_yield")

    lulc_raster = Raster.from_file(vars_dict['lulc_map_uri'])
    aoi_vector = Vector.from_shapely(
        lulc_raster.get_aoi(), lulc_raster.get_projection())
    economics_table = vars_dict['economics_table_dict']
    percentile_yield_dict = vars_dict['percentile_yield_dict']

    # setup useful base rasters
    base_raster_float = lulc_raster.set_datatype(gdal.GDT_Float32)
    base_raster_float_neg1 = base_raster_float.set_nodata(-1)
    base_raster_zeros_float_neg1 = base_raster_float_neg1.zeros()

    crops = percentile_yield_dict.keys()
    crop = percentile_yield_dict.keys()[0]
    c_bin = percentile_yield_dict[crop].keys()[0]
    percentiles = percentile_yield_dict[crop][c_bin].keys()

    percentile_count = 1
    for percentile in percentiles:
        vars_dict['crop_production_dict'] = {}
        if vars_dict['do_economic_returns']:
            returns_raster = base_raster_zeros_float_neg1.copy()

        for crop in crops:
            # ...
            # print "Yield for:", percentile, crop
            climate_bin_raster = _get_climate_bin_over_lulc(
                vars_dict, crop, aoi_vector, base_raster_float).set_nodata(-1)

            reclass_dict = {}
            bins = percentile_yield_dict[crop].keys()
            for c_bin in bins:
                reclass_dict[c_bin] = percentile_yield_dict[
                    crop][c_bin][percentile]

            crop_yield_raster = climate_bin_raster.reclass(reclass_dict)

            masked_lulc_raster = _get_masked_lulc_raster(
                vars_dict, crop, lulc_raster)

            yield_raster = crop_yield_raster * masked_lulc_raster.set_nodata(-1)

            Production_raster = _calculate_production_for_crop(
                vars_dict, crop, yield_raster, percentile=percentile)

            vars_dict['crop_production_dict'][crop] = Production_raster.get_band(1).sum()

            if vars_dict['do_economic_returns']:
                returns_raster += _calc_crop_returns(
                    vars_dict,
                    crop,
                    lulc_raster,
                    Production_raster,
                    returns_raster,
                    economics_table[crop])

            # Clean Up Rasters...
            del climate_bin_raster
            del crop_yield_raster
            del masked_lulc_raster
            del yield_raster
            del Production_raster

        vars_dict = _calc_nutrition(vars_dict)

        # Results Table
        if percentile_count == 1:
            io.create_results_table(vars_dict, percentile=percentile)
        else:
            io.create_results_table(vars_dict, percentile=percentile, first=False)
        percentile_count += 1

        if all([vars_dict['do_economic_returns'], vars_dict[
                'create_crop_production_maps']]):
            output_observed_yield_dir = vars_dict['output_yield_func_dir']
            returns_uri = os.path.join(
                output_observed_yield_dir,
                'economic_returns_map_' + percentile + '.tif')
            returns_raster.save_raster(returns_uri)

    return vars_dict


def _get_climate_bin_over_lulc(vars_dict, crop, aoi_vector, base_raster_float):
    '''
    '''
    crop_observed_yield_raster = Raster.from_file(
        vars_dict['climate_bin_maps_dict'][crop])

    reproj_aoi_vector = aoi_vector.reproject(
        crop_observed_yield_raster.get_projection())

    clipped_crop_raster_unkwn_nodata = crop_observed_yield_raster.clip(
        reproj_aoi_vector.uri)
    clipped_crop_raster = clipped_crop_raster_unkwn_nodata.set_nodata(-1)

    if clipped_crop_raster.get_shape() == (1, 1):
        observed_yield_val = float(clipped_crop_raster.get_band(1).data[0, 0])
        aligned_crop_raster = base_raster_float.ones() * observed_yield_val
    else:
        # this reprojection could result in very long computation times
        reproj_crop_raster = clipped_crop_raster.reproject(
            base_raster_float.get_projection(),
            'nearest',
            base_raster_float.get_affine().a)

        aligned_crop_raster = reproj_crop_raster.align_to(
            base_raster_float, 'nearest')

    return aligned_crop_raster


def calc_regression_yield(vars_dict):
    '''
    Example Args::

        vars_dict = {
            ...

            '': '',
        }
    '''
    vars_dict = _create_yield_func_output_folder(
        vars_dict, "climate_regression_yield")

    lulc_raster = Raster.from_file(vars_dict['lulc_map_uri'])
    aoi_vector = Vector.from_shapely(
        lulc_raster.get_aoi(), lulc_raster.get_projection())
    economics_table = vars_dict['economics_table_dict']

    # setup useful base rasters
    base_raster_float = lulc_raster.set_datatype(gdal.GDT_Float32)
    base_raster_float_neg1 = base_raster_float.set_nodata(-1)
    base_raster_zeros_float_neg1 = base_raster_float_neg1.zeros()

    vars_dict['crop_production_dict'] = {}
    if vars_dict['do_economic_returns']:
        returns_raster = base_raster_zeros_float_neg1.copy()

    for crop in vars_dict['modeled_yield_dict'].keys():
        # print "Yield for:", crop
        # Check that crop is in LULC map, if not, skip

        # Wrangle data...
        climate_bin_raster = _get_climate_bin_over_lulc(
            vars_dict, crop, aoi_vector, base_raster_float).set_nodata(-9999)

        Yield_raster = _calc_regression_yield_for_crop(
            vars_dict,
            crop,
            climate_bin_raster)
        # print crop_yield_raster

        masked_lulc_raster = _get_masked_lulc_raster(
            vars_dict, crop, lulc_raster)

        Yield_given_lulc_raster = Yield_raster * masked_lulc_raster.set_nodata(-9999)

        Production_raster = _calculate_production_for_crop(
            vars_dict, crop, Yield_given_lulc_raster)

        # print "PRODUCTION RASTER"
        # print Production_raster

        vars_dict['crop_production_dict'][crop] = Production_raster.get_band(1).sum()

        if vars_dict['do_economic_returns']:
            returns_raster += _calc_crop_returns(
                vars_dict,
                crop,
                lulc_raster,
                Production_raster.set_nodata(-1),
                returns_raster,
                economics_table[crop])

        # Clean Up Rasters...
        del climate_bin_raster
        del Yield_raster
        del masked_lulc_raster
        del Yield_given_lulc_raster
        del Production_raster

    # print "RETURNS RASTER"
    # print returns_raster
    vars_dict = _calc_nutrition(vars_dict)

    # Results Table
    io.create_results_table(vars_dict)

    if all([vars_dict['do_economic_returns'], vars_dict['create_crop_production_maps']]):
        output_observed_yield_dir = vars_dict['output_yield_func_dir']
        returns_uri = os.path.join(
            output_observed_yield_dir, 'economic_returns_map.tif')
        returns_raster.save_raster(returns_uri)

    return vars_dict


def _calc_regression_yield_for_crop(vars_dict, crop, climate_bin_raster):
    '''returns crop_yield_raster'''
    climate_bin_raster = climate_bin_raster.set_nodata(-9999)
    # Fetch Fertilizer Maps
    fert_maps_dict = vars_dict['modeled_fertilizer_maps_dict']
    NitrogenAppRate_raster = Raster.from_file(
        fert_maps_dict['nitrogen']).set_nodata(-9999)
    PhosphorousAppRate_raster = Raster.from_file(
        fert_maps_dict['phosphorous']).set_nodata(-9999)
    PotashAppRate_raster = Raster.from_file(
        fert_maps_dict['potash']).set_nodata(-9999)
    Irrigation_raster = Raster.from_file(
        vars_dict['modeled_irrigation_map_uri']).set_nodata(-9999)

    irrigated_lulc_mask = Irrigation_raster
    rainfed_lulc_mask = -Irrigation_raster + 1

    # Create Rasters of Yield Parameters
    yield_params = vars_dict['modeled_yield_dict'][crop]
    b_K2O = _create_reg_yield_reclass_dict(yield_params, 'b_K2O')

    b_nut = _create_reg_yield_reclass_dict(yield_params, 'b_nut')
    c_N = _create_reg_yield_reclass_dict(yield_params, 'c_N')
    c_P2O5 = _create_reg_yield_reclass_dict(yield_params, 'c_P2O5')
    c_K2O = _create_reg_yield_reclass_dict(yield_params, 'c_K2O')
    yc = _create_reg_yield_reclass_dict(yield_params, 'yield_ceiling')
    yc_rf = _create_reg_yield_reclass_dict(yield_params, 'yield_ceiling_rf')

    b_K2O_raster = climate_bin_raster.reclass(b_K2O)
    b_nut_raster = climate_bin_raster.reclass(b_nut)
    c_N_raster = climate_bin_raster.reclass(c_N)
    c_P2O5_raster = climate_bin_raster.reclass(c_P2O5)
    c_K2O_raster = climate_bin_raster.reclass(c_K2O)
    YieldCeiling_raster = climate_bin_raster.reclass(yc)
    YieldCeilingRainfed_raster = climate_bin_raster.reclass(yc_rf)

    # Operations as Noted in User's Guide...
    PercentMaxYieldNitrogen_raster = 1 - (
        b_nut_raster * (np.e ** -c_N_raster) * NitrogenAppRate_raster)
    PercentMaxYieldPhosphorous_raster = 1 - (
        b_nut_raster * (np.e ** -c_P2O5_raster) * PhosphorousAppRate_raster)
    PercentMaxYieldPotassium_raster = 1 - (
        b_K2O_raster * (np.e ** -c_K2O_raster) * PotashAppRate_raster)

    PercentMaxYield_raster = (PercentMaxYieldNitrogen_raster.minimum(
        PercentMaxYieldPhosphorous_raster.minimum(
            PercentMaxYieldPotassium_raster)))

    MaxYield_raster = PercentMaxYield_raster * YieldCeiling_raster
    Yield_irrigated_raster = MaxYield_raster * irrigated_lulc_mask
    Yield_rainfed_raster = YieldCeilingRainfed_raster.minimum(MaxYield_raster) * rainfed_lulc_mask
    Yield_raster = Yield_irrigated_raster + Yield_rainfed_raster

    return Yield_raster


def _create_reg_yield_reclass_dict(dictionary, nested_key):
    reclass_dict = {}
    for k in dictionary.keys():
        reclass_dict[k] = dictionary[k][nested_key]
    return reclass_dict


def _calc_nutrition(vars_dict):
    '''
    total_nutrient_amount = production_tons * nutrient_unit * conversion_unit

    Example Args::

        vars_dict = {
            'crop_production_dict': {
                'corn': 12.3,
                'soy': 13.4,
                ...
            },
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
            }
        }

    Example Returns::

        vars_dict = {
            ...
            'crop_total_nutrition_dict': {
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
                }
            }
        }
    '''
    conversion_unit = 1.0  # THIS NEEDS TO BE FILLED IN (ideally per ton)
    crop_production_dict = vars_dict['crop_production_dict']
    nutrition_table_dict = vars_dict['nutrition_table_dict']
    crop_total_nutrition_dict = {}

    for crop in crop_production_dict.keys():
        production = crop_production_dict[crop]
        nutrition_row_per_unit = nutrition_table_dict[crop]
        nutrition_row_total = {}
        for nutrient in nutrition_row_per_unit.keys():
            nutrient_unit = nutrition_row_per_unit[nutrient]
            nutrition_row_total[
                nutrient] = production * nutrient_unit * conversion_unit
        crop_total_nutrition_dict[crop] = nutrition_row_total

    vars_dict['crop_total_nutrition_dict'] = crop_total_nutrition_dict
    return vars_dict
