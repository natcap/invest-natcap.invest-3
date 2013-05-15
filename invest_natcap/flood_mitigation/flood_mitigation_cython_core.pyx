import tempfile
import logging
import math
import collections

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
    pixel_size):
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

    cn_matrix = curve_nums[0]
    cdef int cn_nodata = curve_nums[1]

    dem_matrix = dem[0]
    cdef int dem_nodata = dem[1]

    outflow_direction_matrix = outflow_direction[0]
    cdef int outflow_direction_nodata = outflow_direction[1]

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] output = numpy.copy(flood_height_matrix)

    cdef int num_rows = flood_height_matrix.shape[0]
    cdef int num_cols = flood_height_matrix.shape[1]

    visited = numpy.zeros([num_rows, num_cols], dtype=numpy.int)
    travel_distance = numpy.zeros([num_rows, num_cols], dtype=numpy.float)

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
    diagonal_distance = pixel_size * math.sqrt(2)
    indices = [
        (0, (0, 1), pixel_size),
        (1, (-1, 1), diagonal_distance),
        (2, (-1, 0), pixel_size),
        (3, (-1, -1), diagonal_distance),
        (4, (0, -1), pixel_size),
        (5, (1, -1), diagonal_distance),
        (6, (1, 0), pixel_size),
        (7, (1, 1), diagonal_distance)
    ]

    def _flows_from(source_index, neighbor_id):
        """Indicate whether the source pixel flows into the neighbor identified
        by neighbor_id.  This function returns a boolean."""

        neighbor_value = outflow_direction_matrix[source_index]

        # If there is no outflow direction, then there is no flow to the
        # neighbor and we return False.
        if neighbor_value == outflow_direction_nodata:
            return False

        if neighbor_id in INFLOW_NEIGHBORS[neighbor_value]:
            return False
        return True

    def _fid(index, channel_floodwater, channel_elevation):
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
        pixel_elevation = dem_matrix[index]
        curve_num = cn_matrix[index]

        # If there is a channel cell that has no flood inundation on it, we
        # should reasonably assume that there will not be any flood waters
        # distributed from that cell.
        # NOTE: This behavior is not explicitly stated in the user's guide.
        # TODO: Verify with Rich and/or Yonas that this behavior is correct
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
#        if flooding > channel_floodwater:
#            LOGGER.debug(str('p_elevation=%s, cn=%s, c_floodwater=%s, fid=%s, '
#                'c_elevation=%s'), pixel_elevation, curve_num,
#                channel_floodwater, flooding, channel_elevation)
        return flooding

    iterator = numpy.nditer([channels_matrix, flood_height_matrix, dem_matrix],
        flags=['multi_index'])

    LOGGER.debug('Visiting channel pixels')
    for channel, channel_floodwater, channel_elevation in iterator:
        if channel == 1:
            channel_index = iterator.multi_index
            pixels_to_visit = collections.deque([channel_index])

            visited[channel_index] = 1
#            nearest_channel[channel_index][0] = channel_index[0]
#            nearest_channel[channel_index][1] = channel_index[1]

            while True:
                try:
                    pixel_index = pixels_to_visit.pop()
                except IndexError:
                    # No more indexes to process.
                    break

                for n_id, neighbor_offset, n_distance in indices:
                    n_index = tuple(map(sum, zip(pixel_index, neighbor_offset)))

                    try:
                        if n_index[0] < 0 or n_index[1] < 0:
                            raise IndexError

                        if channels_matrix[n_index] in [1, channels_nodata]:
                            raise SkipNeighbor

                        if _flows_from(n_index, n_id):
                            fid = _fid(n_index, channel_floodwater,
                                channel_elevation)

                            if fid > 0:
#                                if fid > channel_floodwater:
#                                    raise Exception('fid=%s, floodwater=%s' %
#                                        (fid, channel_floodwater))
                                dist_to_n = travel_distance[pixel_index] + n_distance
                                if visited[n_index] == 0 or (visited[n_index] == 1 and
                                    dist_to_n < travel_distance[n_index]):
                                    visited[n_index] = 1
                                    travel_distance[n_index] = dist_to_n
#                                    nearest_channel[n_index][0] = channel_index[0]
#                                    nearest_channel[n_index][1] = channel_index[1]
                                    output[n_index] = fid
                                    pixels_to_visit.append(n_index)

                    except (SkipNeighbor, IndexError, AlreadyVisited):
                        pass

    LOGGER.debug('Finished visiting channel pixels')
    return output
