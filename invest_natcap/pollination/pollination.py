
import os
import logging
import re

from osgeo import gdal

from invest_natcap.invest_core import fileio as fileio
from invest_natcap.pollination import pollination_core as pollination_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('pollination')

def execute(args):
    workspace = args['workspace_dir']

    # If the user has not provided a results suffix, assume it to be an empty
    # string.
    try:
        suffix = args['results_suffix']
    except KeyError:
        suffix = ''

    # Check to see if each of the workspace folders exists.  If not, create the
    # folder in the filesystem.
    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')

    for folder in [inter_dir, out_dir]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

    # Determine which land cover scenarios we should run, and append the
    # appropriate suffix to the landuser_scenarios list as necessary for the
    # scenario.
    landuse_scenarios = ['cur']
    if 'landuse_fut_uri' in args:
        landuse_scenarios.append('fut')

    for scenario in landuse_scenarios:
        LOGGER.info('Starting pollination model for the %s scenario', scenario)
        biophysical_args = {
            'paths': {
                'workspace': workspace,
                'intermediate': inter_dir,
                'output': out_dir,
                'temp': inter_dir
            },
            'do_valuation': args['do_valuation'],
        }

        # If we're doing valuation, we also require certain other parameters to
        # be present.
        if args['do_valuation']:
            for arg in ['half_saturation', 'wild_pollination_proportion']:
                biophysical_args[arg] = args[arg]

        # Open the landcover raster
        biophysical_args['landuse'] = gdal.Open(
            args['landuse_' + scenario +'_uri'].encode('utf-8'), gdal.GA_ReadOnly)

        # Open a Table Handler for the land use attributes table and a different
        # table handler for the Guilds table.
        att_table_handler = fileio.TableHandler(args['landuse_attributes_uri'])
        att_table_fields = att_table_handler.get_fieldnames()
        nesting_fields = [f[2:] for f in att_table_fields if re.match('^n_', f)]
        floral_fields = [f[2:] for f in att_table_fields if re.match('^f_', f)]
        biophysical_args['nesting_fields'] = nesting_fields
        biophysical_args['floral_fields'] = floral_fields

        att_table_handler.set_field_mask('(^n_)|(^f_)', trim=2)
        guilds_handler = fileio.TableHandler(args['guilds_uri'])
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
            user_ag_list = args['ag_classes'].split(' ')
            ag_class_list = [int(r) for r in user_ag_list if r != '']
        except KeyError:
            # If the 'ag_classes' key is not present in the args dictionary, use an
            # empty list in its stead.
            ag_class_list = []

        LOGGER.debug('Parsed ag classes: %s', ag_class_list)
        biophysical_args['ag_classes'] = ag_class_list

        # Create a new raster for a mean of all foraging rasters.
        global_rasters = [
            ('foraging_total', 'frm_tot', out_dir),
            ('foraging_average', 'frm_avg', out_dir),
            ('farm_value_sum', 'frm_val_sum', inter_dir),
            ('service_value_sum', 'sup_val_sum', out_dir),
            ('abundance_total', 'sup_tot', out_dir),
            ('ag_map', 'agmap', inter_dir)]

        for key, raster_base, folder in global_rasters:
            raster_uri = pollination_core.build_uri(
                folder, '%s.tif' % raster_base, [scenario, suffix])
            biophysical_args[key] = raster_uri

        # Fetch a list of all species from the guilds table.
        species_list = [row['species'] for row in guilds_handler.table]

        # Make new rasters for each species.  In this list of tuples, the first
        # value of each tuple is the args dictionary key, and the second value of
        # each tuple is the raster prefix.

        species_rasters = [
            ('nesting', 'hn', inter_dir),
            ('floral', 'hf', inter_dir),
            ('species_abundance', 'sup', inter_dir),
            ('farm_abundance', 'frm', inter_dir),
            ('farm_value', 'frm_val', inter_dir),
            ('value_abundance_ratio', 'val_sup_ratio', inter_dir),
            ('value_abundance_ratio_blur', 'val_sup_ratio_blur', inter_dir),
            ('service_value', 'sup_val', out_dir)]

        biophysical_args['species'] = {}
        for species in species_list:
            biophysical_args['species'][species] = {}
            for group, prefix, folder in species_rasters:
                raster_name = prefix + '_' + species + '.tif'
                raster_uri = pollination_core.build_uri(folder, raster_name,
                    [scenario, suffix])
                biophysical_args['species'][species][group] = raster_uri

        pollination_core.execute_model(biophysical_args)
