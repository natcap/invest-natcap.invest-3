"""InVEST Pollination model file handler module"""

from osgeo import gdal

from invest_natcap.pollination import pollination_core
from invest_natcap.invest_core import fileio
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
        args['landuse_cur_uri'] - a uri to an input land use/land cover raster
        args['landuse_fut_uri'] - a uri to an input land use/land cover raster
        args['landuse_attributes_uri'] - a uri to an input CSV containing data
            on each class in the land use/land cover map (required).
        args['guilds_uri'] - a uri to an input CSV table containing data on
            each species or guild of pollinator to be modeled.
        args['ag_classes'] - a python string of space-separated integers
            representing land cover classes in the input land use/land cover
            map where each class specified is agricultural.  This string may be
            either a python string or a unicode string. (optional)
        args['results_suffix'] - a python string that will be inserted into all
            raster uri paths just before the file extension.

        returns nothing."""

    workspace = args['workspace_dir']

    # If the user has not provided a results suffix, assume it to be an empty
    # string.
    try:
        suffix = args['results_suffix']
    except:
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
        biophysical_args = {}  # Re-initialize the biophysical args
        biophysical_args['paths'] = {
            'workspace': workspace,
            'intermediate': inter_dir,
            'output': out_dir
        }

        # Open the landcover raster
        biophysical_args['landuse'] = gdal.Open(
            str(args['landuse_' + scenario +'_uri']), gdal.GA_ReadOnly)

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

        # Create a new raster for use as a raster of booleans, either 1 if the land
        # cover class is in the ag list, or 0 if the land cover class is not.
        ag_map_uri = pollination_core.build_uri(inter_dir, 'agmap.tif', [scenario, suffix])
        biophysical_args['ag_map'] =\
            pollination_core.make_raster_from_lulc(biophysical_args['landuse'],
            ag_map_uri)

        # Create a new raster for a mean of all foraging rasters.
        frm_avg_uri = pollination_core.build_uri(out_dir, 'frm_tot.tif', [scenario, suffix])
        biophysical_args['foraging_total'] = frm_avg_uri
        frm_avg_uri = pollination_core.build_uri(out_dir, 'frm_avg.tif', [scenario, suffix])
        biophysical_args['foraging_average'] = frm_avg_uri
#        biophysical_args['foraging_average'] = pollination_core.\
#            make_raster_from_lulc(biophysical_args['landuse'], frm_avg_uri)

        # Create a new raster for the total of all pollinator supply rasters.
        sup_tot_uri = pollination_core.build_uri(out_dir, 'sup_tot.tif', [scenario, suffix])
        biophysical_args['abundance_total'] = sup_tot_uri
#        biophysical_args['abundance_total'] = pollination_core.\
#            make_raster_from_lulc(biophysical_args['landuse'], sup_tot_uri)

        # Fetch a list of all species from the guilds table.
        species_list = [row['species'] for row in guilds_handler.table]

        # Make new rasters for each species.  In this list of tuples, the first
        # value of each tuple is the args dictionary key, and the second value of
        # each tuple is the raster prefix.
        species_rasters = [('nesting', 'hn'),
                           ('floral', 'hf'),
                           ('species_abundance', 'sup'),
                           ('farm_abundance', 'frm')]

        biophysical_args['species'] = {}
        for species in species_list:
            biophysical_args['species'][species] = {}
            for group, prefix in species_rasters:
                raster_name = prefix + '_' + species + '.tif'
                raster_uri = pollination_core.build_uri(inter_dir, raster_name,
                    [scenario, suffix])
                biophysical_args['species'][species][group] = raster_uri

        pollination_core.biophysical(biophysical_args)
