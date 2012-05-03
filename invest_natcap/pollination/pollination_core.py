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
        args['ag_map'] - a GDAL dataset
        args['floral'] - a python dictionary with the following structure:
            {'f_<season>': gdal dataset for the floral season}, where
            'f_<season>' is taken from the appropriate column label in the
            landuse_attributes table.
        args['nesting'] - a python dictionary with the following structure:
            {'n_<type>': gdal dataset for the nesting type}, where
            'n_<type>' is taken from the appropriate column label in the
            landuse_attributes table.

        returns nothing."""

    # mask agricultural classes to ag_map.
    make_ag_raster(args['landuse'], args['ag_classes'], args['ag_map'])

    # preprocess landcover rasters f_* and n_*
    pass

def make_ag_raster(landuse_raster, ag_classes, ag_raster):
    """Make an intermediate raster where values of ag_raster are 1 if the
        landcover class is agricultural, 0 if not.

        This function loops through all pixels of landuse_raster.  If the pixel
        value is in ag_classes, the corresponding ag_raster pixel is set to 1.
        Otherwise, the corresponding ag_raster pixel is set to 0.

        landuse_raster - a GDAL dataset
        ag_classes - a python list of ints
        ag_raster - a GDAL dataset

        returns nothing."""

    # If the user has provided agricultural classes, we should only consider
    # those classes as agricultural.  If the user has not provided a list of
    # agricultural classes, we should consider the entire landuse raster as
    # agricultural.
    # This case is triggered when the user provides agricultural classes.
    if len(ag_classes) > 0:
        # Preprocess ag_classes into a dictionary to improve access times in the
        # vectorized function.  Using a dictionary will, on average, make this a
        # constant-time access (O(1)) instead of a linear access time (O(n))
        ag_dict = dict((k, True) for k in ag_classes)

        def ag_func(lu_class):
            """Check to see if the input pixel value is an agricultural pixel.  If
                so, return 1.  Otherwise, return 0."""
            if lu_class in ag_dict:
                return 1
            else:
                return 0
    else:
        # This case is triggered if the user does not provide any land cover
        # classes.  In this case, we fill the raster with 1's to indicate that
        # all pixels are to be considered agricultural.
        def ag_func(lu_class):
            """Indicate that we want all land cover classes considered as
                agricultural.  Always return 1."""
            return 1

    # Vectorize all of this to the output (ag) raster.
    invest_core.vectorize1ArgOp(landuse_raster, ag_func, ag_dict, ag_raster)

