"""InVEST Pollination model file handler module"""

from osgeo import gdal

import pollination_core
from invest_natcap.iui import fileio
import invest_cython_core

import os.path
import re
import logging
logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('pollination_biophysical')

def execute(args):
    """Open files necessary for the biophysical portion of the pollination
        model.

        args - a python dictionary with at least the following components:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation (required)
        args['landuse_uri'] - a uri to an input land use/land cover raster
        args['landuse_attributes_uri'] - a uri to an input CSV containing data
            on each class in the land use/land cover map (required).
        args['guilds_uri'] - a uri to an input CSV table containing data on each
            species or guild of pollinator to be modeled.
        args['ag_classes'] - a python string of space-separated integers
            representing land cover classes in the input land use/land cover
            map where each class specified is agricultural.  This string may be
            either a python string or a unicode string. (optional)

        returns nothing."""

    gdal.AllRegister()

    biophysical_args = {}

    workspace = args['workspace_dir']

    # Check to see if each of the workspace folders exists.  If not, create the
    # folder in the filesystem.
    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')

    for folder in [ inter_dir, out_dir ]:
        if not os.path.isdir(folder):
            os.makedirs(folder)


    # Open the landcover raster
    biophysical_args['landuse'] = gdal.Open(str(args['landuse_uri']),
                                           gdal.GA_ReadOnly)

    # Open a Table Handler for the land use attributes table and a different
    # table handler for the Guilds table.
    att_table_handler = fileio.find_handler(args['landuse_attributes_uri'])
    att_table_handler.set_field_mask('(^n_)|(^f_)', trim=2)
    guilds_handler = fileio.find_handler(args['guilds_uri'])
    guilds_handler.set_field_mask('(^ns_)|(^fs_)', trim=3)

    biophysical_args['landuse_attributes'] = att_table_handler
    biophysical_args['guilds'] = guilds_handler

    # Convert agricultural classes (a space-separated list of ints) into a 
    # list of ints.  If the user has not provided a string list of ints, then
    # use an empty list instead.
    try:
        # This approach will create a list with only ints, even if the user has
        # accidentally entered additional spaces.  Any other incorrect input
        # will throw a ValueError exception.
        ag_class_list = [ int(r) for r in args['ag_classes'].split(' ') if r != '' ]
    except KeyError:
        # If the 'ag_classes' key is not present in the args dictionary, use an
        # empty list in its stead.
        ag_class_list = []

    biophysical_args['ag_classes'] = ag_class_list

    # Create a new raster for use as a raster of booleans, either 1 if the land
    # cover class is in the ag list, or 0 if the land cover class is not.
    ag_map_uri = os.path.join(inter_dir, 'agmap.tif')
    biophysical_args['ag_map'] =\
        make_raster_from_lulc(biophysical_args['landuse'], ag_map_uri)

    # Fetch a list of all species from the guilds table.
    species_list = [row['species'] for row in guilds_handler.table]

    # Make new rasters for each species.  In this list of tuples, the first
    # value of each tuple is the args dictionary key, and the second value of
    # each tuple is the raster prefix. 
    species_rasters =[('nesting', 'hn'),
                      ('floral', 'hf'),
                      ('species_abundance', 'sup'),
                      ('farm_abundance', 'frm')]
    for species in species_list:
        for group, prefix in species_rasters:
            raster_uri = os.path.join(inter_dir, prefix + '_' + species + '.tif')
            dataset = make_raster_from_lulc(args['landuse'], raster_uri)
            biophysical_args['species'][species][group] = dataset

    pollination_core.biophysical(biophysical_args)

def make_raster_from_lulc(lulc_dataset, raster_uri):
    LOGGER.debug('Creating new raster from LULC: %s', raster_uri)
    dataset = invest_cython_core.newRasterFromBase(\
        lulc_dataset, raster_uri, 'GTiff', -1, gdal.GDT_Float32)
    return dataset
