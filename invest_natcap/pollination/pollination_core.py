"""InVEST Pollination model core function  module"""

from invest_natcap import raster_utils

from osgeo import gdal

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

    args['ag_map'] = reclass_ag_raster(args['landuse'], args['ag_map'],
        args['ag_classes'], nodata)

    # Open the average foraging matrix for use in the loop over all species,
    # but first we need to ensure that the matrix is filled with 0's.
    foraging_total_raster = raster_utils.reclassify_by_dictionary(
        args['landuse'], {}, args['foraging_average'], 'GTiff', nodata,
        gdal.GDT_Float32, 0.0)

    # Open the abundance total raster for use in the loop over all species and
    # ensure that it's filled entirely with 0's.
    abundance_total_raster = raster_utils.reclassify_by_dictionary(
        args['landuse'], {}, args['abundance_total'], 'GTiff', nodata,
        gdal.GDT_Float32, 0.0)

    for species, species_dict in args['species'].iteritems():
        guild_dict = args['guilds'].get_table_row('species', species)

        species_abundance = calculate_abundance(args['landuse'],
            args['landuse_attributes'], guild_dict, args['nesting_fields'],
            args['floral_fields'], uris={
                'nesting': species_dict['nesting'],
                'floral': species_dict['floral'],
                'species_abundance': species_dict['species_abundance']
            })

        # Take the pollinator abundance index and multiply it by the species
        # weight in the guilds table.
        abundance_total_raster = add_two_rasters(abundance_total_raster,
            species_abundance, args['abundance_total'])

        farm_abundance = calculate_farm_abundance(species_abundance,
            args['ag_map'], guild_dict['alpha'],
            species_dict['farm_abundance'])

        # Add the current foraging raster to the existing 'foraging_total'
        # raster
        LOGGER.debug('Adding %s foraging abundance raster to total', species)
        foraging_total_raster = add_two_rasters(farm_abundance,
            foraging_total_raster, args['foraging_total'])

    # Calculate the average foraging index based on the total
    # Divide the total pollination foraging index by the number of pollinators
    # to get the mean pollinator foraging index and save that to its raster.
    LOGGER.debug('Calculating the mean foraging index across all species')

    num_species = float(len(args['species'].values()))
    LOGGER.debug('Number of species: %s', num_species)

    # Calculate the mean foraging values per species.
    LOGGER.debug('Calculating mean foraging score')
    divide_raster(foraging_total_raster, num_species, args['foraging_average'])

    # Calculate the mean pollinator supply (pollinator abundance) by taking the
    # abundance_total_matrix and dividing it by the number of pollinators.
    LOGGER.debug('Calculating mean pollinator supply')
    divide_raster(abundance_total_raster, num_species, args['abundance_total'])

    LOGGER.debug('Finished pollination biophysical calculations')


def calculate_abundance(landuse, lu_attr, guild, nesting_fields,
    floral_fields, uris):
    """Calculate pollinator abundance on the landscape.

        landuse - a GDAL dataset of the LULC.
        lu_attr - a TableHandler
        guild - a dictionary containing information about the pollinator.  All
            entries are required:
            'alpha' - the typical foraging distance in m
            'species_weight' - the relative weight
            resource_n - One entry for each nesting field for each fieldname
                denoted in nesting_fields.  This value must be either 0 and 1,
                indicating whether the pollinator uses this nesting resource for
                nesting sites.
            resource_f - One entry for each floral field denoted in
                floral_fields.  This value must be between 0 and 1,
                representing the liklihood that this species will forage during
                this season.
        nesting_fields - a list of string fieldnames.  Used to extract nesting
            fields from the guild dictionary, so fieldnames here must exist in
            guild.
        floral_fields - a list of string fieldnames.  Used to extract floral
            season fields from the guild dictionary.  Fieldnames here must exist
            in guild.
        uris - a dictionary with these entries:
            'nesting' - a URI to where the nesting raster will be saved.
            'floral' - a URI to where the floral resource raster will be saved.
            'species_abundance' - a URI to where the species abundance raster
                will be saved.

        Returns a GDAL dataset of the species abundance."""
    nodata = -1.0
    floral_raster = map_attribute(landuse, lu_attr, guild, floral_fields,
        uris['floral'], sum)
    nesting_raster = map_attribute(landuse, lu_attr, guild, nesting_fields,
        uris['nesting'], max)

    # Now that the per-pixel nesting and floral resources have been
    # calculated, the floral resources still need to factor in
    # neighborhoods.
    # The sigma size is 2 times the pixel size, presumable since the
    # raster's pixel width is a radius for the gaussian blur when we want
    # the diameter of the blur.
    pixel_size = abs(landuse.GetGeoTransform()[1])
    sigma = float(guild['alpha'] / (2 * pixel_size))
    LOGGER.debug('Pixel size: %s | sigma: %s', pixel_size, sigma)

    # Fetch the floral resources raster and matrix from the args dictionary
    # apply a gaussian filter and save the floral resources raster to the
    # dataset.
    LOGGER.debug('Applying neighborhood mappings to floral resources')
    floral_raster = raster_utils.gaussian_filter_dataset(
        floral_raster, sigma, uris['floral'], nodata)

    # Calculate the pollinator abundance index (using Math! to simplify the
    # equation in the documentation.  We're still waiting on Taylor
    # Rickett's reply to see if this is correct.
    # Once the pollination supply has been calculated, we add it to the
    # total abundance matrix.
    LOGGER.debug('Calculating abundance index')
    species_weight = guild['species_weight']
    return raster_utils.vectorize_rasters(
        [nesting_raster, floral_raster],
        lambda x, y: (x * y) * species_weight if x != nodata else nodata,
        raster_out_uri=uris['species_abundance'], nodata=nodata)


def calculate_farm_abundance(species_abundance, ag_map, alpha, uri):
    """Calculate the farm abundance raster.

        species_abundance - a GDAL dataset of species abundance.
        ag_map - a GDAL dataset of values where ag pixels are 1 and non-ag
            pixels are 0.
        alpha - the typical foraging distance of the current pollinator.
        uri - the output URI for the farm_abundance raster.

        Returns a GDAL dataset of the farm abundance raster."""

    LOGGER.debug('Starting to calculate farm abundance')

    pixel_size = abs(species_abundance.GetGeoTransform()[1])
    sigma = float(alpha / (2 * pixel_size))
    LOGGER.debug('Pixel size: %s | sigma: %s', pixel_size, sigma)

    nodata = species_abundance.GetRasterBand(1).GetNoDataValue()
    LOGGER.debug('Using nodata value %s from species abundance raster', nodata)

    # Calculate the foraging ('farm abundance') index by applying a
    # gaussian filter to the foraging raster and then culling all pixels
    # that are not agricultural before saving it to the output raster.
    LOGGER.debug('Calculating foraging/farm abundance index')
    farm_abundance = raster_utils.gaussian_filter_dataset(
        species_abundance, sigma, uri, nodata)

    # Mask the farm abundance raster according to whether the pixel is
    # agricultural.  If the pixel is agricultural, the value is preserved.
    # Otherwise, the value is set to nodata.
    LOGGER.debug('Setting all agricultural pixels to 0')
    return raster_utils.vectorize_rasters(
        [farm_abundance, ag_map],
        lambda x, y: x if y == 1.0 else nodata,
        raster_out_uri=uri, nodata=nodata)


def reclass_ag_raster(landuse, uri, ag_classes, nodata):
    """Reclassify the landuse raster into a raster demarcating the agricultural
        state of a given pixel.

        landuse - a GDAL dataset.  The land use/land cover raster.
        uri - the uri of the output, reclassified ag raster.
        ag_classes - a list of landuse classes that are agricultural.  If an
            empty list is provided, all landcover classes are considered to be
            agricultural.
        nodata - an int or float.

        Returns a GDAL dataset of the ag raster."""

    # mask agricultural classes to ag_map.
    LOGGER.debug('Starting to create an ag raster at %s. Nodata=%s',
        uri, nodata)
    if len(ag_classes) > 0:
        LOGGER.debug('Agricultural classes: %s', ag_classes)
        reclass_rules = dict((r, 1) for r in ag_classes)
        default_value = 0.0
    else:
        LOGGER.debug('User did not define ag classes.')
        reclass_rules = {}
        default_value = 1.0

    LOGGER.debug('Agricultural reclass map=%s', reclass_rules)
    return raster_utils.reclassify_by_dictionary(landuse,
        reclass_rules, uri, 'GTiff', nodata, gdal.GDT_Float32,
        default_value=default_value)


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
        args['species'][<species_name>]['value_abundance_ratio'] - a URI
        args['species'][<species_name>]['value_abundance_ratio_blur'] - a URI
        args['service_value_sum'] - a GDAL dataset
        args['farm_value_sum'] - a URI
        args['foraging_average'] - a GDAL dataset
        args['guilds'] - a fileio tablehandler class
        args['ag_map'] - a GDAL dataset

        returns nothing"""

    LOGGER.debug('Starting valuation')

    # Open matrices for use later.
    farm_value_sum = raster_utils.reclassify_by_dictionary(args['ag_map'],
        {}, args['farm_value_sum'], 'GTiff', -1.0, gdal.GDT_Float32, 0.0)

    service_value_sum = raster_utils.reclassify_by_dictionary(args['ag_map'],
        {}, args['service_value_sum'], 'GTiff', -1.0, gdal.GDT_Float32, 0.0)

    # Loop through all species and calculate the pollinator service value
    for species, species_dict in args['species'].iteritems():

        LOGGER.info('Calculating crop yield due to %s', species)
        # Apply the half-saturation yield function from the documentation and
        # write it to its raster
        farm_value_raster = calculate_yield(species_dict['farm_abundance'],
            species_dict['farm_value'], args['half_saturation'],
            args['wild_pollination_proportion'], -1.0)

        # Add the new farm_value_matrix to the farm value sum matrix.
        farm_value_sum = add_two_rasters(farm_value_sum, farm_value_raster,
            args['farm_value_sum'])

        LOGGER.debug('Calculating service value for %s', species)
        # Calculate sigma for the gaussian blur.  Sigma is based on the species
        # alpha (from the guilds table) and twice the pixel size.
        guild_dict = args['guilds'].get_table_row('species', species)
        pixel_size = abs(farm_value_raster.GetGeoTransform()[1])
        sigma = float(guild_dict['alpha'] / (pixel_size * 2.0))
        LOGGER.debug('Pixel size: %s, sigma: %s')

        service_value_raster = calculate_service(
            rasters={
                'farm_value': farm_value_raster,
                'farm_abundance': species_dict['farm_abundance'],
                'species_abundance': species_dict['species_abundance'],
                'ag_map': args['ag_map']
            },
            nodata=-1.0,
            sigma=sigma,
            part_wild=args['wild_pollination_proportion'],
            out_uris={
                'species_value': species_dict['value_abundance_ratio'],
                'species_value_blurred': species_dict['value_abundance_ratio_blur'],
                'service_value': species_dict['service_value']
            })

        # Add the new service value to the service value sum matrix
        service_value_sum = add_two_rasters(service_value_sum,
            service_value_raster, args['service_value_sum'])

    LOGGER.debug('Finished calculating service value')


def add_two_rasters(raster_1, raster_2, out_uri):
    """Add two rasters where pixels in raster_1 are not nodata.  Pixels are
        considered to have a nodata value iff the pixel value in raster_1 is
        nodata.  Raster_2's pixel value is not checked for nodata.

        raster_1 - a GDAL dataset
        raster_2 - a GDAL dataset
        out_uri - the uri at which to save the resulting raster.

        Returns the resulting dataset."""

    nodata = raster_1.GetRasterBand(1).GetNoDataValue()

    return raster_utils.vectorize_rasters(
        [raster_1, raster_2], lambda x, y: x + y if y != nodata else nodata,
        raster_out_uri=out_uri, nodata=nodata)


def calculate_service(rasters, nodata, sigma, part_wild, out_uris):
    """Calculate the service raster.

        rasters - a dictionary with these entries:
            'farm_value' - a GDAL dataset.
            'farm_abundance' - a GDAL dataset.
            'species_abundance' - a GDAL dataset.
            'ag_map' - a GDAL dataset.  Values are either nodata, 0 (if not an
                    ag pixel) or 1 (if an ag pixel).
        nodata - the nodata value for output rasters.
        sigma - the sigma to be used for the gaussian filter portion of
            calculating the service raster.
        part_wild - a number between 0 and 1 representing the proportion of all
            pollination that is done by wild pollinators.
        out_uris - a dictionary with these entries:
            'species_value' - a URI.  The raster created at this URI will
                represent the part of the farm's value that is attributed to the
                current species.
            'species_value_blurred' - a URI.  The raster created at this URI
                will be a copy of the species_value raster that has had a
                gaussian filter applied to it.  Sigma is used as the sigma input
                to the gaussian filter.
            'service_value' - a URI.  The raster created at this URI will be the
                calculated service value raster.

        Returns a GDAL dataset of the service value raster."""

    LOGGER.debug('Calculating the service value')

    # Open the species foraging matrix and then divide
    # the yield matrix by the foraging matrix for this pollinator.
    LOGGER.debug('Calculating pollinator value to farms')
    ratio_raster = raster_utils.vectorize_rasters(
        [rasters['farm_value'], rasters['farm_abundance']],
        lambda x, y: x / y if x != nodata else nodata,
        raster_out_uri=out_uris['species_value'], nodata=nodata)

    LOGGER.debug('Applying a gaussian filter to the ratio raster.')
    blurred_ratio_raster = raster_utils.gaussian_filter_dataset(
        ratio_raster, sigma, out_uris['species_value_blurred'],
        nodata)

    # Vectorize the ps_vectorized function
    LOGGER.debug('Attributing farm value to the current species')
    service_value_raster = raster_utils.vectorize_rasters(
        [rasters['species_abundance'], blurred_ratio_raster],
        lambda x, y: part_wild * x * y if x != nodata else nodata,
        raster_out_uri=out_uris['service_value'],
        nodata=nodata)

    # Set all agricultural pixels to 0.  This is according to issue 761.
    LOGGER.debug('Marking the value of all non-ag pixels as 0.0.')
    service_value_raster = raster_utils.vectorize_rasters(
        [rasters['ag_map'], service_value_raster],
        lambda x, y: 0.0 if x == 0 else y,
        raster_out_uri=out_uris['service_value'], nodata=nodata)

    LOGGER.debug('Finished calculating service value')
    return service_value_raster


def calculate_yield(in_raster, out_uri, half_sat, wild_poll, out_nodata):
    """Calculate the yield raster.

        in_raster - a GDAL dataset
        out_uri -a uri for the output dataset
        half_sat - the half-saturation constant, a python int or float
        wild_poll - the proportion of crops that are pollinated by wild
            pollinators.  An int or float from 0 to 1.
        out_nodata - the nodata value for the output raster

        returns a GDAL dataset"""

    LOGGER.debug('Calculating yield')

    # Calculate the yield raster
    k = float(half_sat)
    v = float(wild_poll)
    in_nodata = in_raster.GetRasterBand(1).GetNoDataValue()

    # This function is a vectorize-compatible implementation of the yield
    # function from the documentation.
    def calc_yield(frm_avg):
        if frm_avg == in_nodata:
            return out_nodata
        return (1.0 - v) + (v * (frm_avg / (frm_avg + k)))

    # Apply the yield calculation to the foraging_average raster
    return raster_utils.vectorize_rasters([in_raster], calc_yield,
        raster_out_uri=out_uri, nodata=out_nodata)


def divide_raster(raster, divisor, uri):
    """Divide all non-nodata values in raster_1 by divisor and save the output
        raster to uri.

        raster - a GDAL dataset
        divisor - the divisor (a python scalar)
        uri - the uri to which to save the output raster.

        Returns a GDAL dataset."""

    nodata = raster.GetRasterBand(1).GetNoDataValue()

    return raster_utils.vectorize_rasters(
        [raster], lambda x: x / divisor if x != nodata else nodata,
        raster_out_uri=uri, nodata=nodata)


def map_attribute(base_raster, attr_table, guild_dict, resource_fields,
                  out_uri, list_op):
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

        returns nothing."""

    # Get the input raster's nodata value
    base_nodata = base_raster.GetRasterBand(1).GetNoDataValue()

    # Get the output raster's nodata value

    lu_table_dict = attr_table.get_table_dictionary('lulc')

    value_list = dict((r, guild_dict[r]) for r in resource_fields)

    reclass_rules = {base_nodata: -1}
    for lulc in lu_table_dict.keys():
        resource_values = [value_list[r] * lu_table_dict[lulc][r] for r in
            resource_fields]
        reclass_rules[lulc] = list_op(resource_values)

    # Use the rules dictionary to reclassify the LULC accordingly.  This
    # calls the cythonized functionality in raster_utils.
    out_raster = raster_utils.reclassify_by_dictionary(base_raster,
        reclass_rules, out_uri, 'GTiff', -1, gdal.GDT_Float32)
    return out_raster


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
