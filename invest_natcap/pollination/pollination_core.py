"""InVEST Pollination model core function  module"""

import invest_cython_core
from invest_natcap.invest_core import invest_core

import numpy as np
import scipy.ndimage as ndimage

import math
import logging

LOGGER = logging.getLogger('pollination_core')

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
        args['species'] - a python dictionary with the following entries:
        args['species'][species_name] - a python dictionary where 'species_name'
            is the string name of the pollinator species in question.  This
            dictionary should have the following contents:
        args['species'][species_name]['floral'] - a GDAL dataset
        args['species'][species_name]['nesting'] - a GDAL dataset
        args['species'][species_name]['species_abundance'] - a GDAL dataset
        args['species'][species_name]['farm_abundance'] - a GDAL dataset
        args['nesting_fields'] - a python list of string nesting field basenames
        args['floral fields'] - a python list of string floral fields

        returns nothing."""

    # mask agricultural classes to ag_map.
    make_ag_raster(args['landuse'], args['ag_classes'], args['ag_map'])

    for species, species_dict in args['species'].iteritems():
        guild_dict = args['guilds'].get_table_row('species', species)

        for resource in ['nesting', 'floral']:
            # Calculate the attribute's resources
            map_attribute(args['landuse'], args['landuse_attributes'], guild_dict,
                args[resource + '_fields'], species_dict[resource])

        # Now that the per-pixel nesting and floral resources have been calculated,
        # the floral resources still need to factor in neighborhoods.
        # The sigma size is 2 times the pixel size, presumable since the
        # raster's pixel width is a radius for the gaussian blur when we want
        # the diameter of the blur.
        pixel_size = abs(args['landuse'].GetGeoTransform()[1])
        sigma = float(guild_dict['alpha']/(2 * pixel_size))

        # Fetch the floral resources raster and matrix from the args dictionary
        floral_raster = args['species'][species]['floral'].GetRasterBand(1)
        floral_matrix = floral_raster.ReadAsArray()

        # Calculate and Write the filtered floral resource matrix to its raster
        filtered_matrix = blur_and_clip(floral_matrix, sigma,
            floral_raster.GetNoDataValue())
        args['species'][species]['floral'].GetRasterBand(1).WriteArray(
            filtered_matrix)

        # Calculate the pollinator abundance index (using Math! to simplify the
        # equation in the documentation.  Still need to verify with Rich.
        # This looks like it's just floral resources*nesting resources.
        nesting_raster = args['species'][species]['nesting'].GetRasterBand(1)
        nesting_matrix =nesting_raster.ReadAsArray()

        # Mask the nesting matrix so that any values less than 1 are used as 0
        np.putmask(nesting_matrix, nesting_matrix < 0, 0)

        # This is the actual per-multiplication.
        supply_matrix = np.multiply(filtered_matrix, nesting_matrix)

        # Re-mask the raster to the LULC boundary.
        np.putmask(supply_matrix, nesting_raster.ReadAsArray() < 0,
            nesting_raster.GetNoDataValue())

        # Save the pollinator supply matrix to the pollinator supply raster
        args['species'][species]['species_abundance'].GetRasterBand(1).\
            WriteArray(supply_matrix)

        # Calculate the foraging ('farm abundance') index
        foraging_raster = args['species'][species]['farm_abundance'].\
            GetRasterBand(1)

        # Blur and clip the foraging raster
        foraging_matrix = blur_and_clip(supply_matrix, sigma,
            foraging_raster.GetNoDataValue())

        # Wherever a pixel is not an ag pixel, replace it with the foraging
        # raster's nodata value.
        np.putmask(foraging_matrix, args['ag_map'].GetRasterBand(1).\
                   ReadAsArray() == 0, foraging_raster.GetNoDataValue())

        # Write the foraging matrix to disk 
        foraging_raster.WriteArray(foraging_matrix)

def blur_and_clip(in_matrix, sigma, matrix_nodata):
    """Apply a gaussian filter to the input matrix after converting all values
        below 0 to 0.
        in_matrix - a numpy matrix
        sigma - a python int or float used for the gaussian blur
        matrix_nodata - a python int or float

        returns a numpy matrix."""

    # Making a copy of the in_matrix so as to avoid side effects
    matrix = in_matrix.copy()

    # Convert values < 0 to 0
    np.putmask(matrix, matrix < 0, 0)

    # Apply the gaussian blur
    filtered_matrix = ndimage.gaussian_filter(matrix, sigma)

    # Apply the clip based on the mask raster's nodata values
    np.putmask(filtered_matrix, in_matrix < 0, matrix_nodata)

    return filtered_matrix

def map_attribute(base_raster, attr_table, guild_dict, resource_fields, out_raster):
    """Make an intermediate raster where values are mapped from the base raster
        according to the mapping specified by key_field and value_field.

        base_raster - a GDAL dataset
        attr_table - a subclass of fileio.AbstractTableHandler
        guild_dict - a python dictionary representing the guild row for this
            species.
        resource_fields - a python list of string resource fields
        out_raster - a GDAL dataset

        returns nothing."""

    # Get the input raster's nodata value
    base_nodata = base_raster.GetRasterBand(1).GetNoDataValue()

    # Get the output raster's nodata value
    out_nodata = out_raster.GetRasterBand(1).GetNoDataValue()

    lu_table_dict = attr_table.get_table_dictionary('lulc')

    value_list = dict((r, guild_dict[r]) for r in resource_fields)
    # Define a vectorized function to map values to the base raster
    def map_values(lu_code):
        """Take the input pixel value and return the appropriate value based
            on the table's map.  If the value cannot be found, return the
            output raster's nodata value."""
        try:
            if lu_code == base_nodata:
                return out_nodata
            # Max() is how InVEST 2.2 pollination does this, although I think
            # that sum() should actually be used.
            return max([value_list[r] * lu_table_dict[lu_code][r] for r in
                resource_fields])
        except KeyError:
            return out_nodata

    # Vectorize this operation.
    invest_core.vectorize1ArgOp(base_raster.GetRasterBand(1), map_values,
        out_raster.GetRasterBand(1))

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

    # Fetch the landcover raster's nodata value
    lu_nodata = landuse_raster.GetRasterBand(1).GetNoDataValue()

    # Fetch the output raster's nodata valye
    ag_nodata = ag_raster.GetRasterBand(1).GetNoDataValue()

    # This case is triggered when the user provides agricultural classes.
    if len(ag_classes) > 0:
        # Preprocess ag_classes into a dictionary to improve access times in the
        # vectorized function.  Using a dictionary will, on average, make this a
        # constant-time access (O(1)) instead of a linear access time (O(n))
        ag_dict = dict((k, True) for k in ag_classes)

        def ag_func(lu_class):
            """Check to see if the input pixel value is an agricultural pixel.  If
                so, return 1.  Otherwise, return 0.  If the pixel is a nodata
                pixel, return nodata."""
            if lu_class == lu_nodata:
                return ag_nodata
            if lu_class in ag_dict:
                return 1
            return 0
    else:
        # This case is triggered if the user does not provide any land cover
        # classes.  In this case, we fill the raster with 1's to indicate that
        # all pixels are to be considered agricultural.
        def ag_func(lu_class):
            """Indicate that we want all land cover classes considered as
                agricultural.  Always return 1 unless it's a nodata pixel."""
            if lu_class == lu_nodata:
                return ag_nodata
            return 1

    # Vectorize all of this to the output (ag) raster.
    invest_core.vectorize1ArgOp(landuse_raster.GetRasterBand(1), ag_func,
        ag_raster.GetRasterBand(1))

