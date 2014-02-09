"""A raster styling/visualizing module"""
import os
import numpy as np
import Image
import logging
from osgeo import gdal
from osgeo import ogr
from shapely.wkb import loads
from matplotlib import pyplot
from kartograph import Kartograph

from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('raster_stylizing')

def grayscale_raster(raster_in_uri, raster_out_uri):
    """Create a grayscale image from 'raster_in_uri' by using linear
        interpolation to transform the float values to byte values
        between 0 and 256.

        raster_in_uri - a URI to a gdal raster

        raster_out_uri - a URI to a location on disk to save the output
            gdal raster

        returns - nothing
    """

    # If the output URI already exists, remove it
    if os.path.isfile(raster_out_uri):
        os.remove(raster_out_uri)

    # Max and Min value for the grayscaling
    gray_min = 0
    gray_max = 254

    # Make sure raster stats have been calculated
    raster_utils.calculate_raster_stats_uri(raster_in_uri)
    # Get the raster statistics, looking for Min and Max specifcally
    stats = raster_utils.get_statistics_from_uri(raster_in_uri)
    # Get Min, Max values from raster
    raster_min = stats[0]
    raster_max = stats[1]

    LOGGER.debug('Min:Max : %s:%s', raster_min, raster_max)

    # Set the x ranges to interpolate from
    x_range = [raster_min, raster_max]
    # Set the y ranges to interpolate to
    y_range = [gray_min, gray_max]

    # Get the pixel size of the input raster to use as the output
    # cell size
    pixel_size = raster_utils.get_cell_size_from_uri(raster_in_uri)
    nodata_in = raster_utils.get_nodata_from_uri(raster_in_uri)
    out_nodata = 255

    def to_gray(pix):
        """Vectorize function that does a 1d interpolation
            from floating point values to grayscale values"""
        if pix == nodata_in:
            return out_nodata
        else:
            return int(np.interp(pix, x_range, y_range))

    raster_utils.vectorize_datasets(
        [raster_in_uri], to_gray, raster_out_uri, gdal.GDT_Byte, 255,
        pixel_size, 'intersection')

def tif_to_png(tiff_uri, png_uri):
    """Save a tif of type BYTE as a png file

       raster_in_uri - a URI to a gdal raster of type BYTE

       raster_out_uri - a URI to a location on disk to save the output
           png image

       returns - nothing
    """

    # If the output URI already exists, remove it
    if os.path.isfile(png_uri):
        os.remove(png_uri)

    img = Image.open(tiff_uri)
    img.save(png_uri, 'PNG')

def create_thumbnail(image_in_uri, thumbnail_out_uri, size):
    """Generates a thumbnail image as a PNG file given of size 'size'

        image_in_uri - a URI to an image file

        thumbnail_out_uri - a URI to a location on disk for the output
            thumbnail image (png image)

        size - a tuple of integers with the dimensions of the thumbnail

        returns - nothing"""

    # If the output URI already exists, remove it
    if os.path.isfile(thumbnail_out_uri):
        os.remove(thumbnail_out_uri)

    img = Image.open(image_in_uri)
    img.thumbnail(size)
    img.save(thumbnail_out_uri, 'PNG')

def shape_to_image(shape_in_uri, lat_long_shape, tmp_uri, image_out_uri, css_uri):
    """

    """

    if os.path.isfile(tmp_uri):
        os.remove(tmp_uri)
    if os.path.isfile(image_out_uri):
        os.remove(image_out_uri)

    # Copy the datasource to make some preprocessing adjustments
    shape_copy_uri = 'shape_copy.shp'

    def convert_ogr_fields_to_strings(orig_shape_uri, shape_copy_uri):
        """Converts an OGR Shapefile's fields to String values by
            creating a new OGR Shapefile, building it from the
            originals definitions

            orig_shape_uri -

            shape_copy_uri -

            returns - nothing"""

        orig_shape = ogr.Open(orig_shape_uri)
        orig_layer = orig_shape.GetLayer()

        if os.path.isfile(shape_copy_uri):
            os.remove(shape_copy_uri)

        out_driver = ogr.GetDriverByName('ESRI Shapefile')
        out_ds = out_driver.CreateDataSource(shape_copy_uri)
        orig_layer_dfn = orig_layer.GetLayerDefn()
        out_layer = out_ds.CreateLayer(
            orig_layer_dfn.GetName(), orig_layer.GetSpatialRef(),
            orig_layer_dfn.GetGeomType())

        orig_field_count = orig_layer_dfn.GetFieldCount()

        for fld_index in range(orig_field_count):
            orig_field = orig_layer_dfn.GetFieldDefn(fld_index)
            out_field = ogr.FieldDefn(orig_field.GetName(), ogr.OFTString)
            out_layer.CreateField(out_field)

        for orig_feat in orig_layer:
            out_feat = ogr.Feature(feature_def = out_layer.GetLayerDefn())
            geom = orig_feat.GetGeometryRef()
            out_feat.SetGeometry(geom)

            for fld_index in range(orig_field_count):
                field = orig_feat.GetField(fld_index)
                out_feat.SetField(fld_index, str(field))

            out_layer.CreateFeature(out_feat)
            out_feat = None

    convert_ogr_fields_to_strings(shape_in_uri, shape_copy_uri)

    aoi_sr = raster_utils.get_spatial_ref_uri(shape_copy_uri)
    aoi_wkt = aoi_sr.ExportToWkt()

    # Get the Well Known Text of the shapefile
    shapefile_sr = raster_utils.get_spatial_ref_uri(lat_long_shape)
    shapefile_wkt = shapefile_sr.ExportToWkt()

    # NOTE: I think that kartograph is supposed to do the projection
    # adjustment on the fly but it does not seem to be working for
    # me.

    # Reproject the AOI to the spatial reference of the shapefile so that the
    # AOI can be used to clip the shapefile properly
    raster_utils.reproject_datasource_uri(
            shape_copy_uri, shapefile_wkt, tmp_uri)

    css = open(css_uri).read()

    kart = Kartograph()

    config = {"layers":
                {"mylayer":
                    {"src":tmp_uri,
                     "simplify": 1,
                     "labeling": {"ws_id": "ws_id"},
                     "attributes":["ws_id"]}
                 },
              "proj":{"id": "mercator"},
              "export":{"width":1000, "height": 800}
              }

    kart.generate(config, outfile=image_out_uri, stylesheet=css)














