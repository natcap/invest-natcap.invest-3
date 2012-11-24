"""Module for the execution of the biophysical component of the InVEST Nutrient
Retention model."""

import re
import logging
import os
import sys
import shutil

from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
from invest_natcap.nutrient import nutrient_core
from invest_natcap.invest_core import fileio as fileio

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
            'bio_table_uri' - a string uri to a supported table on disk
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

    for folder in [workspace, output_dir, service_dir, intermediate_dir]:
        make_folder(folder)

    biophysical_args = {}

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
        sample_shape = ogr.Open(base_shape_uri, 1)
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

