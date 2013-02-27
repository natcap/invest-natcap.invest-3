"""Module for the execution of the biophysical component of the InVEST Nutrient
Retention model."""

import re
import logging
import os
import sys
import shutil
import csv

from osgeo import gdal
from osgeo import ogr
import numpy

from invest_natcap import raster_utils
from invest_natcap.nutrient import nutrient_core
from invest_natcap.invest_core import fileio as fileio
from invest_natcap.routing import routing_utils

LOGGER = logging.getLogger('nutrient_biophysical')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class InvalidNutrient(Exception):pass


def execute(args):
    """File opening layer for the InVEST nutrient retention model.

        args - a python dictionary with the following entries:
            'workspace_dir' - a string uri pointing to the current workspace.
            'dem_uri' - a string uri pointing to the Digital Elevation Map
                (DEM), a GDAL raster on disk.
            'pixel_yield_uri' - a string uri pointing to the water yield raster
                output from the InVEST Water Yield model.
            'landuse_uri' - a string uri pointing to the landcover GDAL raster.
            'watersheds_uri' - a string uri pointing to an OGR shapefile on
                disk representing the user's watersheds.
            'subwatersheds_uri' - a string uri pointing to an OGR shapefile on
                disk representing the user's subwatersheds.
            'biophysical_table_uri' - a string uri to a supported table on disk
                containing nutrient retention values.
            'calc_p' - True if phosphorous is meant to be modeled, if True then
                biophyscial table and threshold table and valuation table must
                have p fields in them.
            'calc_n' - True if nitrogen is meant to be modeled, if True then
                biophyscial table and threshold table and valuation table must
                have n fields in them.
            'water_purification_threshold_table_uri' - a string uri to a
                csv table containing water purification details.
            'nutrient_type' - a string, either 'nitrogen' or 'phosphorus'
            'accum_threshold' - a number representing the flow accumulation.
            'water_purification_valuation_table_uri' - (optional) a uri to a
                csv used for valuation

        returns nothing.
    """
    def _validate_inputs(nutrients_to_process, lucode_to_parameters, threshold_lookup, valuation_lookup):
        """Validation helper method to organize code"""

        #Make sure all the nutrient inputs are good
        if len(nutrients_to_process) == 0:
            raise ValueError("Neither phosphorous nor nitrogen was selected"
                             " to be processed.  Choose at least one.")

        #Build up a list that'll let us iterate through all the input tables
        #and check for the required rows, and report errors if something
        #is missing.
        row_header_table_list = []

        lu_parameter_row = lucode_to_parameters.values()[0]
        row_header_table_list.append(
            (lu_parameter_row, ['load_', 'eff_'],
             args['biophysical_table_uri']))

        threshold_row = threshold_lookup.values()[0]
        row_header_table_list.append(
            (threshold_row, ['thresh_'],
             args['water_purification_threshold_table_uri']))

        if valuation_lookup != None:
            valuation_row = valuation_lookup.values()[0]
            row_header_table_list.append(
                (valuation_row, ['cost_', 'time_span_', 'discount_'],
                 args['biophysical_table_uri']))

        missing_headers = []
        for row, header_prefixes, table_type in row_header_table_list:
            for nutrient_id in nutrients_to_process:
                for header_prefix in header_prefixes:
                    header = header_prefix + nutrient_id
                    if header not in row:
                        missing_headers.append(
                            "Missing header %s from %s" % (header, table_type))

        if len(missing_headers) > 0:
            raise ValueError('\n'.join(missing_headers))

    #Load all the tables for preprocessing
    workspace = args['workspace_dir']
    output_dir = os.path.join(workspace, 'output')
    service_dir = os.path.join(workspace, 'service')
    intermediate_dir = os.path.join(workspace, 'intermediate')
    file_suffix = ''
    for folder in [workspace, output_dir, service_dir, intermediate_dir]:
        if not os.path.exists(folder):
            LOGGER.debug('Making folder %s', folder)
            os.makedirs(folder)

    #Build up a list of nutrients to process based on what's checked on 
    nutrients_to_process = []
    for nutrient_id in ['n', 'p']:
        if args['calc_' + nutrient_id]:
            nutrients_to_process.append(nutrient_id)
    lucode_to_parameters = raster_utils.get_lookup_from_csv(
        args['biophysical_table_uri'], 'lucode')
    threshold_lookup = raster_utils.get_lookup_from_csv(
        args['water_purification_threshold_table_uri'], 'ws_id')
    valuation_lookup = None
    if 'water_purification_valuation_table_uri' in args:
        valuation_lookup = raster_utils.get_lookup_from_csv(
            args['water_purification_valuation_table_uri'], 'ws_id')
    _validate_inputs(nutrients_to_process, lucode_to_parameters, threshold_lookup, valuation_lookup)

    out_pixel_size = raster_utils.get_cell_size_from_uri(args['landuse_uri'])

    #Align all the input rasters
    dem_uri = raster_utils.temporary_filename()
    water_yield_uri = raster_utils.temporary_filename()
    landuse_uri = raster_utils.temporary_filename()
    raster_utils.align_dataset_list(
        [args['dem_uri'], args['pixel_yield_uri'], args['landuse_uri']],
        [dem_uri, water_yield_uri, landuse_uri], ['nearest'] * 3,
        out_pixel_size, 'intersection', dataset_to_align_index=2,
        aoi_uri=args['watersheds_uri'])

    nodata_landuse = raster_utils.get_nodata_from_uri(landuse_uri)
    nodata_load = -1.0

    #Make the streams
    stream_uri = os.path.join(intermediate_dir, 'stream.tif')
    routing_utils.calculate_stream(dem_uri, args['accum_threshold'], stream_uri)

    def map_load_function(load_type):
        def map_load(lucode):
            if lucode == nodata_landuse:
                return nodata_load
            return lucode_to_parameters[lucode][load_type]
        return map_load

    #Build up the load and efficiency rasters from the landcover map
    load_uri = {}
    eff_uri = {}
    for nutrient in nutrients_to_process:
        load_uri[nutrient] = os.path.join(
            intermediate_dir, 'load_%s.tif' % (nutrient))
        eff_uri[nutrient] = os.path.join(
            intermediate_dir, 'eff_%s.tif' % (nutrient))
        for out_uri, load_type in [(load_uri[nutrient], 'load_%s' % nutrient), 
                                   (eff_uri[nutrient], 'eff_%s' % nutrient)]:
            raster_utils.vectorize_datasets(
                [landuse_uri], map_load_function(load_type), out_uri,
                gdal.GDT_Float32, nodata_load, out_pixel_size, "intersection")

    #Calcualte the sum of water yield pixels
    upstream_water_yield_uri = os.path.join(
        intermediate_dir, 'upstream_water_yield.tif')
    water_loss_uri = raster_utils.temporary_filename()
    zero_raster_uri = raster_utils.temporary_filename()
    routing_utils.make_constant_raster_from_base(
        dem_uri, 0.0, zero_raster_uri)

    routing_utils.route_flux(
        dem_uri, water_yield_uri, zero_raster_uri,
        water_loss_uri, upstream_water_yield_uri,
        aoi_uri=args['watersheds_uri'])

    #Calculate the 'log' of the upstream_water_yield raster
    upstream_water_yield_log_uri = os.path.join(intermediate_dir, 'log_water_yield.tif')
    nodata_upstream = raster_utils.get_nodata_from_uri(upstream_water_yield_uri)
    def nodata_log(value):
        if value == nodata_upstream:
            return nodata_upstream
        if value == 0.0:
            return 0.0
        return numpy.log(value)
    raster_utils.vectorize_datasets(
        [upstream_water_yield_uri], nodata_log, upstream_water_yield_log_uri,
        gdal.GDT_Float32, nodata_upstream, out_pixel_size, "intersection")

    field_summaries = {
        'mn_run_ind': raster_utils.aggregate_raster_values_uri(
            upstream_water_yield_log_uri, args['watersheds_uri'], 'ws_id', 
            'mean')
        }

    watershed_output_datasource_uri = os.path.join(output_dir, 'watershed_outputs%s.shp' % file_suffix)
    #If there is already an existing shapefile with the same name and path, delete it
    #Copy the input shapefile into the designated output folder
    if os.path.isfile(watershed_output_datasource_uri):
        os.remove(watershed_output_datasource_uri)
    esri_driver = ogr.GetDriverByName('ESRI Shapefile')
    original_datasource = ogr.Open(args['watersheds_uri'])
    output_datasource = esri_driver.CopyDataSource(original_datasource, watershed_output_datasource_uri)
    output_layer = output_datasource.GetLayer()

    for field_name in field_summaries:
        field_def = ogr.FieldDefn(field_name, ogr.OFTReal)
        output_layer.CreateField(field_def)

    #Initialize each feature field to 0.0
    for feature_id in xrange(output_layer.GetFeatureCount()):
        feature = output_layer.GetFeature(feature_id)
        for field_name in field_summaries:
            try:
                ws_id = feature.GetFieldAsInteger('ws_id')
                feature.SetField(field_name, float(field_summaries[field_name][ws_id]))
            except KeyError:
                LOGGER.warning('unknown field %s' % field_name)
                feature.SetField(field_name, 0.0)
        #Save back to datasource
        output_layer.SetFeature(feature)

    #Burn the mean runoff values to a raster that matches the watersheds
    upstream_water_yield_dataset = gdal.Open(upstream_water_yield_uri)
    mean_runoff_uri = os.path.join(intermediate_dir, 'mean_runoff.tif')
    mean_runoff_dataset = raster_utils.new_raster_from_base(
        upstream_water_yield_dataset, mean_runoff_uri, 'GTiff', -1.0,
        gdal.GDT_Float32, -1.0)
    upstream_water_yield_dataset = None
    gdal.RasterizeLayer(
        mean_runoff_dataset, [1], output_layer, options=['ATTRIBUTE=mn_run_ind'])
    mean_runoff_dataset = None

    def alv_calculation(load, runoff_index, mean_runoff_index):
        if nodata_load in [load, runoff_index, mean_runoff_index]:
            return nodata_load
        return load * runoff_index / mean_runoff_index
    alv_uri = {}
    retention_uri = {}
    export_uri = {}
    field_summaries = {}
    for nutrient in nutrients_to_process:
        alv_uri[nutrient] = os.path.join(intermediate_dir, 'alv_%s.tif' % nutrient)
        raster_utils.vectorize_datasets(
            [load_uri[nutrient], upstream_water_yield_log_uri, mean_runoff_uri],
            alv_calculation, alv_uri[nutrient], gdal.GDT_Float32, nodata_load,
            out_pixel_size, "intersection")
        retention_uri[nutrient] = os.path.join(
            intermediate_dir, '%s_retention.tif' % nutrient)
        tmp_flux_uri = raster_utils.temporary_filename()
        routing_utils.route_flux(
            dem_uri, load_uri[nutrient], eff_uri[nutrient], 
            retention_uri[nutrient], tmp_flux_uri,
            aoi_uri=args['watersheds_uri'])
        export_uri[nutrient] = os.path.join(output_dir, '%s_export.tif' % nutrient)
        routing_utils.pixel_amount_exported(
            dem_uri, stream_uri, eff_uri[nutrient], load_uri[nutrient],
            export_uri[nutrient], aoi_uri=args['watersheds_uri'])

        field_summaries['%s_adjl_tot' % nutrient] = (
            raster_utils.aggregate_raster_values_uri(
                alv_p_uri, args['watersheds_uri'], 'ws_id', 'sum'))
        field_summaries['%s_ret_sm' % nutrient] = (
            raster_utils.aggregate_raster_values_uri(
                retention_uri[nutrient], args['watersheds_uri'], 'ws_id', 'sum', 
                threshold_amount_list=threshold_lookup[nutrient]))
        field_summaries['%s_exp_tot' % nutrient] = (
            raster_utils.aggregate_raster_values_uri(
                export_uri[nutrient], args['watersheds_uri'], 'ws_id', 'sum'))
        field_summaries['%s_ret_tot' % nutrient] = (
            raster_utils.aggregate_raster_values_uri(
                retention_uri[nutrient], args['watersheds_uri'], 'ws_id', 'sum'))

#    field_summaries = {
        #These are raw load values
#        'p_adjl_tot': raster_utils.aggregate_raster_values_uri(alv_p_uri, args['watersheds_uri'], 'ws_id', 'sum'),
#        'n_adjl_tot': raster_utils.aggregate_raster_values_uri(alv_n_uri, args['watersheds_uri'], 'ws_id', 'sum'),
#        'p_adjl_mn': raster_utils.aggregate_raster_values_uri(alv_p_uri, args['watersheds_uri'], 'ws_id', 'mean'),
#        'n_adjl_mn': raster_utils.aggregate_raster_values_uri(alv_n_uri, args['watersheds_uri'], 'ws_id', 'mean'),

        #These are the thresholded service values
#        'n_ret_sm': raster_utils.aggregate_raster_values_uri(n_retention_uri, args['watersheds_uri'], 'ws_id', 'sum', thre#shold_amount_list=n_threshold_lookup),
#        'n_ret_mn': raster_utils.aggregate_raster_values_uri(n_retention_uri, args['watersheds_uri'], 'ws_id', 'mean', thr#eshold_amount_list=n_threshold_lookup),
#        'p_ret_sm': raster_utils.aggregate_raster_values_uri(p_retention_uri, args['watersheds_uri'], 'ws_id', 'sum', threshold_amount_list=p_threshold_lookup),
#        'p_ret_mn': raster_utils.aggregate_raster_values_uri(p_retention_uri, args['watersheds_uri'], 'ws_id', 'mean', threshold_amount_list=p_threshold_lookup),

        #These are the total values
#        'n_exp_tot': raster_utils.aggregate_raster_values_uri(n_export_uri, args['watersheds_uri'], 'ws_id', 'sum'),
#        'n_exp_mean': raster_utils.aggregate_raster_values_uri(n_export_uri, args['watersheds_uri'], 'ws_id', 'mean'),
#        'p_exp_tot': raster_utils.aggregate_raster_values_uri(p_export_uri, args['watersheds_uri'], 'ws_id', 'sum'),
#        'p_exp_mean': raster_utils.aggregate_raster_values_uri(p_export_uri, args['watersheds_uri'], 'ws_id', 'mean'),
#        'n_ret_tot': raster_utils.aggregate_raster_values_uri(n_retention_uri, args['watersheds_uri'], 'ws_id', 'sum'),
#        'n_ret_mean': raster_utils.aggregate_raster_values_uri(n_retention_uri, args['watersheds_uri'], 'ws_id', 'mean'),
#        'p_ret_tot': raster_utils.aggregate_raster_values_uri(p_retention_uri, args['watersheds_uri'], 'ws_id', 'sum'),
#        'p_ret_mean': raster_utils.aggregate_raster_values_uri(p_retention_uri, args['watersheds_uri'], 'ws_id', 'mean')
#        }

    #Do valuation if necessary
    if valuation_lookup != None:
        for ws_id, value in field_summaries['p_ret_sm'].iteritems():
            discount = disc(valuation_lookup[ws_id]['time_span'],
                            valuation_lookup[ws_id]['discount'])
            field_summaries['p_value'][ws_id] = (
                field_summaries['p_ret_sm'][ws_id] * 
                valuation_lookup[ws_id]['cost'] * discount)
            field_summaries['n_value'][ws_id] = (
                field_summaries['n_ret_sm'][ws_id] * 
                valuation_lookup[ws_id]['cost'] * discount)

    #Create an output field for each key in the field summary dictionary
    for field_name in field_summaries:
        field_def = ogr.FieldDefn(field_name, ogr.OFTReal)
        output_layer.CreateField(field_def)

    #Populate the values of those new fields with the ws_id indexed values in the field summary dictionary.
    for feature_id in xrange(output_layer.GetFeatureCount()):
        feature = output_layer.GetFeature(feature_id)
        for field_name in field_summaries:
            try:
                ws_id = feature.GetFieldAsInteger('ws_id')
                feature.SetField(field_name, float(field_summaries[field_name][ws_id]))
            except KeyError:
                LOGGER.warning('unknown field %s' % field_name)
                feature.SetField(field_name, 0.0)
        #Save back to datasource
        output_layer.SetFeature(feature)


def disc(years, percent_rate):
    """Calculate discount rate for a given number of years
    
        years - an integer number of years
        percent_rate - a discount rate in percent

        returns the discount rate for the number of years to use in 
            a calculation like yearly_cost * disc(years, percent_rate)"""

    discount = 0.0
    for time_index in range(int(years) - 1):
        discount += 1.0 / (1.0 + percent_rate / 100.0) ** time_index
    return discount
