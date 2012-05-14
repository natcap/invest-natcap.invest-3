"""InVEST Pollination model valuation URI module"""

from osgeo import gdal

import pollination_core
from invest_natcap.iui import fileio

import os.path
import logging

LOGGER = logging.getLogger('pollination_valuation')


def execute(args):
    """Open files necessary for the valuation portion of the pollination model
        and execute the valuation component.

        args - a python dictionary with at least the following entries:
        args['workspace_dir'] - a uri to a directory that contains files for
            the previous run of the pollination biophysical model and that will
            contain files produced by this model.
        args['guilds_uri'] - a uri to an inut CSV table containing data on each
            species or guild of pollinator to be modeled.
        args['half_saturation'] - a python int or float representing the
            half-saturation constant.
        args['wild_pollination_proportion'] - a python int or float
            representing the proportion of total crop yield attributed only
            to wild pollination.

        returns nothing"""

    valuation_args = {}
    valuation_args['half_saturation'] = args['half_saturation']
    valuation_args['wild_pollination_proportion'] =\
        args['wild_pollination_proportion']

    # It should be safe to assume that this workspace should already contain
    # intermediate and output folders, since we expect those folders to exist
    # from a previous run of the biophysical model.
    workspace = args['workspace_dir']
    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')

    guilds_table = fileio.find_handler(args['guilds_uri'])
    valuation_args['guilds'] = guilds_table

    # Open rasters that we need from the workspace, which should have been
    # created from the run of the pollination biophysical model.
    foraging_avg_uri = os.path.join(out_dir, 'frm_avg.tif')
    LOGGER.debug('Opening raster from biophysical: %s', foraging_avg_uri)
    valuation_args['foraging_average'] = gdal.Open(foraging_avg_uri)
    agmap_uri = os.path.join(inter_dir, 'agmap.tif')
    LOGGER.debug('Opening raster from biophysical: %s', foraging_avg_uri)
    valuation_args['ag_map'] = gdal.Open(agmap_uri)

    valuation_args['species'] = {}
    for species in [row['species'] for row in guilds_table.table]:
        valuation_args['species'][species] = {}
        supply_uri = os.path.join(inter_dir, 'sup_' + species + '.tif')
        foraging_uri = os.path.join(inter_dir, 'frm_' + species + '.tif')
        LOGGER.debug('Opening raster from biophysical: %s', foraging_uri)
        LOGGER.debug('Opening raster from biophysical: %s', supply_uri)
        valuation_args['species'][species]['species_abundance'] = gdal.Open(
            supply_uri)
        valuation_args['species'][species]['farm_abundance'] = gdal.Open(
            foraging_uri)

    # Create the total supply raster using the foraging average raster as a
    # base
    service_value_uri = os.path.join(out_dir, 'sup_val.tif')
    valuation_args['service_value'] = pollination_core.make_raster_from_lulc(
        valuation_args['foraging_average'], service_value_uri)

    # Create the total farm value raster using the foraging average raster as a
    # base
    farm_value_uri = os.path.join(inter_dir, 'frm_val.tif')
    valuation_args['farm_value'] = pollination_core.make_raster_from_lulc(
        valuation_args['foraging_average'], farm_value_uri)

    # Execute the model.
    pollination_core.valuation(valuation_args)
