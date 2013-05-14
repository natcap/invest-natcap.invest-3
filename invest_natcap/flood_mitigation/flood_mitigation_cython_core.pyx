import tempfile

import gdal
cimport numpy

from invest_natcap.flood_mitigation import flood_mitigation
from invest_natcap import raster_utils

def flood_water_discharge(runoff_uri, flow_direction_uri, time_interval,
    output_uri, outflow_weights_uri, outflow_direction_uri, prev_discharge_uri):

    runoff_data_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] runoff_array = raster_utils.load_memory_mapped_array(
        runoff_uri, runoff_data_file)

    cdef int n_rows = runoff_array.shape[0]
    cdef int n_cols = runoff_array.shape[1]

    cdef int row_index, col_index

    for row_index in xrange(n_rows):
        for col_index in xrange(n_cols):
            if runoff_array[row_index, col_index] == 0:
                runoff_array[row_index, col_index] = -1

    return 0
