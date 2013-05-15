import tempfile
import logging

import gdal
import numpy
cimport numpy

from invest_natcap import raster_utils

# This dictionary represents the outflow_matrix values that flow into the
# current pixel.  It's used in several of the flood_mitigation functions.
INFLOW_NEIGHBORS = {
    0: [3, 4],
    1: [4, 5],
    2: [5, 6],
    3: [6, 7],
    4: [7, 0],
    5: [0, 1],
    6: [1, 2],
    7: [2, 3],
}

class SkipNeighbor(Exception):
    """An exception to indicate that we wish to skip this neighbor pixel"""
    pass

logging.basicConfig(format='%(asctime)s %(name)-20s %(funcName)-20s \
    %(levelname)-8s %(message)s', level=logging.DEBUG,
    datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('flood_mitigation_cython')

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

def flood_discharge(runoff_tuple, outflow_direction_tuple,
    outflow_weights_matrix, prev_discharge_matrix, out_discharge_nodata, in_pixel_area,
    in_time_interval):

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] runoff_matrix = runoff_tuple[0]
    cdef int runoff_nodata = runoff_tuple[1]

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction = outflow_direction_tuple[0]
    cdef int outflow_direction_nodata = outflow_direction_tuple[1]

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights = outflow_weights_matrix
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] prev_discharge = prev_discharge_matrix

    cdef int discharge_nodata = out_discharge_nodata
    cdef float pixel_area = in_pixel_area
    cdef float time_interval = in_time_interval

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] discharge_matrix = prev_discharge.copy()

    # list of neighbor ids and their indices relative to the current pixel
    # tuple items are: neighbor_id, row_offset, col_offset.
    cdef int *neighbor_row_offset = [0, -1, -1, -1, 0, 1, 1, 1]
    cdef int *neighbor_col_offset = [1, 1, 0, -1, -1, -1, 0, 1]

    cdef int *first_inflow_neighbor = [3, 4, 5, 6, 7, 0, 1, 2]
    cdef int *second_inflow_neighbor = [4, 5, 6, 7, 0, 1, 2, 3]

    cdef float first_neighbor_weight
    cdef int neighbor_id
    cdef float neighbor_prev_discharge
    cdef int neighbor_value
    cdef double fractional_flow, neighbor_runoff
    cdef double discharge_sum, discharge

    cdef float runoff
    cdef int n_rows = runoff_matrix.shape[0]
    cdef int n_cols = runoff_matrix.shape[1]
    cdef int row_index, col_index, n_index_row, n_index_col, row_offset, col_offset

    for row_index in xrange(n_rows):
        for col_index in xrange(n_cols):
            runoff = runoff_matrix[row_index, col_index]

            if runoff == runoff_nodata:
                discharge_sum = discharge_nodata
            elif outflow_direction[row_index, col_index] == outflow_direction_nodata:
                discharge_sum = discharge_nodata
            else:
                discharge_sum = 0.0  # re-initialize the discharge sum

                for neighbor_id in xrange(8):
                    # Add the index offsets to the current index to get the
                    # neighbor's index.
                    n_index_row = row_index + neighbor_row_offset[neighbor_id]
                    n_index_col = col_index + neighbor_col_offset[neighbor_id]
                    try:
                        if n_index_row < 0 or n_index_col < 0:
                            # The neighbor index is beyond the bounds of the matrix
                            # We need a special case check here because a negative
                            # index will actually return a correct pixel value, just
                            # from the other side of the matrix, which we don't
                            # want.
                            raise IndexError

                        neighbor_value = outflow_direction[n_index_row, n_index_col]
                        possible_inflow_neighbors = INFLOW_NEIGHBORS[neighbor_value]

                        if neighbor_id in possible_inflow_neighbors:
                            # Only get the neighbor's runoff value if we know that
                            # the neighbor flows into this pixel.
                            neighbor_runoff = runoff_matrix[n_index_row, n_index_col]
                            if neighbor_runoff == runoff_nodata:
                                raise SkipNeighbor

                            neighbor_prev_discharge = prev_discharge[n_index_row, n_index_col]
                            if neighbor_prev_discharge == discharge_nodata:
                                raise SkipNeighbor

                            # determine fractional flow from this neighbor into this
                            # pixel.
                            first_neighbor_weight = outflow_weights[n_index_row, n_index_col]

                            if first_inflow_neighbor[neighbor_value] == neighbor_id:
                                fractional_flow = 1.0 - first_neighbor_weight
                            else:
                                fractional_flow = first_neighbor_weight

                            discharge = (((neighbor_runoff * pixel_area) +
                                (neighbor_prev_discharge * time_interval)) *
                                fractional_flow)

                            discharge_sum = discharge_sum + discharge

                    except (IndexError, KeyError, SkipNeighbor):
                        # IndexError happens when the neighbor does not exist.
                        # In this case, we assume there is no inflow from this
                        # neighbor.
                        # KeyError happens when the neighbor has a nodata value.
                        # When this happens, we assume there is no inflow from this
                        # neighbor.
                        # NeighborHasNoRunoffData happens when the neighbor's runoff
                        # value is nodata.
                        pass

                discharge_sum = discharge_sum / time_interval

            # Set the discharge matrix value to the calculated discharge value.
            discharge_matrix[row_index, col_index] = discharge_sum
    return discharge_matrix
