import tempfile
import os

import numpy as np
from affine import Affine
import gdal

from raster import *

workspace_dir = '../../../test/invest-data/test/data/crop_production/'
input_dir = os.path.join(os.path.realpath(__file__), 'data/')

# AOI Parameters
aoi_dict = {
    'shape': (3, 3),
    'affine': Affine.identity(),
    'proj': 32633
}


def create_lulc_map(aoi_dict):
    # set arguments
    array = np.ones(aoi_dict['shape'])
    affine = aoi_dict['affine']
    proj = aoi_dict['proj']
    datatype = gdal.GDT_Float64
    nodata_val = -9999.0

    # initialize raster
    return Raster.from_array(array, affine, proj, datatype, nodata_val)


def create_global_map():
    shape = (180, 360)
    affine = Affine(1, 0, -180, 0, -1, 90)
    proj = 4326
    datatype = gdal.GDT_Float64
    nodata_val = -9999

    global_raster_factory = RasterFactory(
        proj,
        datatype,
        nodata_val,
        shape[0],
        shape[1],
        affine=affine)

    return global_raster_factory.horizontal_ramp(1.0, 10.0)


def create_observed_yield_maps_dir():
    temp_dir = tempfile.mkdtemp()

    corn_raster = create_global_map()
    rice_raster = create_global_map()
    soy_raster = create_global_map()

    corn_raster.save_raster(os.path.join(temp_dir, 'corn_yield.tif'))
    rice_raster.save_raster(os.path.join(temp_dir, 'rice_yield.tif'))
    soy_raster.save_raster(os.path.join(temp_dir, 'soy_yield.tif'))

    return temp_dir


def create_irrigation_map(aoi_dict):
    # set arguments
    array = np.ones(aoi_dict['shape'])
    affine = aoi_dict['affine']
    proj = aoi_dict['proj']
    datatype = gdal.GDT_Int32
    nodata_val = -1

    # initialize raster
    return Raster.from_array(array, affine, proj, datatype, nodata_val)


def create_fertilizer_map(aoi_dict):
    # set arguments
    array = np.ones(aoi_dict['shape'])
    affine = aoi_dict['affine']
    proj = aoi_dict['proj']
    datatype = gdal.GDT_Float64
    nodata_val = -9999.0

    # initialize raster
    return Raster.from_array(array, affine, proj, datatype, nodata_val)


def create_fertilizer_maps_dir(aoi_dict):
    temp_dir = tempfile.mkdtemp()

    nitrogen_raster = create_fertilizer_map(aoi_dict)
    phosphorous_raster = create_fertilizer_map(aoi_dict)
    potash_raster = create_fertilizer_map(aoi_dict)

    nitrogen_raster.save_raster(os.path.join(temp_dir, 'nitrogen.tif'))
    phosphorous_raster.save_raster(os.path.join(temp_dir, 'phosphorous.tif'))
    potash_raster.save_raster(os.path.join(temp_dir, 'potash.tif'))

    return temp_dir


def get_args():

    args = {
        'workspace_dir': workspace_dir,
        'results_suffix': 'scenario_name',
        'lulc_map_uri': create_lulc_map(aoi_dict).uri,
        'crop_lookup_table_uri': os.path.join(
            input_dir, 'crop_lookup_table.csv'),
        'spatial_dataset_dir': os.path.join(input_dir, 'spatial_dataset'),
        'create_crop_production_maps': True,
        'do_yield_observed': True,
        'do_yield_percentile': True,
        'do_yield_regression_model': True,
        'modeled_fertilizer_maps_dir': create_fertilizer_maps_dir(aoi_dict),
        'modeled_irrigation_map_uri': create_irrigation_map(aoi_dict).uri,
        'do_nutrition': True,
        'nutrition_table_uri': os.path.join(input_dir, 'nutrition_table.csv'),
        'do_economic_returns': True,
        'economics_table_uri': os.path.join(input_dir, 'economics_table.csv')
    }

    return args


def get_vars_dict():

    args = get_args()

    derived_vars = {
        'observed_yield_maps_dir': create_observed_yield_maps_dir(),
        'percentile_yield_tables_dir': os.path.join(
            input_dir, 'climate_percentile_yield'),
        'percentile_yield_dict': {},
        'crop_lookup_dict': {},
        'economics_table_dict': {},
        'climate_bin_maps_dir': os.path.join(input_dir, 'climate_bin_maps'),
        'modeled_fertilizer_maps_dict': {},
        'modeled_yield_tables_dir': os.path.join(
            input_dir, 'climate_regression_yield'),
        'modeled_yield_dict': {},
        'observed_yields_maps_dict': {},
        'nutrition_table_dict': {},
        'climate_bin_maps_dict': {}
    }

    vars_dict = dict(args.items() + derived_vars.items())

    return vars_dict
