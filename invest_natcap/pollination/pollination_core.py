"""InVEST Pollination model core function  module"""

def biophysical(args):
    """Execute the biophysical component of the pollination model.

        args - a python dictionary with at least the following entries:
        args['landuse'] - a GDAL dataset
        args['landuse_attributes'] - a python list, where each entry in the list
            is a dictionary representing the row's information.  In each
            dictionary, the field name maps to the field's value.  This
            dictionary represents the land use land cover attribute table.
        args['guilds'] - a python list of dictionaries in the same structure as
            the list of dictionaries for args['landuse_attributes'], only that
            this dictionary represents pollinator guilds.
        args['ag_classes'] - a python list of ints representing agricultural
            classes in the landuse map.  This list may be empty to represent the
            fact that no landuse classes are to be designated as strictly
            agricultural.

        returns nothing."""
    pass
