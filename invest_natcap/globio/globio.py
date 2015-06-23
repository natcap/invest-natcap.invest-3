"""GLOBIO InVEST Model"""

import os
import logging

import gdal
import ogr
import osr
import numpy
import pygeoprocessing

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('invest_natcap.globio.globio')


def execute(args):
    """main execute entry point"""

    #append a _ to the suffix if it's not empty and doens't already have one
    try:
        file_suffix = args['results_suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''

    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'output')
    tmp_dir = os.path.join(args['workspace_dir'], 'tmp')

    pygeoprocessing.geoprocessing.create_directories(
        [intermediate_dir, output_dir, tmp_dir])

    if not args['predefined_globio']:
        out_pixel_size = pygeoprocessing.geoprocessing.get_cell_size_from_uri(
            args['lulc_uri'])
    else:
        out_pixel_size = pygeoprocessing.geoprocessing.get_cell_size_from_uri(
            args['globio_lulc_uri'])

    if not args['predefined_globio']:
        #reclassify the landcover map
        lulc_to_globio_table = pygeoprocessing.get_lookup_from_table(
            args['lulc_to_globio_table_uri'], 'lucode')

        lulc_to_globio = dict(
            [(lulc_code, int(table['globio_lucode'])) for
             (lulc_code, table) in lulc_to_globio_table.items()])

        intermediate_globio_lulc_uri = os.path.join(
            intermediate_dir, 'intermediate_globio_lulc%s.tif' %
            file_suffix)
        globio_nodata = -1
        pygeoprocessing.geoprocessing.reclassify_dataset_uri(
            args['lulc_uri'], lulc_to_globio, intermediate_globio_lulc_uri,
            gdal.GDT_Int32, globio_nodata, exception_flag='values_required')

        globio_lulc_uri = os.path.join(
            intermediate_dir, 'globio_lulc%s.tif' % file_suffix)

        sum_yieldgap_uri = args['sum_yieldgap_uri']
        potential_vegetation_uri = args['potential_vegetation_uri']
        pasture_uri = args['pasture_uri']

        #smoothed forest areas are forest areas run through a gaussian filter
        forest_areas_uri = os.path.join(
            tmp_dir, 'forest_areas%s.tif' % file_suffix)
        forest_areas_nodata = -1

        def forest_area_mask_op(lulc_array):
            """masking out forest areas"""
            nodata_mask = lulc_array == globio_nodata
            result = (lulc_array == 130)
            return numpy.where(nodata_mask, forest_areas_nodata, result)

        LOGGER.info("create mask of forest areas")
        pygeoprocessing.geoprocessing.vectorize_datasets(
            [intermediate_globio_lulc_uri], forest_area_mask_op,
            forest_areas_uri, gdal.GDT_Int32, forest_areas_nodata,
            out_pixel_size, "intersection", dataset_to_align_index=0,
            assert_datasets_projected=False, vectorize_op=False)

        LOGGER.info('gaussian filter forest areas')
        sigma = 9.0
        gaussian_kernel_uri = os.path.join(
            tmp_dir, 'gaussian_kernel%s.tif' % file_suffix)
        make_gaussian_kernel_uri(sigma, gaussian_kernel_uri)
        smoothed_forest_areas_uri = os.path.join(
            tmp_dir, 'smoothed_forest_areas%s.tif' %
            file_suffix)
        pygeoprocessing.geoprocessing.convolve_2d_uri(
            forest_areas_uri, gaussian_kernel_uri, smoothed_forest_areas_uri)

        ffqi_uri = os.path.join(
            intermediate_dir, 'ffqi%s.tif' % file_suffix)

        def ffqi_op(forest_areas_array, smoothed_forest_areas):
            """mask out ffqi only where there's an ffqi"""
            return numpy.where(
                forest_areas_array != forest_areas_nodata,
                forest_areas_array * smoothed_forest_areas,
                forest_areas_nodata)

        LOGGER.info('calculate ffqi')
        pygeoprocessing.geoprocessing.vectorize_datasets(
            [forest_areas_uri, smoothed_forest_areas_uri], ffqi_op,
            ffqi_uri, gdal.GDT_Float32, forest_areas_nodata,
            out_pixel_size, "intersection", dataset_to_align_index=0,
            assert_datasets_projected=False, vectorize_op=False)

        #remap globio lulc to an internal lulc based on ag and yield gaps
        #these came from the 'expansion_scenarios.py' script as numbers Justin
        #provided way back on the unilever project.
        pasture_threshold = float(args['pasture_threshold'])
        intensification_threshold = float(args['intensification_threshold'])
        primary_threshold = float(args['primary_threshold'])

        sum_yieldgap_nodata = pygeoprocessing.get_nodata_from_uri(
            args['sum_yieldgap_uri'])

        potential_vegetation_nodata = (
            pygeoprocessing.geoprocessing.get_nodata_from_uri(
                args['potential_vegetation_uri']))
        pasture_nodata = pygeoprocessing.geoprocessing.get_nodata_from_uri(
            args['pasture_uri'])

        def create_globio_lulc(
                lulc_array, sum_yieldgap, potential_vegetation_array,
                pasture_array, ffqi):

            #Step 1.2b: Assign high/low based on yieldgap.
            nodata_mask = lulc_array == globio_nodata
            high_low_intensity_agriculture = numpy.where(
                sum_yieldgap < intensification_threshold, 9.0, 8.0)

            #Step 1.2c: Stamp ag_split classes onto input LULC
            lulc_ag_split = numpy.where(
                lulc_array == 132.0, high_low_intensity_agriculture,
                lulc_array)
            nodata_mask = nodata_mask | (lulc_array == globio_nodata)

            #Step 1.3a: Split Scrublands and grasslands into pristine
            #vegetations, livestock grazing areas, and man-made pastures.
            three_types_of_scrubland = numpy.where(
                (potential_vegetation_array <= 8) & (lulc_ag_split == 131),
                6.0, 5.0)

            three_types_of_scrubland = numpy.where(
                (three_types_of_scrubland == 5.0) &
                (pasture_array < pasture_threshold), 1.0,
                three_types_of_scrubland)

            #Step 1.3b: Stamp ag_split classes onto input LULC
            broad_lulc_shrub_split = numpy.where(
                lulc_ag_split == 131, three_types_of_scrubland, lulc_ag_split)

            #Step 1.4a: Split Forests into Primary, Secondary
            four_types_of_forest = numpy.empty(lulc_array.shape)
            #1.0 is primary forest
            four_types_of_forest[(ffqi >= primary_threshold)] = 1
            #3 is secondary forest
            four_types_of_forest[(ffqi < primary_threshold)] = 3

            #Step 1.4b: Stamp ag_split classes onto input LULC
            globio_lulc = numpy.where(
                broad_lulc_shrub_split == 130, four_types_of_forest,
                broad_lulc_shrub_split)  # stamp primary vegetation

            return numpy.where(nodata_mask, globio_nodata, globio_lulc)

        LOGGER.info('create the globio lulc')
        pygeoprocessing.geoprocessing.vectorize_datasets(
            [intermediate_globio_lulc_uri, sum_yieldgap_uri,
             potential_vegetation_uri, pasture_uri, ffqi_uri],
            create_globio_lulc, globio_lulc_uri, gdal.GDT_Int32, globio_nodata,
            out_pixel_size, "intersection", dataset_to_align_index=0,
            assert_datasets_projected=False, vectorize_op=False)
    else:
        LOGGER.info('no need to calcualte GLOBIO LULC because it is passed in')
        globio_lulc_uri = args['globio_lulc_uri']
        globio_nodata = pygeoprocessing.get_nodata_from_uri(globio_lulc_uri)


    """This is from Justin's old code:
    #Step 1.2b: Assign high/low according to threshold based on yieldgap.
    #high_low_intensity_agriculture_uri = args["export_folder"]+"high_low_intensity_agriculture_"+args['run_id']+".tif"
    high_intensity_agriculture_threshold = 1 #hardcode for now until UI is determined. Eventually this is a user input. Do I bring it into the ARGS dict?
    high_low_intensity_agriculture = numpy.where(sum_yieldgap < float(args['yieldgap_threshold']*high_intensity_agriculture_threshold), 9.0, 8.0) #45. = average yieldgap on global cells with nonzero yieldgap.


    #Step 1.2c: Stamp ag_split classes onto input LULC
    broad_lulc_ag_split = numpy.where(broad_lulc_array==132.0, high_low_intensity_agriculture, broad_lulc_array)

    #Step 1.3a: Split Scrublands and grasslands into pristine vegetations,
    #livestock grazing areas, and man-made pastures.
    three_types_of_scrubland = numpy.zeros(scenario_lulc_array.shape)
    potential_vegetation_array = geotiff_to_array(aligned_agriculture_uris[0])
    three_types_of_scrubland = numpy.where((potential_vegetation_array <= 8) & (broad_lulc_ag_split== 131), 6.0, 5.0) # < 8 min potential veg means should have been forest, 131 in broad  is grass, so 1.0 implies man made pasture
    pasture_array = geotiff_to_array(aligned_agriculture_uris[1])
    three_types_of_scrubland = numpy.where((three_types_of_scrubland == 5.0) & (pasture_array < args['pasture_threshold']), 1.0, three_types_of_scrubland)

    #Step 1.3b: Stamp ag_split classes onto input LULC
    broad_lulc_shrub_split = numpy.where(broad_lulc_ag_split==131, three_types_of_scrubland, broad_lulc_ag_split)

    #Step 1.4a: Split Forests into Primary, Secondary, Lightly Used and Plantation.
    sigma = 9
    primary_threshold = args['primary_threshold']
    secondary_threshold = args['secondary_threshold']
    is_natural = (broad_lulc_shrub_split == 130) | (broad_lulc_shrub_split == 1)
    blurred = scipy.ndimage.filters.gaussian_filter(is_natural.astype(float), sigma, mode='constant', cval=0.0)
    ffqi = blurred * is_natural

    four_types_of_forest = numpy.empty(scenario_lulc_array.shape)
    four_types_of_forest[(ffqi >= primary_threshold)] = 1.0
    four_types_of_forest[(ffqi < primary_threshold) & (ffqi >= secondary_threshold)] = 3.0
    four_types_of_forest[(ffqi < secondary_threshold)] = 4.0

    #Step 1.4b: Stamp ag_split classes onto input LULC
    globio_lulc = numpy.where(broad_lulc_shrub_split == 130 ,four_types_of_forest, broad_lulc_shrub_split) #stamp primary vegetation

    return globio_lulc"""

    #load the infrastructure layers from disk
    infrastructure_filenames = []
    infrastructure_nodata_list = []
    for root_directory, _, filename_list in os.walk(
            args['infrastructure_dir']):

        for filename in filename_list:
            LOGGER.debug(filename)
            if filename.lower().endswith(".tif"):
                LOGGER.debug("tiff added %s", filename)
                infrastructure_filenames.append(
                    os.path.join(root_directory, filename))
                infrastructure_nodata_list.append(
                    pygeoprocessing.geoprocessing.get_nodata_from_uri(
                        infrastructure_filenames[-1]))
            if filename.lower().endswith(".shp"):
                LOGGER.debug("shape added %s", filename)
                infrastructure_tmp_raster = (
                   os.path.join(args['workspace_dir'], os.path.basename(filename.lower() + ".tif")))
                pygeoprocessing.geoprocessing.new_raster_from_base_uri(
                    globio_lulc_uri, infrastructure_tmp_raster,
                    'GTiff', -1.0, gdal.GDT_Int32, fill_value=0)
                pygeoprocessing.geoprocessing.rasterize_layer_uri(
                    infrastructure_tmp_raster,
                    os.path.join(root_directory, filename), burn_values=[1],
                    option_list=["ALL_TOUCHED=TRUE"])
                infrastructure_filenames.append(infrastructure_tmp_raster)
                infrastructure_nodata_list.append(
                    pygeoprocessing.geoprocessing.get_nodata_from_uri(
                        infrastructure_filenames[-1]))

    if len(infrastructure_filenames) == 0:
        raise ValueError(
            "infrastructure directory didn't have any GeoTIFFS or "
            "Shapefiles at %s", args['infrastructure_dir'])

    infrastructure_nodata = -1
    infrastructure_uri = os.path.join(
        intermediate_dir, 'combined_infrastructure%s.tif' % file_suffix)

    def collapse_infrastructure_op(*infrastructure_array_list):
        """Combines all input infrastructure into a single map where if any
            pixel on the stack is 1 gets passed through, any nodata pixel
            masks out all of them"""
        nodata_mask = (
            infrastructure_array_list[0] == infrastructure_nodata_list[0])
        infrastructure_result = infrastructure_array_list[0] > 0
        for index in range(1, len(infrastructure_array_list)):
            current_nodata = (
                infrastructure_array_list[index] ==
                infrastructure_nodata_list[index])

            infrastructure_result = (
                infrastructure_result |
                ((infrastructure_array_list[index] > 0) & ~current_nodata))

            nodata_mask = (
                nodata_mask & current_nodata)

        return numpy.where(
            nodata_mask, infrastructure_nodata, infrastructure_result)

    LOGGER.info('collapse infrastructure into one raster')
    pygeoprocessing.geoprocessing.vectorize_datasets(
        infrastructure_filenames, collapse_infrastructure_op,
        infrastructure_uri, gdal.GDT_Byte, infrastructure_nodata,
        out_pixel_size, "intersection", dataset_to_align_index=0,
        assert_datasets_projected=False, vectorize_op=False)

    #calc_msa_f
    primary_veg_mask_uri = os.path.join(
        tmp_dir, 'primary_veg_mask%s.tif' % file_suffix)
    primary_veg_mask_nodata = -1

    def primary_veg_mask_op(lulc_array):
        """masking out natural areas"""
        nodata_mask = lulc_array == globio_nodata
        result = (lulc_array == 1)
        return numpy.where(nodata_mask, primary_veg_mask_nodata, result)

    LOGGER.info("create mask of primary veg areas")
    pygeoprocessing.geoprocessing.vectorize_datasets(
        [globio_lulc_uri], primary_veg_mask_op,
        primary_veg_mask_uri, gdal.GDT_Int32, primary_veg_mask_nodata,
        out_pixel_size, "intersection", dataset_to_align_index=0,
        assert_datasets_projected=False, vectorize_op=False)

    LOGGER.info('gaussian filter primary veg')
    sigma = 9.0
    gaussian_kernel_uri = os.path.join(
        output_dir, 'gaussian_kernel%s.tif' % file_suffix)
    make_gaussian_kernel_uri(sigma, gaussian_kernel_uri)
    smoothed_primary_veg_mask_uri = os.path.join(
        intermediate_dir, 'smoothed_primary_veg_mask%s.tif' % file_suffix)
    pygeoprocessing.geoprocessing.convolve_2d_uri(
        primary_veg_mask_uri, gaussian_kernel_uri,
        smoothed_primary_veg_mask_uri)

    primary_veg_smooth_uri = os.path.join(
        intermediate_dir, 'primary_veg_smooth%s.tif' % file_suffix)

    def primary_veg_smooth_op(primary_veg_mask_array, smoothed_primary_veg_mask):
        """mask out ffqi only where there's an ffqi"""
        return numpy.where(
            primary_veg_mask_array != primary_veg_mask_nodata,
            primary_veg_mask_array * smoothed_primary_veg_mask,
            primary_veg_mask_nodata)

    LOGGER.info('calculate primary_veg_smooth')
    pygeoprocessing.geoprocessing.vectorize_datasets(
        [primary_veg_mask_uri, smoothed_primary_veg_mask_uri],
        primary_veg_smooth_op, primary_veg_smooth_uri, gdal.GDT_Float32,
        primary_veg_mask_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, assert_datasets_projected=False,
        vectorize_op=False)

    msa_nodata = -1
    def msa_f_op(primary_veg_smooth):
        """calcualte msa fragmentation"""
        nodata_mask = primary_veg_mask_nodata == primary_veg_smooth

        msa_f = numpy.empty(primary_veg_smooth.shape)
        msa_f[:] = 1.0
        #These thresholds come from FFQI from Justin's code; I don't
        #know where they otherwise came from.
        msa_f[(primary_veg_smooth > .9825) & (primary_veg_smooth <= .9984)] = 0.95
        msa_f[(primary_veg_smooth > .89771) & (primary_veg_smooth <= .9825)] = 0.90
        msa_f[(primary_veg_smooth > .578512) & (primary_veg_smooth <= .89771)] = 0.7
        msa_f[(primary_veg_smooth > .42877) & (primary_veg_smooth <= .578512)] = 0.6
        msa_f[(primary_veg_smooth <= .42877)] = 0.3
        msa_f[nodata_mask] = msa_nodata

        return msa_f

    LOGGER.info('calculate msa_f')
    msa_f_uri = os.path.join(output_dir, 'msa_f%s.tif' % file_suffix)
    pygeoprocessing.geoprocessing.vectorize_datasets(
        [primary_veg_smooth_uri], msa_f_op, msa_f_uri, gdal.GDT_Float32,
        msa_nodata, out_pixel_size, "intersection", dataset_to_align_index=0,
        assert_datasets_projected=False, vectorize_op=False)

    #calc_msa_i
    infrastructure_impact_zones = {
        'no impact': 1.0,
        'low impact': 0.9,
        'medium impact': 0.8,
        'high impact': 0.4
    }

    def msa_i_op(lulc_array, distance_to_infrastructure):
        """calculate msa infrastructure"""
        msa_i_tropical_forest = numpy.empty(lulc_array.shape)
        distance_to_infrastructure *= out_pixel_size #convert to meters
        msa_i_tropical_forest[:] = infrastructure_impact_zones['no impact']
        msa_i_tropical_forest[(distance_to_infrastructure > 4000.0) & (distance_to_infrastructure <= 14000.0)] = infrastructure_impact_zones['low impact']
        msa_i_tropical_forest[(distance_to_infrastructure > 1000.0) & (distance_to_infrastructure <= 4000.0)] = infrastructure_impact_zones['medium impact']
        msa_i_tropical_forest[(distance_to_infrastructure <= 1000.0)] = infrastructure_impact_zones['high impact']

        msa_i_temperate_and_boreal_forest = numpy.empty(lulc_array.shape)
        msa_i_temperate_and_boreal_forest[:] = infrastructure_impact_zones['no impact']
        msa_i_temperate_and_boreal_forest[(distance_to_infrastructure > 1200.0) & (distance_to_infrastructure <= 4200.0)] = infrastructure_impact_zones['low impact']
        msa_i_temperate_and_boreal_forest[(distance_to_infrastructure > 300.0) & (distance_to_infrastructure <= 1200.0)] = infrastructure_impact_zones['medium impact']
        msa_i_temperate_and_boreal_forest[(distance_to_infrastructure <= 300.0)] = infrastructure_impact_zones['high impact']

        msa_i_cropland_and_grassland = numpy.empty(lulc_array.shape)
        msa_i_cropland_and_grassland[:] = infrastructure_impact_zones['no impact']
        msa_i_cropland_and_grassland[(distance_to_infrastructure > 2000.0) & (distance_to_infrastructure <= 7000.0)] = infrastructure_impact_zones['low impact']
        msa_i_cropland_and_grassland[(distance_to_infrastructure > 500.0) & (distance_to_infrastructure <= 2000.0)] = infrastructure_impact_zones['medium impact']
        msa_i_cropland_and_grassland[(distance_to_infrastructure <= 500.0)] = infrastructure_impact_zones['high impact']

        msa_i = numpy.where((lulc_array >= 1) & (lulc_array <= 5), msa_i_temperate_and_boreal_forest, infrastructure_impact_zones['no impact'])
        msa_i = numpy.where((lulc_array >= 6) & (lulc_array <= 12), msa_i_cropland_and_grassland, msa_i)

        return msa_i

    LOGGER.info('calculate msa_i')
    distance_to_infrastructure_uri = os.path.join(
        intermediate_dir, 'distance_to_infrastructure%s.tif' % file_suffix)
    pygeoprocessing.geoprocessing.distance_transform_edt(
        infrastructure_uri, distance_to_infrastructure_uri)
    msa_i_uri = os.path.join(output_dir, 'msa_i%s.tif' % file_suffix)
    pygeoprocessing.geoprocessing.vectorize_datasets(
        [globio_lulc_uri, distance_to_infrastructure_uri], msa_i_op, msa_i_uri,
        gdal.GDT_Float32, msa_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, assert_datasets_projected=False,
        vectorize_op=False)

    #calc_msa_lu
    lu_msa_lookup = {
        0.0: 0.0, #map 0 to 0
        1.0: 1.0, #primary veg
        2.0: 0.7, #lightly used natural forest
        3.0: 0.5, #secondary forest
        4.0: 0.2, #forest plantation
        5.0: 0.7, #livestock grazing
        6.0: 0.1, #man-made pastures
        7.0: 0.5, #agroforesty
        8.0: 0.3, #low-input agriculture
        9.0: 0.1, #intenstive agriculture
        10.0: 0.05, #built-up areas
    }
    msa_lu_uri = os.path.join(
        output_dir, 'msa_lu%s.tif' % file_suffix)
    LOGGER.info('calculate msa_lu')
    pygeoprocessing.geoprocessing.reclassify_dataset_uri(
        globio_lulc_uri, lu_msa_lookup, msa_lu_uri,
        gdal.GDT_Float32, globio_nodata, exception_flag='values_required')

    LOGGER.info('calculate msa')
    msa_uri = os.path.join(
        output_dir, 'msa%s.tif' % file_suffix)
    def msa_op(msa_f, msa_lu, msa_i):
        return numpy.where(
            msa_f != globio_nodata, msa_f* msa_lu * msa_i, globio_nodata)
    pygeoprocessing.geoprocessing.vectorize_datasets(
        [msa_f_uri, msa_lu_uri, msa_i_uri], msa_op, msa_uri,
        gdal.GDT_Float32, msa_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, assert_datasets_projected=False,
        vectorize_op=False)

    #summarize by AOI if it exists
    if 'aoi_uri' in args:
        aoi_summary_uri = os.path.join(
            output_dir, 'aoi_summary%s.shp' %
            file_suffix)
        LOGGER.debug('creating new datasource %s', aoi_summary_uri)
        pygeoprocessing.copy_datasource_uri(args['aoi_uri'], aoi_summary_uri)

        LOGGER.debug('aggregating raster values')
        key_dict = pygeoprocessing.aggregate_raster_values_uri(
            msa_uri, args['aoi_uri'], 'OBJECTID')

        LOGGER.debug('adding msa to shape')
        add_column_to_shape(
            aoi_summary_uri, key_dict.pixel_mean, 'msa_mean', 'OBJECTID')

    for filename_to_delete in [smoothed_forest_areas_uri,
                               smoothed_primary_veg_mask_uri,
                               forest_areas_uri,
                               primary_veg_mask_uri,
                               gaussian_kernel_uri]:
        try:
            os.remove(filename_to_delete)
        except OSError:
            LOGGER.warn(
                'attemped to remove %s, but couldn\'t', filename_to_delete)
    try:
        os.rmdir(tmp_dir)
    except OSError:
        LOGGER.warn('attempted to remove %s but couldn\'t', tmp_dir)

def make_gaussian_kernel_uri(sigma, kernel_uri):
    """create a gaussian kernel raster"""
    max_distance = sigma * 5
    kernel_size = int(numpy.round(max_distance * 2 + 1))

    driver = gdal.GetDriverByName('GTiff')
    kernel_dataset = driver.Create(
        kernel_uri.encode('utf-8'), kernel_size, kernel_size, 1,
        gdal.GDT_Float32, options=['BIGTIFF=IF_SAFER'])

    #Make some kind of geotransform, it doesn't matter what but
    #will make GIS libraries behave better if it's all defined
    kernel_dataset.SetGeoTransform([444720, 30, 0, 3751320, 0, -30])
    srs = osr.SpatialReference()
    srs.SetUTM(11, 1)
    srs.SetWellKnownGeogCS('NAD27')
    kernel_dataset.SetProjection(srs.ExportToWkt())

    kernel_band = kernel_dataset.GetRasterBand(1)
    kernel_band.SetNoDataValue(-9999)

    col_index = numpy.array(xrange(kernel_size))
    integration = 0.0
    for row_index in xrange(kernel_size):
        kernel = numpy.exp(
            -((row_index - max_distance)**2 +
                (col_index - max_distance) ** 2)/(2.0*sigma**2)).reshape(
                    1, kernel_size)

        integration += numpy.sum(kernel)
        kernel_band.WriteArray(kernel, xoff=0, yoff=row_index)

    for row_index in xrange(kernel_size):
        kernel_row = kernel_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=kernel_size, win_ysize=1)
        kernel_row /= integration
        kernel_band.WriteArray(kernel_row, 0, row_index)

def add_column_to_shape(shape_uri, field_dict, field_name, key):
    """Add a new field to a shapefile with values from a dictionary.
        The dictionaries keys should match to the values of a unique fields
        values in the shapefile

        shape_uri - a URI path to a ogr datasource on disk with a unique field
            'key'. The field 'key' should have values that
            correspond to the keys of 'field_dict'

        field_dict - a python dictionary with keys mapping to values. These
            values will be what is filled in for the new field

        field_name - a string for the name of the new field to add

        key - a string for the field name in 'shape_uri' that represents
            the unique features

        returns - nothing"""

    shape = ogr.Open(shape_uri, 1)
    layer = shape.GetLayer()

    # Create the new field
    field_defn = ogr.FieldDefn(field_name, ogr.OFTReal)
    layer.CreateField(field_defn)

    # Get the number of features (polygons) and iterate through each
    num_features = layer.GetFeatureCount()
    for feat_id in xrange(num_features):
        feat = layer.GetFeature(feat_id)

        # Get the index for the unique field
        ws_id = feat.GetFieldIndex(key)

        # Get the unique value that will index into the dictionary as a key
        ws_val = feat.GetField(ws_id)

        # Using the unique value from the field of the feature, index into the
        # dictionary to get the corresponding value
        field_val = float(field_dict[ws_val])

        # Get the new fields index and set the new value for the field
        field_index = feat.GetFieldIndex(field_name)
        feat.SetField(field_index, field_val)

        layer.SetFeature(feat)
