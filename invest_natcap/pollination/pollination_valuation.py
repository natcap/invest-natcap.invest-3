"""InVEST Pollination model valuation URI module"""

import os.path

def execute(args):
    """Open files necessary for the valuation portion of the pollination model
        and execute the valuation component.

        args - a python dictionary with at least the following entries:
        args['workspace_dir'] - a uri to a directory that contains files for the
            previous run of the pollination biophysical model and that will
            contain files produced by this model.
        args['guilds_uri'] - a uri to an inut CSV table containing data on each
            species or guild of pollinator to be modeled.
        args['half_saturation'] - a python int or float representing the
            half-saturation constant.
        args['wild_pollination_proportion'] - a python int or float representing
            the proportion of total crop yield attributed only to wild
            pollination.

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

    guilds_table = fileio.file_handler(args['guilds_uri'])

    # Open rasters that we need from the workspace, which should have been
    # created from the run of the pollination biophysical model.
    foraging_avg_uri = os.path.join(workspace, 'frm_avg.tif')
    valuation_args['foraging_average'] = gdal.Open(foraging_avg_uri)

    valuation_args['species'] = {}
    for species in [row['species'] for row in guilds_table.table]:
        valuation_args['species'][species] = {}
        valuation_args['species'][species]['species_abundance'] = gdal.Open(
            os.path.join(inter_dir, 'sup_' + species + '.tif'))
        valuation_args['species'][species]['farm_abundance'] = gdal.Open(
            os.path.join(inter_dir, 'frm_' + species + '.tif'))

    pollination_core.valuation(valuation_args)

