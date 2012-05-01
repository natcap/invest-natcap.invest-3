"""InVEST Pollination model file handler module"""

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
            map where each class specified is agricultural. (optional)

        returns nothing."""

    pass
