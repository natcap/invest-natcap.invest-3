import tempfile
import logging
import math
import collections

import gdal
cimport numpy
import numpy
import cython

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

class AlreadyVisited(Exception):
    """An exception to indicate that we've already visited this pixel."""
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

    cdef float first_neighbor_weight, neighbor_prev_discharge, runoff
    cdef int neighbor_value, neighbor_id
    cdef double fractional_flow, neighbor_runoff
    cdef double discharge_sum, discharge

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

def calculate_fid(flood_height, dem, channels, curve_nums, outflow_direction,
    in_pixel_size):
    """Actually perform the matrix calculations for the flood inundation depth
        function.  This is equation 20 from the flood mitigation user's guide.

        flood_height - a numpy matrix of flood water heights.
        dem - a numpy matrix of elevations.
        channels - a numpy matrix of channels.
        curve_nums - a numpy matrix of curve numbers.
        outflow_direction - a numpy matrix indicating which pixels flow into one
            another.  See routing_utils for details on this matrix.
        pixel_size -a numpy indicating the mean of the height and width of a
            pixel.

        All matrices MUST have the same sizes.

        Returns a numpy matrix of the calculated flood inundation height."""

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flood_height_matrix = flood_height[0]
    cdef int flood_height_nodata = flood_height[1]

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] channels_matrix = channels[0]
    cdef int channels_nodata = channels[1]

#    cdef numpy.ndarray[numpy.npy_float32, ndim=2] cn_matrix = curve_nums[0]
    cdef numpy.ndarray cn_matrix = curve_nums[0]
    cdef int cn_nodata = curve_nums[1]

#    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_matrix = dem[0]
    cdef numpy.ndarray dem_matrix = dem[0]
    cdef int dem_nodata = dem[1]

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_matrix = outflow_direction[0]
    cdef int outflow_direction_nodata = outflow_direction[1]

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] output = numpy.copy(flood_height_matrix)

    cdef int num_rows = flood_height_matrix.shape[0]
    cdef int num_cols = flood_height_matrix.shape[1]

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] visited = numpy.zeros([num_rows,
        num_cols], dtype=numpy.byte)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] travel_distance = numpy.zeros(
        [num_rows, num_cols], dtype=numpy.float32)

    for name, matrix, nodata in [
        ('flood height', flood_height_matrix, flood_height_nodata),
        ('dem', dem_matrix, dem_nodata),
        ('channels', channels_matrix, channels_nodata),
        ('curve numbers', cn_matrix, cn_nodata),
        ('outflow direction',outflow_direction_matrix, outflow_direction_nodata),
        ('output', output, -1),
        ('visited', visited, None),
        ('travel distance', travel_distance, None)]:
        LOGGER.debug('Matrix %-20s size=%-16s nodata=%-10s', name, matrix.shape,
            nodata)
        assert ((matrix.shape[0] == num_rows) and (matrix.shape[1] == num_cols)), ('Input'
            'rasters must all be the '
            'same size.  %s, %s found.' % matrix.shape, (num_rows, num_cols))


    # to track our nearest channel cell, create a matrix that has two values for
    # each of the elements in the 2-d matrix.  These two extra values represent
    # the index of the closes channel cell.
#    nearest_channel = numpy.zeros(flood_height_matrix.shape + (2,),
#        dtype=numpy.int)

    # We know the diagonal distance thanks to trigonometry.  We're assuming that
    # we measure from the center of this pixel to the center of the neighboring
    # pixel.
    cdef double pixel_size = in_pixel_size
    cdef double diagonal_distance = pixel_size * math.sqrt(2)

#    @cython.cfunc
    @cython.returns(cython.bint)
    @cython.locals(neighbor_id=cython.int, neighbor_value=cython.int)
    def _flows_from(neighbor_id, neighbor_value):
        """Indicate whether the source pixel flows into the neighbor identified
        by neighbor_id.  This function returns a boolean."""

        # If there is no outflow direction, then there is no flow to the
        # neighbor and we return False.
        if neighbor_value == outflow_direction_nodata:
            return False

        if neighbor_id in INFLOW_NEIGHBORS[neighbor_value]:
            return False
        return True

#    @cython.cfunc
    @cython.returns(cython.double)
    @cython.locals(i_row=cython.int, i_col=cython.int,
        channel_floodwater=cython.double, channel_elevation=cython.double)
    def _fid(i_row, i_col, channel_floodwater, channel_elevation):
        """Calculate the on-pixel flood inundation depth, as represented by
            equation 20 in the flood mitigation user's guide.

            index - the tuple index of the pixel on which to calculate FID
            channel_floodwater - the numeric depth of the closest channel cell's
                floodwaters
            channel_elevation - the numeric depth of the closest channel cell's
                elevation

            Note that for this equation to be accurate, the dem and the
            floodwaters must be in the same units.

            Returns a float."""

        cdef double pixel_elevation = dem_matrix[i_row, i_col]
        cdef double curve_num = cn_matrix[i_row, i_col]
        cdef double flooding

        # If there is a channel cell that has no flood inundation on it, we
        # should reasonably assume that there will not be any flood waters
        # distributed from that cell.
        # NOTE: This behavior is not explicitly stated in the user's guide,
        # but Rich says it makes sense.
        if channel_floodwater == 0:
            return 0.0

        if (channel_floodwater == flood_height_nodata or
            pixel_elevation == dem_nodata or
            curve_num == cn_nodata or
            channel_elevation == dem_nodata):
            return 0.0

        elevation_diff = pixel_elevation - channel_elevation
        flooding = channel_floodwater - elevation_diff - curve_num

        if flooding <= 0:
            return 0.0
        return flooding

    cdef double channel_floodwater, channel_elevation, fid, channel
    cdef double dist_to_n, n_distance
    cdef int pixel_col_index, pixel_row_index
    cdef int n_row, n_col, n_id, n_dir

    cdef int *neighbor_row_offset = [0, -1, -1, -1, 0, 1, 1, 1]
    cdef int *neighbor_col_offset = [1, 1, 0, -1, -1, -1, 0, 1]

    LOGGER.debug('Visiting channel pixels')
    for channel_row in xrange(num_rows):
        for channel_col in xrange(num_cols):
            channel = channels_matrix[channel_row, channel_col]

            if channel == 1:
                channel_floodwater = flood_height_matrix[channel_row, channel_col]
                channel_elevation = dem_matrix[channel_row, channel_col]
                pixels_to_visit = collections.deque([(channel_row, channel_col)])

                visited[channel_row, channel_col] = 1
    #            nearest_channel[channel_index][0] = channel_index[0]
    #            nearest_channel[channel_index][1] = channel_index[1]

                while True:
                    try:
                        pixel_index = pixels_to_visit.pop()
                        pixel_row_index = pixel_index[0]
                        pixel_col_index = pixel_index[1]
                    except IndexError:
                        # No more indexes to process.
                        break

                    for n_id in xrange(8):
                        n_row = pixel_row_index + neighbor_row_offset[n_id]
                        n_col = pixel_col_index + neighbor_col_offset[n_id]

                        if n_id % 2 == 0:
                            n_distance = pixel_size
                        else:
                            n_distance = diagonal_distance

                        try:
                            if n_row < 0 or n_col < 0:
                                raise IndexError

                            if channels_matrix[n_row, n_col] in [1, channels_nodata]:
                                raise SkipNeighbor

                            n_dir = outflow_direction_matrix[n_row, n_col]
                            if _flows_from(n_id, n_dir):
                                fid = _fid(n_row, n_col, channel_floodwater,
                                    channel_elevation)

                                if fid > 0:
                                    dist_to_n = travel_distance[n_row, n_col] + n_distance
                                    if (visited[n_row, n_col] == 0 or
                                        (visited[n_row, n_col] == 1 and
                                        dist_to_n < travel_distance[n_row,
                                            n_col])):
                                        visited[n_row, n_col] = 1
                                        travel_distance[n_row, n_col] = dist_to_n
    #                                    nearest_channel[n_row, n_col][0] = channel_index[0]
    #                                    nearest_channel[n_row, n_col][1] = channel_index[1]
                                        output[n_row, n_col] = fid
                                        pixels_to_visit.append((n_row, n_col))

                        except (SkipNeighbor, IndexError, AlreadyVisited):
                            pass

    LOGGER.debug('Finished visiting channel pixels')
    return output
