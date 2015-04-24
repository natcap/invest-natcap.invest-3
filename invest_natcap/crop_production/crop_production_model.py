'''
The Crop Production Model module contains functions for running the model
'''

import os
import logging
import pprint

import gdal
import numpy as np

import crop_production_io as io
from raster import Raster
from vector import Vector
import pygeoprocessing.geoprocessing as pygeo

LOGGER = logging.getLogger('CROP_PRODUCTION')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

pp = pprint.PrettyPrinter(indent=4)

nodata_int = -9999
nodata_float = -16777216


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

    lulc_raster = Raster.from_file(
        vars_dict['lulc_map_uri']).set_nodata(nodata_int)
    aoi_vector = Vector.from_shapely(
        lulc_raster.get_aoi(), lulc_raster.get_projection())

    # setup useful base rasters
    base_raster_float = lulc_raster.set_datatype_and_nodata(
        gdal.GDT_Float64, nodata_float)

    if vars_dict['do_economic_returns']:
        returns_raster = base_raster_float.zeros()

    crops = vars_dict['crops_in_aoi_list']
    for crop in crops:
        LOGGER.debug('Calculating observed yield for %s' % crop)
        # Wrangle Data...
        observed_yield_over_aoi_raster = _get_observed_yield_from_dataset(
            vars_dict,
            crop,
            aoi_vector,
            base_raster_float)

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

        total_production = float(np.around(
            Production_raster.get_band(1).sum(), decimals=2))
        vars_dict['crop_production_dict'][crop] = total_production

        if vars_dict['do_economic_returns']:
            returns_raster += _calc_crop_returns(
                vars_dict,
                crop,
                lulc_raster,
                Production_raster,
                returns_raster,
                vars_dict['economics_table_dict'][crop])

        # Clean Up Rasters...
        del observed_yield_over_aoi_raster
        del ObservedLocalYield_raster
        del Production_raster

    if vars_dict['do_nutrition']:
        vars_dict = _calc_nutrition(vars_dict)

    # Results Table
    io.create_results_table(vars_dict)

    if all([vars_dict['do_economic_returns'],
            vars_dict['create_crop_production_maps']]):
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
        reproj_aoi_vector.uri).set_nodata(nodata_float)

    if clipped_crop_raster.get_shape() == (1, 1):
        observed_yield_val = float(clipped_crop_raster.get_band(1)[0, 0])
        aligned_crop_raster = observed_yield_val * base_raster_float.ones()
    else:
        # this reprojection could result in very long computation times
        reproj_crop_raster = clipped_crop_raster.reproject(
            base_raster_float.get_projection(),
            'nearest',
            base_raster_float.get_affine().a)

        aligned_crop_raster = reproj_crop_raster.align_to(
            base_raster_float, 'nearest')

    # print "\nAligned Crop Raster"
    # print aligned_crop_raster

    return aligned_crop_raster


def _get_yield_given_lulc(vars_dict, crop, lulc_raster, observed_yield_over_aoi_raster):
    masked_lulc_int_raster = _get_masked_lulc_raster(
        vars_dict, crop, lulc_raster)
    masked_lulc_raster = masked_lulc_int_raster.set_datatype_and_nodata(
        gdal.GDT_Float64, nodata_float)

    Yield_given_lulc_raster = observed_yield_over_aoi_raster * masked_lulc_raster

    # print "\nYield Given LULC"
    # print Yield_given_lulc_raster

    return Yield_given_lulc_raster


def _get_masked_lulc_raster(vars_dict, crop, lulc_raster):
    crop_lookup_dict = vars_dict['crop_lookup_dict']
    inv_crop_lookup_dict = {v: k for k, v in crop_lookup_dict.items()}

    reclass_table = {}
    for key in vars_dict['observed_yields_maps_dict'].keys():
        reclass_table[inv_crop_lookup_dict[key]] = 0
    reclass_table[inv_crop_lookup_dict[crop]] = 1

    masked_lulc_raster = lulc_raster.reclass(reclass_table)

    # print "\nMasked LULC Raster"
    # print masked_lulc_raster

    return masked_lulc_raster


def _calculate_production_for_crop(vars_dict, crop, yield_raster, percentile=None):
    '''
    '''
    ha_per_m2 = 0.0001
    ha_per_cell = yield_raster.get_cell_area() * ha_per_m2

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

    # print "\nProduction raster"
    # print Production_raster
    # print "Hectare per cell"
    # print ha_per_cell

    return Production_raster


def _calc_crop_returns(vars_dict, crop, lulc_raster, production_raster, returns_raster, economics_table):
    '''
    Cost_crop = CostPerTonInputTotal_crop + CostPerHectareInputTotal_crop
    Revenue_crop = Production_crop * Price_crop
    Returns_crop = Revenue_crop - Cost_crop
    '''
    cost_per_hectare_input_raster = _calc_cost_of_per_hectare_inputs(
        vars_dict, crop, lulc_raster)

    if vars_dict['fertilizer_maps_dir']:
        cost_per_ton_input_raster = _calc_cost_of_per_ton_inputs(
            vars_dict, crop, lulc_raster)

        cost_raster = cost_per_hectare_input_raster + cost_per_ton_input_raster
    else:
        cost_raster = cost_per_hectare_input_raster

    price = vars_dict['economics_table_dict'][crop]['price_per_tonne']
    revenue_raster = production_raster * price

    returns_raster = revenue_raster - cost_raster

    total_cost = float(np.around(
        cost_raster.get_band(1).sum(), decimals=2))
    total_revenue = float(np.around(
        revenue_raster.get_band(1).sum(), decimals=2))
    total_returns = float(np.around(
        returns_raster.get_band(1).sum(), decimals=2))

    vars_dict['economics_table_dict'][crop]['total_cost'] = total_cost
    vars_dict['economics_table_dict'][crop]['total_revenue'] = total_revenue
    vars_dict['economics_table_dict'][crop]['total_returns'] = total_returns

    # print "\n%s production raster" % crop
    # print production_raster
    # print "\n%s cost raster" % crop
    # print cost_raster
    # print "\n%s revenue raster" % crop
    # print revenue_raster
    # print "\n%s returns raster" % crop
    # print returns_raster

    return returns_raster


def _calc_cost_of_per_ton_inputs(vars_dict, crop, lulc_raster):
    '''
    sum_across_fert(FertAppRate_fert * LULCCropCellArea * CostPerTon_fert)
    '''

    economics_table_crop = vars_dict['economics_table_dict'][crop]
    fert_maps_dict = vars_dict['modeled_fertilizer_maps_dict']

    masked_lulc_raster = _get_masked_lulc_raster(vars_dict, crop, lulc_raster)
    masked_lulc_raster_float = masked_lulc_raster.set_datatype_and_nodata(
        gdal.GDT_Float64, nodata_float)

    CostPerTonInputTotal_raster = masked_lulc_raster_float.zeros()

    try:
        cost_nitrogen_per_kg = economics_table_crop['cost_nitrogen_per_kg']
        Nitrogen_raster = Raster.from_file(fert_maps_dict['nitrogen']).set_nodata(
            nodata_float)
        NitrogenCost_raster = Nitrogen_raster * cost_nitrogen_per_kg
        CostPerTonInputTotal_raster += NitrogenCost_raster
    except:
        pass
    try:
        cost_phosphorous_per_kg = economics_table_crop[
            'cost_phosphorous_per_kg']
        Phosphorous_raster = Raster.from_file(fert_maps_dict['nitrogen']).set_nodata(
            nodata_float)
        PhosphorousCost_raster = Phosphorous_raster * cost_phosphorous_per_kg
        CostPerTonInputTotal_raster += PhosphorousCost_raster
    except:
        pass
    try:
        cost_potash_per_kg = economics_table_crop['cost_potash_per_kg']
        Potash_raster = Raster.from_file(fert_maps_dict['potash']).set_nodata(
            nodata_float)
        PotashCost_raster = Potash_raster * cost_potash_per_kg
        CostPerTonInputTotal_raster += PotashCost_raster
    except:
        pass

    CostPerTonInputTotal_masked_raster = CostPerTonInputTotal_raster * masked_lulc_raster_float

    # print "\nCost Per Hectare Input Total Raster"
    # print CostPerTonInputTotal_masked_raster

    return CostPerTonInputTotal_masked_raster


def _calc_cost_of_per_hectare_inputs(vars_dict, crop, lulc_raster):
    '''
    CostPerHectareInputTotal_crop = Mask_raster * CostPerHectare_input * ha_per_cell
    '''
    economics_table_crop = vars_dict['economics_table_dict'][crop]
    masked_lulc_raster = _get_masked_lulc_raster(vars_dict, crop, lulc_raster)
    masked_lulc_raster_float = masked_lulc_raster.set_datatype_and_nodata(
        gdal.GDT_Float64, nodata_float)
    CostPerHectareInputTotal_raster = masked_lulc_raster_float.zeros()
    ha_per_m2 = 0.0001
    ha_per_cell = masked_lulc_raster.get_cell_area() * ha_per_m2

    try:
        cost_labor_per_cell = economics_table_crop['cost_labor_per_ha'] * ha_per_cell
        CostLabor_raster = masked_lulc_raster_float * cost_labor_per_cell 
        CostPerHectareInputTotal_raster += CostLabor_raster
    except:
        pass
    try:
        cost_machine_per_cell = economics_table_crop['cost_machine_per_ha'] * ha_per_cell
        CostMachine_raster = masked_lulc_raster_float * cost_machine_per_cell 
        CostPerHectareInputTotal_raster += CostMachine_raster
    except:
        pass
    try:
        cost_seed_per_cell = economics_table_crop['cost_seed_per_ha'] * ha_per_cell
        CostSeed_raster = masked_lulc_raster_float * cost_seed_per_cell
        CostPerHectareInputTotal_raster += CostSeed_raster
    except:
        pass
    try:
        cost_irrigation_per_cell = economics_table_crop['cost_irrigation_per_ha'] * ha_per_cell
        CostIrrigation_raster = masked_lulc_raster_float * cost_irrigation_per_cell
        CostPerHectareInputTotal_raster += CostIrrigation_raster
    except:
        pass

    CostPerHectareInputTotal_masked_raster = CostPerHectareInputTotal_raster * masked_lulc_raster_float

    # print "\nCost Per Hectare Input Total Raster"
    # print CostPerHectareInputTotal_masked_raster

    return CostPerHectareInputTotal_masked_raster


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

    lulc_raster = Raster.from_file(vars_dict['lulc_map_uri']).set_nodata(nodata_int)
    aoi_vector = Vector.from_shapely(
        lulc_raster.get_aoi(), lulc_raster.get_projection())
    percentile_yield_dict = vars_dict['percentile_yield_dict']

    # setup useful base rasters
    base_raster_float = lulc_raster.set_datatype_and_nodata(
        gdal.GDT_Float64, nodata_float)

    crops = vars_dict['crops_in_aoi_list']
    crop = crops[0]
    climate_bin = percentile_yield_dict[crop].keys()[0]
    percentiles = percentile_yield_dict[crop][climate_bin].keys()

    percentile_count = 1
    for percentile in percentiles:
        vars_dict['crop_production_dict'] = {}
        if vars_dict['do_economic_returns']:
            economics_table = vars_dict['economics_table_dict']
            returns_raster = base_raster_float.zeros()

        for crop in crops:
            LOGGER.debug('Calculating percentile yield for %s in %s' % (
                crop, percentile))
            # Wrangle Data...
            climate_bin_raster = _get_climate_bin_over_lulc(
                vars_dict, crop, aoi_vector, base_raster_float)

            reclass_dict = {}
            climate_bins = percentile_yield_dict[crop].keys()
            for climate_bin in climate_bins:
                reclass_dict[climate_bin] = percentile_yield_dict[
                    crop][climate_bin][percentile]

            # Find Yield and Production
            crop_yield_raster = climate_bin_raster.reclass(reclass_dict)

            masked_lulc_raster = _get_masked_lulc_raster(
                vars_dict, crop, lulc_raster).set_datatype_and_nodata(
                gdal.GDT_Float64, nodata_float)

            yield_raster = crop_yield_raster * masked_lulc_raster

            Production_raster = _calculate_production_for_crop(
                vars_dict, crop, yield_raster, percentile=percentile)

            total_production = float(np.around(
                Production_raster.get_band(1).sum(), decimals=2))
            vars_dict['crop_production_dict'][crop] = total_production

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

        if vars_dict['do_nutrition']:
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
    climate_bin_raster = Raster.from_file(
        vars_dict['climate_bin_maps_dict'][crop])

    reproj_aoi_vector = aoi_vector.reproject(
        climate_bin_raster.get_projection())

    clipped_climate_bin_raster = climate_bin_raster.clip(
        reproj_aoi_vector.uri).set_nodata(nodata_int)

    if clipped_climate_bin_raster.get_shape() == (1, 1):
        climate_bin_val = float(clipped_climate_bin_raster.get_band(
            1)[0, 0])
        aligned_climate_bin_raster = base_raster_float.ones() * climate_bin_val
    else:
        # note: this reprojection could result in very long computation times
        reproj_climate_bin_raster = clipped_climate_bin_raster.reproject(
            base_raster_float.get_projection(),
            'nearest',
            base_raster_float.get_affine().a)

        aligned_climate_bin_raster = reproj_climate_bin_raster.align_to(
            base_raster_float, 'nearest')

    return aligned_climate_bin_raster


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

    lulc_raster = Raster.from_file(
        vars_dict['lulc_map_uri']).set_nodata(nodata_int)
    aoi_vector = Vector.from_shapely(
        lulc_raster.get_aoi(), lulc_raster.get_projection())

    # setup useful base rasters
    base_raster_float = lulc_raster.set_datatype_and_nodata(
        gdal.GDT_Float64, nodata_float)

    vars_dict['crop_production_dict'] = {}
    if vars_dict['do_economic_returns']:
        economics_table = vars_dict['economics_table_dict']
        returns_raster = base_raster_float.zeros()

    crops = vars_dict['crops_in_aoi_list']
    for crop in crops:
        LOGGER.debug('Calculating regression yield for %s' % crop)
        # Wrangle data...
        climate_bin_raster = _get_climate_bin_over_lulc(
            vars_dict, crop, aoi_vector, base_raster_float)

        masked_lulc_raster = _get_masked_lulc_raster(
            vars_dict, crop, lulc_raster).set_datatype_and_nodata(
            gdal.GDT_Float64, nodata_float)

        # Operations as Noted in User's Guide...
        Yield_raster = _calc_regression_yield_for_crop(
            vars_dict,
            crop,
            climate_bin_raster)

        Yield_given_lulc_raster = Yield_raster * masked_lulc_raster

        Production_raster = _calculate_production_for_crop(
            vars_dict, crop, Yield_given_lulc_raster)

        total_production = float(np.around(
            Production_raster.get_band(1).sum(), decimals=2))
        vars_dict['crop_production_dict'][crop] = total_production

        if vars_dict['do_economic_returns']:
            returns_raster += _calc_crop_returns(
                vars_dict,
                crop,
                lulc_raster,
                Production_raster.set_nodata(nodata_float),
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
    if vars_dict['do_nutrition']:
        vars_dict = _calc_nutrition(vars_dict)

    # Results Table
    io.create_results_table(vars_dict)

    if all([vars_dict['do_economic_returns'],
            vars_dict['create_crop_production_maps']]):
        output_observed_yield_dir = vars_dict['output_yield_func_dir']
        returns_uri = os.path.join(
            output_observed_yield_dir, 'economic_returns_map.tif')
        returns_raster.save_raster(returns_uri)

    return vars_dict


def _calc_regression_yield_for_crop(vars_dict, crop, climate_bin_raster):
    '''returns crop_yield_raster'''

    # Fetch Fertilizer Maps
    fert_maps_dict = vars_dict['modeled_fertilizer_maps_dict']
    NitrogenAppRate_raster = Raster.from_file(
        fert_maps_dict['nitrogen']).set_nodata(nodata_float)
    PhosphorousAppRate_raster = Raster.from_file(
        fert_maps_dict['phosphorous']).set_nodata(nodata_float)
    PotashAppRate_raster = Raster.from_file(
        fert_maps_dict['potash']).set_nodata(nodata_float)
    Irrigation_raster = Raster.from_file(
        vars_dict['modeled_irrigation_map_uri']).set_nodata(nodata_float)

    irrigated_lulc_mask = (Irrigation_raster).set_datatype_and_nodata(
        gdal.GDT_Float64, nodata_float)
    rainfed_lulc_mask = (-Irrigation_raster + 1).set_datatype_and_nodata(
        gdal.GDT_Float64, nodata_float)

    # Create Rasters of Yield Parameters
    yield_params = vars_dict['modeled_yield_dict'][crop]

    nodata = climate_bin_raster.get_nodata(1)

    b_K2O = _create_reg_yield_reclass_dict(
        yield_params, 'b_K2O', nodata)
    b_nut = _create_reg_yield_reclass_dict(
        yield_params, 'b_nut', nodata)
    c_N = _create_reg_yield_reclass_dict(
        yield_params, 'c_N', nodata)
    c_P2O5 = _create_reg_yield_reclass_dict(
        yield_params, 'c_P2O5', nodata)
    c_K2O = _create_reg_yield_reclass_dict(
        yield_params, 'c_K2O', nodata)
    yc = _create_reg_yield_reclass_dict(
        yield_params, 'yield_ceiling', nodata)
    yc_rf = _create_reg_yield_reclass_dict(
        yield_params, 'yield_ceiling_rf', nodata)

    print b_K2O
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
    Yield_rainfed_raster = YieldCeilingRainfed_raster.minimum(
        MaxYield_raster) * rainfed_lulc_mask
    Yield_raster = Yield_irrigated_raster + Yield_rainfed_raster

    return Yield_raster


def _create_reg_yield_reclass_dict(dictionary, nested_key, nodata):
    reclass_dict = {}
    for k in dictionary.keys():
        reclass_dict[k] = dictionary[k][nested_key]
        # print reclass_dict[k]
    # reclass_dict[int(nodata)] = int(nodata)
    # print reclass_dict
    return reclass_dict


def _calc_nutrition(vars_dict):
    '''
    total_nutrient_amount = production_tons * nutrient_unit * (1 - fraction_refuse)

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
    crop_production_dict = vars_dict['crop_production_dict']
    crop_total_nutrition_dict = {}

    for crop in crop_production_dict.keys():
        production = crop_production_dict[crop]
        nutrition_row_per_unit = vars_dict['nutrition_table_dict'][crop]
        fraction_refuse = nutrition_row_per_unit['fraction_refuse']
        nutrition_row_total = {}
        for nutrient in nutrition_row_per_unit.keys():
            if nutrient == 'fraction_refuse':
                continue
            nutrient_unit = nutrition_row_per_unit[nutrient]
            if type(nutrient_unit) not in [int, float]:
                nutrient_unit = 0
            total_nutrient = float(np.around((
                production * nutrient_unit * (1 - fraction_refuse)),
                decimals=2))
            nutrition_row_total[nutrient] = total_nutrient
        crop_total_nutrition_dict[crop] = nutrition_row_total

    vars_dict['crop_total_nutrition_dict'] = crop_total_nutrition_dict
    return vars_dict
