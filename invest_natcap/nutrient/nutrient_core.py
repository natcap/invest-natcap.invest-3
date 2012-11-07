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

    alv = adjusted_loading_value(args['nutrient_export'], args['pixel_yield'],
        args['watersheds'], args['folders']['intermediate'])

    flow_path = get_flow_path(args['dem'])
    retention_raster = get_retention(args['nutrient_retained'], alv,
        flow_path)

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


    for layer in watersheds:
        for shape_index, watershed in enumerate(layer):
            temp_filename = 'watershed_raster_%s.tif' % str(shape_index)

            r_min, r_max, r_mean, r_stddev = get_raster_stat_under_polygon(
                runoff_index, watershed, layer, temp_filename)

            field_index = watershed.GetFieldIndex('mn_runoff')
            LOGGER.debug('Field index: %s, Min: %s, Max: %s, Mean: %s',
                         field_index, r_min, r_max, r_mean)
            print(field_index, r_min, r_max, r_mean)
            watershed.SetField(field_index, r_mean)
            layer.SetFeature(watershed)

def get_raster_stat_under_polygon(raster, shape, sample_layer, raster_path=None,
        stat='all'):
    """Calculate statistics for the input raster under the input polygon.

        raster - a GDAL raster dataset of which statistics should be calculated
        shape - an OGR Feature object complete with spatial reference
            information.
        raster_path=None - the URI that the temp raster should be saved to.  If
            this value is None, the raster will not be saved to disk.
        stat='all' - either 'all' or 'count'.  If count, the int number of
            pixels under this shape will be returned

        Returns a 4-element tuple with:
            (minimum, maximum, mean, standard_deviation)"""

    LOGGER.debug('Starting to calculate stats under a shape.  Target stat=%s',
        stat)
    mask_fill = None
    temp_nodata = -1.0

    if stat == 'all':
        temp_nodata = raster.GetRasterBand(1).GetNoDataValue()
        LOGGER.debug('Setting temp_nodata to %s from input raster', temp_nodata)

        def get_stats(mask_raster):
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
            matrix = mask_raster.GetRasterBand(1).ReadAsArray()
            count = np.count_nonzero(matrix)
            return count
    else:
        raise OptionNotRecognized('Option %s not recognized' % stat)

    # Get the input raster's geotransform information so we can determine the
    # pixel height and width for creating a new raster later.
    raster_geotransform = raster.GetGeoTransform()
    pixel_width = abs(raster_geotransform[1])
    pixel_height = abs(raster_geotransform[5])
    LOGGER.debug('Pixel width=%s, height=%s', pixel_width, pixel_height)

    # Create a memory-bound shapefile for rasterizing later.
    LOGGER.debug('Creating a temp shapefile and layer for rasterizing')
    ogr_driver = ogr.GetDriverByName('Memory')
    temp_shapefile = ogr_driver.CreateDataSource('/tmp/temp_shapefile')
    temp_layer = temp_shapefile.CreateLayer('temp_shapefile',
        sample_layer.GetSpatialRef(), geom_type=ogr.wkbPolygon)
    temp_layer_defn = temp_layer.GetLayerDefn()

    # Make a copy of the feature passed in by the user and save it to the temp
    # shapefile.
    LOGGER.debug('Making a copy of the input feature for rasterizing')
    feature_geom = shape.GetGeometryRef()
    temp_feature = ogr.Feature(temp_layer_defn)
    temp_feature.SetGeometry(feature_geom)
    temp_feature.SetFrom(shape)
    temp_layer.CreateFeature(temp_feature)

    temp_feature.Destroy()
    temp_layer.SyncToDisk()

    # Create a raster from the extents of the shapefile.  I do this here so that
    # we can calculate stats using GDAL, which is about 15x faster than doing
    # the same set of statistics on a numpy matrix with numpy operations.  See
    # invest_natcap.nutrient.compare_mean_calculation for an example.
    temp_raster = raster_utils.create_raster_from_vector_extents(
        pixel_width, pixel_height, gdal.GDT_Float32, temp_nodata,
        '/tmp/watershed_raster.tif', temp_shapefile)
    LOGGER.debug('Temp raster created with rows=%s, cols=%s',
        temp_raster.RasterXSize, temp_raster.RasterYSize)


    if mask_fill != None:
        LOGGER.debug('Filling temp raster with %s', mask_fill)
        temp_raster.GetRasterBand(1).Fill(mask_fill)

    # Rasterize the temp shapefile layer onto the temp raster.  Burn values are
    # all set to 1 so we can use this as a mask in the subsequent call to
    # vectorize_rasters().
    LOGGER.debug('Rasterizing the temp layer onto the temp raster')
    gdal.RasterizeLayer(temp_raster, [1], temp_layer, burn_values=[1])

    return get_stats(temp_raster)

