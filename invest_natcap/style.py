"""A raster styling/visualizing module"""
import os
import numpy as np
import Image
import logging
from osgeo import gdal
from osgeo import ogr
from shapely.geometry import Polygon
from shapely.wkb import loads
from matplotlib import pyplot

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
    min = stats[0]
    max = stats[1]

    LOGGER.debug('Min:Max : %s:%s', min, max)

    # Set the x ranges to interpolate from
    x_range = [min, max]
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

def shape_to_image(shape_in_uri, image_out_uri):
    """

    """
    
    def drawPolygon(polygon, graph):
        xLista, yLista = polygon.exterior.xy
        graph.fill(xLista, yLista, "y")
        graph.plot(xLista, yLista, "k-")
    
    
    fig = pyplot.figure(figsize=(4, 4), dpi=180)
    ax = fig.add_subplot(111)
    
    ds = ogr.Open(shape_in_uri)
    layer = ds.GetLayer()
    for feat in layer:
        geom = feat.GetGeometryRef()
        geom_wkt = geom.ExportToWkb()
        geom_shply = loads(geom_wkt)
        drawPolygon(geom_shply, ax)
    
    pyplot.savefig(image_out_uri)
    #pixel_size = 30
    
    #raster_utils.create_raster_from_vector_extents_uri(
    #    shape_in_uri, pixel_size, gdal_format, nodata_out_value, output_uri)
    
    #raster_utils.rasterize_layer_uri(
    #    raster_uri, shapefile_uri, burn_values=[], option_list=[])
 
