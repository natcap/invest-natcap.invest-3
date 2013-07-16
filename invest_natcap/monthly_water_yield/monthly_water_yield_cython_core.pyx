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

def calculate_tp(dem_uri, precip_uri, dt_uri, tp_out_uri):
    """Function to calculate the sum of the direct flows onto a pixel
        plus the precipitation on that pixel.

        dem_uri - a URI to a GDAL dataset representing the DEM.
        precip_uri - a URI to a GDAL dataset representing the DEM.
        dt_uri - a URI to a GDAL dataset representing the direct flow
        tp_out_uri - a URI to an output GDAL dataset that represents the total
            flow on to a pixel plus the precipitation on that pixel.

        returns nothing"""
        
    cdef int current_row, current_col, neighbor_row, neighbor_col
    cdef int n_cols, n_rows

    #Diagonal offsets are based off the following index notation for neighbors
    #    3 2 1
    #    4 p 0
    #    5 6 7

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]

    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]

    cdef float tp_current

    flow_direction_uri = raster_utils.temporary_filename()
    routing_utils.flow_direction_inf(dem_uri, flow_direction_uri)

    flow_direction_band, flow_direction_nodata = (
        raster_utils.extract_band_and_nodata(flow_direction_uri))
    n_cols = flow_direction_band.XSize
    n_rows = flow_direction_band.YSize

    flow_direction_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flow_direction_array = (
        raster_utils.load_memory_mapped_array(
            flow_direction_uri, flow_direction_file))

    dt_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dt_array = (
        raster_utils.load_memory_mapped_array(
            dt_uri, dt_file))
    dt_nodata = raster_utils.get_nodata_from_uri(dt_uri)

    for current_row in range(1, n_rows-1):
        for current_col in range(1, n_cols-1):
            tp_current = 0.0
            for direction_index in range(8):
                neighbor_row = current_row + row_offsets[direction_index]
                neighbor_col = current_col + col_offsets[direction_index]

                dt_current = dt_array[neighbor_row, neighbor_col]
