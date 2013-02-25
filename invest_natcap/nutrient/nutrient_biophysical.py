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

def make_folder(folder):
    if not os.path.exists(folder):
        LOGGER.debug('Making the folder %s', folder)
        os.makedirs(folder)
    else:
        LOGGER.debug('Folder %s already exists, deleting and recreating', folder)
        shutil.rmtree(folder)
        os.makedirs(folder)

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
            'threshold_uri' - a string uri to a supported table on disk
                containing water purification details.
            'nutrient_type' - a string, either 'nitrogen' or 'phosphorus'
            'accum_threshold' - a number representing the flow accumulation.

        returns nothing.
    """
    workspace = args['workspace_dir']
    output_dir = os.path.join(workspace, 'output')
    service_dir = os.path.join(workspace, 'service')
    intermediate_dir = os.path.join(workspace, 'intermediate')

    file_suffix = ''


    for folder in [workspace, output_dir, service_dir, intermediate_dir]:
        make_folder(folder)

    biophysical_args = {}

    out_pixel_size = raster_utils.get_cell_size_from_uri(args['landuse_uri'])

    #Align all the input rasters
    dem_uri = os.path.join(intermediate_dir, 'dem.tif')
    water_yield_uri = os.path.join(intermediate_dir, 'water_yield.tif')
    landuse_uri = raster_utils.temporary_filename()
    raster_utils.align_dataset_list(
        [args['dem_uri'], args['pixel_yield_uri'], args['landuse_uri']],
        [dem_uri, water_yield_uri, landuse_uri], ['nearest'] * 3,
        out_pixel_size, 'intersection', dataset_to_align_index=2,
        aoi_uri=args['watersheds_uri'])

    #Map the loading factor to the LULC map
    lucode_to_parameters = {}
    parameters_to_map = ['load_n', 'eff_n', 'load_p', 'eff_p']
    with open(args['biophysical_table_uri'], 'rU') as biophysical_table_file:
        biophysical_table_reader = csv.reader(biophysical_table_file)
        headers = biophysical_table_reader.next()
        lucode_index = headers.index('lucode')
        for row in biophysical_table_reader:
            lucode = int(row[lucode_index])
            parameter_dict = {}
            for parameter in parameters_to_map:
                parameter_dict[parameter] = float(row[headers.index(parameter)])
            lucode_to_parameters[lucode] = parameter_dict

    nodata_landuse = raster_utils.get_nodata_from_uri(landuse_uri)
    load_p_uri = os.path.join(intermediate_dir, 'load_p.tif')
    load_n_uri = os.path.join(intermediate_dir, 'load_n.tif')

    nodata_load = -1.0

    def map_load_function(load_type):
        def map_load(lucode):
            if lucode == nodata_landuse:
                return nodata_load
            return lucode_to_parameters[lucode][load_type]
        return map_load

    for out_uri, load_type in [(load_p_uri, 'load_p'), (load_n_uri, 'load_n')]:
        raster_utils.vectorize_datasets(
            [landuse_uri], map_load_function(load_type), out_uri,
            gdal.GDT_Float32, nodata_load, out_pixel_size, "intersection")

    #Calcualte the sum of water yield pixels
    upstream_water_yield_uri = os.path.join(
        intermediate_dir, 'upstream_water_yield.tif')
    water_loss_uri = os.path.join(intermediate_dir, 'water_loss.tif')
    zero_raster_uri = os.path.join(intermediate_dir, 'zero_raster.tif')
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

    output_datasource.Destroy()

    alv_p_uri = os.path.join(intermediate_dir, 'alv_p.tif')
    alv_n_uri = os.path.join(intermediate_dir, 'alv_n.tif')

    def alv_calculation(load, runoff_index, mean_runoff_index):
        if nodata_load in [load, runoff_index, mean_runoff_index]:
            return nodata_load
        return load * runoff_index / mean_runoff_index

    raster_utils.vectorize_datasets(
        [load_p_uri, upstream_water_yield_log_uri, mean_runoff_uri], alv_calculation, alv_p_uri,
        gdal.GDT_Float32, nodata_load, out_pixel_size, "intersection")

    raster_utils.vectorize_datasets(
        [load_n_uri, upstream_water_yield_log_uri, mean_runoff_uri], alv_calculation, alv_n_uri,
        gdal.GDT_Float32, nodata_load, out_pixel_size, "intersection")


    return 



    # Open rasters provided in the args dictionary.
    LOGGER.info('Opening user-defined rasters')
    raster_list = ['dem_uri', 'pixel_yield_uri', 'landuse_uri']
    for raster_key in raster_list:
        new_key = re.sub('_uri$', '', raster_key)
        LOGGER.debug('Opening "%s" raster at %s', new_key, str(args[raster_key]))
        biophysical_args[new_key] = gdal.Open(str(args[raster_key]))

    # Open shapefiles provided in the args dictionary
    LOGGER.info('Opening user-defined shapefiles')
    encoding = sys.getfilesystemencoding()
    ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
    shapefile_list = ['watersheds_uri', 'subwatersheds_uri']
    for shape_key in shapefile_list:
        new_key = re.sub('_uri$', '', shape_key)
        new_uri = os.path.splitext(str(args[shape_key]))[0]
        LOGGER.debug('Opening "%s" shapefile at %s', new_key, new_uri)

        base_shape_uri = args[shape_key].encode(encoding)
        LOGGER.debug('Opening with encoded %s' % base_shape_uri)
        sample_shape = ogr.Open(base_shape_uri, 0)
        shapefile_folder = os.path.join(output_dir, new_key)
        make_folder(shapefile_folder)

        copy_uri = os.path.join(output_dir, new_key)
        
        copy = ogr_driver.CopyDataSource(sample_shape, copy_uri)
        LOGGER.debug('Saving shapefile copy to %s', copy_uri)
        LOGGER.debug('Copied shape: %s', copy)

        # Create the known new fields for this shapefile.
        # thresh_c is the per-pixel contributed threshold.  Used in calculating
        # the service raster, it's the result of (thresh/contrib)
        for column_name in ['nut_export', 'nut_retain', 'mn_runoff', 'thresh_c']:
            LOGGER.debug('Creating new field %s in %s', column_name, copy_uri)
            new_field = ogr.FieldDefn(column_name, ogr.OFTReal)
            copy.GetLayer(0).CreateField(new_field)

        biophysical_args[new_key] = copy

    LOGGER.info('Opening tables')
    LOGGER.debug('Nutrient type: %s', args['nutrient_type'])
    if args['nutrient_type'] == 'nitrogen':
        suffix = '_n'
    elif args['nutrient_type'] == 'phosphorus':
        suffix = '_p'
    else:
        raise InvalidNutrient('Invalid Nutrient type %s found.' %
                              args['nutrient_type'])

    bio_table_regex = '|'.join([r + suffix for r in ['load', 'eff']])
    LOGGER.debug('Bio table regexp: %s', bio_table_regex)

    thresh_table_regex = 'thresh' + suffix
    LOGGER.debug('Threshold table regexp: %s', thresh_table_regex)

    biophysical_args['bio_table'] = fileio.TableHandler(args['bio_table_uri'])
    biophysical_args['bio_table'].set_field_mask(bio_table_regex, 2, 'back')
    biophysical_args['threshold_table'] =\
        fileio.TableHandler(args['threshold_table_uri'])
    biophysical_args['threshold_table'].set_field_mask(thresh_table_regex, 2, 'back')

    # Extract the threshold data in the threshold table and save it to the new
    # watersheds shapefile.
    watersheds_layer = biophysical_args['watersheds'].GetLayer(0)
    threshold_fields = biophysical_args['threshold_table'].fieldnames
    new_fieldnames = [f for f in threshold_fields if f not in ['ws_id', 'id']]
    LOGGER.debug('New fields to be created in watersheds:%s', new_fieldnames)

    # Create the new fieldnames in the watersheds layer
    for field_name in new_fieldnames:
        LOGGER.debug('Creating new fieldname %s', field_name)
        new_field = ogr.FieldDefn(field_name, ogr.OFTReal)
        watersheds_layer.CreateField(new_field)

    # Extract the data to be saved to the new fields from the threshold table
    # and set the field values.
    for row in biophysical_args['threshold_table']:
        watershed = watersheds_layer.GetFeature(int(row['ws_id']))
        LOGGER.debug('Creating feature %s for row %s', watershed, row)
        for field_name in new_fieldnames:
            LOGGER.debug('Setting field %s to table value %s', field_name,
                         row[field_name])
            field_index = watershed.GetFieldIndex(field_name)
            LOGGER.debug('field %s index %s', field_name, field_index)
            watershed.SetField(field_index, str(row[field_name]))
        watersheds_layer.SetFeature(watershed)
        watershed.Destroy()

    LOGGER.info('Copying other values for internal use')
    biophysical_args['accum_threshold'] = args['accum_threshold']
    biophysical_args['folders'] = {
        'workspace': workspace,
        'intermediate': intermediate_dir,
        'output': output_dir
    }

    # Run the nutrient model with the biophysical args dictionary.
    nutrient_core.biophysical(biophysical_args)

