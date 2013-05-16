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

        flood_height - A tuple: flood_height[0] must be a 2d numpy matrix of flood
            water heights, and have a datatype of numpy.float32.
            flood_height[1] is the numeric value representing nodata for the
            matrix at flood_height[0].
        dem - A tuple: dem[0] is a 2d numpy matrix of elevations that has a
            datatype of numpy.float32.  dem[0] is the numeric value representing
            nodata for the dem matrix.
        channels - A tuple: channels[0] is a 2d numpy matrix where a value of 1
            means that the pixel is a channel pixel and a value of 0 means that
            the pixel is not a channel pixel.  This must have a datatype of
            numpy.byte.  channels[1] is the nodata value for the channels
            matrix.
        curve_nums - A tuple: curve_nums[0] is a 2d numpy matrix of curve
            numbers on the landscape (see the documentation for guidance on
            creating this matrix).  This matrix must have the datatype
            numpy.float32.  curve_nums[1] is the nodata value for the curve_nums
            matrix.
        outflow_direction - A tuple: outflow_direction[0] is a 2d numpy matrix
            indicating which pixels flow into one another.  See routing_utils
            for details on this matrix.  This matrix must have a datatype of
            numpy.byte.  outflow_direction[1] is the nodata value for the
            outflow direction matrix.
        pixel_size -a number indicating the mean of the height and width of a
            pixel.

        All matrices MUST have identical sizes.

        Returns a numpy matrix of the calculated flood inundation height.  This
        matrix has the same size and shape as the input matrices and has a
        datatype of numpy.float32.  The nodata value is -1."""

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flood_height_matrix = flood_height[0]
    cdef int flood_height_nodata = flood_height[1]

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] channels_matrix = channels[0]
    cdef int channels_nodata = channels[1]

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] cn_matrix = curve_nums[0]
    cdef int cn_nodata = curve_nums[1]

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_matrix = dem[0]
    cdef int dem_nodata = dem[1]

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_matrix = outflow_direction[0]
    cdef int outflow_direction_nodata = outflow_direction[1]

    # Output matrix is based on the size and shape of the flood height matrix.
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] output = numpy.copy(flood_height_matrix)

    cdef int num_rows = flood_height_matrix.shape[0]
    cdef int num_cols = flood_height_matrix.shape[1]

    # visited and travel_distance are used in the dynamic programming solution
    # to this function down below.
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

    # If I uncomment this decorator, the compiler for cython complains about an
    # unused numpy-related import.  Leaving it commented out causes a slight
    # slowdown (since this function is not pure c), but it means that the
    # program works just fine.
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

    # See the comment above for this cfunc decorator.
#    @cython.cfunc
    @cython.returns(cython.double)
    @cython.locals(channel_floodwater=cython.double,
        channel_elevation=cython.double, pixel_elevation=cython.double,
        pixel_cn=cython.double)
    def _fid(channel_floodwater, channel_elevation, pixel_elevation, pixel_cn):
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
            pixel_cn == cn_nodata or
            channel_elevation == dem_nodata):
            return 0.0

        elevation_diff = pixel_elevation - channel_elevation
        flooding = channel_floodwater - elevation_diff - pixel_cn

        if flooding <= 0:
            return 0.0
        return flooding

    cdef double channel_floodwater, channel_elevation, fid, channel
    cdef double dist_to_n, n_distance
    cdef int pixel_col_index, pixel_row_index
    cdef int n_row, n_col, n_id, n_dir
    cdef double pixel_elevation, curve_num

    # Implementing these as c arrays eliminates expensive python loops.
    cdef int *neighbor_row_offset = [0, -1, -1, -1, 0, 1, 1, 1]
    cdef int *neighbor_col_offset = [1, 1, 0, -1, -1, -1, 0, 1]

    LOGGER.debug('Visiting channel pixels')
    for channel_row in xrange(num_rows):
        for channel_col in xrange(num_cols):
            channel = channels_matrix[channel_row, channel_col]

            # We only care about when this channel pixel is actually a channel.
            # If it's 0 or nodata, we don't care.
            if channel == 1:
                channel_floodwater = flood_height_matrix[channel_row, channel_col]
                channel_elevation = dem_matrix[channel_row, channel_col]

                # I use python's deque here because:
                #   1.  It's easier to understand what it's doing and
                #   2.  Implementing the same functionality with a C queue
                #       provides no significant speedup.
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
                        # No more indexes to process in the pixel queue, so we
                        # can move on to the next channel cell.
                        break

                    # Looping over the range of available neighbors is faster
                    # than a python list, and we already know the index offsets
                    # (declared above).
                    for n_id in xrange(8):
                        n_row = pixel_row_index + neighbor_row_offset[n_id]
                        n_col = pixel_col_index + neighbor_col_offset[n_id]

                        try:
                            # If either neighbor index is negative, numpy will
                            # happily index into the other side of the matrix.
                            # We therefore need to skip the neighbor entirely.
                            if n_row < 0 or n_col < 0:
                                raise IndexError

                            # If the neighbor is a channel cell or has no
                            # channel data, we also want to skip it.
                            if channels_matrix[n_row, n_col] in [1, channels_nodata]:
                                raise SkipNeighbor

                            n_dir = outflow_direction_matrix[n_row, n_col]
                            if _flows_from(n_id, n_dir):
                                pixel_elevation = dem_matrix[n_row, n_col]
                                curve_num = cn_matrix[n_row, n_col]
                                fid = _fid(channel_floodwater,
                                    channel_elevation, pixel_elevation,
                                    curve_num)

                                # we only care about distributing water when the
                                # flood inundation depth > 0.  If there's no
                                # water to distribute, we don't care about this
                                # neighbor.
                                if fid > 0:
                                    # The distance to the pixel is determined by its
                                    # position.  If its neighbor id is even, it's
                                    # immediately above, below or next to us.  Otherwise, we
                                    # need the distance along the diagonal.
                                    if n_id % 2 == 0:
                                        n_distance = pixel_size
                                    else:
                                        n_distance = diagonal_distance

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
