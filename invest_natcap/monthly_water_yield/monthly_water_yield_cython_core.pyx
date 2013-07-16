import logging
import tempfile

import numpy
cimport numpy
import osgeo
from osgeo import gdal

from invest_natcap.routing import routing_utils
from invest_natcap import raster_utils

from libcpp.stack cimport stack
from libcpp.queue cimport queue
from libc.math cimport atan
from libc.math cimport tan
from libc.math cimport sqrt

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('monthly water yield cython core')

def calculate_tp(dem_uri, precip_uri, dt_out_uri, tp_out_uri):
    """Function to calculate the sum of the direct flows onto a pixel
        plus the precipitation on that pixel.

        dem_uri - a URI to a GDAL dataset representing the DEM.
        precip_uri - a URI to a GDAL dataset representing the DEM.
        dt_uri - a URI to a GDAL dataset representing the direct flow
        tp_out_uri - a URI to an output GDAL dataset that represents the total
            flow on to a pixel plus the precipitation on that pixel.

        returns nothing"""
        
    cdef int row_index, col_index, n_cols, n_rows



    flow_direction_uri = raster_utils.temporary_filename()
    routing_utils.flow_direction_inf(dem_uri, flow_direction_uri)

    flow_direction_band, flow_direction_nodata = (
        raster_utils.extract_band_and_nodata(flow_direction_uri))
    n_cols = flow_direction_band.XSize
    n_rows = flow_direction_band.YSize


    flow_direction_file = tempfile.TemporaryFile()

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] float_direction_array = (
        raster_utils.load_memory_mapped_array(
            flow_direction_uri, flow_direction_file))


    for row_index in range(1, n_rows):
        for col_index in range(1, n_cols):
            pass
