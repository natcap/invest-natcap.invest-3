#cython: profile=False

import logging
import os
import collections

import numpy
cimport numpy
cimport cython
import osgeo
from osgeo import gdal
from cython.operator cimport dereference as deref

from libcpp.stack cimport stack
from libcpp.queue cimport queue
from libcpp.set cimport set as c_set
from libc.math cimport atan
from libc.math cimport atan2
from libc.math cimport tan
from libc.math cimport sqrt
from libc.math cimport ceil

cdef extern from "time.h" nogil:
    ctypedef int time_t
    time_t time(time_t*)

from invest_natcap import raster_utils


logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing cython core')

cdef double PI = 3.141592653589793238462643383279502884

cdef int MAX_WINDOW_SIZE = 2**12
cdef double INF = numpy.inf

@cython.boundscheck(False)
@cython.wraparound(False)
def calculate_transport(
    outflow_direction_uri, outflow_weights_uri, sink_cell_set, source_uri,
    absorption_rate_uri, loss_uri, flux_uri, absorption_mode, stream_uri=None):
    """This is a generalized flux transport algorithm that operates
        on a 2D grid given a per pixel flow direction, per pixel source,
        and per pixel absorption rate.  It produces a grid of loss per
        pixel, and amount of outgoing flux per pixel.

        outflow_direction_uri - a uri to a byte dataset that indicates the
            first counter clockwise outflow neighbor as an index from the
            following diagram

            3 2 1
            4 x 0
            5 6 7

        outflow_weights_uri - a uri to a float32 dataset whose elements
            correspond to the percent outflow from the current cell to its
            first counter-clockwise neighbor
        sink_cell_set - a set of flat integer indexes for the cells in flow
            graph that have no outflow
        source_uri - a GDAL dataset that has source flux per pixel
        absorption_rate_uri - a GDAL floating point dataset that has a percent
            of flux absorbed per pixel
        loss_uri - an output URI to to the dataset that will output the
            amount of flux absorbed by each pixel
        flux_uri - a URI to an output dataset that records the amount of flux
            travelling through each pixel
        absorption_mode - either 'flux_only' or 'source_and_flux'. For
            'flux_only' the outgoing flux is (in_flux * absorption + source).
            If 'source_and_flux' then the output flux
            is (in_flux + source) * absorption.
        stream_uri - (optional) a raster to a stream classification layer that
            if 1 indicates a stream 0 if not.  If flux hits a stream the total
            flux is set to zero so that it can't be further routed out of the
            stream if it diverges later.

        returns nothing"""

    #Calculate flow graph

    #Pass transport
    cdef time_t start
    time(&start)

    #Create output arrays for loss and flux
    outflow_direction_dataset = gdal.Open(outflow_direction_uri)
    cdef int n_cols = outflow_direction_dataset.RasterXSize
    cdef int n_rows = outflow_direction_dataset.RasterYSize
    outflow_direction_band = outflow_direction_dataset.GetRasterBand(1)

    cdef int n_block_rows = 3
    cdef int n_block_cols = 3
    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = outflow_direction_band.GetBlockSize()

    #center point of global index
    cdef int global_row, global_col #index into the overall raster
    cdef int row_index, col_index #the index of the cache block
    cdef int row_block_offset, col_block_offset #index into the cache block
    cdef int global_block_row, global_block_col #used to walk the global blocks

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #define all the caches
    cdef numpy.ndarray[numpy.npy_int8, ndim=4] outflow_direction_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int8)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] outflow_weights_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] source_block =numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] absorption_rate_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] loss_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] flux_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_int8, ndim=4] stream_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int8)

    cdef numpy.ndarray[numpy.npy_int8, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.int8)

    cdef int outflow_direction_nodata = raster_utils.get_nodata_from_uri(
        outflow_direction_uri)

    outflow_weights_dataset = gdal.Open(outflow_weights_uri)
    outflow_weights_band = outflow_weights_dataset.GetRasterBand(1)
    cdef int outflow_weights_nodata = raster_utils.get_nodata_from_uri(
        outflow_weights_uri)
    source_dataset = gdal.Open(source_uri)
    source_band = source_dataset.GetRasterBand(1)
    cdef int source_nodata = raster_utils.get_nodata_from_uri(
        source_uri)
    absorption_rate_dataset = gdal.Open(absorption_rate_uri)
    absorption_rate_band = absorption_rate_dataset.GetRasterBand(1)
    cdef int absorption_rate_nodata = raster_utils.get_nodata_from_uri(
        absorption_rate_uri)

    #Create output arrays for loss and flux
    transport_nodata = -1.0
    loss_dataset = raster_utils.new_raster_from_base(
        outflow_direction_dataset, loss_uri, 'GTiff', transport_nodata,
        gdal.GDT_Float32)
    loss_band = loss_dataset.GetRasterBand(1)
    flux_dataset = raster_utils.new_raster_from_base(
        outflow_direction_dataset, flux_uri, 'GTiff', transport_nodata,
        gdal.GDT_Float32)
    flux_band = flux_dataset.GetRasterBand(1)

    cache_dirty[:] = 0
    band_list = [outflow_direction_band, outflow_weights_band, source_band, absorption_rate_band, loss_band, flux_band]
    block_list = [outflow_direction_block, outflow_weights_block, source_block, absorption_rate_block, loss_block, flux_block]
    update_list = [False, False, False, False, True, True]

    cdef int stream_nodata = 0
    if stream_uri != None:
        stream_dataset = gdal.Open(stream_uri)
        stream_band = stream_dataset.GetRasterBand(1)
        stream_nodata = raster_utils.get_nodata_from_uri(stream_uri)
        band_list.append(stream_band)
        block_list.append(stream_block)
        update_list.append(False)
    else:
        stream_band = None

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    #Process flux through the grid
    cdef stack[int] cells_to_process
    for cell in sink_cell_set:
        cells_to_process.push(cell)
    cdef stack[int] cell_neighbor_to_process
    for _ in range(cells_to_process.size()):
        cell_neighbor_to_process.push(0)

    #Diagonal offsets are based off the following index notation for neighbors
    #    3 2 1
    #    4 p 0
    #    5 6 7

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]

    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]

    cdef int neighbor_direction
    cdef double absorption_rate
    cdef double outflow_weight
    cdef double in_flux
    cdef int current_neighbor_index
    cdef int current_index
    cdef int absorb_source = (absorption_mode == 'source_and_flux')

    cdef time_t last_time, current_time
    time(&last_time)
    while cells_to_process.size() > 0:
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info('calculate transport cells_to_process.size() = %d' % (cells_to_process.size()))
            last_time = current_time

        current_index = cells_to_process.top()
        cells_to_process.pop()
        with cython.cdivision(True):
            global_row = current_index / n_cols
            global_col = current_index % n_cols
        #see if we need to update the row cache
        block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)

        #Ensure we are working on a valid pixel, if not set everything to 0
        if source_block[row_index, col_index, row_block_offset, col_block_offset] == source_nodata:
            flux_block[row_index, col_index, row_block_offset, col_block_offset] = 0.0
            loss_block[row_index, col_index, row_block_offset, col_block_offset] = 0.0
            cache_dirty[row_index, col_index] = 1

        #We have real data that make the absorption array nodata sometimes
        #right now the best thing to do is treat it as 0.0 so everything else
        #routes
        if absorption_rate_block[row_index, col_index, row_block_offset, col_block_offset] == absorption_rate_nodata:
            absorption_rate_block[row_index, col_index, row_block_offset, col_block_offset] = 0.0

        if flux_block[row_index, col_index, row_block_offset, col_block_offset] == transport_nodata:
            if stream_block[row_index, col_index, row_block_offset, col_block_offset] == 0:
                flux_block[row_index, col_index, row_block_offset, col_block_offset] = (
                    source_block[row_index, col_index, row_block_offset, col_block_offset])
            else:
                flux_block[row_index, col_index, row_block_offset, col_block_offset] = 0.0
            loss_block[row_index, col_index, row_block_offset, col_block_offset] = 0.0
            cache_dirty[row_index, col_index] = 1
            if absorb_source:
                absorption_rate = absorption_rate_block[row_index, col_index, row_block_offset, col_block_offset]
                loss_block[row_index, col_index, row_block_offset, col_block_offset] = (
                    absorption_rate * flux_block[row_index, col_index, row_block_offset, col_block_offset])
                flux_block[row_index, col_index, row_block_offset, col_block_offset] *= (1 - absorption_rate)

        current_neighbor_index = cell_neighbor_to_process.top()
        cell_neighbor_to_process.pop()
        for direction_index in xrange(current_neighbor_index, 8):
            #get percent flow from neighbor to current cell
            neighbor_row = global_row + row_offsets[direction_index]
            neighbor_col = global_col + col_offsets[direction_index]

            #See if neighbor out of bounds
            if (neighbor_row < 0 or neighbor_row >= n_rows or neighbor_col < 0 or neighbor_col >= n_cols):
                continue

            block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)
            #if neighbor inflows
            neighbor_direction = outflow_direction_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]
            if neighbor_direction == outflow_direction_nodata:
                continue

            #check if the cell flows directly, or is one index off
            if (inflow_offsets[direction_index] != neighbor_direction and
                    ((inflow_offsets[direction_index] - 1) % 8) != neighbor_direction):
                #then neighbor doesn't inflow into current cell
                continue

            #Calculate the outflow weight
            outflow_weight = outflow_weights_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]

            if ((inflow_offsets[direction_index] - 1) % 8) == neighbor_direction:
                outflow_weight = 1.0 - outflow_weight

            if outflow_weight <= 0.0:
                continue
            in_flux = flux_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]

            if in_flux != transport_nodata:
                absorption_rate = absorption_rate_block[row_index, col_index, row_block_offset, col_block_offset]

                #If it's not a stream, route the flux normally
                if stream_block[row_index, col_index, row_block_offset, col_block_offset] == 0:
                    flux_block[row_index, col_index, row_block_offset, col_block_offset] += (
                        outflow_weight * in_flux * (1.0 - absorption_rate))

                    loss_block[row_index, col_index, row_block_offset, col_block_offset] += (
                        outflow_weight * in_flux * absorption_rate)
                else:
                    #Otherwise if it is a stream, all flux routes to the outlet
                    #we don't want it absorbed later
                    flux_block[row_index, col_index, row_block_offset, col_block_offset] = 0.0
                    loss_block[row_index, col_index, row_block_offset, col_block_offset] = 0.0
                cache_dirty[row_index, col_index] = 1
            else:
                #we need to process the neighbor, remember where we were
                #then add the neighbor to the process stack
                cells_to_process.push(current_index)
                cell_neighbor_to_process.push(direction_index)

                #Calculating the flat index for the neighbor and starting
                #at it's neighbor index of 0
                #a global neighbor row needs to be calculated
                cells_to_process.push(neighbor_row * n_cols + neighbor_col)
                cell_neighbor_to_process.push(0)
                break

    block_cache.flush_cache()


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def calculate_flow_weights(
    flow_direction_uri, outflow_weights_uri, outflow_direction_uri):
    """This function calculates the flow weights from a d-infinity based
        flow algorithm to assist in walking up the flow graph.

        flow_direction_uri - uri to a flow direction GDAL dataset that's
            used to calculate the flow graph
        outflow_weights_uri - a uri to a float32 dataset that will be created
            whose elements correspond to the percent outflow from the current
            cell to its first counter-clockwise neighbor
        outflow_direction_uri - a uri to a byte dataset that will indicate the
            first counter clockwise outflow neighbor as an index from the
            following diagram

            3 2 1
            4 x 0
            5 6 7

        returns nothing"""

    cdef time_t start
    time(&start)

    flow_direction_dataset = gdal.Open(flow_direction_uri)
    cdef double flow_direction_nodata
    flow_direction_band, flow_direction_nodata = \
        raster_utils.extract_band_and_nodata(flow_direction_dataset)
    flow_direction_band = flow_direction_dataset.GetRasterBand(1)

    cdef int n_block_rows = 3
    cdef int n_block_cols = 3
    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = flow_direction_band.GetBlockSize()

    cdef numpy.ndarray[numpy.npy_float32, ndim=4] flow_direction_block = numpy.empty(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)

    #This is the array that's used to keep track of the connections of the
    #current cell to those *inflowing* to the cell, thus the 8 directions
    cdef int n_cols, n_rows
    n_cols, n_rows = flow_direction_band.XSize, flow_direction_band.YSize

    cdef int outflow_direction_nodata = 9
    outflow_direction_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, outflow_direction_uri, 'GTiff',
        outflow_direction_nodata, gdal.GDT_Byte, fill_value=outflow_direction_nodata)
    outflow_direction_band = outflow_direction_dataset.GetRasterBand(1)
    cdef numpy.ndarray[numpy.npy_byte, ndim=4] outflow_direction_block = (
        numpy.empty((n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int8))

    cdef double outflow_weights_nodata = -1.0
    outflow_weights_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, outflow_weights_uri, 'GTiff',
        outflow_weights_nodata, gdal.GDT_Float32, fill_value=outflow_weights_nodata)
    outflow_weights_band = outflow_weights_dataset.GetRasterBand(1)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] outflow_weights_block = (
        numpy.empty((n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32))

    #center point of global index
    cdef int global_row, global_col, global_block_row, global_block_col #index into the overall raster
    cdef int row_index, col_index #the index of the cache block
    cdef int row_block_offset, col_block_offset #index into the cache block

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #define all the caches
    cdef numpy.ndarray[numpy.npy_int8, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.int8)

    cache_dirty[:] = 0
    band_list = [flow_direction_band, outflow_direction_band, outflow_weights_band]
    block_list = [flow_direction_block, outflow_direction_block, outflow_weights_block]
    update_list = [False, True, True]

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)


    #The number of diagonal offsets defines the neighbors, angle between them
    #and the actual angle to point to the neighbor
    cdef int n_neighbors = 8
    cdef double *angle_to_neighbor = [0.0, 0.7853981633974483, 1.5707963267948966, 2.356194490192345, 3.141592653589793, 3.9269908169872414, 4.71238898038469, 5.497787143782138]

    #diagonal offsets index is 0, 1, 2, 3, 4, 5, 6, 7 from the figure above
    cdef int *diagonal_offsets = [
        1, -n_cols+1, -n_cols, -n_cols-1, -1, n_cols-1, n_cols, n_cols+1]

    #Iterate over flow directions
    cdef int neighbor_direction_index
    cdef long current_index
    cdef double flow_direction, flow_angle_to_neighbor, outflow_weight

    cdef time_t last_time, current_time
    time(&last_time)
    for global_block_row in xrange(int(ceil(float(n_rows) / block_row_size))):
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info("calculate_flow_weights %.1f%% complete", (global_row + 1.0) / n_rows * 100)
            last_time = current_time
        for global_block_col in xrange(int(ceil(float(n_cols) / block_col_size))):
            for global_row in xrange(global_block_row*block_row_size, min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(global_block_col*block_col_size, min((global_block_col+1)*block_col_size, n_cols)):
                    block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
                    flow_direction = flow_direction_block[row_index, col_index, row_block_offset, col_block_offset]
                    #make sure the flow direction is defined, if not, skip this cell
                    if flow_direction == flow_direction_nodata:
                        continue
                    found = False
                    for neighbor_direction_index in range(n_neighbors):
                        flow_angle_to_neighbor = abs(angle_to_neighbor[neighbor_direction_index] - flow_direction)
                        if flow_angle_to_neighbor <= PI/4.0:
                            found = True

                            #Determine if the direction we're on is oriented at 90
                            #degrees or 45 degrees.  Given our orientation even number
                            #neighbor indexes are oriented 90 degrees and odd are 45
                            outflow_weight = 0.0

                            if neighbor_direction_index % 2 == 0:
                                outflow_weight = 1.0 - tan(flow_angle_to_neighbor)
                            else:
                                outflow_weight = tan(PI/4.0 - flow_angle_to_neighbor)

                            # clamping the outflow weight in case it's too large or small
                            if outflow_weight >= 1.0:
                                outflow_weight = 1.0
                            if outflow_weight <= 0.0:
                                outflow_weight = 1.0
                                neighbor_direction_index = (neighbor_direction_index + 1) % 8
                            outflow_direction_block[row_index, col_index, row_block_offset, col_block_offset] = neighbor_direction_index
                            outflow_weights_block[row_index, col_index, row_block_offset, col_block_offset] = outflow_weight
                            cache_dirty[row_index, col_index] = 1

                            #we found the outflow direction
                            break
                    if not found:
                        LOGGER.warn('no flow direction found for %s %s' % \
                                         (row_index, col_index))
    block_cache.flush_cache()

cdef struct Row_Col_Weight_Tuple:
    int row_index
    int col_index
    int weight

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef _build_flat_set(
    char *dem_uri, float nodata_value, c_set[int] &flat_set):

    cdef int *neighbor_row_offset = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *neighbor_col_offset = [1,  1,  0, -1, -1, -1, 0, 1]

    cdef double dem_value, neighbor_dem_value

    dem_ds = gdal.Open(dem_uri)
    band = dem_ds.GetRasterBand(1)

    cdef int n_block_rows = 3
    cdef int n_block_cols = 3
    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = band.GetBlockSize()
    cdef int n_rows = dem_ds.RasterYSize
    cdef int n_cols = dem_ds.RasterXSize

    #center point of global index
    cdef int global_row, global_col #index into the overall raster
    cdef int row_index, col_index #the index of the cache block
    cdef int row_block_offset, col_block_offset #index into the cache block
    cdef int global_block_row, global_block_col #used to walk the global blocks

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #define all the caches
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] dem_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)

    cdef numpy.ndarray[numpy.npy_int8, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.int8)

    cache_dirty[:] = 0
    band_list = [band]
    block_list = [dem_block]
    update_list = [False]
    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef time_t last_time, current_time
    time(&last_time)
    #not flat on the edges of the raster, could be a sink
    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))
    for global_block_row in xrange(n_global_block_rows):
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info("_build_flat_set %.1f%% complete", (global_row + 1.0) / n_rows * 100)
            last_time = current_time
        for global_block_col in xrange(n_global_block_cols):
            for global_row in xrange(global_block_row*block_row_size, min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(global_block_col*block_col_size, min((global_block_col+1)*block_col_size, n_cols)):

                    block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
                    dem_value = dem_block[row_index, col_index, row_block_offset, col_block_offset]
                    if dem_value == nodata_value:
                        continue

                    #check all the neighbors, if nodata or lower, this isn't flat
                    for neighbor_index in xrange(8):
                        neighbor_row = neighbor_row_offset[neighbor_index] + global_row
                        neighbor_col = neighbor_col_offset[neighbor_index] + global_col

                        if neighbor_row >= n_rows or neighbor_row < 0 or neighbor_col >= n_cols or neighbor_col < 0:
                            continue
                        block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)
                        neighbor_dem_value = dem_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]
                        if neighbor_dem_value < dem_value or neighbor_dem_value == nodata_value:
                            break
                    else:
                        #This is a flat element
                        flat_set.insert(global_row * n_cols + global_col)


def fill_pits(dem_uri, dem_out_uri):
    """This function fills regions in a DEM that don't drain to the edge
        of the dataset.  The resulting DEM will likely have plateaus where the
        pits are filled.

        dem_uri - the original dem URI
        dem_out_uri - the original dem with pits raised to the highest drain
            value

        returns nothing"""

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]

    dem_ds = gdal.Open(dem_uri, gdal.GA_ReadOnly)
    cdef int n_rows = dem_ds.RasterYSize
    cdef int n_cols = dem_ds.RasterXSize

    dem_band = dem_ds.GetRasterBand(1)

    #copy the dem to a different dataset so we know the type
    dem_band = dem_ds.GetRasterBand(1)
    raw_nodata_value = raster_utils.get_nodata_from_uri(dem_uri)

    cdef double nodata_value
    if raw_nodata_value is not None:
        nodata_value = raw_nodata_value
    else:
        LOGGER.warn("Nodata value not set, defaulting to -9999.9")
        nodata_value = -9999.9
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_out_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        INF)
    dem_out_ds = gdal.Open(dem_out_uri, gdal.GA_Update)
    dem_out_band = dem_out_ds.GetRasterBand(1)
    cdef int row_index, col_index, neighbor_index
    cdef float min_dem_value, cur_dem_value, neighbor_dem_value
    cdef int pit_count = 0

    for row_index in range(n_rows):
        dem_out_array = dem_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1)
        dem_out_band.WriteArray(dem_out_array, xoff=0, yoff=row_index)

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_array

    for row_index in range(1, n_rows - 1):
        #load 3 rows at a time
        dem_array = dem_out_band.ReadAsArray(
            xoff=0, yoff=row_index-1, win_xsize=n_cols, win_ysize=3)

        for col_index in range(1, n_cols - 1):
            min_dem_value = nodata_value
            cur_dem_value = dem_array[1, col_index]
            if cur_dem_value == nodata_value:
                continue
            for neighbor_index in range(8):
                neighbor_dem_value = dem_array[
                    1 + row_offsets[neighbor_index],
                    col_index + col_offsets[neighbor_index]]
                if neighbor_dem_value == nodata_value:
                    continue
                if (neighbor_dem_value < min_dem_value or
                    min_dem_value == nodata_value):
                    min_dem_value = neighbor_dem_value
            if min_dem_value > cur_dem_value:
                #it's a pit, bump it up
                dem_array[1, col_index] = min_dem_value
                pit_count += 1

        dem_out_band.WriteArray(
            dem_array[1, :].reshape((1,n_cols)), xoff=0, yoff=row_index)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def resolve_flat_regions_for_drainage(dem_uri, dem_out_uri):
    """This function resolves the flat regions on a DEM that cause undefined
        flow directions to occur during routing.  The algorithm is the one
        presented in "The assignment of drainage direction over float surfaces
        in raster digital elevation models by Garbrecht and Martz (1997)

        dem_carray - a chunked floating point array that represents a digital
            elevation model.  Any flat regions that would cause an undefined
            flow direction will be adjusted in height so that every pixel
            on the dem has a local defined slope.

        nodata_value - this value will be ignored on the DEM as a valid height
            value

        returns nothing"""

    cdef int n_rows, n_cols
    n_rows, n_cols = raster_utils.get_row_col_from_uri(dem_uri)
    raw_nodata_value = raster_utils.get_nodata_from_uri(dem_uri)

    cdef float nodata_value
    if raw_nodata_value is not None:
        nodata_value = raw_nodata_value
    else:
        LOGGER.warn("Nodata value not set, defaulting to -9999.9")
        nodata_value = -9999.9

    #copy dem_uri to a float dataset so we know the type
    pixel_size = raster_utils.get_cell_size_from_uri(dem_uri)
    dem_tmp_fill_uri = raster_utils.temporary_filename()
    raster_utils.vectorize_datasets(
        [dem_uri], lambda x: x, dem_tmp_fill_uri, gdal.GDT_Float32,
        nodata_value, pixel_size, 'intersection',
        vectorize_op=False, datasets_are_pre_aligned=False)

    cdef int n_block_rows = 3
    cdef int n_block_cols = 3

    #center point of global index
    cdef int global_row, global_col #index into the overall raster
    cdef int row_index, col_index #the index of the cache block
    cdef int row_block_offset, col_block_offset #index into the cache block
    cdef int global_block_row, global_block_col #used to walk the global blocks

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #search for flat cells
    #search for flat areas, iterate through the array 3 rows at a time
    cdef c_set[int] flat_set
    cdef c_set[int] flat_set_for_looping
    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    _build_flat_set(dem_tmp_fill_uri, nodata_value, flat_set)

    dem_out_ds = gdal.Open(dem_tmp_fill_uri, gdal.GA_Update)
    dem_out_band = dem_out_ds.GetRasterBand(1)

    cdef int flat_index
    #make a copy of the flat index so we can break it down for iteration but
    #keep the old one for rapid testing of flat cells
    for flat_index in flat_set:
        flat_set_for_looping.insert(flat_set_for_looping.end(), flat_index)

    dem_sink_offset_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_sink_offset_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        fill_value=INF)
    dem_sink_offset_ds = gdal.Open(dem_sink_offset_uri, gdal.GA_Update)
    dem_sink_offset_band = dem_sink_offset_ds.GetRasterBand(1)

    dem_edge_offset_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_edge_offset_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        fill_value=INF)
    dem_edge_offset_ds = gdal.Open(dem_edge_offset_uri, gdal.GA_Update)
    dem_edge_offset_band = dem_edge_offset_ds.GetRasterBand(1)

    cdef queue[int] flat_region_queue

    #no path in the raster will will be greater than this
    cdef int MAX_DISTANCE = n_rows * n_cols

    #these queues will keep track of the indices for traversing the sink and edge cells
    cdef queue[Row_Col_Weight_Tuple] sink_queue
    cdef queue[Row_Col_Weight_Tuple] edge_queue

    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = dem_out_band.GetBlockSize()

    dem_ds = gdal.Open(dem_uri)
    dem_band = dem_ds.GetRasterBand(1)
    block_col_size, block_row_size = dem_band.GetBlockSize()

    cdef numpy.ndarray[numpy.npy_float32, ndim=4] dem_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] dem_sink_offset_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] dem_edge_offset_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_int8, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.int8)

    band_list = [dem_out_band, dem_sink_offset_band, dem_edge_offset_band]
    block_list = [dem_block, dem_sink_offset_block, dem_edge_offset_block]
    update_list = [False, True, True]
    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)
    cdef Row_Col_Weight_Tuple current_cell_tuple

    cdef Row_Col_Weight_Tuple t
    cdef int weight, region_count = 0
    cdef time_t last_time, current_time
    time(&last_time)

    while flat_set_for_looping.size() > 0:
        #This pulls the flat index out for looping
        flat_index = deref(flat_set_for_looping.begin())
        flat_set_for_looping.erase(flat_index)

        global_row = flat_index / n_cols
        global_col = flat_index % n_cols
        block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)

        if dem_block[row_index, col_index, row_block_offset, col_block_offset] == nodata_value:
            continue

        #see if we already processed this cell looking for edges and sinks
        if dem_sink_offset_block[row_index, col_index, row_block_offset, col_block_offset] != INF:
            continue

        #mark the cell as visited
        dem_sink_offset_block[row_index, col_index, row_block_offset, col_block_offset] = MAX_DISTANCE
        cache_dirty[row_index, col_index] = 1 #just changed dem_sink_offset, we're dirty
        flat_region_queue.push(flat_index)
        region_count += 1
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info('working on plateau #%d (reports every 5 seconds) number of flat cells remaining %d' % (region_count, flat_set_for_looping.size()))
            last_time = current_time

        #Visit a flat region and search for sinks and edges
        while flat_region_queue.size() > 0:
            flat_index = flat_region_queue.front()
            flat_set_for_looping.erase(flat_index)
            flat_region_queue.pop()

            global_row = flat_index / n_cols
            global_col = flat_index % n_cols
            block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)

            #test if this point is an edge
            #if it's flat it could be an edge
            if flat_set.find(flat_index) != flat_set.end():
                for neighbor_index in xrange(8):
                    neighbor_row = global_row + row_offsets[neighbor_index]
                    neighbor_col = global_col + col_offsets[neighbor_index]

                    if neighbor_row < 0 or neighbor_row >= n_rows or neighbor_col < 0 or neighbor_col >= n_cols:
                        continue

                    block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)
                    #ignore nodata
                    if dem_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] == nodata_value:
                        continue

                    #if we don't abut a higher pixel then it's an edge
                    if (dem_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] >
                            dem_block[row_index, col_index, row_block_offset, col_block_offset]):

                        t = Row_Col_Weight_Tuple(global_row, global_col, 0)
                        edge_queue.push(t)
                        dem_edge_offset_block[row_index, col_index, row_block_offset, col_block_offset] = 0
                        cache_dirty[row_index, col_index] = 1
                        break
            else:
                #it's been pushed onto the plateau queue, so we know it's in the same
                #region, but it's not flat, so it must be a sink
                t = Row_Col_Weight_Tuple(global_row, global_col, 0)
                sink_queue.push(t)
                dem_sink_offset_block[row_index, col_index, row_block_offset, col_block_offset] = 0
                cache_dirty[row_index, col_index] = 1

            #loop neighbor and test to see if we can extend
            for neighbor_index in xrange(8):
                neighbor_row = global_row + row_offsets[neighbor_index]
                neighbor_col = global_col + col_offsets[neighbor_index]
                if neighbor_row < 0 or neighbor_row >= n_rows or neighbor_col < 0 or neighbor_col >= n_cols:
                    continue
                block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)

                #skip if we're not on the same plateau
                if (dem_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] !=
                    dem_block[row_index, col_index, row_block_offset, col_block_offset]):
                    continue

                #ignore if we've already visited the neighbor
                if dem_sink_offset_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] != INF:
                    continue

                #otherwise extend our search
                flat_region_queue.push(neighbor_row * n_cols + neighbor_col)
                dem_sink_offset_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] = MAX_DISTANCE
                cache_dirty[neighbor_row_index, neighbor_col_index] = 1

        #process sink offsets for region
        while sink_queue.size() > 0:
            current_cell_tuple = sink_queue.front()
            sink_queue.pop()

            global_row = current_cell_tuple.row_index
            global_col = current_cell_tuple.col_index
            weight = current_cell_tuple.weight
            block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)

            for neighbor_index in xrange(8):
                neighbor_row = global_row + row_offsets[neighbor_index]
                neighbor_col = global_col + col_offsets[neighbor_index]

                if neighbor_row < 0 or neighbor_row >= n_rows or neighbor_col < 0 or neighbor_col >= n_cols:
                    continue

                flat_index = neighbor_row * n_cols + neighbor_col
                #If the neighbor is not flat then skip
                if flat_set.find(flat_index) == flat_set.end():
                    continue

                block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)

                #If the neighbor is at a different height, then skip
                if (dem_block[row_index, col_index, row_block_offset, col_block_offset] !=
                    dem_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]):
                    continue

                #if the neighbor's weight is less than the weight we'd project to it
                #no need to update it, we're done w/ that direction
                if (dem_sink_offset_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] <=
                    weight + 1):
                    continue

                #otherwise, project onto the neighbor
                t = Row_Col_Weight_Tuple(neighbor_row, neighbor_col, weight + 1)
                sink_queue.push(t)
                dem_sink_offset_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] = weight + 1
                cache_dirty[neighbor_row_index, neighbor_col_index] = 1

        #process edge offsets for region
        while edge_queue.size() > 0:
            current_cell_tuple = edge_queue.front()
            edge_queue.pop()

            global_row = current_cell_tuple.row_index
            global_col = current_cell_tuple.col_index
            weight = current_cell_tuple.weight
            block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)

            for neighbor_index in xrange(8):
                neighbor_row = global_row + row_offsets[neighbor_index]
                neighbor_col = global_col + col_offsets[neighbor_index]

                if neighbor_row < 0 or neighbor_row >= n_rows or neighbor_col < 0 or neighbor_col >= n_cols:
                    continue
                block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)

                flat_index = neighbor_row * n_cols + neighbor_col
                #If the neighbor is not flat then skip
                if flat_set.find(flat_index) == flat_set.end():
                    continue

                #if the neighbors weight is less than the weight we'll project, skip
                if dem_edge_offset_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] <= weight + 1:
                    continue

                dem_edge_offset_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] = weight + 1
                cache_dirty[neighbor_row_index, neighbor_col_index] = 1
                #otherwise project the current weight to the neighbor
                t = Row_Col_Weight_Tuple(neighbor_row, neighbor_col, weight + 1)
                edge_queue.push(t)

    #Find max distance
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] block
    cdef int max_distance = -1

    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))
    cdef int block_col_width, block_row_width

    for global_block_row in xrange(n_global_block_rows):
        for global_block_col in xrange(n_global_block_cols):

            block_cache.update_cache(
                global_block_row*block_row_size, global_block_col*block_col_size,
                &row_index, &col_index, &row_block_offset, &col_block_offset)

            block_col_width = min((global_block_col+1)*block_col_size, n_cols) - global_block_col*block_col_size
            block_row_width = min((global_block_row+1)*block_row_size, n_rows) - global_block_row*block_row_size
            block = dem_edge_offset_block[row_index, col_index, 0:block_row_width, 0:block_col_width]

            try:
                max_distance = max(
                    max_distance, numpy.max(block[(block!=INF) & (block!=nodata_value)]))
            except ValueError:
                #no non-infinity elements, that's normal
                pass

    #Add the final offsets to the dem array
    def offset_dem(dem_sink_offset_array, dem_edge_offset_array, dem_array):
        #ensure the final division is a 64 float bit calculation
        offset_array = numpy.zeros(dem_sink_offset_array.shape, dtype=numpy.float64)
        offset_array = numpy.where(
            (dem_sink_offset_array != INF) &
            (dem_sink_offset_array != MAX_DISTANCE),
            2.0*dem_sink_offset_array, offset_array)

        offset_array = numpy.where(
            (dem_edge_offset_array != INF) &
            (dem_edge_offset_array != MAX_DISTANCE),
            max_distance+1-dem_edge_offset_array+offset_array, offset_array)
        return dem_array + offset_array / 10000.0

    block_cache.flush_cache()

    dem_out_band = None
    dem_sink_offset_band = None
    dem_edge_offset_band = None

    gdal.Dataset.__swig_destroy__(dem_out_ds)
    gdal.Dataset.__swig_destroy__(dem_sink_offset_ds)
    gdal.Dataset.__swig_destroy__(dem_edge_offset_ds)
    #The float64 on the ouput is important here because we're dividing by small 32 bit floats and we had
    #a bug once where the / 10000.0 constant didn't capture the precision between relatively large offset values of
    #147 and 146.
    raster_utils.vectorize_datasets(
        [dem_sink_offset_uri, dem_edge_offset_uri, dem_tmp_fill_uri], offset_dem, dem_out_uri, gdal.GDT_Float64,
        nodata_value, pixel_size, 'intersection',
        vectorize_op=False)

    for ds_uri in [dem_sink_offset_uri, dem_edge_offset_uri, dem_tmp_fill_uri, ]:
        try:
            os.remove(ds_uri)
        except OSError as e:
            LOGGER.warn("couldn't remove %s because it's still open", ds_uri)
            LOGGER.warn(e)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def flow_direction_inf(dem_uri, flow_direction_uri):
    """Calculates the D-infinity flow algorithm.  The output is a float
        raster whose values range from 0 to 2pi.

        Algorithm from: Tarboton, "A new method for the determination of flow
        directions and upslope areas in grid digital elevation models," Water
        Resources Research, vol. 33, no. 2, pages 309 - 319, February 1997.

        Also resolves flow directions in flat areas of DEM.

        dem_uri (string) - (input) a uri to a single band GDAL Dataset with elevation values
        flow_direction_uri - (input/output) a uri to an existing GDAL dataset with
            of same as dem_uri.  Flow direction will be defined in regions that have
            nodata values in them.  non-nodata values will be ignored.  This is so
            this function can be used as a two pass filter for resolving flow directions
            on a raw dem, then filling plateaus and doing another pass.

       returns nothing"""

    cdef int col_index, row_index, n_cols, n_rows, max_index, facet_index, flat_index
    cdef double e_0, e_1, e_2, s_1, s_2, d_1, d_2, flow_direction, slope, \
        flow_direction_max_slope, slope_max, nodata_flow

    cdef float dem_nodata
    #need this if statement because dem_nodata is statically typed
    if raster_utils.get_nodata_from_uri(dem_uri) != None:
        dem_nodata = raster_utils.get_nodata_from_uri(dem_uri)
    else:
        #we don't have a nodata value, traditional one
        dem_nodata = -9999

    dem_ds = gdal.Open(dem_uri)
    dem_band = dem_ds.GetRasterBand(1)

    #facet elevation and factors for slope and flow_direction calculations
    #from Table 1 in Tarboton 1997.
    #THIS IS IMPORTANT:  The order is row (j), column (i), transposed to GDAL
    #convention.
    cdef int *e_0_offsets = [+0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0]
    cdef int *e_1_offsets = [+0, +1,
                             -1, +0,
                             -1, +0,
                             +0, -1,
                             +0, -1,
                             +1, +0,
                             +1, +0,
                             +0, +1]
    cdef int *e_2_offsets = [-1, +1,
                             -1, +1,
                             -1, -1,
                             -1, -1,
                             +1, -1,
                             +1, -1,
                             +1, +1,
                             +1, +1]
    cdef int *a_c = [0, 1, 1, 2, 2, 3, 3, 4]
    cdef int *a_f = [1, -1, 1, -1, 1, -1, 1, -1]

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]

    n_rows, n_cols = raster_utils.get_row_col_from_uri(dem_uri)
    d_1 = raster_utils.get_cell_size_from_uri(dem_uri)
    d_2 = d_1
    cdef double max_r = numpy.pi / 4.0

    #Create a flow carray and respective dataset
    cdef float flow_nodata = -9999
    raster_utils.new_raster_from_base_uri(
        dem_uri, flow_direction_uri, 'GTiff', flow_nodata,
        gdal.GDT_Float32, fill_value=flow_nodata)

    flow_direction_dataset = gdal.Open(flow_direction_uri, gdal.GA_Update)
    flow_band = flow_direction_dataset.GetRasterBand(1)

    cdef int n_block_rows = 3, n_block_cols = 3 #the number of blocks we'll cache

    #center point of global index
    cdef int block_row_size, block_col_size
    block_col_size, block_row_size = dem_band.GetBlockSize()
    cdef int global_row, global_col, e_0_row, e_0_col, e_1_row, e_1_col, e_2_row, e_2_col #index into the overall raster
    cdef int e_0_row_index, e_0_col_index #the index of the cache block
    cdef int e_0_row_block_offset, e_0_col_block_offset #index into the cache block
    cdef int e_1_row_index, e_1_col_index #the index of the cache block
    cdef int e_1_row_block_offset, e_1_col_block_offset #index into the cache block
    cdef int e_2_row_index, e_2_col_index #the index of the cache block
    cdef int e_2_row_block_offset, e_2_col_block_offset #index into the cache block

    cdef int global_block_row, global_block_col #used to walk the global blocks

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #define all the caches
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] flow_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    #DEM block is a 64 bit float so it can capture the resolution of small DEM offsets
    #from the plateau resolution algorithm.
    cdef numpy.ndarray[numpy.npy_float64, ndim=4] dem_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float64)

    #the BlockCache object needs parallel lists of bands, blocks, and boolean tags to indicate which ones are updated
    band_list = [dem_band, flow_band]
    block_list = [dem_block, flow_block]
    update_list = [False, True]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef int row_offset, col_offset
    cdef int y_offset, local_y_offset
    cdef int max_downhill_facet
    cdef double lowest_dem, dem_value, flow_direction_value

    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))
    cdef time_t last_time, current_time
    cdef float current_flow
    time(&last_time)
    #flow not defined on the edges, so just go 1 row in
    for global_block_row in xrange(n_global_block_rows):
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info("flow_direction_inf %.1f%% complete", (global_row + 1.0) / n_rows * 100)
            last_time = current_time
        for global_block_col in xrange(n_global_block_cols):
            for global_row in xrange(global_block_row*block_row_size, min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(global_block_col*block_col_size, min((global_block_col+1)*block_col_size, n_cols)):
                    #is cache block not loaded?

                    e_0_row = e_0_offsets[0] + global_row
                    e_0_col = e_0_offsets[1] + global_col

                    block_cache.update_cache(e_0_row, e_0_col, &e_0_row_index, &e_0_col_index, &e_0_row_block_offset, &e_0_col_block_offset)

                    e_0 = dem_block[e_0_row_index, e_0_col_index, e_0_row_block_offset, e_0_col_block_offset]
                    #skip if we're on a nodata pixel skip
                    if e_0 == dem_nodata:
                        continue

                    max_downhill_facet = -1
                    lowest_dem = e_0

                    #Calculate the flow flow_direction for each facet
                    slope_max = 0 #use this to keep track of the maximum down-slope
                    flow_direction_max_slope = 0 #flow direction on max downward slope
                    max_index = 0 #index to keep track of max slope facet

                    for facet_index in range(8):
                        #This defines the three points the facet

                        e_1_row = e_1_offsets[facet_index * 2 + 0] + global_row
                        e_1_col = e_1_offsets[facet_index * 2 + 1] + global_col
                        e_2_row = e_2_offsets[facet_index * 2 + 0] + global_row
                        e_2_col = e_2_offsets[facet_index * 2 + 1] + global_col
                        #make sure one of the facets doesn't hang off the edge
                        if (e_1_row < 0 or e_1_row >= n_rows or
                            e_2_row < 0 or e_2_row >= n_rows or
                            e_1_col < 0 or e_1_col >= n_cols or
                            e_2_col < 0 or e_2_col >= n_cols):
                            continue

                        block_cache.update_cache(e_1_row, e_1_col, &e_1_row_index, &e_1_col_index, &e_1_row_block_offset, &e_1_col_block_offset)
                        block_cache.update_cache(e_2_row, e_2_col, &e_2_row_index, &e_2_col_index, &e_2_row_block_offset, &e_2_col_block_offset)

                        e_1 = dem_block[e_1_row_index, e_1_col_index, e_1_row_block_offset, e_1_col_block_offset]
                        e_2 = dem_block[e_2_row_index, e_2_col_index, e_2_row_block_offset, e_2_col_block_offset]

                        if e_1 == dem_nodata and e_2 == dem_nodata:
                            continue

                        #s_1 is slope along straight edge
                        s_1 = (e_0 - e_1) / d_1 #Eqn 1
                        #slope along diagonal edge
                        s_2 = (e_1 - e_2) / d_2 #Eqn 2

                        #can't calculate flow direction if one of the facets is nodata
                        if e_1 == dem_nodata or e_2 == dem_nodata:
                            #calc max slope here
                            if e_1 != dem_nodata:
                                #straight line to next pixel
                                slope = s_1
                            else:
                                #diagonal line to next pixel
                                slope = (e_0 - e_2) / sqrt(d_1 **2 + d_2 ** 2)
                        else:
                            #both facets are defined, this is the core of
                            #d-infinity algorithm
                            flow_direction = atan2(s_2, s_1) #Eqn 3

                            if flow_direction < 0: #Eqn 4
                                #If the flow direction goes off one side, set flow
                                #direction to that side and the slope to the straight line
                                #distance slope
                                flow_direction = 0
                                slope = s_1
                            elif flow_direction > max_r: #Eqn 5
                                #If the flow direciton goes off the diagonal side, figure
                                #out what its value is and
                                flow_direction = max_r
                                slope = (e_0 - e_2) / sqrt(d_1 ** 2 + d_2 ** 2)
                            else:
                                slope = sqrt(s_1 ** 2 + s_2 ** 2) #Eqn 3

                        #update the maxes depending on the results above
                        if slope > slope_max:
                            flow_direction_max_slope = flow_direction
                            slope_max = slope
                            max_index = facet_index

                    #if there's a downward slope, save the flow direction
                    if slope_max > 0:
                        flow_block[e_0_row_index, e_0_col_index, e_0_row_block_offset, e_0_col_block_offset] = (
                            a_f[max_index] * flow_direction_max_slope +
                            a_c[max_index] * 3.14159265 / 2.0)
                        cache_dirty[e_0_row_index, e_0_col_index] = 1

    block_cache.flush_cache()
    flow_band = None
    gdal.Dataset.__swig_destroy__(flow_direction_dataset)
    flow_direction_dataset = None
    raster_utils.calculate_raster_stats_uri(flow_direction_uri)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def find_sinks(dem_uri):
    """Discover and return the sinks in the dem array

        dem_carray - a uri to a gdal dataset

        returns a set of flat integer index indicating the sinks in the region"""

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]

    dem_ds = gdal.Open(dem_uri)
    dem_band = dem_ds.GetRasterBand(1)
    cdef int n_cols = dem_band.XSize
    cdef int n_rows = dem_band.YSize
    cdef double nodata_value = raster_utils.get_nodata_from_uri(dem_uri)

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_array = (
        numpy.zeros((3, n_cols), dtype=numpy.float32))

    cdef int col_index, row_index
    cdef int sink_set_index = 0
    cdef int y_offset, local_y_offset, neighbor_index
    cdef int neighbor_row_index, neighbor_col_index
    cdef int sink_set_size = 10
    cdef numpy.ndarray[numpy.npy_int32, ndim=1] sink_set = (
        numpy.empty((sink_set_size,), dtype=numpy.int32))
    cdef numpy.ndarray[numpy.npy_int32, ndim=1] tmp_sink_set
    for row_index in range(n_rows):
        #the col index will be 0 since we go row by row
        #We load 3 rows at a time
        y_offset = row_index - 1
        local_y_offset = 1
        if y_offset < 0:
            y_offset = 0
            local_y_offset = 0
        if y_offset >= n_rows - 2:
            #could be 0 or 1
            local_y_offset = 2
            y_offset = n_rows - 3

        dem_band.ReadAsArray(
            xoff=0, yoff=y_offset, win_xsize=n_cols,
            win_ysize=3, buf_obj=dem_array)

        for col_index in range(n_cols):
            if dem_array[local_y_offset, col_index] == nodata_value:
                continue
            for neighbor_index in range(8):
                neighbor_row_index = local_y_offset + row_offsets[neighbor_index]
                #greater than 2 because we're reading by rows
                if neighbor_row_index < 0 or neighbor_row_index > 2:
                    continue
                neighbor_col_index = col_index + col_offsets[neighbor_index]
                if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                    continue

                if dem_array[neighbor_row_index, neighbor_col_index] == nodata_value:
                    continue

                if (dem_array[neighbor_row_index, neighbor_col_index] < dem_array[local_y_offset, col_index]):
                    #this cell can drain into another
                    break
            else: #else for the for loop
                #every cell we encountered was nodata or higher than current
                #cell, must be a sink
                if sink_set_index >= sink_set_size:
                    tmp_sink_set = numpy.empty(
                        (sink_set_size * 2,), dtype=numpy.int32)
                    tmp_sink_set[0:sink_set_size] = sink_set
                    sink_set_size *= 2
                    sink_set = tmp_sink_set
                sink_set[sink_set_index] = row_index * n_cols + col_index
                sink_set_index += 1

    tmp_sink_set = numpy.empty((sink_set_index,), dtype=numpy.int32)
    tmp_sink_set[0:sink_set_index] = sink_set[0:sink_set_index]
    return tmp_sink_set


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def distance_to_stream(flow_direction_uri, stream_uri, distance_uri, factor_uri=None):
    """This function calculates the flow downhill distance to the stream layers

        flow_direction_uri - a raster with d-infinity flow directions
        stream_uri - a raster where 1 indicates a stream all other values
            ignored must be same dimensions and projection as
            flow_direction_uri)
        distance_uri - an output raster that will be the same dimensions as
            the input rasters where each pixel is in linear units the drainage
            from that point to a stream.
        factor_uri - a floating point raster that is used to multiply the stepsize by
            for each current pixel

        returns nothing"""

    cdef float distance_nodata = -9999
    raster_utils.new_raster_from_base_uri(
        flow_direction_uri, distance_uri, 'GTiff', distance_nodata,
        gdal.GDT_Float32, fill_value=distance_nodata)

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]

    cdef int n_rows, n_cols
    n_rows, n_cols = raster_utils.get_row_col_from_uri(
        flow_direction_uri)

    cdef stack[int] visit_stack

    stream_ds = gdal.Open(stream_uri)
    stream_band = stream_ds.GetRasterBand(1)
    cdef float cell_size = raster_utils.get_cell_size_from_uri(stream_uri)

    distance_ds = gdal.Open(distance_uri, gdal.GA_Update)
    distance_band = distance_ds.GetRasterBand(1)

    outflow_weights_uri = raster_utils.temporary_filename()
    outflow_direction_uri = raster_utils.temporary_filename()
    calculate_flow_weights(
        flow_direction_uri, outflow_weights_uri, outflow_direction_uri)
    outflow_weights_ds = gdal.Open(outflow_weights_uri)
    outflow_weights_band = outflow_weights_ds.GetRasterBand(1)
    cdef float outflow_nodata = raster_utils.get_nodata_from_uri(
        outflow_weights_uri)
    outflow_direction_ds = gdal.Open(outflow_direction_uri)
    outflow_direction_band = outflow_direction_ds.GetRasterBand(1)

    cdef int outflow_direction_nodata = raster_utils.get_nodata_from_uri(
        outflow_direction_uri)

    #not flat on the edges of the raster, could be a sink
    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = stream_band.GetBlockSize()
    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))

    #the BlockCache object needs parallel lists of bands, blocks, and boolean tags to indicate which ones are updated
    cdef int n_block_rows = 3
    cdef int n_block_cols = 3

    cdef numpy.ndarray[numpy.npy_float32, ndim=4] stream_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_int8, ndim=4] outflow_direction_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int8)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] outflow_weights_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] distance_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)

    band_list = [stream_band, outflow_direction_band, outflow_weights_band, distance_band]
    block_list = [stream_block, outflow_direction_block, outflow_weights_block, distance_block]
    update_list = [False, False, False, True]

    cdef numpy.ndarray[numpy.npy_float32, ndim=4] factor_block
    cdef int factor_exists = factor_uri != None
    if factor_exists:
        factor_block = numpy.zeros(
            (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
        factor_ds = gdal.Open(factor_uri)
        factor_band = factor_ds.GetRasterBand(1)
        band_list.append(factor_band)
        block_list.append(factor_block)
        update_list.append(False)

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    #center point of global index
    cdef int global_row, global_col #index into the overall raster
    cdef int row_index, col_index #the index of the cache block
    cdef int row_block_offset, col_block_offset #index into the cache block
    cdef int global_block_row, global_block_col #used to walk the global blocks

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #build up the stream pixel indexes
    cdef time_t last_time, current_time
    time(&last_time)
    for global_block_row in xrange(n_global_block_rows):
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info("find_sinks %.1f%% complete", (global_block_row + 1.0) / n_global_block_rows * 100)
            last_time = current_time
        for global_block_col in xrange(n_global_block_cols):
            for global_row in xrange(global_block_row*block_row_size, min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(global_block_col*block_col_size, min((global_block_col+1)*block_col_size, n_cols)):
                    block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)

                    if stream_block[row_index, col_index, row_block_offset, col_block_offset] == 1:
                        #it's a stream, remember that
                        visit_stack.push(global_row * n_cols + global_col)

    cdef int flat_index
    cdef int neighbor_outflow_direction, neighbor_index, outflow_direction
    cdef float neighbor_outflow_weight, current_distance, cell_travel_distance
    cdef float outflow_weight, neighbor_distance, step_size
    cdef float factor
    cdef int it_flows_here
    cdef int step_count = 0
    cdef int downstream_index, downstream_uncalculated

    while visit_stack.size() > 0:
        flat_index = visit_stack.top()
        visit_stack.pop()

        global_row = flat_index / n_cols
        global_col = flat_index % n_cols

        step_count += 1
        time(&current_time)
        if current_time - last_time > 5.0:
            last_time = current_time
            LOGGER.info(
                'visit_stack on stream distance size: %d (reports every 5.0 secs)' %
                (visit_stack.size()))


        block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
        current_distance = distance_block[row_index, col_index, row_block_offset, col_block_offset]

        if current_distance != distance_nodata:
            #if cell is already defined, then skip
            continue

        outflow_weight = outflow_weights_block[row_index, col_index, row_block_offset, col_block_offset]
        if stream_block[row_index, col_index, row_block_offset, col_block_offset] == 1 or outflow_weight == outflow_nodata:
            #it's a stream, set distance to zero
            distance_block[row_index, col_index, row_block_offset, col_block_offset] = 0
            cache_dirty[row_index, col_index] = 1
        else:
            #check to see if downstream neighbors are processed
            downstream_uncalculated = False
            for downstream_index in range(2):
                block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
                outflow_weight = outflow_weights_block[row_index, col_index, row_block_offset, col_block_offset]
                outflow_direction = outflow_direction_block[row_index, col_index, row_block_offset, col_block_offset]
                if downstream_index == 1:
                    outflow_weight = 1.0 - outflow_weight
                    outflow_direction = (outflow_direction + 1) % 8

                if outflow_weight > 0.0:
                    neighbor_row = global_row + row_offsets[outflow_direction]
                    neighbor_col = global_col + col_offsets[outflow_direction]
                    if neighbor_row < 0 or neighbor_row >= n_rows or neighbor_col < 0 or neighbor_col >= n_cols:
                        #out of bounds
                        continue

                    block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)
                    neighbor_distance = distance_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]
                    neighbor_outflow_weight = outflow_weights_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]

                    #make sure that downstream neighbor isn't processed and
                    #isn't a nodata pixel for some reason
                    if neighbor_distance == distance_nodata and neighbor_outflow_weight != outflow_nodata:
                        visit_stack.push(neighbor_row * n_cols + neighbor_col)
                        downstream_uncalculated = True

            if downstream_uncalculated:
                #need to process downstream first
                continue

            #calculate current
            block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
            distance_block[row_index, col_index, row_block_offset, col_block_offset] = 0
            cache_dirty[row_index, col_index] = 1
            outflow_weight = outflow_weights_block[row_index, col_index, row_block_offset, col_block_offset]
            outflow_direction = outflow_direction_block[row_index, col_index, row_block_offset, col_block_offset]
            for downstream_index in range(2):

                if downstream_index == 1:
                    outflow_weight = 1.0 - outflow_weight
                    outflow_direction = (outflow_direction + 1) % 8

                if outflow_weight > 0.0:
                    neighbor_row = global_row + row_offsets[outflow_direction]
                    if neighbor_row < 0 or neighbor_row >= n_rows:
                        #out of bounds
                        continue

                    neighbor_col = global_col + col_offsets[outflow_direction]
                    if neighbor_col < 0 or neighbor_col >= n_cols:
                        #out of bounds
                        continue

                    block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)
                    neighbor_distance = distance_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]

                    if outflow_direction % 2 == 1:
                        #increase distance by a square root of 2 for diagonal
                        step_size = cell_size * 1.41421356237
                    else:
                        step_size = cell_size

                    if neighbor_distance != distance_nodata:
                        block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
                        if factor_exists:
                            factor = factor_block[row_index, col_index, row_block_offset, col_block_offset]
                        else:
                            factor = 1.0
                        distance_block[row_index, col_index, row_block_offset, col_block_offset] += (
                            neighbor_distance + step_size * factor) * outflow_weight
                        cache_dirty[row_index, col_index] = 1

        #push any upstream neighbors that inflow onto the stack
        for neighbor_index in range(8):
            neighbor_row = global_row + row_offsets[neighbor_index]
            if neighbor_row < 0 or neighbor_row >= n_rows:
                #out of bounds
                continue
            neighbor_col = global_col + col_offsets[neighbor_index]
            if neighbor_col < 0 or neighbor_col >= n_cols:
                #out of bounds
                continue

            block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)
            neighbor_outflow_direction = outflow_direction_block[
                neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]
            #if the neighbor is no data, don't try to set that
            if neighbor_outflow_direction == outflow_direction_nodata:
                continue

            neighbor_outflow_weight = outflow_weights_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]

            it_flows_here = False
            if neighbor_outflow_direction == inflow_offsets[neighbor_index]:
                #the neighbor flows into this cell
                it_flows_here = True

            if (neighbor_outflow_direction + 1) % 8 == inflow_offsets[neighbor_index]:
                #the offset neighbor flows into this cell
                it_flows_here = True
                neighbor_outflow_weight = 1.0 - neighbor_outflow_weight

            if (it_flows_here and neighbor_outflow_weight > 0.0 and
                distance_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] ==
                distance_nodata):
                #not touched yet, set distance push on the visit stack
                visit_stack.push(neighbor_row * n_cols + neighbor_col)

    block_cache.flush_cache()

    for dataset in [outflow_weights_ds, outflow_direction_ds]:
        gdal.Dataset.__swig_destroy__(dataset)
    for dataset_uri in [outflow_weights_uri, outflow_direction_uri]:
        os.remove(dataset_uri)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def cache_block_experiment(ds_uri, out_uri):
    LOGGER.info('starting cache_block_experiment')
    cdef int neighbor_index #a number between 0 and 7 indicating neighbor in the following configuration
    # 321
    # 4x0
    # 567
    cdef int *neighbor_row_offset = [0, -1, -1, -1, 0, 1, 1, 1]
    cdef int *neighbor_col_offset = [1, 1, 0, -1, -1, -1, 0, 1]

    ds = gdal.Open(ds_uri)
    ds_band = ds.GetRasterBand(1)
    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = ds_band.GetBlockSize()
    cdef int n_rows = ds.RasterYSize
    cdef int n_cols = ds.RasterXSize

    cdef float out_nodata = -1.0
    raster_utils.new_raster_from_base_uri(
        ds_uri, out_uri, 'GTiff', out_nodata, gdal.GDT_Float32)
    out_ds = gdal.Open(out_uri, gdal.GA_Update)
    out_band = out_ds.GetRasterBand(1)

    cdef int n_block_rows = 3, n_block_cols = 3 #the number of blocks we'll cache

    #center point of global index
    cdef int global_row, global_col #index into the overall raster
    cdef int row_index, col_index #the index of the cache block
    cdef int row_block_offset, col_block_offset #index into the cache block
    cdef int global_block_row, global_block_col #used to walk the global blocks

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #define all the caches
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] ds_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] out_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)

    #the BlockCache object needs parallel lists of bands, blocks, and boolean tags to indicate which ones are updated
    band_list = [ds_band, out_band]
    block_list = [ds_block, out_block]
    update_list = [False, True]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef float current_value
    LOGGER.info('starting iteration through blocks')

    cdef time_t last_time, current_time
    time(&last_time)
    for global_block_row in xrange(int(numpy.ceil(float(n_rows) / block_row_size))):
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info("cache_block_experiment %.1f%% complete", (global_row + 1.0) / n_rows * 100)
            last_time = current_time
        for global_block_col in xrange(int(numpy.ceil(float(n_cols) / block_col_size))):
            LOGGER.info('global_block_row global_block_col %d %d', global_block_row, global_block_col)
            for global_row in xrange(global_block_row*block_row_size, min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(global_block_col*block_col_size, min((global_block_col+1)*block_col_size, n_cols)):
                    #is cache block not loaded?
                    block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
                    current_value = ds_block[row_index, col_index, row_block_offset, col_block_offset]
                    for neighbor_index in xrange(8):
                        neighbor_row = neighbor_row_offset[neighbor_index] + global_row
                        neighbor_col = neighbor_col_offset[neighbor_index] + global_col

                        #make sure we're in bounds
                        if (neighbor_row >= n_rows or neighbor_row < 0 or neighbor_col >= n_cols or neighbor_col < 0):
                            continue
                        block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)

                        current_value += ds_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]
                        cache_dirty[neighbor_row_index, neighbor_col_index] = 1
                    out_block[row_index, col_index, row_block_offset, col_block_offset] = current_value
                    cache_dirty[row_index, col_index] = 1

    #save off the dirty cache
    block_cache.flush_cache()


@cython.boundscheck(False)
@cython.wraparound(False)
def percent_to_sink(
    sink_pixels_uri, export_rate_uri, outflow_direction_uri,
    outflow_weights_uri, effect_uri):
    """This function calculates the amount of load from a single pixel
        to the source pixels given the percent export rate per pixel.

        sink_pixels_uri - the pixels of interest that will receive flux.
            This may be a set of stream pixels, or a single pixel at a
            watershed outlet.

        export_rate_uri - a GDAL floating point dataset that has a percent
            of flux exported per pixel

        outflow_direction_uri - a uri to a byte dataset that indicates the
            first counter clockwise outflow neighbor as an index from the
            following diagram

            3 2 1
            4 x 0
            5 6 7

        outflow_weights_uri - a uri to a float32 dataset whose elements
            correspond to the percent outflow from the current cell to its
            first counter-clockwise neighbor

        effect_uri - the output GDAL dataset that shows the percent of flux
            emanating per pixel that will reach any sink pixel

        returns nothing"""

    LOGGER.info("calculating percent to sink")
    cdef time_t start_time
    time(&start_time)

    sink_pixels_dataset = gdal.Open(sink_pixels_uri)
    sink_pixels_band = sink_pixels_dataset.GetRasterBand(1)
    cdef int sink_pixels_nodata = raster_utils.get_nodata_from_uri(
        sink_pixels_uri)
    export_rate_dataset = gdal.Open(export_rate_uri)
    export_rate_band = export_rate_dataset.GetRasterBand(1)
    cdef double export_rate_nodata = raster_utils.get_nodata_from_uri(
        export_rate_uri)
    outflow_direction_dataset = gdal.Open(outflow_direction_uri)
    outflow_direction_band = outflow_direction_dataset.GetRasterBand(1)
    cdef int outflow_direction_nodata = raster_utils.get_nodata_from_uri(
        outflow_direction_uri)
    outflow_weights_dataset = gdal.Open(outflow_weights_uri)
    outflow_weights_band = outflow_weights_dataset.GetRasterBand(1)
    cdef float outflow_weights_nodata = raster_utils.get_nodata_from_uri(
        outflow_weights_uri)

    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = sink_pixels_band.GetBlockSize()
    cdef int n_rows = sink_pixels_dataset.RasterYSize
    cdef int n_cols = sink_pixels_dataset.RasterXSize

    cdef double effect_nodata = -1.0
    raster_utils.new_raster_from_base_uri(
        sink_pixels_uri, effect_uri, 'GTiff', effect_nodata,
        gdal.GDT_Float32, fill_value=effect_nodata)
    effect_dataset = gdal.Open(effect_uri, gdal.GA_Update)
    effect_band = effect_dataset.GetRasterBand(1)

    cdef int n_block_rows = 3, n_block_cols = 3 #the number of blocks we'll cache

    #center point of global index
    cdef int global_row, global_col #index into the overall raster
    cdef int row_index, col_index #the index of the cache block
    cdef int row_block_offset, col_block_offset #index into the cache block
    cdef int global_block_row, global_block_col #used to walk the global blocks

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #define all the caches

    cdef numpy.ndarray[numpy.npy_int32, ndim=4] sink_pixels_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] export_rate_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_int8, ndim=4] outflow_direction_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int8)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] outflow_weights_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] out_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] effect_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)

    #the BlockCache object needs parallel lists of bands, blocks, and boolean tags to indicate which ones are updated
    block_list = [sink_pixels_block, export_rate_block, outflow_direction_block, outflow_weights_block, effect_block]
    band_list = [sink_pixels_band, export_rate_band, outflow_direction_band, outflow_weights_band, effect_band]
    update_list = [False, False, False, False, True]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef float outflow_weight, neighbor_outflow_weight
    cdef int neighbor_outflow_direction

    #Diagonal offsets are based off the following index notation for neighbors
    #    3 2 1
    #    4 p 0
    #    5 6 7

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]
    cdef int flat_index
    cdef queue[int] process_queue
    #Queue the sinks
    for global_block_row in xrange(int(numpy.ceil(float(n_rows) / block_row_size))):
        for global_block_col in xrange(int(numpy.ceil(float(n_cols) / block_col_size))):
            for global_row in xrange(global_block_row*block_row_size, min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(global_block_col*block_col_size, min((global_block_col+1)*block_col_size, n_cols)):
                    block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
                    if sink_pixels_block[row_index, col_index, row_block_offset, col_block_offset] == 1:
                        effect_block[row_index, col_index, row_block_offset, col_block_offset] = 1.0
                        cache_dirty[row_index, col_index] = 1
                        process_queue.push(global_row * n_cols + global_col)

    while process_queue.size() > 0:
        flat_index = process_queue.front()
        process_queue.pop()
        with cython.cdivision(True):
            global_row = flat_index / n_cols
            global_col = flat_index % n_cols

        block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
        if export_rate_block[row_index, col_index, row_block_offset, col_block_offset] == export_rate_nodata:
            continue

        #if the outflow weight is nodata, then not a valid pixel
        outflow_weight = outflow_weights_block[row_index, col_index, row_block_offset, col_block_offset]
        if outflow_weight == outflow_weights_nodata:
            continue

        for neighbor_index in range(8):
            neighbor_row = global_row + row_offsets[neighbor_index]
            neighbor_col = global_col + col_offsets[neighbor_index]
            if neighbor_row < 0 or neighbor_row >= n_rows or neighbor_col < 0 or neighbor_col >= n_cols:
                #out of bounds
                continue

            block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)

            if sink_pixels_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] == 1:
                #it's already a sink
                continue

            neighbor_outflow_direction = (
                outflow_direction_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset])
            #if the neighbor is no data, don't try to set that
            if neighbor_outflow_direction == outflow_direction_nodata:
                continue

            neighbor_outflow_weight = (
                outflow_weights_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset])
            #if the neighbor is no data, don't try to set that
            if neighbor_outflow_weight == outflow_direction_nodata:
                continue

            it_flows_here = False
            if neighbor_outflow_direction == inflow_offsets[neighbor_index]:
                #the neighbor flows into this cell
                it_flows_here = True

            if (neighbor_outflow_direction - 1) % 8 == inflow_offsets[neighbor_index]:
                #the offset neighbor flows into this cell
                it_flows_here = True
                neighbor_outflow_weight = 1.0 - neighbor_outflow_weight

            if it_flows_here:
                #If we haven't processed that effect yet, set it to 0 and append to the queue
                if effect_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] == effect_nodata:
                    process_queue.push(neighbor_row * n_cols + neighbor_col)
                    effect_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] = 0.0
                    cache_dirty[neighbor_row_index, neighbor_col_index] = 1

                #the percent of the pixel upstream equals the current percent
                #times the percent flow to that pixels times the
                effect_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] += (
                    effect_block[row_index, col_index, row_block_offset, col_block_offset] *
                    neighbor_outflow_weight *
                    export_rate_block[row_index, col_index, row_block_offset, col_block_offset])
                cache_dirty[neighbor_row_index, neighbor_col_index] = 1

    block_cache.flush_cache()
    cdef time_t end_time
    time(&end_time)
    LOGGER.info('Done calculating percent to sink elapsed time %ss' % \
                    (end_time - start_time))


cdef class BlockCache:
    cdef numpy.int32_t[:,:] row_tag_cache
    cdef numpy.int32_t[:,:] col_tag_cache
    cdef numpy.int8_t[:,:] cache_dirty
    cdef int n_block_rows
    cdef int n_block_cols
    cdef int block_col_size
    cdef int block_row_size
    cdef int n_rows
    cdef int n_cols
    band_list = []
    block_list = []
    update_list = []

    def __cinit__(
        self, int n_block_rows, int n_block_cols, int n_rows, int n_cols, int block_row_size, int block_col_size, band_list, block_list, update_list, numpy.int8_t[:,:] cache_dirty):
        self.n_block_rows = n_block_rows
        self.n_block_cols = n_block_cols
        self.block_col_size = block_col_size
        self.block_row_size = block_row_size
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.row_tag_cache = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.int32)
        self.col_tag_cache = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.int32)
        self.cache_dirty = cache_dirty
        self.row_tag_cache[:] = -1
        self.col_tag_cache[:] = -1
        self.band_list[:] = band_list
        self.block_list[:] = block_list
        self.update_list[:] = update_list

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    cdef void update_cache(self, int global_row, int global_col, int *row_index, int *col_index, int *row_block_offset, int *col_block_offset):
        cdef int cache_row_size, cache_col_size
        cdef int global_row_offset, global_col_offset
        cdef int row_tag, col_tag

        row_block_offset[0] = global_row % self.block_row_size
        row_index[0] = (global_row // self.block_row_size) % self.n_block_rows
        row_tag = (global_row // self.block_row_size) // self.n_block_rows

        col_block_offset[0] = global_col % self.block_col_size
        col_index[0] = (global_col // self.block_col_size) % self.n_block_cols
        col_tag = (global_col // self.block_col_size) // self.n_block_cols

        cdef int current_row_tag = self.row_tag_cache[row_index[0], col_index[0]]
        cdef int current_col_tag = self.col_tag_cache[row_index[0], col_index[0]]

        if current_row_tag != row_tag or current_col_tag != col_tag:
            if self.cache_dirty[row_index[0], col_index[0]]:
                global_col_offset = (current_col_tag * self.n_block_cols + col_index[0]) * self.block_col_size
                cache_col_size = self.n_cols - global_col_offset
                if cache_col_size > self.block_col_size:
                    cache_col_size = self.block_col_size

                global_row_offset = (current_row_tag * self.n_block_rows + row_index[0]) * self.block_row_size
                cache_row_size = self.n_rows - global_row_offset
                if cache_row_size > self.block_row_size:
                    cache_row_size = self.block_row_size

                for band, block, update in zip(self.band_list, self.block_list, self.update_list):
                    if update:
                        band.WriteArray(block[row_index[0], col_index[0], 0:cache_row_size, 0:cache_col_size],
                            yoff=global_row_offset, xoff=global_col_offset)
                self.cache_dirty[row_index[0], col_index[0]] = 0
            self.row_tag_cache[row_index[0], col_index[0]] = row_tag
            self.col_tag_cache[row_index[0], col_index[0]] = col_tag

            global_col_offset = (col_tag * self.n_block_cols + col_index[0]) * self.block_col_size
            global_row_offset = (row_tag * self.n_block_rows + row_index[0]) * self.block_row_size

            cache_col_size = self.n_cols - global_col_offset
            if cache_col_size > self.block_col_size:
                cache_col_size = self.block_col_size
            cache_row_size = self.n_rows - global_row_offset
            if cache_row_size > self.block_row_size:
                cache_row_size = self.block_row_size

            for band, block in zip(self.band_list, self.block_list):
                band.ReadAsArray(
                    xoff=global_col_offset, yoff=global_row_offset,
                    win_xsize=cache_col_size, win_ysize=cache_row_size,
                    buf_obj=block[row_index[0], col_index[0], 0:cache_row_size, 0:cache_col_size])

    cdef void flush_cache(self):
        cdef int global_row_offset, global_col_offset
        cdef int cache_row_size, cache_col_size
        cdef int row_index, col_index
        for row_index in xrange(self.n_block_rows):
            for col_index in xrange(self.n_block_cols):
                row_tag = self.row_tag_cache[row_index, col_index]
                col_tag = self.col_tag_cache[row_index, col_index]

                if self.cache_dirty[row_index, col_index]:
                    global_col_offset = (col_tag * self.n_block_cols + col_index) * self.block_col_size
                    cache_col_size = self.n_cols - global_col_offset
                    if cache_col_size > self.block_col_size:
                        cache_col_size = self.block_col_size

                    global_row_offset = (row_tag * self.n_block_rows + row_index) * self.block_row_size
                    cache_row_size = self.n_rows - global_row_offset
                    if cache_row_size > self.block_row_size:
                        cache_row_size = self.block_row_size

                    for band, block, update in zip(self.band_list, self.block_list, self.update_list):
                        if update:
                            band.WriteArray(block[row_index, col_index, 0:cache_row_size, 0:cache_col_size],
                                yoff=global_row_offset, xoff=global_col_offset)
        for band in self.band_list:
            band.FlushCache()


def flat_edges(dem_uri, flow_direction_uri, high_edges, low_edges):
    """This function locates flat cells that border on higher and lower terrain
        and places them into sets for further processing.

        Args:

            dem_uri (string) - (input) a uri to a single band GDAL Dataset with
                elevation values
            flow_direction_uri (string) - (input/output) a uri to a single band
                GDAL Dataset with partially defined d_infinity flow directions
            high_edges (set) - (output) will contain all the high edge cells
            low_eges (set) - (output) will contain all the low edge cells

        Returns:
            nothing"""

    cdef int *neighbor_row_offset = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *neighbor_col_offset = [1,  1,  0, -1, -1, -1, 0, 1]

    dem_ds = gdal.Open(dem_uri)
    dem_band = dem_ds.GetRasterBand(1)
    flow_ds = gdal.Open(flow_direction_uri, gdal.GA_Update)
    flow_band = flow_ds.GetRasterBand(1)

    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = dem_band.GetBlockSize()
    cdef int n_rows = dem_ds.RasterYSize
    cdef int n_cols = dem_ds.RasterXSize

    cdef int n_block_rows = 3, n_block_cols = 3

    cdef numpy.ndarray[numpy.npy_float32, ndim=4] flow_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] dem_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.float32)

    band_list = [dem_band, flow_band]
    block_list = [dem_block, flow_block]
    update_list = [False, False]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.byte)

    block_col_size, block_row_size = dem_band.GetBlockSize()

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size,
        block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))

    cdef int global_row, global_col

    cdef int cell_row_index, cell_col_index
    cdef int cell_row_block_index, cell_col_block_index
    cdef int cell_row_block_offset, cell_col_block_offset

    cdef int neighbor_index
    cdef int neighbor_row, neighbor_col
    cdef int neighbor_row_index, neighbor_col_index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset

    cdef float cell_dem, cell_flow, neighbor_dem, neighbor_flow

    cdef float dem_nodata = raster_utils.get_nodata_from_uri(
        dem_uri)
    cdef float flow_nodata = raster_utils.get_nodata_from_uri(
        flow_direction_uri)

    cdef time_t last_time, current_time
    time(&last_time)

    for global_block_row in xrange(n_global_block_rows):
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info(
                "flat_edges %.1f%% complete", (global_row + 1.0) / n_rows * 100)
            last_time = current_time
        for global_block_col in xrange(n_global_block_cols):
            for global_row in xrange(
                    global_block_row*block_row_size,
                    min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(
                        global_block_col*block_col_size,
                        min((global_block_col+1)*block_col_size, n_cols)):

                    block_cache.update_cache(
                        global_row, global_col,
                        &cell_row_index, &cell_col_index,
                        &cell_row_block_offset, &cell_col_block_offset)

                    cell_dem = dem_block[cell_row_index, cell_col_index,
                        cell_row_block_offset, cell_col_block_offset]

                    if cell_dem == dem_nodata:
                        continue

                    cell_flow = flow_block[cell_row_index, cell_col_index,
                        cell_row_block_offset, cell_col_block_offset]

                    for neighbor_index in xrange(8):
                        neighbor_row = (
                            neighbor_row_offset[neighbor_index] + global_row)
                        neighbor_col = (
                            neighbor_col_offset[neighbor_index] + global_col)

                        if (neighbor_row >= n_rows or neighbor_row < 0 or
                                neighbor_col >= n_cols or neighbor_col < 0):
                            continue

                        block_cache.update_cache(
                            neighbor_row, neighbor_col,
                            &neighbor_row_index, &neighbor_col_index,
                            &neighbor_row_block_offset,
                            &neighbor_col_block_offset)
                        neighbor_dem = dem_block[
                            neighbor_row_index, neighbor_col_index,
                            neighbor_row_block_offset,
                            neighbor_col_block_offset]

                        if neighbor_dem == dem_nodata:
                            continue

                        neighbor_flow = flow_block[
                            neighbor_row_index, neighbor_col_index,
                            neighbor_row_block_offset,
                            neighbor_col_block_offset]

                        if (cell_flow != flow_nodata and
                                neighbor_flow == flow_nodata and
                                cell_dem == neighbor_dem):
                            low_edges.add(global_row * n_cols + global_col)
                            break
                        elif (cell_flow == flow_nodata and
                                cell_dem < neighbor_dem):
                            high_edges.add(global_row * n_cols + global_col)
                            break


def label_flats(dem_uri, low_edges, labels_uri):
    """A flood fill function to give all the cells of each flat a unique
        label

        Args:
            dem_uri (string) - (input) a uri to a single band GDAL Dataset with
                elevation values
            low_edges (Set) - (input) Contains all the low edge cells of the dem
                written as flat indexes in row major order
            labels_uri (string) - (output) a uri to a single band integer gdal
                dataset that will be created that will contain labels for the
                flat regions of the DEM.
            """

    cdef int *neighbor_row_offset = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *neighbor_col_offset = [1,  1,  0, -1, -1, -1, 0, 1]

    dem_ds = gdal.Open(dem_uri)
    dem_band = dem_ds.GetRasterBand(1)

    cdef int labels_nodata = -1
    labels_ds = raster_utils.new_raster_from_base(
        dem_ds, labels_uri, 'GTiff', labels_nodata,
        gdal.GDT_Int32)
    labels_band = labels_ds.GetRasterBand(1)

    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = dem_band.GetBlockSize()
    cdef int n_rows = dem_ds.RasterYSize
    cdef int n_cols = dem_ds.RasterXSize

    cdef int n_block_rows = 3, n_block_cols = 3

    cdef numpy.ndarray[numpy.npy_float32, ndim=4] labels_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] dem_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.float32)

    band_list = [dem_band, labels_band]
    block_list = [dem_block, labels_block]
    update_list = [False, True]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.byte)

    block_col_size, block_row_size = dem_band.GetBlockSize()

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size,
        block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))

    cdef int global_row, global_col

    cdef int cell_row_index, cell_col_index
    cdef int cell_row_block_index, cell_col_block_index
    cdef int cell_row_block_offset, cell_col_block_offset

    cdef int neighbor_index
    cdef int neighbor_row, neighbor_col
    cdef int neighbor_row_index, neighbor_col_index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset

    cdef float cell_dem, neighbor_dem, neighbor_label
    cdef float cell_label, flat_cell_label

    cdef float dem_nodata = raster_utils.get_nodata_from_uri(
        dem_uri)

    cdef time_t last_time, current_time
    time(&last_time)

    cdef int flat_cell_index
    cdef int flat_fill_cell_index
    cdef int label = 1
    cdef int fill_cell_row, fill_cell_col
    cdef queue[int] to_fill
    cdef float flat_height, current_flat_height
    cdef int visit_number = 0
    for flat_cell_index in low_edges:
        visit_number += 1
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info(
                "label_flats %.1f%% complete",
                float(visit_number) / len(low_edges) * 100)
            last_time = current_time
        global_row = flat_cell_index / n_cols
        global_col = flat_cell_index % n_cols

        block_cache.update_cache(
            global_row, global_col,
            &cell_row_index, &cell_col_index,
            &cell_row_block_offset, &cell_col_block_offset)

        cell_label = labels_block[cell_row_index, cell_col_index,
            cell_row_block_offset, cell_col_block_offset]

        flat_height = dem_block[cell_row_index, cell_col_index,
            cell_row_block_offset, cell_col_block_offset]

        if cell_label == labels_nodata:
            #label flats
            to_fill.push(flat_cell_index)
            while not to_fill.empty():
                flat_fill_cell_index = to_fill.front()
                to_fill.pop()
                fill_cell_row = flat_fill_cell_index / n_cols
                fill_cell_col = flat_fill_cell_index % n_cols
                if (fill_cell_row < 0 or fill_cell_row >= n_rows or
                        fill_cell_col < 0 or fill_cell_col >= n_cols):
                    continue

                block_cache.update_cache(
                    fill_cell_row, fill_cell_col,
                    &cell_row_index, &cell_col_index,
                    &cell_row_block_offset, &cell_col_block_offset)

                current_flat_height = dem_block[cell_row_index, cell_col_index,
                    cell_row_block_offset, cell_col_block_offset]

                if current_flat_height != flat_height:
                    continue

                flat_cell_label = labels_block[
                    cell_row_index, cell_col_index,
                    cell_row_block_offset, cell_col_block_offset]

                if flat_cell_label != labels_nodata:
                    continue

                #set the label
                labels_block[
                    cell_row_index, cell_col_index,
                    cell_row_block_offset, cell_col_block_offset] = label
                cache_dirty[cell_row_index, cell_col_index] = 1

                #visit the neighbors
                for neighbor_index in xrange(8):
                    neighbor_row = (
                        fill_cell_row + neighbor_row_offset[neighbor_index])
                    neighbor_col = (
                        fill_cell_col + neighbor_col_offset[neighbor_index])
                    to_fill.push(neighbor_row * n_cols + neighbor_col)

            label += 1
    block_cache.flush_cache()


def clean_high_edges(labels_uri, high_edges):
    """Removes any high edges that do not have labels and reports them if so.

        Args:
            labels_uri (string) - (input) a uri to a single band integer gdal
                dataset that contain labels for the cells that lie in
                flat regions of the DEM.
            high_edges (set) - (input/output) a set containing row major order
                flat indexes


        Returns:
            nothing"""

    labels_ds = gdal.Open(labels_uri)
    labels_band = labels_ds.GetRasterBand(1)

    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = labels_band.GetBlockSize()
    cdef int n_rows = labels_ds.RasterYSize
    cdef int n_cols = labels_ds.RasterXSize

    cdef int n_block_rows = 3, n_block_cols = 3

    cdef numpy.ndarray[numpy.npy_int32, ndim=4] labels_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.int32)

    band_list = [labels_band]
    block_list = [labels_block]
    update_list = [False]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size,
        block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef int labels_nodata = raster_utils.get_nodata_from_uri(
        labels_uri)
    cdef int flat_cell_label

    cdef int cell_row_index, cell_col_index
    cdef int cell_row_block_index, cell_col_block_index
    cdef int cell_row_block_offset, cell_col_block_offset

    cdef int flat_index
    cdef int flat_row, flat_col
    unlabled_set = set()
    for flat_index in high_edges:
        flat_row = flat_index / n_cols
        flat_col = flat_index % n_cols

        block_cache.update_cache(
            flat_row, flat_col,
            &cell_row_index, &cell_col_index,
            &cell_row_block_offset, &cell_col_block_offset)

        flat_cell_label = labels_block[
            cell_row_index, cell_col_index,
            cell_row_block_offset, cell_col_block_offset]

        #this is a flat that does not have an outlet
        if flat_cell_label == labels_nodata:
            unlabled_set.add(flat_index)

    if len(unlabled_set) > 0:
        high_edges.difference_update(unlabled_set)
        LOGGER.warn("Not all flats have outlets")
    block_cache.flush_cache()


def away_from_higher(
            high_edges, labels_uri, flow_direction_uri, flat_mask_uri,
            flat_height):
    """Builds a gradient away from higher terrain.

        Take Care, Take Care, Take Care
        The Earth Is Not a Cold Dead Place
        Those Who Tell The Truth Shall Die,
            Those Who Tell The Truth Shall Live Forever
        All Of A Sudden I Miss Everyone

        The Birth And Death Of The Day
        What Do You Go Home To?
        Catastrophe, And The Cure.
        Have you passed through this night?
        With Tired Eyes, Tired Minds, Tired Souls, We Slept


        Args:
            high_edges (set) - (input) all the high edge cells of the DEM which
                are part of drainable flats.
            labels_uri (string) - (input) a uri to a single band integer gdal
                dataset that contain labels for the cells that lie in
                flat regions of the DEM.
            flow_direction_uri (string) - (input) a uri to a single band
                GDAL Dataset with partially defined d_infinity flow directions
            flat_mask_uri (string) - (output) gdal dataset that contains the
                number of increments to be applied to each cell to form a
                gradient away from higher terrain.  cells not in a flat have a
                value of 0
            flat_height (collections.defaultdict) - (input/output) Has an entry
                for each label value of of labels_uri indicating the maximal
                number of increments to be applied to the flat idientifed by
                that label.

        Returns:
            nothing"""

    cdef int *neighbor_row_offset = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *neighbor_col_offset = [1,  1,  0, -1, -1, -1, 0, 1]

    cdef int flat_mask_nodata = -9999
    #fill up the flat mask with 0s so it can be used to route a dem later
    raster_utils.new_raster_from_base_uri(
        labels_uri, flat_mask_uri, 'GTiff', flat_mask_nodata,
        gdal.GDT_Int32, fill_value=0)
    flat_height.clear()

    labels_ds = gdal.Open(labels_uri)
    labels_band = labels_ds.GetRasterBand(1)
    flat_mask_ds = gdal.Open(flat_mask_uri, gdal.GA_Update)
    flat_mask_band = flat_mask_ds.GetRasterBand(1)
    flow_direction_ds = gdal.Open(flow_direction_uri)
    flow_direction_band = flow_direction_ds.GetRasterBand(1)

    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = labels_band.GetBlockSize()
    cdef int n_rows = labels_ds.RasterYSize
    cdef int n_cols = labels_ds.RasterXSize

    cdef int n_block_rows = 3, n_block_cols = 3

    cdef numpy.ndarray[numpy.npy_int32, ndim=4] labels_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.int32)
    cdef numpy.ndarray[numpy.npy_int32, ndim=4] flat_mask_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.int32)
    cdef numpy.ndarray[numpy.npy_int32, ndim=4] flow_direction_block = (
        numpy.zeros(
            (n_block_rows, n_block_cols, block_row_size, block_col_size),
            dtype=numpy.int32))

    band_list = [labels_band, flat_mask_band, flow_direction_band]
    block_list = [labels_block, flat_mask_block, flow_direction_block]
    update_list = [False, True, False]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size,
        block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef int cell_row_index, cell_col_index
    cdef int cell_row_block_index, cell_col_block_index
    cdef int cell_row_block_offset, cell_col_block_offset

    cdef int loops = 1

    high_edges_queue = collections.deque()
    cdef int neighbor_row, neighbor_col
    cdef int flat_index
    cdef int flat_row, flat_col
    cdef int flat_mask
    cdef int labels_nodata = raster_utils.get_nodata_from_uri(labels_uri)
    cdef int cell_label, neighbor_label
    cdef float neighbor_flow
    cdef float flow_nodata = raster_utils.get_nodata_from_uri(
        flow_direction_uri)

    for flat_index in high_edges:
        high_edges_queue.append(flat_index)

    marker = -1
    high_edges_queue.append(marker)
    while len(high_edges_queue) > 1:
        flat_index = high_edges_queue.popleft()
        if flat_index == marker:
            loops += 1
            high_edges_queue.append(marker)
            continue

        flat_row = flat_index / n_cols
        flat_col = flat_index % n_cols

        block_cache.update_cache(
            flat_row, flat_col,
            &cell_row_index, &cell_col_index,
            &cell_row_block_offset, &cell_col_block_offset)

        flat_mask = flat_mask_block[
            cell_row_index, cell_col_index,
            cell_row_block_offset, cell_col_block_offset]

        cell_label = labels_block[
            cell_row_index, cell_col_index,
            cell_row_block_offset, cell_col_block_offset]

        if flat_mask != 0:
            continue

        #update the cell mask and the max height of the flat
        #making it negative because it's easier to do here than in towards lower
        flat_mask_block[
            cell_row_index, cell_col_index,
            cell_row_block_offset, cell_col_block_offset] = -loops
        cache_dirty[cell_row_index, cell_col_index] = 1
        flat_height[cell_label] = loops

        #visit the neighbors
        for neighbor_index in xrange(8):
            neighbor_row = (
                flat_row + neighbor_row_offset[neighbor_index])
            neighbor_col = (
                flat_col + neighbor_col_offset[neighbor_index])

            if (neighbor_row < 0 or neighbor_row >= n_rows or
                    neighbor_col < 0 or neighbor_col >= n_cols):
                continue

            block_cache.update_cache(
                neighbor_row, neighbor_col,
                &cell_row_index, &cell_col_index,
                &cell_row_block_offset, &cell_col_block_offset)

            neighbor_label = labels_block[
                cell_row_index, cell_col_index,
                cell_row_block_offset, cell_col_block_offset]

            neighbor_flow = flow_direction_block[
                cell_row_index, cell_col_index,
                cell_row_block_offset, cell_col_block_offset]

            if (neighbor_label != labels_nodata and
                    neighbor_label == cell_label and
                    neighbor_flow == flow_nodata):
                high_edges_queue.append(neighbor_row * n_cols + neighbor_col)

    block_cache.flush_cache()


def towards_lower(
            low_edges, labels_uri, flow_direction_uri, flat_mask_uri,
            flat_height):
    """Builds a gradient towards lower terrain.

        Args:
            low_edges (set) - (input) all the low edge cells of the DEM which
                are part of drainable flats.
            labels_uri (string) - (input) a uri to a single band integer gdal
                dataset that contain labels for the cells that lie in
                flat regions of the DEM.
            flow_direction_uri (string) - (input) a uri to a single band
                GDAL Dataset with partially defined d_infinity flow directions
            flat_mask_uri (string) - (input/output) gdal dataset that contains
                the negative step increments from toward_higher and will contain
                the number of steps to be applied to each cell to form a
                gradient away from higher terrain.  cells not in a flat have a
                value of 0
            flat_height (collections.defaultdict) - (input/output) Has an entry
                for each label value of of labels_uri indicating the maximal
                number of increments to be applied to the flat idientifed by
                that label.

        Returns:
            nothing"""

    cdef int *neighbor_row_offset = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *neighbor_col_offset = [1,  1,  0, -1, -1, -1, 0, 1]

    flat_mask_nodata = raster_utils.get_nodata_from_uri(flat_mask_uri)

    labels_ds = gdal.Open(labels_uri)
    labels_band = labels_ds.GetRasterBand(1)
    flat_mask_ds = gdal.Open(flat_mask_uri, gdal.GA_Update)
    flat_mask_band = flat_mask_ds.GetRasterBand(1)
    flow_direction_ds = gdal.Open(flow_direction_uri)
    flow_direction_band = flow_direction_ds.GetRasterBand(1)

    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = labels_band.GetBlockSize()
    cdef int n_rows = labels_ds.RasterYSize
    cdef int n_cols = labels_ds.RasterXSize

    cdef int n_block_rows = 3, n_block_cols = 3

    cdef numpy.ndarray[numpy.npy_int32, ndim=4] labels_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.int32)
    cdef numpy.ndarray[numpy.npy_int32, ndim=4] flat_mask_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size),
        dtype=numpy.int32)
    cdef numpy.ndarray[numpy.npy_int32, ndim=4] flow_direction_block = (
        numpy.zeros(
            (n_block_rows, n_block_cols, block_row_size, block_col_size),
            dtype=numpy.int32))

    band_list = [labels_band, flat_mask_band, flow_direction_band]
    block_list = [labels_block, flat_mask_block, flow_direction_block]
    update_list = [False, True, False]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size,
        block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef int cell_row_index, cell_col_index
    cdef int cell_row_block_index, cell_col_block_index
    cdef int cell_row_block_offset, cell_col_block_offset

    cdef int loops = 1

    low_edges_queue = collections.deque()
    cdef int neighbor_row, neighbor_col
    cdef int flat_index
    cdef int flat_row, flat_col
    cdef int flat_mask
    cdef int labels_nodata = raster_utils.get_nodata_from_uri(labels_uri)
    cdef int cell_label, neighbor_label
    cdef float neighbor_flow
    cdef float flow_nodata = raster_utils.get_nodata_from_uri(
        flow_direction_uri)

    for flat_index in low_edges:
        low_edges_queue.append(flat_index)

    marker = -1
    low_edges_queue.append(marker)
    while len(low_edges_queue) > 1:
        flat_index = low_edges_queue.popleft()
        if flat_index == marker:
            loops += 1
            low_edges_queue.append(marker)
            continue

        flat_row = flat_index / n_cols
        flat_col = flat_index % n_cols

        block_cache.update_cache(
            flat_row, flat_col,
            &cell_row_index, &cell_col_index,
            &cell_row_block_offset, &cell_col_block_offset)

        flat_mask = flat_mask_block[
            cell_row_index, cell_col_index,
            cell_row_block_offset, cell_col_block_offset]

        if flat_mask > 0:
            continue

        cell_label = labels_block[
            cell_row_index, cell_col_index,
            cell_row_block_offset, cell_col_block_offset]

        if flat_mask < 0:
            flat_mask_block[
                cell_row_index, cell_col_index,
                cell_row_block_offset, cell_col_block_offset] = (
                    flat_height[cell_label] + flat_mask + 2 * loops)
        else:
            flat_mask_block[
                cell_row_index, cell_col_index,
                cell_row_block_offset, cell_col_block_offset] = 2 * loops
        cache_dirty[cell_row_index, cell_col_index] = 1

        #visit the neighbors
        for neighbor_index in xrange(8):
            neighbor_row = (
                flat_row + neighbor_row_offset[neighbor_index])
            neighbor_col = (
                flat_col + neighbor_col_offset[neighbor_index])

            if (neighbor_row < 0 or neighbor_row >= n_rows or
                    neighbor_col < 0 or neighbor_col >= n_cols):
                continue

            block_cache.update_cache(
                neighbor_row, neighbor_col,
                &cell_row_index, &cell_col_index,
                &cell_row_block_offset, &cell_col_block_offset)

            neighbor_label = labels_block[
                cell_row_index, cell_col_index,
                cell_row_block_offset, cell_col_block_offset]

            neighbor_flow = flow_direction_block[
                cell_row_index, cell_col_index,
                cell_row_block_offset, cell_col_block_offset]

            if (neighbor_label != labels_nodata and
                    neighbor_label == cell_label and
                    neighbor_flow == flow_nodata):
                low_edges_queue.append(neighbor_row * n_cols + neighbor_col)

    block_cache.flush_cache()


def flow_direction_inf_masked_flow_dirs(
        flat_mask_uri, labels_uri, flow_direction_uri):
    """Calculates the D-infinity flow algorithm for regions defined from flat
        drainage resolution.

        Flow algorithm from: Tarboton, "A new method for the determination of
        flow directions and upslope areas in grid digital elevation models,"
        Water Resources Research, vol. 33, no. 2, pages 309 - 319, February
        1997.

        Also resolves flow directions in flat areas of DEM.

        flat_mask_uri (string) - (input) a uri to a single band GDAL Dataset
            that has offset values from the flat region resolution algorithm.
            The offsets in flat_mask are the relative heights only within the
            flat regions defined in labels_uri.
        labels_uri (string) - (input) a uri to a single band integer gdal
                dataset that contain labels for the cells that lie in
                flat regions of the DEM.
        flow_direction_uri - (input/output) a uri to an existing GDAL dataset
            of same size as dem_uri.  Flow direction will be defined in regions
            that have nodata values in them that overlap regions of labels_uri.
            This is so this function can be used as a two pass filter for
            resolving flow directions on a raw dem, then filling plateaus and
            doing another pass.

       returns nothing"""

    cdef int col_index, row_index, n_cols, n_rows, max_index, facet_index, flat_index
    cdef double e_0, e_1, e_2, s_1, s_2, d_1, d_2, flow_direction, slope, \
        flow_direction_max_slope, slope_max, nodata_flow

    flat_mask_ds = gdal.Open(flat_mask_uri)
    flat_mask_band = flat_mask_ds.GetRasterBand(1)

    #facet elevation and factors for slope and flow_direction calculations
    #from Table 1 in Tarboton 1997.
    #THIS IS IMPORTANT:  The order is row (j), column (i), transposed to GDAL
    #convention.
    cdef int *e_0_offsets = [+0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0]
    cdef int *e_1_offsets = [+0, +1,
                             -1, +0,
                             -1, +0,
                             +0, -1,
                             +0, -1,
                             +1, +0,
                             +1, +0,
                             +0, +1]
    cdef int *e_2_offsets = [-1, +1,
                             -1, +1,
                             -1, -1,
                             -1, -1,
                             +1, -1,
                             +1, -1,
                             +1, +1,
                             +1, +1]
    cdef int *a_c = [0, 1, 1, 2, 2, 3, 3, 4]
    cdef int *a_f = [1, -1, 1, -1, 1, -1, 1, -1]

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]

    n_rows, n_cols = raster_utils.get_row_col_from_uri(flat_mask_uri)
    d_1 = raster_utils.get_cell_size_from_uri(flat_mask_uri)
    d_2 = d_1
    cdef double max_r = numpy.pi / 4.0


    cdef float flow_nodata = raster_utils.get_nodata_from_uri(
        flow_direction_uri)
    flow_direction_dataset = gdal.Open(flow_direction_uri, gdal.GA_Update)
    flow_band = flow_direction_dataset.GetRasterBand(1)

    cdef float label_nodata = raster_utils.get_nodata_from_uri(labels_uri)
    label_dataset = gdal.Open(labels_uri)
    label_band = label_dataset.GetRasterBand(1)

    cdef int n_block_rows = 3, n_block_cols = 3 #the number of blocks we'll cache

    #center point of global index
    cdef int block_row_size, block_col_size
    block_col_size, block_row_size = flat_mask_band.GetBlockSize()
    cdef int global_row, global_col, e_0_row, e_0_col, e_1_row, e_1_col, e_2_row, e_2_col #index into the overall raster
    cdef int e_0_row_index, e_0_col_index #the index of the cache block
    cdef int e_0_row_block_offset, e_0_col_block_offset #index into the cache block
    cdef int e_1_row_index, e_1_col_index #the index of the cache block
    cdef int e_1_row_block_offset, e_1_col_block_offset #index into the cache block
    cdef int e_2_row_index, e_2_col_index #the index of the cache block
    cdef int e_2_row_block_offset, e_2_col_block_offset #index into the cache block

    cdef int global_block_row, global_block_col #used to walk the global blocks

    #neighbor sections of global index
    cdef int neighbor_row, neighbor_col #neighbor equivalent of global_{row,col}
    cdef int neighbor_row_index, neighbor_col_index #neighbor cache index
    cdef int neighbor_row_block_offset, neighbor_col_block_offset #index into the neighbor cache block

    #define all the caches
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] flow_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    #flat_mask block is a 64 bit float so it can capture the resolution of small flat_mask offsets
    #from the plateau resolution algorithm.
    cdef numpy.ndarray[numpy.npy_int32, ndim=4] flat_mask_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int32)
    cdef numpy.ndarray[numpy.npy_int32, ndim=4] label_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int32)

    #the BlockCache object needs parallel lists of bands, blocks, and boolean tags to indicate which ones are updated
    band_list = [flat_mask_band, flow_band, label_band]
    block_list = [flat_mask_block, flow_block, label_block]
    update_list = [False, True, False]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    cdef int row_offset, col_offset
    cdef int y_offset, local_y_offset
    cdef int max_downhill_facet
    cdef double lowest_flat_mask, flat_mask_value, flow_direction_value

    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))
    cdef time_t last_time, current_time
    cdef float current_flow
    cdef int current_label, e_1_label, e_2_label
    time(&last_time)
    #flow not defined on the edges, so just go 1 row in
    for global_block_row in xrange(n_global_block_rows):
        time(&current_time)
        if current_time - last_time > 5.0:
            LOGGER.info("flow_direction_inf %.1f%% complete", (global_row + 1.0) / n_rows * 100)
            last_time = current_time
        for global_block_col in xrange(n_global_block_cols):
            for global_row in xrange(global_block_row*block_row_size, min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(global_block_col*block_col_size, min((global_block_col+1)*block_col_size, n_cols)):
                    #is cache block not loaded?

                    e_0_row = e_0_offsets[0] + global_row
                    e_0_col = e_0_offsets[1] + global_col

                    block_cache.update_cache(e_0_row, e_0_col, &e_0_row_index, &e_0_col_index, &e_0_row_block_offset, &e_0_col_block_offset)

                    current_label = label_block[
                        e_0_row_index, e_0_col_index,
                        e_0_row_block_offset, e_0_col_block_offset]

                    #if a label isn't defiend we're not in a flat region
                    if current_label == label_nodata:
                        continue

                    current_flow = flow_block[
                        e_0_row_index, e_0_col_index,
                        e_0_row_block_offset, e_0_col_block_offset]

                    #this can happen if we have been passed an existing flow
                    #direction raster, perhaps from an earlier iteration in a
                    #multiphase flow resolution algorithm
                    if current_flow != flow_nodata:
                        continue

                    e_0 = flat_mask_block[e_0_row_index, e_0_col_index, e_0_row_block_offset, e_0_col_block_offset]
                    #skip if we're on a nodata pixel skip

                    max_downhill_facet = -1
                    lowest_flat_mask = e_0

                    #Calculate the flow flow_direction for each facet
                    slope_max = 0 #use this to keep track of the maximum down-slope
                    flow_direction_max_slope = 0 #flow direction on max downward slope
                    max_index = 0 #index to keep track of max slope facet

                    for facet_index in range(8):
                        #This defines the three points the facet

                        e_1_row = e_1_offsets[facet_index * 2 + 0] + global_row
                        e_1_col = e_1_offsets[facet_index * 2 + 1] + global_col
                        e_2_row = e_2_offsets[facet_index * 2 + 0] + global_row
                        e_2_col = e_2_offsets[facet_index * 2 + 1] + global_col
                        #make sure one of the facets doesn't hang off the edge
                        if (e_1_row < 0 or e_1_row >= n_rows or
                            e_2_row < 0 or e_2_row >= n_rows or
                            e_1_col < 0 or e_1_col >= n_cols or
                            e_2_col < 0 or e_2_col >= n_cols):
                            continue

                        block_cache.update_cache(e_1_row, e_1_col, &e_1_row_index, &e_1_col_index, &e_1_row_block_offset, &e_1_col_block_offset)
                        block_cache.update_cache(e_2_row, e_2_col, &e_2_row_index, &e_2_col_index, &e_2_row_block_offset, &e_2_col_block_offset)

                        e_1 = flat_mask_block[e_1_row_index, e_1_col_index, e_1_row_block_offset, e_1_col_block_offset]
                        e_2 = flat_mask_block[e_2_row_index, e_2_col_index, e_2_row_block_offset, e_2_col_block_offset]

                        e_1_label = label_block[e_1_row_index, e_1_col_index, e_1_row_block_offset, e_1_col_block_offset]
                        e_2_label = label_block[e_2_row_index, e_2_col_index, e_2_row_block_offset, e_2_col_block_offset]

                        #if labels aren't t the same as the current, we can't flow to them
                        if e_1_label != current_label and e_2_label != current_label:
                            continue

                        #s_1 is slope along straight edge
                        s_1 = (e_0 - e_1) / d_1 #Eqn 1
                        #slope along diagonal edge
                        s_2 = (e_1 - e_2) / d_2 #Eqn 2

                        #can't calculate flow direction if one of the facets is nodata
                        if e_1_label != current_label or e_2_label != current_label:
                            #calc max slope here
                            if e_1_label == current_label:
                                #straight line to next pixel
                                slope = s_1
                            else:
                                #diagonal line to next pixel
                                slope = (e_0 - e_2) / sqrt(d_1 **2 + d_2 ** 2)
                        else:
                            #both facets are defined, this is the core of
                            #d-infinity algorithm
                            flow_direction = atan2(s_2, s_1) #Eqn 3

                            if flow_direction < 0: #Eqn 4
                                #If the flow direction goes off one side, set flow
                                #direction to that side and the slope to the straight line
                                #distance slope
                                flow_direction = 0
                                slope = s_1
                            elif flow_direction > max_r: #Eqn 5
                                #If the flow direciton goes off the diagonal side, figure
                                #out what its value is and
                                flow_direction = max_r
                                slope = (e_0 - e_2) / sqrt(d_1 ** 2 + d_2 ** 2)
                            else:
                                slope = sqrt(s_1 ** 2 + s_2 ** 2) #Eqn 3

                        #update the maxes depending on the results above
                        if slope > slope_max:
                            flow_direction_max_slope = flow_direction
                            slope_max = slope
                            max_index = facet_index

                    #if there's a downward slope, save the flow direction
                    if slope_max > 0:
                        flow_block[e_0_row_index, e_0_col_index, e_0_row_block_offset, e_0_col_block_offset] = (
                            a_f[max_index] * flow_direction_max_slope +
                            a_c[max_index] * 3.14159265 / 2.0)
                        cache_dirty[e_0_row_index, e_0_col_index] = 1

    block_cache.flush_cache()
    flow_band = None
    gdal.Dataset.__swig_destroy__(flow_direction_dataset)
    flow_direction_dataset = None
    raster_utils.calculate_raster_stats_uri(flow_direction_uri)