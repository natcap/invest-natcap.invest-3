"""File for core operations of the InVEST Nutrient Retention model."""

import logging
import math
import os.path

from osgeo import gdal
from osgeo import ogr
import numpy as np

import invest_cython_core
from invest_natcap import raster_utils as raster_utils

LOGGER = logging.getLogger('nutrient_core')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class OptionNotRecognized(Exception): pass

def biophysical(args):
    """This function executes the biophysical Nutrient Retention model.

        args - a python dictionary with the following entries:
            'nutrient_export' - a GDAL dataset of nutrient export (a
                reclassified landuse/landcover raster)
            'pixel_yield' - a GDAL dataset of per-pixel water yield.
            'watersheds' - an OGR shapefile

        Returns nothing."""
    print args

    # Reclassifying the LULC raster to be the nutrient_export raster.
    # This is done here in the URI layer so that lower layers don't need to be
    # aware of the paths to the workspace, intermediate, output, etc. folders.
    nutrient_export = get_lulc_map(args['landuse'], args['bio_table'],
        'load', args['folders']['intermediate'])
    nutrient_retained = get_lulc_map(args['landuse'], args['bio_table'],
        'eff', args['folders']['intermediate'])

    alv = adjusted_loading_value(nutrient_export, args['pixel_yield'],
        args['watersheds'], args['folders']['intermediate'])

    flow_path = get_flow_path(args['dem'])

    retention_raster = get_retention(nutrient_retained, alv,
        flow_path)

    for shapefile in [args['watersheds'], args['subwatersheds']]:
        for field, raster in [
            ('nut_export', alv), ('nut_retain', retention_raster)]:
                aggregate_by_shape(raster, shapefile, field, 'sum')

    threshold_raster_path = os.path.join(args['folders']['intermediate'],
        'threshold.tif')
    service_raster_path = os.path.join(args['folders']['intermediate'],
        'service.tif')
    net_service = service(retention_raster, args['watersheds'],
        threshold_raster_path, service_raster_path)

def aggregate_by_shape(raster, shapefile, fieldname, statistic):
    """Aggregate raste values under each feature in shapefile, saving the
    resulting statistic to the shapefile fieldname fieldname.

        raster - a GDAL dataset
        shapefile - an OGR datasource
        fieldname - a string denoting a field that exists in shapefile
        statistic - a statistic to calculate, one of the stat arguments for
            calculate_raster_value_under_shapefile().

    Returns nothing."""

    shape_list = split_datasource(shapefile)

    # Loop through the provided watersheds, calculate how many pixels are under
    # the feature and then calculate the per-pixel threshold, setting it to the
    # 'thresh_c' column.
    shape_index = 0
    for layer in shapefile:
        for shape in layer:
            aggregate_value = get_raster_stat_under_polygon(raster,
                shape_list[shape_index], stat=statistic)

            index = shape.GetFieldIndex(fieldname)
            shape.SetField(index, aggregate_value)
            layer.SetFeature(shape)
            shape_index += 1
        shape_index += 1
        layer.ResetReading()

def service(retention, watersheds, threshold_uri=None, service_uri=None):
    """Calculate the biophysical service of the nutrient retention on a
    landscape over the input watersheds.  This calculation is done on a
    per-pixel basis, but only in watershed areas.

        retention - a GDAL raster of nutrient retention and export.
        watersheds - an OGR shapefile of watersheds on this landscape.  This
            shapefile must have the following fields: 'thresh', 'thresh_c',
            which should be of the type OGR.OFT_Real.
        threshold_uri=None - a string URI to where the threshold raster should
            be stored on disk.  If None, the raster will be stored temporarily
            in memory and will not be saved to disk.
        service_uri=None - a string URI to where the service raster should be
            stored on disk.  If Nonw, the service raster will be stored
            temporarily in memory and will not be saved to disk in this
            function.

        Returns a GDAL dataset of the service raster."""

    watersheds_list = split_datasource(watersheds)

    # Loop through the provided watersheds, calculate how many pixels are under
    # the feature and then calculate the per-pixel threshold, setting it to the
    # 'thresh_c' column.
    watershed_index = 0
    for layer in watersheds:
        for watershed in layer:
            pixel_count = get_raster_stat_under_polygon(retention,
                watersheds_list[watershed_index], stat='count')
            threshold_index = watershed.GetFieldIndex('thresh')
            threshold = watershed.GetFieldAsDouble(threshold_index)

            ratio = threshold/float(pixel_count)
            LOGGER.debug('Calculated thresholdi ratio: %s', ratio)
            ratio_index = watershed.GetFieldIndex('thresh_c')
            watershed.SetField(ratio_index, threshold_index)
            layer.SetFeature(watershed)
            watershed_index += 1
        watershed_index += 1
        layer.ResetReading()

    # If the user has not provided a threshold URI, make the output type MEM.
    # Otherwise, assume GTiff.
    output_type = 'GTiff'
    if threshold_uri == None:
        output_type = 'MEM'

    threshold_raster = raster_utils.new_raster_from_base(retention,
        threshold_uri, output_type, -1.0, gdal.GDT_Float32)
    gdal.RasterizeLayer(threshold_raster, [1], watersheds.GetLayer(0),
        options=['ATTRIBUTE=thresh_c'])

    # Subtract the threshold ratio from the retention raster, as denoted in the
    # service (net_x) function in the documentation.
    nodata = retention.GetRasterBand(1).GetNoDataValue()
    service_op = np.vectorize(lambda x, y: x - y if y != nodata else
        nodata)
    return raster_utils.vectorize_rasters([retention, threshold_raster],
        service_op, raster_out_uri=service_uri, nodata=nodata)

def get_lulc_map(landcover, table, field, folder):
    lu_map = table.get_map('lucode', field)
    lu_map = dict((float(k), (float(v)/1000. if float(v) > 1 else float(v)))
                  for (k, v) in lu_map.iteritems())
    uri = os.path.join(folder, field + '_export.tif')
    raster = raster_utils.reclassify_by_dictionary(
        landcover, lu_map, uri, 'GTiff', -1.0,
        gdal.GDT_Float32)

    return raster

def get_retention(absorption, alv, flow_path):
    """Calculate the quantity of nutrient retained by the landscape.  This is
    calculated by a linear system of equations.

        absorption - a GDAL raster, usually a reclassified land cover raster.
            Example: land cover raster reclassed with the 'eff_n'/'eff_p' field
            in the biophysical input table.
        alv - a GDAL raster representing the nutrient export from this pixel.
            Example: The Adjusted Loading Value raster calculated by calling
            nutrient_core.adjusted_loading_value().
        flow_path - a GDAL raster representing the flow direction.  Values are in
            radians representing the flow direction and are based on the
            DEM.

        Returns a GDAL dataset."""

    # THIS FUNCTION DOES NOTHING RIGHT NOW BECAUSE WE DON'T YET HAVE THE
    # COMPUTATIONAL FRAMEWORK TO CALCULATE THE RETENTION RASTER.
    return absorption

def get_flow_path(dem):
    # According to the OSGEO python bindings, [0, 0, None, None] should extract
    # the entire matrix.
    # trac.osgeo.org/gdal/browser/trunk/gdal/swig/python/osgeo/gdal.py#L767
    bounding_box = [0, 0, None, None]

    # Create a flow_direction raster for use in the flow_direction function.
    flow_direction = raster_utils.new_raster_from_base(dem,
        '/tmp/flow_direction', 'GTiff', -1.0, gdal.GDT_Float32)
    invest_cython_core.flow_direction_inf(dem, bounding_box, flow_direction)

def adjusted_loading_value(export_raster, wyield_raster, watersheds, workspace):
    """Calculate the adjusted loading value (ALV_x).

        export_raster - a gdal raster where pixel values represent the nutrient
            export for that pixel.  This is likely to be a reclassified LULC
            raster.
        wyield_raster - a gdal raster of water yield per pixel.
        watersheds - a list of OGR shapefiles representing watersheds and/or
            subwatersheds

        returns a GDAL rasterband representing the ALV."""

    # Substituting the actual runoff index here by just taking the
    # per-element natural log of the water yield raster. [wyield_raster]
    # should eventually be replaced with the water_yield_upstream_sum
    # raster (the sigma Y_u in the nutrient retention documentation)
    #
    # Also, the lambda notation here necessarily checks for the nodata value and
    # just returns the nodata if it is found.  If the value of x is less than 0,
    # a ValueError is thrown.
    wyield_nodata = wyield_raster.GetRasterBand(1).GetNoDataValue()
    v_op = np.vectorize(lambda x: math.log(x) if x != wyield_nodata else
        wyield_nodata)
    runoff_idx = raster_utils.vectorize_rasters([wyield_raster], v_op)

    # Calculate the mean runoff index per watershed.
    mean_runoff_index(runoff_idx, watersheds, workspace)

    # Take the mean runoff index field calculated and rasterize it onto a new
    # raster the same dimensions of the runoff_index raster.
    runoff_mean_uri = os.path.join(workspace, 'runoff_mean.tif')
    runoff_mean = raster_utils.new_raster_from_base(runoff_idx, runoff_mean_uri, 'GTiff',
        wyield_nodata, gdal.GDT_Float32)
    gdal.RasterizeLayer(runoff_mean, [1], watersheds.GetLayer(0),
                        options=['ATTRIBUTE=mn_runoff'])
    runoff_mean.FlushCache()

    # Now that we have the rasterized runoff mean, vectorize a single operation
    # that takes in one step calcualtes HSS*pol_x.
    alv_op = np.vectorize(lambda x, y, z: (x/y)*z if y != wyield_nodata else
        wyield_nodata)
    alv_uri = os.path.join(workspace, 'alv.tif')
    alv_raster = raster_utils.vectorize_rasters([runoff_idx, runoff_mean,
            export_raster], alv_op, raster_out_uri=alv_uri, nodata=-1.0)

    return alv_raster


def mean_runoff_index(runoff_index, watersheds, output_folder):
    """Calculate the mean runoff index per watershed.

        runoff_index - a GDAL raster of the runoff index per pixel.
        watersheds - an OGR shapefile that is open for writing.

        Returns an OGR shapefile where the 'mean_runoff' field contains the
        calculated runoff index."""

#    # Create a temp raster based on the 
#    gdal_driver = gdal.GetDriverByName('MEM')
#    raster = driver.CreateCopy('/tmp/mem_mask_watersheds', runoff_index)
#    band, nodata = raster_utils.extract_band_and_nodata(raster)
#    band.fill(nodata)

    watersheds_list = split_datasource(watersheds)

    watersheds_index = 0
    for layer in watersheds:
        for shape_index, watershed in enumerate(layer):
            temp_filename = 'watershed_raster_%s.tif' % str(shape_index)

            r_min, r_max, r_mean, r_stddev = get_raster_stat_under_polygon(
                runoff_index, watersheds_list[watersheds_index], temp_filename)

            field_index = watershed.GetFieldIndex('mn_runoff')
            LOGGER.debug('Field index: %s, Min: %s, Max: %s, Mean: %s',
                         field_index, r_min, r_max, r_mean)
            print(field_index, r_min, r_max, r_mean)
            watershed.SetField(field_index, r_mean)
            layer.SetFeature(watershed)
            watersheds_index += 1
        watersheds_index += 1
        layer.ResetReading()

def get_raster_stat_under_polygon(raster, shapefile, raster_path=None,
        stat='all', op=None, method='per_feature'):
    """Calculate statistics for the input raster under the input polygon.

        raster - a GDAL raster dataset of which statistics should be calculated
        shape - an OGR Feature object complete with spatial reference
            information.
        raster_path=None - the URI that the temp raster should be saved to.  If
            this value is None, the raster will not be saved to disk.
        stat='all' - One of these options:
            'all' - causes this function to return a 4-element list of [minimum,
                    maximum, mean, standard_deviation]
            'count' - Causes this function to return an int of the number of
                pixels in raster that are under shape.
            'count_numpy' - same as 'count', only implemented in numpy.
            'sum' - calculcates the sum of the pixels under each feature.
            'op' - use the user-defined operation function.  Return type is up
                to the user.
        op=None - a python function that takes a GDAL dataset as it's single
            argument.  This function may use closures to access other
            information such as GDAL datasets.  Op will only be used if
            stat='op'.
        method='per_feature' - one of:
            'all' - causes statistic to be collected over all features in
                shapefile.
            'per_feature' - causes statistics to be collected per feature in
                shapefile.

            The raster passed in to op will be filled with -1.0 and will have
            values of 1 where shape overlaps it.  The raster's size will equal
            that of shape and will have a pixel size equal to raster.  The
            return type is up to the user.

        Return value and type is determined by what is passed in to the stat
        argument and what method is selected.  If method='per_feature', a list
        of values returned from op will be returned.  If method='all', the
        output of op will be returned, as it is calculated for all features in
        the shapefile.  Raises OptionNotRecognized if an invalid option is given.
        Raises TypeError if 'op' is specified for the stat, but no function is
        given."""

    LOGGER.debug('Starting to calculate stats under a shape.  Target stat=%s',
        stat)
    mask_fill = None
    temp_nodata = -1.0

    if stat == 'all':
        temp_nodata = raster.GetRasterBand(1).GetNoDataValue()
        LOGGER.debug('Setting temp_nodata to %s from input raster', temp_nodata)

        def get_stats(mask_raster):
            """Calculate the min, max, mean and standard deviation of the pixels
                in raster where the pixels of mask_raster are 1.

                mask_raster - a GDAL dataset where values are 1.0 or 0.0 (and
                        the nodata value must be some other value).

                Returns a list with [min. max, mean, stddev]."""

            # Now that we have a mask of which pixels are in the shape of interest, make
            # an output raster where the pixels have the value of the input raster's
            # pixel only if the pixel is in the watershed of interest.  Otherwise, the
            # pixel will have the nodata value.
            LOGGER.debug('Getting the pixels under the mask')
            watershed_pixels = raster_utils.vectorize_rasters([mask_raster,
                raster], lambda x, y: y if x == 1 else temp_nodata,
                nodata=temp_nodata, raster_out_uri=raster_path)

            LOGGER.debug('Extracting statistics from raster')
            stats = watershed_pixels.GetRasterBand(1).GetStatistics(0, 1)
            return stats

    elif stat == 'count':
        # Need to set the mask fill to 0 (while keeping the nodata value at
        # -1.0 so that the mean will consider values of 0 as well as 1.  Because
        # we know exactly how many pixels are in the raster we can use MATH to
        # get the number of pixels in the watershed from the mean.
        mask_fill = 0.0
        LOGGER.debug('Setting fill value to %s', mask_fill)

        def get_stats(mask_raster):
            """Calculate the number of masked pixels (which have a value of 1 in
                mask_raster).

                mask_raster - a GDAL dataset where values are 1.0 or 0.0 (and
                    the nodata value must be some other value).

                Returns an int of how many values in mask_raster have a value of
                1.0."""

            LOGGER.debug('Calculating pixel count under the mask with MATH!')
            stats = mask_raster.GetRasterBand(1).GetStatistics(0, 1)

            columns = mask_raster.RasterXSize
            rows = mask_raster.RasterYSize
            mean = stats[2]  # third element in the stats list
            LOGGER.debug('Mask stats: Rows=%s, cols=%s, mean=%s', rows, columns,
                mean)

            pixels_in_raster = float(columns * rows)
            pixels_under_shape = mean * pixels_in_raster
            LOGGER.debug('In mask raster: %s, under shape: %s',
                pixels_in_raster, pixels_under_shape)

            # In case the stored GDAL mean is not entirely precise, take the
            # ceiling of the pixels under the shape calculated.
            return int(math.ceil(pixels_under_shape))

    elif stat == 'numpy_count':
        mask_fill = 0.0
        LOGGER.debug('Setting mask_fill to %s', mask_fill)

        def get_stats(mask_raster):
            """Calculate the number of nonzero pixels in the input mask raster.
            This calculation is done by loading the mask raster into a numpy
            matrix before calling numpy.count_nonzero().

            mask_raster - a GDAL dataset where values are 1.0 or 0.0 (and the
                nodata value must be some other value).

            returns an int of the number of pixels masked in the mask_raster."""

            LOGGER.debug('Calculating pixel count under the mask with numpy.')
            matrix = mask_raster.GetRasterBand(1).ReadAsArray()
            count = np.count_nonzero(matrix)
            LOGGER.debug('In mask matrix: %s, under shape: %s', matrix.size,
                count)
            return count
    elif stat == 'sum':
        mask_fill = 0.0
        LOGGER.debug('Setting mask_fill to %s', mask_fill)

        def get_stats(mask_raster):
            """Calculate the sum of all the pixels under the mask.
                Returns an int or a float."""
            LOGGER.debug('Calculating pixel sum under the mask')

            # Now that we have a mask of which pixels are in the shape of interest, make
            # an output raster where the pixels have the value of the input raster's
            # pixel only if the pixel is in the watershed of interest.  Otherwise, the
            # pixel will have the nodata value.
            LOGGER.debug('Getting the pixels under the mask')
            watershed_pixels = raster_utils.vectorize_rasters([mask_raster,
                raster], lambda x, y: y if x == 1 else temp_nodata,
                nodata=temp_nodata, raster_out_uri=raster_path)

            stats = watershed_pixels.GetRasterBand(1).GetStatistics(0, 1)
            columns = watershed_pixels.RasterXSize
            rows = watershed_pixels.RasterYSize
            mean = stats[2]

            pixels_in_raster = float(columns * rows)
            return mean * pixels_in_raster
    elif stat == 'op':
        LOGGER.debug('Using the user-defined operation from arguments')
        def get_stats(mask_raster):
            LOGGER.debug('Starting user-defined operation')
            return op(mask_raster)
    else:
        raise OptionNotRecognized('Option %s not recognized' % stat)

    # Get the input raster's geotransform information so we can determine the
    # pixel height and width for creating a new raster later.
    raster_geotransform = raster.GetGeoTransform()
    pixel_width = abs(raster_geotransform[1])
    pixel_height = abs(raster_geotransform[5])
    LOGGER.debug('Pixel width=%s, height=%s', pixel_width, pixel_height)

    # Check the method of processing desired by the user, but default to assess
    # stats across the entire shapefile.
    shapefiles_to_use = [shapefile]
    if method == 'all':
        LOGGER.debug('Statistic will be calculated over all features')
    elif method == 'per_feature':
        LOGGER.debug('Statistic will be calculated per feature')
        shapefiles_to_use = split_datasource(shapefile)
    else:
        LOGGER.warn('Method %s not recognized.  Defaulting to all features.',
            method)

    return_stats = []
    for feature_ds in shapefiles_to_use:
        # Create a raster from the extents of the shapefile.  I do this here so that
        # we can calculate stats using GDAL, which is about 15x faster than doing
        # the same set of statistics on a numpy matrix with numpy operations.  See
        # invest_natcap.nutrient.compare_mean_calculation for an example.
        temp_raster = raster_utils.create_raster_from_vector_extents(
            pixel_width, pixel_height, gdal.GDT_Float32, temp_nodata,
            '/tmp/watershed_raster.tif', shapefile)
        LOGGER.debug('Temp raster created with rows=%s, cols=%s',
            temp_raster.RasterXSize, temp_raster.RasterYSize)


        if mask_fill != None:
            LOGGER.debug('Filling temp raster with %s', mask_fill)
            temp_raster.GetRasterBand(1).Fill(mask_fill)

        # Rasterize the temp shapefile layer onto the temp raster.  Burn values are
        # all set to 1 so we can use this as a mask in the subsequent call to
        # vectorize_rasters().
        LOGGER.debug('Rasterizing the temp layer onto the temp raster')
        gdal.RasterizeLayer(temp_raster, [1], shapefile.GetLayer(0), burn_values=[1])

        return_stats.append(get_stats(temp_raster))

    if len(return_stats) == 1:
        return return_stats[0]
    return return_stats

def split_datasource(ds, uris=None):
    """Split the input OGR datasource into a list of datasources, each with a
    single layer containing a single feature.

        ds - an OGR datasource.
        uris - a list of uris to where the new datasources should be saved on
            disk.  Must have a URI for each feature in ds (even if features are
            split across multiple layers).

    Returns a list of OGR datasources."""

    num_features = sum([l.GetFeatureCount() for l in ds])
    if uris == None:
        driver_string = 'Memory'
        uris = ['/tmp/temp_shapefile'] * num_features
    else:
        driver_string = 'ESRI Shapefile'

    LOGGER.debug('Splitting datasource into separate shapefiles')
    ogr_driver = ogr.GetDriverByName(driver_string)
    output_shapefiles = []
    for layer in ds:
        for feature in layer:
            LOGGER.debug('Creating new shapefile')
            uri_index = len(output_shapefiles)
            temp_shapefile = ogr_driver.CreateDataSource(uris[uri_index])
            temp_layer = temp_shapefile.CreateLayer('temp_shapefile',
                layer.GetSpatialRef(), geom_type=ogr.wkbPolygon)
            temp_layer_defn = temp_layer.GetLayerDefn()

            LOGGER.debug('Creating new feature with duplicate geometry')
            feature_geom = feature.GetGeometryRef()
            temp_feature = ogr.Feature(temp_layer_defn)
            temp_feature.SetGeometry(feature_geom)
            temp_feature.SetFrom(feature)
            temp_layer.CreateFeature(temp_feature)

            temp_feature.Destroy()
            temp_layer.SyncToDisk()
            output_shapefiles.append(temp_shapefile)
        layer.ResetReading()

    LOGGER.debug('Finished creating the new shapefiles %s', output_shapefiles)
    return output_shapefiles

def valuation(args):
    value_table = args['valuation_table'].get_table_dictionary('ws_id', False)
    value_table = dict((int(k), v) for (k, v) in value_table.iteritems())
    for layer in args['watersheds']:
        for index, watershed in enumerate(layer):
            ws_data = value_table[index]

            retained_index = watershed.GetFieldIndex('nut_retained')
            retained = watershed.GetField(retained_index)

            value = watershed_value(ws_data['cost'], retained,
                ws_data['time_span'], ws_data['discount'])

            value_index = watershed.GetFieldIndex('nut_value')
            watershed.SetField(value_index, value)
            watershed.SetFeature()
        layer.ResetReading()


def watershed_value(ws_cost, amt_retained, timespan, discount_rate):
    yearly_discounts = map(lambda t: 1.0/((1.0 + discount_rate)**t), range(timespan))
    LOGGER.debug('Yearly discounts: %s' % yearly_discounts)

    total_discount = sum(yearly_discounts)
    LOGGER.debug('Time discount: %s', total_discount)

    value = ws_cost * amt_retained * total_discount
    LOGGER.debug('Value calculated: %s', value)

    return value
