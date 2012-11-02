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
        args['watersheds'], args['workspace'])

    pass

def get_flow_accumulation(dem):
    # According to the OSGEO python bindings, [0, 0, None, None] should extract
    # the entire matrix.
    # trac.osgeo.org/gdal/browser/trunk/gdal/swig/python/osgeo/gdal.py#L767
    bounding_box = [0, 0, None, None]

    # Create a flow_direction raster for use in the flow_direction function.
    flow_direction = raster_utils.new_raster_from_base(dem,
        '/tmp/flow_direction', 'GTiff', -1.0, gdal.GDT_Float32)
    invest_cython_core.flow_direction_inf(dem, bounding_box, flow_direction)

    # INSERT FLOW ACCUMULATION/RETENION RASTER CALCULATION HERE
    # do the flow_accumulation
    flow_accumulation = raster_utils.flow_accumulation_dinf(flow_direction, dem,
        '/tmp/flow_accumulation.tif')

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
    watersheds = mean_runoff_index(runoff_idx, watersheds, workspace)

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

    ogr_driver = ogr.GetDriverByName('Memory')
    raster_geotransform = runoff_index.GetGeoTransform()
    pixel_width = abs(raster_geotransform[1])
    pixel_height = abs(raster_geotransform[5])

    for layer in watersheds:
        for shape_index, watershed in enumerate(layer):
            temp_shapefile = ogr_driver.CreateDataSource('/tmp/temp_shapefile')
            temp_layer = temp_shapefile.CreateLayer('temp_shapefile',
                watersheds.GetLayer(0).GetSpatialRef(), geom_type=ogr.wkbPolygon)
            temp_layer_defn = temp_layer.GetLayerDefn()

            feature_geom = watershed.GetGeometryRef()
            temp_feature = ogr.Feature(temp_layer_defn)
            temp_feature.SetGeometry(feature_geom)
            temp_feature.SetFrom(watershed)
            temp_layer.CreateFeature(temp_feature)

            temp_feature.Destroy()
            temp_layer.SyncToDisk()

            temp_nodata = -1.0
            temp_raster = raster_utils.create_raster_from_vector_extents(
                pixel_width, pixel_height, gdal.GDT_Float32, temp_nodata,
                '/tmp/watershed_raster.tif', temp_shapefile)

            gdal.RasterizeLayer(temp_raster, [1], temp_layer, burn_values=[1])

            temp_filename = 'watershed_raster_%s.tif' % str(shape_index)
            watershed_pixels = raster_utils.vectorize_rasters([temp_raster,
                runoff_index], lambda x, y: y if x == 1 else temp_nodata,
                nodata=temp_nodata, raster_out_uri = os.path.join(output_folder,
                temp_filename))

            r_min, r_max, r_mean, r_stdev = watershed_pixels.GetRasterBand(1).GetStatistics(0, 1)

            field_index = watershed.GetFieldIndex('mn_runoff')
            LOGGER.debug('Field index: %s, Min: %s, Max: %s, Mean: %s',
                         field_index, r_min, r_max, r_mean)
            print(field_index, r_min, r_max, r_mean)
            watershed.SetField(field_index, r_mean)
            layer.SetFeature(watershed)


