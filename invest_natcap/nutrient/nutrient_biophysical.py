"""Module for the execution of the biophysical component of the InVEST Nutrient
Retention model."""

import re
import logging
import os

from osgeo import gdal
from osgeo import ogr

from invest_natcap import raster_utils
from invest_natcap.nutrient import nutrient_core

LOGGER = logging.getLogger('nutrient_biophysical')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

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
    print args

    workspace = args['workspace_dir']
    output_dir = os.path.join(workspace, 'output')
    service_dir = os.path.join(workspace, 'service')
    intermediate_dir = os.path.join(workspace, 'intermediate')

    for folder in [workspace, output_dir, service_dir, intermediate_dir]:
        try:
            os.makedirs(folder)
        except OSError:
            # Thrown when folder already exists
            pass

    biophysical_args = {}

    # Open rasters provided in the args dictionary.
    raster_list = ['dem_uri', 'pixel_yield_uri', 'landuse_uri']
    for raster_key in raster_list:
        new_key = re.sub('_uri$', '', raster_key)
        LOGGER.debug('Old key: %s ... new key: %s', raster_key, new_key)
        LOGGER.debug('Opening %s raster at %s', new_key, str(args[raster_key]))
        biophysical_args[new_key] = gdal.Open(str(args[raster_key]))

    # Create outputs based on the bounding box of the watersheds to be
    # considered that are provided by the user.

    # Use raster_utils.create_raster_from_vector_extents
    # Structure: (args_dict_key, uri)
    new_rasters = [
        ('adj_load_mean', [output_dir, 'adjil_mn.tif']),
        ('adj_load_sum', [output_dir, 'adjil_sm.tif']),
        ('n_retained_sum', [service_dir, 'nret_sm.tif']),
        ('n_retained_mean', [service_dir, 'nret_mn.tif']),
        ('n_exported_mean', [output_dir, 'nexp_mn.tif']),
        ('n_exported_sum', [output_dir, 'nexp_sm.tif'])
    ]
    landuse_gt = biophysical_args['landuse'].GetGeoTransform()
    pixel_width = int(abs(landuse_gt[1]))
    pixel_height = int(abs(landuse_gt[5]))
    for dict_key, uri_parts in new_rasters:
        uri = os.path.join(*uri_parts)
        LOGGER.debug('Using %s for new raster', uri)
        biophysical_args[dict_key] =\
            raster_utils.create_raster_from_vector_extents(
            pixel_width, pixel_height, gdal.GDT_Float32, -1.0, uri,
            ogr.Open(args['watersheds_uri']))

