"""InVEST Pollination model core function  module"""

import invest_cython_core
from invest_natcap.invest_core import invest_core

from osgeo import gdal
import numpy as np
import scipy.ndimage as ndimage

import os.path
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
            classes in the landuse map.  This list may be empty to represent
            the fact that no landuse classes are to be designated as strictly
            agricultural.
        args['ag_map'] - a GDAL dataset
        args['species'] - a python dictionary with the following entries:
        args['species'][species_name] - a python dictionary where 'species
            name' is the string name of the pollinator species in question.
            This dictionary should have the following contents:
        args['species'][species_name]['floral'] - a GDAL dataset
        args['species'][species_name]['nesting'] - a GDAL dataset
        args['species'][species_name]['species_abundance'] - a GDAL dataset
        args['species'][species_name]['farm_abundance'] - a GDAL dataset
        args['nesting_fields'] - a python list of string nesting field
            basenames
        args['floral fields'] - a python list of string floral fields
        args['foraging_average'] - a GDAL dataset
        args['abundance_total'] - a GDAL dataset

        returns nothing."""

    # mask agricultural classes to ag_map.
    make_ag_raster(args['landuse'], args['ag_classes'], args['ag_map'])

    # Open the average foraging matrix for use in the loop over all species,
    # but first we need to ensure that the matrix is filled with 0's.
    foraging_total_raster = args['foraging_average'].GetRasterBand(1)
    foraging_matrix_shape = foraging_total_raster.ReadAsArray().shape
    foraging_total_matrix = np.zeros(foraging_matrix_shape)

    # Open the abundance total raster for use in the loop over all species and
    # ensure that it's filled entirely with 0's.
    abundance_total_raster = args['abundance_total'].GetRasterBand(1)
    abundance_matrix_shape = abundance_total_raster.ReadAsArray().shape
    abundance_total_matrix = np.zeros(abundance_matrix_shape)

    for species, species_dict in args['species'].iteritems():
        guild_dict = args['guilds'].get_table_row('species', species)

        for resource, op in [('nesting', max), ('floral', sum)]:
            # Calculate the attribute's resources
            map_attribute(args['landuse'], args['landuse_attributes'],
                guild_dict, args[resource + '_fields'],
                species_dict[resource], op)

        # Now that the per-pixel nesting and floral resources have been
        # calculated, the floral resources still need to factor in
        # neighborhoods.
        # The sigma size is 2 times the pixel size, presumable since the
        # raster's pixel width is a radius for the gaussian blur when we want
        # the diameter of the blur.
        pixel_size = abs(args['landuse'].GetGeoTransform()[1])
        sigma = float(guild_dict['alpha'] / (2 * pixel_size))

        # Fetch the floral resources raster and matrix from the args dictionary
        # apply a gaussian filter and save the floral resources raster to the
        # dataset.
        floral_raster = args['species'][species]['floral'].GetRasterBand(1)
        filtered_matrix = clip_and_op(floral_raster.ReadAsArray(), sigma,
            ndimage.gaussian_filter, floral_raster.GetNoDataValue())
        args['species'][species]['floral'].GetRasterBand(1).WriteArray(
            filtered_matrix)

        # Calculate the pollinator abundance index (using Math! to simplify the
        # equation in the documentation.  We're still waiting on Taylor
        # Rickett's reply to see if this is correct.
        # Once the pollination supply has been calculated, we add it to the
        # total abundance matrix.
        nesting_raster = args['species'][species]['nesting'].GetRasterBand(1)
        supply_matrix = clip_and_op(nesting_raster.ReadAsArray(),
            filtered_matrix, np.multiply, nesting_raster.GetNoDataValue())
        abundance_total_matrix = clip_and_op(abundance_total_matrix,
            supply_matrix, np.add, nesting_raster.GetNoDataValue())
        args['species'][species]['species_abundance'].GetRasterBand(1).\
            WriteArray(supply_matrix)

        # Calculate the foraging ('farm abundance') index by applying a
        # gaussian filter to the foraging raster and then culling all pixels
        # that are not agricultural before saving it to the output raster.
        foraging_raster = args['species'][species]['farm_abundance'].\
            GetRasterBand(1)
        foraging_matrix = clip_and_op(supply_matrix, sigma,
            ndimage.gaussian_filter, foraging_raster.GetNoDataValue())
        np.putmask(foraging_matrix, args['ag_map'].GetRasterBand(1).\
                   ReadAsArray() == 0, foraging_raster.GetNoDataValue())
        foraging_raster.WriteArray(foraging_matrix)

        # Add the current foraging raster to the existing 'foraging_total'
        # raster
        foraging_total_matrix = clip_and_op(foraging_matrix,
            foraging_total_matrix, np.add, foraging_raster.GetNoDataValue())

    # Calculate the average foraging index based on the total
    # This is a function that meets the criteria for the operation passed in to
    # clip_and_op.
    def divide(matrix, divisor):
        """Divide matrix by divisor.  Matrix must be a numpy matrix.  Divisor
            must be a scalar.  Returns a numpy matrix."""
        return matrix / divisor

    # Divide the total pollination foraging index by the number of pollinators
    # to get the mean pollinator foraging index and save that to its raster.
    num_species = float(len(args['species'].values()))
    LOGGER.debug('Number of species: %s', num_species)
    foraging_total_matrix = clip_and_op(foraging_total_matrix,
        num_species, divide, foraging_total_raster.GetNoDataValue())
    foraging_total_raster.WriteArray(foraging_total_matrix)

    # Calculate the mean pollinator supply (pollinator abundance) by taking the
    # abundance_total_matrix and dividing it by the number of pollinators.
    # Then, save the resulting matrix to its raster
    np.putmask(foraging_total_matrix, foraging_total_matrix < 0, 0)
    abundance_total_matrix = clip_and_op(abundance_total_matrix, num_species,
        divide, abundance_total_raster.GetNoDataValue())
    abundance_total_raster.WriteArray(abundance_total_matrix)


def valuation(args):
    """Perform the computation of the valuation component of the pollination
        model.

        args - a python dictionary with at least the following entries:
        args['half_saturation'] - a python int or float
        args['wild_pollination_proportion'] - a python int or float between 0
            and 1.
        args['species'][<species_name>]['species_abundance'] - a GDAL dataset
        args['species'][<species_name>]['farm_abundance'] - a GDAL dataset
        args['service_value'] - a GDAL dataset
        args['farm_value'] - a GDAL dataset
        args['foraging_average'] - a GDAL dataset
        args['guilds'] - a fileio tablehandler class
        args['ag_map'] - a GDAL dataset

        returns nothing"""

    # Apply the half-saturation yield function from the documentation.
    calculate_yield(args['foraging_average'], args['farm_value'],
        args['half_saturation'], args['wild_pollination_proportion'])

    # Open matrices for use later.
    farm_value_matrix = args['farm_value'].GetRasterBand(1).ReadAsArray()
    farm_avg_matrix = args['foraging_average'].GetRasterBand(1).ReadAsArray()
    agmap_raster = args['ag_map'].GetRasterBand(1)
    agmap_matrix = agmap_raster.ReadAsArray()

    # Define necessary scalars based on inputs.
    agmap_nodata = agmap_raster.GetNoDataValue()
    in_nodata = args['foraging_average'].GetRasterBand(1).GetNoDataValue()
    out_nodata = args['farm_value'].GetRasterBand(1).GetNoDataValue()
    num_species = len(args['species'].values())

    # Calculate the total foraging matrix by multiplying the foraging average
    # raster by the number of species.
    def multiply(matrix, multiplicand):
        return matrix * multiplicand
    farm_tot_matrix = clip_and_op(farm_avg_matrix, num_species, multiply,
        in_nodata, out_nodata)

    # Fill the farm total matrix with 0's ... this is not done automatically
    # when creating a new raster, so we need to do it here.
    farm_tot_matrix.fill(0)

    # Loop through all species and calculate the pollinator service value
    for species, species_dict in args['species'].iteritems():
        # Open necessary matrices
        species_foraging_matrix = species_dict['farm_abundance'].\
            GetRasterBand(1).ReadAsArray()
        species_supply_matrix = species_dict['species_abundance'].\
            GetRasterBand(1).ReadAsArray()

        def ps_vectorized(agmap, frm_val, frm_s, frm_avg, sup_s):
            """Apply the pollinator service value function from the
                documentation.
                    agmap - the boolean matrix of ag pixels
                    frm_val - the farm value matrix (from the yield function)
                    frm_s - the species foraging abundance matrix
                    frm_avg - the average foraging abundance matrix
                    sup_s - the species abundance matrix."""

            if agmap == agmap_nodata:
                return out_nodata
            contrib = (frm_val * frm_s) / (frm_avg * num_species)
            return (agmap * ((contrib * sup_s) / frm_s))

        # Vectorize the ps_vectorized function
        vOp = np.vectorize(ps_vectorized)
        ag_masked_matrix = vOp(agmap_matrix, farm_value_matrix,
            species_foraging_matrix, farm_avg_matrix, species_supply_matrix)

        # Calculate sigma for the gaussian blur.  Sigma is based on the species
        # alpha (from the guilds table) and twice the pixel size.
        guild_dict = args['guilds'].get_table_row('species', species)
        pixel_size = abs(args['farm_value'].GetGeoTransform()[1])
        sigma = float(guild_dict['alpha'] / (pixel_size * 2.0))

        # Apply a gaussian blur to the species' supply raster
        blurred_supply = clip_and_op(ag_masked_matrix, sigma,
            ndimage.gaussian_filter, in_nodata, out_nodata)

        # Add the pollinator service value to the total value raster
        farm_tot_matrix = clip_and_op(farm_tot_matrix, blurred_supply,
            np.add, in_nodata, out_nodata)

    # Write the pollination service value to its raster
    args['service_value'].GetRasterBand(1).WriteArray(farm_tot_matrix)


def calculate_yield(in_raster, out_raster, half_sat, wild_poll):
    """Calculate the yield raster.

        in_raster - a GDAL dataset
        out_raster -a GDAL dataset
        half_sat - the half-saturation constant, a python int or float
        wild_poll - the proportion of crops that are pollinated by wild
            pollinators.  An int or float from 0 to 1.

        returns nothing"""

    # Calculate the yield raster
    k = float(half_sat)
    v = float(wild_poll)
    in_nodata = in_raster.GetRasterBand(1).GetNoDataValue()
    out_nodata = out_raster.GetRasterBand(1).GetNoDataValue()

    # This function is a vectorize-compatible implementation of the yield
    # function from the documentation.
    def calc_yield(frm_avg):
        if frm_avg == in_nodata:
            return out_nodata
        return (1.0 - v) + (v * (frm_avg / (frm_avg + k)))

    # Apply the yield calculation to the foraging_average raster
    invest_core.vectorize1ArgOp(in_raster.GetRasterBand(1), calc_yield,
        out_raster.GetRasterBand(1))


def clip_and_op(in_matrix, arg1, op, in_matrix_nodata=-1, out_matrix_nodata=-1, kwargs={}):
    """Apply an operation to a matrix after the matrix is adjusted for nodata
        values.  After the operation is complete, the matrix will have pixels
        culled based on the input matrix's original values that were less than
        0 (which assumes a nodata value of below zero).

        in_matrix - a numpy matrix for use as the first argument to op
        arg1 - an argument of whatever type is necessary for the second
            argument of op
        op - a python callable object with two arguments: in_matrix and arg1
        in_matrix_nodata - a python int or float
        out_matrix_nodata - a python int or float
        kwargs={} - a python dictionary of keyword arguments to be passed in to
            op when it is called.

        returns a numpy matrix."""

    # Making a copy of the in_matrix so as to avoid side effects from putmask
    matrix = in_matrix.copy()

    # Convert nodata values to 0
    np.putmask(matrix, matrix == in_matrix_nodata, 0)

    # Apply the operation specified by the user
    filtered_matrix = op(matrix, arg1, **kwargs)

    # Restore nodata values to their proper places.
    np.putmask(filtered_matrix, in_matrix == in_matrix_nodata, out_matrix_nodata)

    return filtered_matrix


def map_attribute(base_raster, attr_table, guild_dict, resource_fields,
                  out_raster, list_op):
    """Make an intermediate raster where values are mapped from the base raster
        according to the mapping specified by key_field and value_field.

        base_raster - a GDAL dataset
        attr_table - a subclass of fileio.AbstractTableHandler
        guild_dict - a python dictionary representing the guild row for this
            species.
        resource_fields - a python list of string resource fields
        out_raster - a GDAL dataset
        list_op - a python callable that takes a list of numerical arguments
            and returns a python scalar.  Examples: sum; max

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
            return list_op([value_list[r] * lu_table_dict[lu_code][r] for r in
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
        # Preprocess ag_classes into a dictionary to improve access times in
        # the vectorized function.  Using a dictionary will, on average, make
        # this a constant-time access instead of a linear time access.
        ag_dict = dict((k, True) for k in ag_classes)

        def ag_func(lu_class):
            """Check to see if the input pixel value is an agricultural pixel.
                If so, return 1.  Otherwise, return 0.  If the pixel is a
                nodata pixel, return nodata."""
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


def make_raster_from_lulc(lulc_dataset, raster_uri):
    LOGGER.debug('Creating new raster from LULC: %s', raster_uri)
    dataset = invest_cython_core.newRasterFromBase(\
        lulc_dataset, raster_uri, 'GTiff', -1, gdal.GDT_Float32)
    return dataset

def build_uri(directory, basename, suffix=[]):
    """Take the input directory and basename, inserting the provided suffixes
        just before the file extension.  Each string in the suffix list will be
        underscore-separated.

        directory - a python string folder path
        basename - a python string filename
        suffix='' - a python list of python strings to be separated by
            underscores and concatenated with the basename just before the
            extension.

        returns a python string of the complete path with the correct
        filename."""

    file_base, extension = os.path.splitext(basename)

    # If a siffix is provided, we want the suffix to be prepended with an
    # underscore, so as to separate the file basename and the suffix.  If a
    # suffix is an empty string, ignore it.
    if len(suffix) > 0:
        suffix = '_' + '_'.join([s for s in suffix if s != ''])

    new_filepath = file_base + suffix + extension
    return os.path.join(directory, new_filepath)
