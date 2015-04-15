import tempfile
import os

import numpy as np
from affine import Affine
import gdal

import crop_production_io as io
from raster import *

workspace_dir = '../../test/invest-data/test/data/crop_production/'
input_dir = '../../test/invest-data/test/data/crop_production/input/'
# input_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/')

# AOI Parameters
pixel_size = 100
aoi_dict = {
    'shape': (3, 3),
    'affine': Affine(pixel_size, 0, 0, 0, -pixel_size, pixel_size*3),
    'proj': 32610
}


def create_lulc_map(aoi_dict):
    # set arguments
    array = np.ones(aoi_dict['shape'])
    array[0] = 1
    array[1] = 2
    array[2] = 3
    affine = aoi_dict['affine']
    proj = aoi_dict['proj']
    datatype = gdal.GDT_Int16
    nodata_val = -9999.0

    # initialize raster
    r = Raster.from_array(array, affine, proj, datatype, nodata_val)

    lulc_map_uri = os.path.join(input_dir, 'lulc_map.tif')
    r.save_raster(lulc_map_uri)
    return lulc_map_uri

def create_lulc_map2(aoi_dict):
    # set arguments
    array = np.ones(aoi_dict['shape'])
    array[0] = 1
    array[1] = 2
    array[2] = 3
    affine = aoi_dict['affine']
    proj = aoi_dict['proj']
    datatype = gdal.GDT_Int16
    nodata_val = -9999.0

    # initialize raster
    r = Raster.from_array(array, affine, proj, datatype, nodata_val)

    return r

def create_global_raster_factory(datatype):
    pixel_size = 0.083333
    size = 180/pixel_size
    shape = (size, size*2)
    affine = Affine(pixel_size, 0, -180, 0, -pixel_size, 90)
    proj = 4326
    nodata_val = -9999

    global_raster_factory = RasterFactory(
        proj,
        datatype,
        nodata_val,
        shape[0],
        shape[1],
        affine=affine)

    return global_raster_factory

def create_observed_yield_maps_dir():
    observed_yield_dir = os.path.join(
        input_dir, 'spatial_dataset/observed_yield/')

    global_raster_factory = create_global_raster_factory(gdal.GDT_Float64)

    corn_raster = global_raster_factory.horizontal_ramp(0.0, 1.0)
    rice_raster = global_raster_factory.horizontal_ramp(1.0, 2.0)
    soy_raster = global_raster_factory.horizontal_ramp(2.0, 3.0)

    corn_raster.save_raster(os.path.join(
        observed_yield_dir, 'corn_yield.tif'))
    rice_raster.save_raster(os.path.join(
        observed_yield_dir, 'rice_yield.tif'))
    soy_raster.save_raster(os.path.join(
        observed_yield_dir, 'soy_yield.tif'))

    return observed_yield_dir


def create_climate_bin_maps_dir():
    climate_bin_dir = os.path.join(
        input_dir, 'spatial_dataset/climate_bin_maps/')

    global_raster_factory = create_global_raster_factory(gdal.GDT_Int32)

    corn_raster = global_raster_factory.alternating(1, 10)
    rice_raster = global_raster_factory.alternating(1, 10)
    soy_raster = global_raster_factory.alternating(1, 10)

    corn_raster.save_raster(os.path.join(
        climate_bin_dir, 'corn_climate_bin.tif'))
    rice_raster.save_raster(os.path.join(
        climate_bin_dir, 'rice_climate_bin.tif'))
    soy_raster.save_raster(os.path.join(
        climate_bin_dir, 'soy_climate_bin.tif'))

    return climate_bin_dir


def create_irrigation_map(aoi_dict):
    # set arguments
    array = np.ones(aoi_dict['shape'])
    affine = aoi_dict['affine']
    proj = aoi_dict['proj']
    datatype = gdal.GDT_Int32
    nodata_val = -1

    # initialize raster
    r = Raster.from_array(array, affine, proj, datatype, nodata_val)

    irrigation_uri = os.path.join(input_dir, 'irrigation.tif')
    r.save_raster(irrigation_uri)
    return irrigation_uri


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
    fertilizer_maps_dir = os.path.join(input_dir, 'fertilizer_maps/')

    nitrogen_raster = create_fertilizer_map(aoi_dict)
    phosphorous_raster = create_fertilizer_map(aoi_dict)
    potash_raster = create_fertilizer_map(aoi_dict)

    nitrogen_raster.save_raster(os.path.join(
        fertilizer_maps_dir, 'nitrogen.tif'))
    phosphorous_raster.save_raster(os.path.join(
        fertilizer_maps_dir, 'phosphorous.tif'))
    potash_raster.save_raster(os.path.join(
        fertilizer_maps_dir, 'potash.tif'))

    return fertilizer_maps_dir


def get_crop_lookup_table(uri):
    vars_dict = {'crop_lookup_table_uri': uri}
    return io.read_crop_lookup_table(vars_dict)['crop_lookup_dict']


def get_observed_yield_maps_dict():
    return get_vars_dict()['observed_yields_maps_dict']


def get_args():

    args = {
        'workspace_dir': workspace_dir,
        'results_suffix': 'scenario_name',
        'lulc_map_uri': create_lulc_map(aoi_dict),
        'crop_lookup_table_uri': os.path.join(
            input_dir, 'crop_lookup_table.csv'),
        'spatial_dataset_dir': os.path.join(input_dir, 'spatial_dataset'),
        'create_crop_production_maps': True,
        'do_yield_observed': True,
        'do_yield_percentile': True,
        'do_yield_regression_model': True,
        'modeled_fertilizer_maps_dir': create_fertilizer_maps_dir(aoi_dict),
        'modeled_irrigation_map_uri': create_irrigation_map(aoi_dict),
        'do_nutrition': True,
        'nutrition_table_uri': os.path.join(input_dir, 'nutrition_table.csv'),
        'do_economic_returns': True,
        'economics_table_uri': os.path.join(input_dir, 'economics_table.csv')
    }

    return args


def get_vars_dict():

    args = get_args()

    derived_vars = io.fetch_args(args)

    generated_vars = {
        'observed_yield_maps_dir': create_observed_yield_maps_dir(),
        'percentile_yield_tables_dir': os.path.join(
            input_dir, 'climate_percentile_yield'),
        'percentile_yield_dict': derived_vars['percentile_yield_dict'],
        'crop_lookup_dict': derived_vars['crop_lookup_dict'],
        'economics_table_dict': derived_vars['economics_table_dict'],
        'climate_bin_maps_dir': os.path.join(input_dir, 'climate_bin_maps'),
        'modeled_yield_tables_dir': os.path.join(
            input_dir, 'climate_regression_yield'),
        'modeled_yield_dict': derived_vars['modeled_yield_dict'],
        'observed_yields_maps_dict': derived_vars['observed_yields_maps_dict'],
        'nutrition_table_dict': derived_vars['nutrition_table_dict'],
        'climate_bin_maps_dir': create_climate_bin_maps_dir(),
        'output_dir': derived_vars['output_dir']
    }

    vars_dict = dict(args.items() + generated_vars.items())

    derived_vars = io.fetch_args(args)
    for i in derived_vars.keys():
        if i not in vars_dict.keys():
            vars_dict[i] = derived_vars[i]

    return vars_dict
