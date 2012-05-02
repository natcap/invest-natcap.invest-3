"""InVEST Pollination model core function  module"""

def biophysical(args):
    """Execute the biophysical component of the pollination model.

        args - a python dictionary with at least the following entries:
        args['landuse'] - a GDAL dataset
        args['landuse_attributes'] - A fileio AbstractTableHandler object
        args['guilds'] - A fileio AbstractTableHandler object
        args['ag_classes'] - a python list of ints representing agricultural
            classes in the landuse map.  This list may be empty to represent the
            fact that no landuse classes are to be designated as strictly
            agricultural.
        args['floral'] - a python dictionary with the following structure:
            {'f_<season>': gdal dataset for the floral season}, where
            'f_<season>' is taken from the appropriate column label in the
            landuse_attributes table.
        args['nesting'] - a python dictionary with the following structure:
            {'n_<type>': gdal dataset for the nesting type}, where
            'n_<type>' is taken from the appropriate column label in the
            landuse_attributes table.

        returns nothing."""
    pass
