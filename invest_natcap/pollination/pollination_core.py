"""InVEST Pollination model core function  module"""

import invest_cython_core
from invest_natcap import raster_utils
from invest_natcap.invest_core import invest_core

from osgeo import gdal
import numpy as np
import scipy.ndimage as ndimage

import os.path
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
        args['paths'] - a dictionary with the following entries:
            'workspace' - the workspace path
            'intermediate' - the intermediate folder path
            'output' - the output folder path

        returns nothing."""

    LOGGER.debug('Starting pollination biophysical calculations')

    nodata = -1.0
    LOGGER.debug('Using nodata value of %s for internal rasters', nodata)

    lu_nodata = args['landuse'].GetRasterBand(1).GetNoDataValue()
    LOGGER.debug('Landcover nodata=%s', lu_nodata)

    # mask agricultural classes to ag_map.
    #make_ag_raster(args['landuse'], args['ag_classes'], args['ag_map'])
    if len(args['ag_classes']) > 0:
        LOGGER.debug('Agricultural classes: %s', args['ag_classes'])
        reclass = dict((r, 1) for r in args['ag_classes'])
        LOGGER.debug('Reclassifying ag classes as 1.')
        args['ag_map'] = raster_utils.reclassify_by_dictionary(args['landuse'],
            reclass, args['ag_map'], 'GTiff', nodata, gdal.GDT_Float32)
    else:
        LOGGER.debug('User did not define ag classes.')
        args['ag_map'] = raster_utils.vectorize_rasters([args['landuse']],
            lambda x: 1.0 if x != lu_nodata else nodata,
            raster_out_uri=args['ag_map'], nodata=nodata)



    # Open the average foraging matrix for use in the loop over all species,
    # but first we need to ensure that the matrix is filled with 0's.
#    foraging_total_raster = args['foraging_average']
    foraging_total_raster = raster_utils.vectorize_rasters([args['landuse']],
        lambda x: 0.0 if x != lu_nodata else nodata,
        raster_out_uri=args['foraging_average'], nodata=nodata)

    # Open the abundance total raster for use in the loop over all species and
    # ensure that it's filled entirely with 0's.
    abundance_total_raster = raster_utils.vectorize_rasters([args['landuse']],
        lambda x: 0.0 if x != lu_nodata else nodata,
        raster_out_uri=args['abundance_total'], nodata=nodata)

#    abundance_total_raster = args['abundance_total']
#    abundance_total_raster.GetRasterBand(1).Fill(0.0)
#    abundance_matrix_shape = abundance_total_raster.ReadAsArray().shape
#    abundance_total_matrix = np.zeros(abundance_matrix_shape)

    for species, species_dict in args['species'].iteritems():
        guild_dict = args['guilds'].get_table_row('species', species)

        mapped_resource_rasters = {}
        finished_rasters = {}

        for resource, op in [('nesting', max), ('floral', sum)]:
            # Calculate the attribute's resources
            LOGGER.debug('Calculating %s resource raster', resource)
            mapped_resource_rasters[resource] = map_attribute(
                args['landuse'], args['landuse_attributes'],
                guild_dict, args[resource + '_fields'],
                args['species'][species][resource], op, 'GTiff')

        finished_rasters['nesting'] = mapped_resource_rasters['nesting']

        # Now that the per-pixel nesting and floral resources have been
        # calculated, the floral resources still need to factor in
        # neighborhoods.
        # The sigma size is 2 times the pixel size, presumable since the
        # raster's pixel width is a radius for the gaussian blur when we want
        # the diameter of the blur.
        pixel_size = abs(args['landuse'].GetGeoTransform()[1])
        sigma = float(guild_dict['alpha'] / (2 * pixel_size))
        LOGGER.debug('Pixel size: %s | sigma: %s', pixel_size, sigma)

        # Fetch the floral resources raster and matrix from the args dictionary
        # apply a gaussian filter and save the floral resources raster to the
        # dataset.
        LOGGER.debug('Applying neighborhood mappings to %s floral resources',
            species)
        floral_raster = mapped_resource_rasters['floral'].GetRasterBand(1)
        finished_rasters['floral'] = raster_utils.gaussian_filter_dataset(
                mapped_resource_rasters['floral'], sigma,
                args['species'][species]['floral'], -1.0)
#        filtered_matrix = clip_and_op(floral_raster.ReadAsArray(), sigma,
#            ndimage.gaussian_filter, floral_raster.GetNoDataValue())
#        args['species'][species]['floral'].GetRasterBand(1).WriteArray(
#            filtered_matrix)

        # Calculate the pollinator abundance index (using Math! to simplify the
        # equation in the documentation.  We're still waiting on Taylor
        # Rickett's reply to see if this is correct.
        # Once the pollination supply has been calculated, we add it to the
        # total abundance matrix.
        LOGGER.debug('Calculating %s abundance index', species)
        finished_rasters['supply'] = raster_utils.vectorize_rasters(
            [mapped_resource_rasters['nesting'], finished_rasters['floral']],
            lambda x, y: x*y if x != -1.0 else -1.0,
            raster_out_uri=args['species'][species]['species_abundance'],
            nodata=-1.0)

#        nesting_raster = args['species'][species]['nesting'].GetRasterBand(1)
#        supply_matrix = clip_and_op(nesting_raster.ReadAsArray(),
#            filtered_matrix, np.multiply, nesting_raster.GetNoDataValue())

        # Take the pollinator abundance index and multiply it by the species
        # weight in the guilds table.
        species_weight = guild_dict['species_weight']
        abundance_total_raster = raster_utils.vectorize_rasters(
            [abundance_total_raster, finished_rasters['supply']],
            lambda x, y: x + (y*species_weight) if x != -1.0 else -1.0,
            raster_out_uri=args['abundance_total'],
            nodata=-1.0)

#        abundance_total_matrix = clip_and_op(abundance_total_matrix,
#            supply_matrix, np.add, nesting_raster.GetNoDataValue())

#        abundance_total_matrix = clip_and_op(abundance_total_matrix,
#            guild_dict['species_weight'], np.multiply)
#        args['species'][species]['species_abundance'].GetRasterBand(1).\
#            WriteArray(supply_matrix)

        # Calculate the foraging ('farm abundance') index by applying a
        # gaussian filter to the foraging raster and then culling all pixels
        # that are not agricultural before saving it to the output raster.
        LOGGER.debug('Calculating %s foraging/farm abundance index', species)
        finished_rasters['foraging'] = raster_utils.gaussian_filter_dataset(
            finished_rasters['supply'], sigma,
            args['species'][species]['farm_abundance'], -1.0)

        finished_rasters['farm_abundance_masked'] = raster_utils.vectorize_rasters(
            [finished_rasters['foraging'], args['ag_map']],
            lambda x, y: x if y == 1.0 else -1.0,
            raster_out_uri=args['species'][species]['farm_abundance'],
            nodata=-1.0)

#        foraging_raster = args['species'][species]['farm_abundance'].\
#            GetRasterBand(1)
#        foraging_matrix = clip_and_op(supply_matrix, sigma,
#            ndimage.gaussian_filter, foraging_raster.GetNoDataValue())
#        np.putmask(foraging_matrix, args['ag_map'].GetRasterBand(1).\
#                   ReadAsArray() == 0, foraging_raster.GetNoDataValue())
#        foraging_raster.WriteArray(foraging_matrix)

        # Add the current foraging raster to the existing 'foraging_total'
        # raster
        LOGGER.debug('Adding %s foraging abundance raster to total', species)
        foraging_total_raster = raster_utils.vectorize_rasters(
            [finished_rasters['farm_abundance_masked'], foraging_total_raster],
            lambda x, y: x + y if x != -1.0 else -1.0,
            raster_out_uri=args['foraging_total'], nodata=-1.0)
#        foraging_total_matrix = clip_and_op(foraging_matrix,
#            foraging_total_matrix, np.add, foraging_raster.GetNoDataValue())

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
    foraging_total_raster = raster_utils.vectorize_rasters(
        [foraging_total_raster],
        lambda x: x / num_species if x != -1.0 else -1.0,
        raster_out_uri = args['foraging_average'], nodata=-1.0)
#    foraging_total_matrix = clip_and_op(foraging_total_matrix,
#        num_species, divide, foraging_total_raster.GetNoDataValue())
#    foraging_total_raster.WriteArray(foraging_total_matrix)

    # Calculate the mean pollinator supply (pollinator abundance) by taking the
    # abundance_total_matrix and dividing it by the number of pollinators.
    # Then, save the resulting matrix to its raster
    LOGGER.debug('Calculating mean pollinator supply')
    abundance_total_matrix = raster_utils.vectorize_rasters(
        [abundance_total_raster],
        lambda x: x / num_species if x != -1.0 else -1.0,
        raster_out_uri=args['abundance_total'], nodata=-1.0)
#    np.putmask(foraging_total_matrix, foraging_total_matrix < 0, 0)
#    abundance_total_matrix = clip_and_op(abundance_total_matrix, num_species,
#        divide, abundance_total_raster.GetNoDataValue())
#    abundance_total_raster.WriteArray(abundance_total_matrix)

    LOGGER.debug('Finished pollination biophysical calculations')


def valuation(args):
    """Perform the computation of the valuation component of the pollination
        model.

        args - a python dictionary with at least the following entries:
        args['half_saturation'] - a python int or float
        args['wild_pollination_proportion'] - a python int or float between 0
            and 1.
        args['species'][<species_name>]['species_abundance'] - a GDAL dataset
        args['species'][<species_name>]['farm_abundance'] - a GDAL dataset
        args['species'][<species_name>]['farm_value'] - a GDAL dataset
        args['species'][<species_name>]['service_value'] - a GDAL dataset
        args['service_value_sum'] - a GDAL dataset
        args['farm_value_sum'] - a GDAL dataset
        args['foraging_average'] - a GDAL dataset
        args['guilds'] - a fileio tablehandler class
        args['ag_map'] - a GDAL dataset

        returns nothing"""

    LOGGER.debug('Starting valuation')

    # Open matrices for use later.
    farm_value_sum_matrix = args['farm_value_sum'].GetRasterBand(1).\
        ReadAsArray()
    farm_value_sum_matrix.fill(0)
    service_value_sum_matrix = args['service_value_sum'].GetRasterBand(1).\
        ReadAsArray()
    service_value_sum_matrix.fill(0)

    # Define necessary scalars based on inputs.
    in_nodata = args['foraging_average'].GetRasterBand(1).GetNoDataValue()
    out_nodata = in_nodata

    # Loop through all species and calculate the pollinator service value
    for species, species_dict in args['species'].iteritems():

        LOGGER.info('Calculating crop yield due to %s', species)
        # Apply the half-saturation yield function from the documentation and
        # write it to its raster
        calculate_yield(species_dict['farm_abundance'],
            species_dict['farm_value'],args['half_saturation'],
            args['wild_pollination_proportion'])
        farm_value_matrix = species_dict['farm_value'].GetRasterBand(1).ReadAsArray()
        species_dict['farm_value'].GetRasterBand(1).WriteArray(farm_value_matrix)

        # Add the new farm_value_matrix to the farm value sum matrix.
        farm_value_sum_matrix = clip_and_op(farm_value_sum_matrix,
            farm_value_matrix, np.add, in_nodata, out_nodata)

        LOGGER.debug('Calculating service value for %s', species)
        # Open the species foraging matrix and then divide
        # the yield matrix by the foraging matrix for this pollinator.
        species_farm_matrix = species_dict['farm_abundance'].GetRasterBand(1).\
            ReadAsArray()
        ratio_matrix = clip_and_op(farm_value_matrix, species_farm_matrix,
            np.divide, in_nodata, out_nodata)

        # Calculate sigma for the gaussian blur.  Sigma is based on the species
        # alpha (from the guilds table) and twice the pixel size.
        guild_dict = args['guilds'].get_table_row('species', species)
        pixel_size = abs(species_dict['farm_value'].GetGeoTransform()[1])
        sigma = float(guild_dict['alpha'] / (pixel_size * 2.0))
        LOGGER.debug('Pixel size: %s, sigma: %s')

        LOGGER.debug('Applying the blur to the ratio matrix.')
        blurred_ratio_matrix = clip_and_op(ratio_matrix, sigma,
            ndimage.gaussian_filter, in_nodata, out_nodata)

        # Open necessary matrices
        species_supply_matrix = species_dict['species_abundance'].\
            GetRasterBand(1).ReadAsArray()

        v_c = args['wild_pollination_proportion']

        def ps_vectorized(sup_s, blurred_ratio):
            """Apply the pollinator service value function.
                sup_s - the species abundance matrix
                blurred_ratio - the ratio of (yield/farm abundance) with a
                    gaussian filter applied to it."""
            if sup_s == in_nodata:
                return out_nodata
            return v_c * sup_s * blurred_ratio

        # Vectorize the ps_vectorized function
        vOp = np.vectorize(ps_vectorized)
        service_value_matrix = vOp(species_supply_matrix, blurred_ratio_matrix)

        # Set all agricultural pixels to 0.  This is according to issue 761.
        ag_matrix = args['ag_map'].GetRasterBand(1).ReadAsArray()
        np.putmask(service_value_matrix, ag_matrix == 0, 0.0)
        species_dict['service_value'].GetRasterBand(1).WriteArray(
            service_value_matrix)

        # Add the new service value to the service value sum matrix
        service_value_sum_matrix = clip_and_op(service_value_sum_matrix,
            service_value_matrix, np.add, in_nodata, out_nodata)

    # Write the pollination service value to its raster
    args['service_value_sum'].GetRasterBand(1).WriteArray(service_value_sum_matrix)
    args['farm_value_sum'].GetRasterBand(1).WriteArray(farm_value_sum_matrix)
    LOGGER.debug('Finished calculating service value')

def calculate_yield(in_raster, out_raster, half_sat, wild_poll):
    """Calculate the yield raster.

        in_raster - a GDAL dataset
        out_raster -a GDAL dataset
        half_sat - the half-saturation constant, a python int or float
        wild_poll - the proportion of crops that are pollinated by wild
            pollinators.  An int or float from 0 to 1.

        returns nothing"""

    LOGGER.debug('Calculating yield')

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

    LOGGER.debug('Finished calculating yield')

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
                  out_uri, list_op, raster_type):
    """Make an intermediate raster where values are mapped from the base raster
        according to the mapping specified by key_field and value_field.

        base_raster - a GDAL dataset
        attr_table - a subclass of fileio.AbstractTableHandler
        guild_dict - a python dictionary representing the guild row for this
            species.
        resource_fields - a python list of string resource fields
        out_uri - a uri for the output dataset
        list_op - a python callable that takes a list of numerical arguments
            and returns a python scalar.  Examples: sum; max
        raster_type - either 'MEM' or 'GTiff'

        returns nothing."""

    # Get the input raster's nodata value
    base_nodata = base_raster.GetRasterBand(1).GetNoDataValue()

    # Get the output raster's nodata value
#    out_nodata = out_raster.GetRasterBand(1).GetNoDataValue()

    lu_table_dict = attr_table.get_table_dictionary('lulc')

    value_list = dict((r, guild_dict[r]) for r in resource_fields)

    reclass_rules = {base_nodata: -1}
    for lulc, landcover_dict in lu_table_dict.iteritems():
        resource_values = [value_list[r] * lu_table_dict[lulc][r] for r in
            resource_fields]
        reclass_rules[lulc] = list_op(resource_values)

    # Use the rules dictionary to reclassify the LULC accordingly.  This
    # calls the cythonized functionality in raster_utils.
    out_raster = raster_utils.reclassify_by_dictionary(base_raster,
        reclass_rules, out_uri, raster_type, -1, gdal.GDT_Float32)
#
#    # Define a vectorized function to map values to the base raster
#    def map_values(lu_code):
#        """Take the input pixel value and return the appropriate value based
#            on the table's map.  If the value cannot be found, return the
#            output raster's nodata value."""
#        try:
#            if lu_code == base_nodata:
#                return out_nodata
#            # Max() is how InVEST 2.2 pollination does this, although I think
#            # that sum() should actually be used.
#            return list_op([value_list[r] * lu_table_dict[lu_code][r] for r in
#                resource_fields])
#        except KeyError:
#            return out_nodata
#
#    # Vectorize this operation.
#    invest_core.vectorize1ArgOp(base_raster.GetRasterBand(1), map_values,
#        out_raster.GetRasterBand(1))
    return out_raster


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

    LOGGER.debug('Making agricultural raster')
    LOGGER.debug('Landuse: %s, Ag raster: %s. ag classes: %s', landuse_raster,
            ag_raster, ag_classes)
    # Fetch the landcover raster's nodata value
    lu_nodata = landuse_raster.GetRasterBand(1).GetNoDataValue()

    # Fetch the output raster's nodata valye
    ag_nodata = ag_raster.GetRasterBand(1).GetNoDataValue()

    # This case is triggered when the user provides agricultural classes.
    if len(ag_classes) > 0:
        LOGGER.debug('User has defined agricultural classes')
        # Preprocess ag_classes into a dictionary to improve access times in
        # the vectorized function.  Using a dictionary will, on average, make
        # this a constant-time access instead of a linear time access.
        ag_dict = dict((k, True) for k in ag_classes)
        LOGGER.debug('Ag dictionary: %s', ag_dict)

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

    ag_raster.FlushCache()
    LOGGER.debug('Finished making agricultural raster')

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
