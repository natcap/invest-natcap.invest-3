# cython: profile=False

import collections
import tempfile
import time
import logging
import sys
import tables
import os

import numpy
cimport numpy
cimport cython
import scipy.sparse
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

from invest_natcap import raster_utils


logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing cython core')

cdef double PI = 3.141592653589793238462643383279502884

cdef int MAX_WINDOW_SIZE = 2**12
cdef double INF = numpy.inf

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
    LOGGER.info('Processing transport through grid')
    start = time.clock()

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
    
    cdef int absorb_source = (absorption_mode == 'source_and_flux')

    last_time = time.time()
    while cells_to_process.size() > 0:
        current_time = time.time()
        if current_time - last_time > 5.0:
            LOGGER.info('Steps cells_to_process.size() = %d' % (cells_to_process.size()))
            last_time = current_time
    
        current_index = cells_to_process.top()
        cells_to_process.pop()
        global_row = current_index / n_cols
        global_col = current_index % n_cols
        #see if we need to update the row cache
        block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
        
        #Ensure we are working on a valid pixel
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

            if (inflow_offsets[direction_index] != neighbor_direction and inflow_offsets[direction_index] != (neighbor_direction - 1) % 8):
                #then neighbor doesn't inflow into current cell
                continue

            #Calculate the outflow weight
            outflow_weight = outflow_weights_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]
            
            if inflow_offsets[direction_index] == (neighbor_direction - 1) % 8:
                outflow_weight = 1.0 - outflow_weight

            if outflow_weight < 0.001:
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

    LOGGER.info('Flushing remaining dirty cache to disk')
    block_cache.flush_cache()
    LOGGER.info('Done processing transport elapsed time %ss' %
                (time.clock() - start))


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

    LOGGER.info('Calculating flow graph')
    start = time.clock()

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

    last_time = time.time()        
    for global_block_row in xrange(int(ceil(float(n_rows) / block_row_size))):
        current_time = time.time()
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

                            #This will handle cases where almost all flow is going in
                            #one direction, or is supposed to go in one direction,
                            #but because of machine error splits insignificantly
                            #between two cells. The 0.999 is a little overkill but works
                            if outflow_weight > 0.999:
                                outflow_weight = 1.0

                            #If the outflow is nearly 0, make push it all
                            #to the next neighbor
                            if outflow_weight < 0.001:
                                outflow_weight = 1.0
                                neighbor_direction_index = (neighbor_direction_index + 1) % 8

                            outflow_direction_block[row_index, col_index, row_block_offset, col_block_offset] = neighbor_direction_index
                            outflow_weights_block[row_index, col_index, row_block_offset, col_block_offset] = outflow_weight
                            cache_dirty[row_index, col_index] = 1

                            #we found the outflow direction
                            break
                    if not found:
                        LOGGER.debug('no flow direction found for %s %s' % \
                                         (row_index, col_index))
    block_cache.flush_cache()
        
    LOGGER.info('Done calculating flow weights elapsed time %ss' % \
                    (time.clock()-start))


'''def percent_to_sink(
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
    start_time = time.clock()

    cdef double effect_nodata = -1.0
    raster_utils.new_raster_from_base_uri(
        sink_pixels_uri, effect_uri, 'GTiff', effect_nodata,
        gdal.GDT_Float32, fill_value=effect_nodata)
    effect_dataset = gdal.Open(effect_uri, gdal.GA_Update)
    effect_band = effect_dataset.GetRasterBand(1)

    cdef int n_block_rows = 3
    cdef int n_block_cols = 3
    cdef int block_col_size, block_row_size
    block_col_size, block_row_size = effect_band.GetBlockSize()

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
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] effect_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_int8, ndim=4] sink_pixels_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int8)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] export_rate_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_int8, ndim=4] outflow_direction_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.int8)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] outflow_weights_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_int8, ndim=2] cache_dirty = numpy.zeros(
        (n_block_rows, n_block_cols), dtype=numpy.int8)

    outflow_weights_dataset = gdal.Open(outflow_weights_uri)
    outflow_weights_band = outflow_weights_dataset.GetRasterBand(1)
    cdef int outflow_weights_nodata = raster_utils.get_nodata_from_uri(
        outflow_weights_uri)

    cdef int n_cols = effect_dataset.RasterXSize
    cdef int n_rows = effect_dataset.RasterYSize
    
    sink_pixels_dataset = gdal.Open(sink_pixels_uri)
    sink_pixels_band = sink_pixels_dataset.GetRasterBand(1)
    cdef int sink_pixels_nodata = raster_utils.get_nodata_from_uri(
        sink_pixels_uri)
    
    export_rate_dataset = gdal.Open(export_rate_uri)
    export_rate_band = export_rate_dataset.GetRasterBand(1)
    cdef float export_rate_nodata = raster_utils.get_nodata_from_uri(
        export_rate_uri)
    
    outflow_direction_dataset = gdal.Open(outflow_direction_uri)
    outflow_direction_band = outflow_direction_dataset.GetRasterBand(1)
    cdef int outflow_direction_nodata = raster_utils.get_nodata_from_uri(
        outflow_direction_uri)
    
    #####################################
    cache_dirty[:] = 0
    band_list = [effect_band, sink_pixels_band, export_rate_band, outflow_direction_band, outflow_weights_band]
    block_list = [effect_block, sink_pixels_block, export_rate_block, outflow_direction_block, outflow_weights_block]
    update_list = [False, False, False, False, True, True]
    
    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)


    #Diagonal offsets are based off the following index notation for neighbors
    #    3 2 1
    #    4 p 0
    #    5 6 7

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]

    cdef int flat_index, neighbor_index, neighbor_outflow_direction
    cdef double outflow_weight, neighbor_outflow_weight
    
    #initially nothing is loaded in the cache, use -1 to indicate that as a tag
    
    cdef queue[int] process_queue
    #Queue the sinks
    for global_row in xrange(n_rows):
        for global_col in xrange(n_cols):
            block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
            if sink_pixels_block[row_index, col_index, row_block_offset, col_block_offset] == 1:
                effect_block[row_index, col_index, row_block_offset, col_block_offset] = 1.0
                cache_dirty[row_index, col_index] = 1
                process_queue.push(global_row * n_cols + global_col)
        
    while process_queue.size() > 0:
        flat_index = process_queue.front()
        process_queue.pop()
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
            neighbor_col = global_col = col_offsets[neighbor_index]
            if neighbor_row < 0 or neighbor_row >= n_rows or neighbor_col < 0 or neighbor_col_index >= n_cols:
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
                    process_queue.push(neighbor_row_index * n_cols + neighbor_col_index)
                    effect_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] = 0.0

                #the percent of the pixel upstream equals the current percent 
                #times the percent flow to that pixels times the 
                effect_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] += (
                    effect_block[row_index, col_index, row_block_offset, col_block_offset] *
                    neighbor_outflow_weight *
                    export_rate_block[row_index, col_index, row_block_offset, col_block_offset])
                cache_dirty[neighbor_row_index, neighbor_col_index] = 1

    cache_dirty.flush_cache()
    LOGGER.info('Done calculating percent to sink elapsed time %ss' % \
                    (time.clock() - start_time))
'''


cdef struct Row_Col_Weight_Tuple:
    int row_index
    int col_index
    int weight

    
cdef _build_flat_set(
    char *dem_uri, float nodata_value, c_set[int] &flat_set):
    
    LOGGER.debug('in _build_flat_set')
    
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
    
    last_time = time.time()
    #not flat on the edges of the raster, could be a sink
    for global_block_row in xrange(int(ceil(float(n_rows) / block_row_size))):
        current_time = time.time()
        if current_time - last_time > 5.0:
            LOGGER.info("cache_block_experiment %.1f%% complete", (global_row + 1.0) / n_rows * 100)
            last_time = current_time
        for global_block_col in xrange(int(ceil(float(n_cols) / block_col_size))):
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
                        
                        if (neighbor_row >= n_rows or neighbor_row < 0 or neighbor_col >= n_cols or neighbor_col < 0):
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
    LOGGER.info('in fill pits input dem blocksize %s, dem_uri = %s' % (str(dem_band.GetBlockSize()), dem_uri))
        
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
    LOGGER.info("%d pits were filled." % (pit_count,))
        
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

    LOGGER.info('identify flat cells')
    
    #search for flat cells
    #search for flat areas, iterate through the array 3 rows at a time
    cdef c_set[int] flat_set
    cdef c_set[int] flat_set_for_looping
    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    _build_flat_set(dem_tmp_fill_uri, nodata_value, flat_set)
    LOGGER.debug("flat_set size %d" % (flat_set.size()))
    
    dem_out_ds = gdal.Open(dem_tmp_fill_uri, gdal.GA_Update)
    dem_out_band = dem_out_ds.GetRasterBand(1)

    cdef int flat_index
    #make a copy of the flat index so we can break it down for iteration but
    #keep the old one for rapid testing of flat cells
    for flat_index in flat_set:
        flat_set_for_looping.insert(flat_set_for_looping.end(), flat_index)

    LOGGER.info('finished flat cell detection, now identify plateaus')

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

    LOGGER.info('identify sink cells')
    cdef int sink_cell_hits = 0, edge_cell_hits = 0

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
    last_time = time.time()
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
        current_time = time.time()
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

                    #if we don't abut a higher pixel then skip
                    if (dem_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset] <=
                        dem_block[row_index, col_index, row_block_offset, col_block_offset]):
                        continue

                    #otherwise we're next to an uphill pixel, that means we're an edge
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
            sink_cell_hits += 1
            current_cell_tuple = sink_queue.front()
            sink_queue.pop()
            
            global_row = current_cell_tuple.row_index
            global_col = current_cell_tuple.col_index
            weight = current_cell_tuple.weight
            block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)

            for neighbor_index in xrange(8):
                neighbor_row = global_row + row_offsets[neighbor_index]
                neighbor_col = global_col + col_offsets[neighbor_index]

                if neighbor_row_index < 0 or neighbor_row_index >= n_rows or neighbor_col_index < 0 or neighbor_col_index >= n_cols:
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
            edge_cell_hits += 1
            current_cell_tuple = edge_queue.front()
            edge_queue.pop()
            
            global_row = current_cell_tuple.row_index
            global_col = current_cell_tuple.col_index
            weight = current_cell_tuple.weight
            block_cache.update_cache(global_row, global_col, &row_index, &col_index, &row_block_offset, &col_block_offset)
            
            for neighbor_index in xrange(8):
                neighbor_row = global_row + row_offsets[neighbor_index]
                neighbor_col = global_col + col_offsets[neighbor_index]

                if neighbor_row_index < 0 or neighbor_row_index >= n_rows or neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                    continue
                block_cache.update_cache(neighbor_row, neighbor_col, &neighbor_row_index, &neighbor_col_index, &neighbor_row_block_offset, &neighbor_col_block_offset)
                
                #If the neighbor is not at the same height, skip
                if (dem_block[row_index, col_index, row_block_offset, col_block_offset] != 
                    dem_block[neighbor_row_index, neighbor_col_index, neighbor_row_block_offset, neighbor_col_block_offset]):
                    continue

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
    LOGGER.debug('calculating max distance')
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

    LOGGER.debug("max_distance %s" % (str(max_distance)))
    
    #Add the final offsets to the dem array
    def offset_dem(dem_sink_offset_array, dem_edge_offset_array, dem_array):
        mask_array = ((dem_sink_offset_array != INF) &
                      (dem_edge_offset_array != INF) &
                      (dem_sink_offset_array != MAX_DISTANCE) &
                      (dem_edge_offset_array != MAX_DISTANCE))

        offset_array = numpy.where(
            (dem_sink_offset_array != INF) & 
            (dem_sink_offset_array != MAX_DISTANCE), 
            2.0*dem_sink_offset_array, 0.0)
            
        offset_array = numpy.where(
            (dem_edge_offset_array != INF) & 
            (dem_edge_offset_array != MAX_DISTANCE), 
            max_distance+1-dem_edge_offset_array+offset_array, 0.0)

        dem_array += offset_array / 10000.0
        return dem_array

    
    LOGGER.info('saving back the dirty cache')
    block_cache.flush_cache()
    
    dem_out_band = None
    dem_sink_offset_band = None
    dem_edge_offset_band = None
    
    gdal.Dataset.__swig_destroy__(dem_out_ds)
    gdal.Dataset.__swig_destroy__(dem_sink_offset_ds)
    gdal.Dataset.__swig_destroy__(dem_edge_offset_ds)
    
    raster_utils.vectorize_datasets(
        [dem_sink_offset_uri, dem_edge_offset_uri, dem_tmp_fill_uri], offset_dem, dem_out_uri, gdal.GDT_Float32,
        nodata_value, pixel_size, 'intersection',
        vectorize_op=False, datasets_are_pre_aligned=True)

    
def flow_direction_inf(dem_uri, flow_direction_uri):
    """Calculates the D-infinity flow algorithm.  The output is a float
        raster whose values range from 0 to 2pi.
        
        Algorithm from: Tarboton, "A new method for the determination of flow
        directions and upslope areas in grid digital elevation models," Water
        Resources Research, vol. 33, no. 2, pages 309 - 319, February 1997.

        Also resolves flow directions in flat areas of DEM.
        
       dem_uri - a uri to a single band GDAL Dataset with elevation values
       flow_direction_uri - a uri to write a single band float raster of same
            dimensions.  After the function call it will have flow direction 
            in it.
        
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
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] dem_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    
    #the BlockCache object needs parallel lists of bands, blocks, and boolean tags to indicate which ones are updated
    band_list = [dem_band, flow_band]
    block_list = [dem_block, flow_block]
    update_list = [False, True]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    LOGGER.info("calculating d-inf per pixel flows")
    
    cdef int row_offset, col_offset
    cdef int y_offset, local_y_offset
    cdef int max_downhill_facet
    cdef double lowest_dem, dem_value, flow_direction_value
    cdef float current_time, last_time

    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))
    last_time = time.time()
    #flow not defined on the edges, so just go 1 row in 
    for global_block_row in xrange(n_global_block_rows):
        current_time = time.time()
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
                    #we have a special case if we're on the border of the raster
                    if (e_0_col == 0 or e_0_col == n_cols - 1 or e_0_row == 0 or e_0_row == n_rows - 1):
                        #loop through the neighbor edges, and manually set a direction
                        for facet_index in range(8):
                            e_1_row = row_offsets[facet_index] + global_row
                            e_1_col = col_offsets[facet_index] + global_col
                            if (e_1_col == -1 or e_1_col == n_cols or e_1_row == -1 or e_1_row == n_rows):
                                continue
                            block_cache.update_cache(e_1_row, e_1_col, &e_1_row_index, &e_1_col_index, &e_1_row_block_offset, &e_1_col_block_offset)
                            e_1 = dem_block[e_1_row_index, e_1_col_index, e_1_row_block_offset, e_1_col_block_offset]
                            if e_1 == dem_nodata:
                                continue
                            if e_1 < lowest_dem:
                                lowest_dem = e_1
                                max_downhill_facet = facet_index
                                
                        if max_downhill_facet != -1:
                            flow_direction = 3.14159265 / 4.0 * max_downhill_facet
                        else:
                            #we need to point to the left or right
                            if global_col == 0:
                                flow_direction = 3.14159265 / 2.0 * 2
                            elif global_col == n_cols - 1:
                                flow_direction = 3.14159265 / 2.0 * 0
                            elif global_row == 0:
                                flow_direction = 3.14159265 / 2.0 * 1
                            elif global_row == n_rows - 1:
                                flow_direction = 3.14159265 / 2.0 * 3
                        flow_block[e_0_row_index, e_0_col_index, e_0_row_block_offset, e_0_col_block_offset] = flow_direction
                        cache_dirty[e_0_row_index, e_0_col_index] = 1
                        #done with this pixel, go to the next
                        continue
                        
                    #Calculate the flow flow_direction for each facet
                    slope_max = 0 #use this to keep track of the maximum down-slope
                    flow_direction_max_slope = 0 #flow direction on max downward slope
                    max_index = 0 #index to keep track of max slope facet
                    
                    #max_downhill_facet = -1
                    #lowest_dem = e_0
                    contaminated = False
                    for facet_index in range(8):
                        #This defines the three points the facet

                        e_1_row = e_1_offsets[facet_index * 2 + 0] + global_row
                        e_1_col = e_1_offsets[facet_index * 2 + 1] + global_col
                        e_2_row = e_2_offsets[facet_index * 2 + 0] + global_row
                        e_2_col = e_2_offsets[facet_index * 2 + 1] + global_col

                        block_cache.update_cache(e_1_row, e_1_col, &e_1_row_index, &e_1_col_index, &e_1_row_block_offset, &e_1_col_block_offset)
                        block_cache.update_cache(e_2_row, e_2_col, &e_2_row_index, &e_2_col_index, &e_2_row_block_offset, &e_2_col_block_offset)
                        
                        e_1 = dem_block[e_1_row_index, e_1_col_index, e_1_row_block_offset, e_1_col_block_offset]
                        e_2 = dem_block[e_2_row_index, e_2_col_index, e_2_row_block_offset, e_2_col_block_offset]

                        if facet_index % 2 == 0 and e_1 != dem_nodata and e_1 < lowest_dem:
                            lowest_dem = e_1
                            max_downhill_facet = facet_index
                        elif facet_index % 2 == 1 and e_2 != dem_nodata and e_2 < lowest_dem:
                            lowest_dem = e_2
                            max_downhill_facet = facet_index
                        
                        #avoid calculating a slope on nodata values
                        if e_1 == dem_nodata or e_2 == dem_nodata:
                            #If any neighbors are nodata, it's contaminated
                            contaminated = True
                            continue
                            
                        #s_1 is slope along straight edge
                        s_1 = (e_0 - e_1) / d_1 #Eqn 1
                        #slope along diagonal edge
                        s_2 = (e_1 - e_2) / d_2 #Eqn 2
                        
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
                            
                        if slope > slope_max:
                            flow_direction_max_slope = flow_direction
                            slope_max = slope
                            max_index = facet_index
                        
                    # This is the fallthrough condition for the for loop, we reach
                    # it only if we haven't encountered an invalid slope or pixel
                    # that caused the above algorithm to break out 
                    #Calculate the global angle depending on the max slope facet
                    if not contaminated:
                        if slope_max > 0:
                            flow_block[e_0_row_index, e_0_col_index, e_0_row_block_offset, e_0_col_block_offset] = (
                                a_f[max_index] * flow_direction_max_slope +
                                a_c[max_index] * 3.14159265 / 2.0)
                            cache_dirty[e_0_row_index, e_0_col_index] = 1
                        #just in case we set 2pi rather than 0
                        #if abs(flow_array[0, col_index] - 3.14159265 * 2.0) < 1e-10:
                        #    flow_array[0, col_index]  = 0.0
                    else:
                        if max_downhill_facet != -1:
                            flow_block[e_0_row_index, e_0_col_index, e_0_row_block_offset, e_0_col_block_offset] = (
                                3.14159265 / 4.0 * max_downhill_facet)
                            cache_dirty[e_0_row_index, e_0_col_index] = 1

    block_cache.flush_cache()
    flow_band = None
    gdal.Dataset.__swig_destroy__(flow_direction_dataset)
    flow_direction_dataset = None
    raster_utils.calculate_raster_stats_uri(flow_direction_uri)


'''
    while unresolved_cells_defer.size() > 0:
        flat_index = unresolved_cells_defer.front()
        unresolved_cells_defer.pop()
    
        global_row = flat_index / n_cols
        global_col = flat_index % n_cols
        #We load 3 rows at a time and we know unresolved directions can only
        #occur in the middle of the raster
        if global_row == 0 or global_row == n_rows - 1 or global_col == 0 or global_col == n_cols - 1:
            raise Exception('When resolving unresolved direction cells, encountered a pixel on the edge (%d, %d)' % (row_index, col_index))
        if y_offset != row_index - 1:
            if dirty_cache:
                flow_band.WriteArray(flow_array, 0, y_offset)
                dirty_cache = 0
            local_y_offset = 1
            y_offset = row_index - 1
            flow_array = flow_band.ReadAsArray(
                xoff=0, yoff=y_offset, win_xsize=n_cols, win_ysize=3)
                
            flow_array[1, col_index] = flow_nodata
            dirty_cache = 1
            
    if dirty_cache:
        flow_band.WriteArray(flow_array, 0, y_offset)
        dirty_cache = 0
'''



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
    
    LOGGER.debug("n_cols, n_rows %d %d" % (n_cols, n_rows))

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

    
def distance_to_stream(flow_direction_uri, stream_uri, distance_uri):
    """This function calculates the flow downhill distance to the stream layers
    
        flow_direction_uri - a raster with d-infinity flow directions
        stream_uri - a raster where 1 indicates a stream all other values
            ignored must be same dimensions and projection as
            flow_direction_uri)
        distance_uri - an output raster that will be the same dimensions as
            the input rasters where each pixel is in linear units the drainage
            from that point to a stream.
            
        returns nothing"""
    
    cdef float distance_nodata = -9999
    raster_utils.new_raster_from_base_uri(
        flow_direction_uri, distance_uri, 'GTiff', distance_nodata,
        gdal.GDT_Float32, fill_value=distance_nodata)

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]
    
    cdef int row_index, col_index, n_rows, n_cols
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
    
    cdef int CACHE_ROWS = n_rows
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] stream_cache
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_cache 
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights_cache
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] distance_cache
    cdef numpy.ndarray[numpy.npy_int32, ndim=1] cache_tag
    cdef numpy.ndarray[numpy.npy_byte, ndim=1] cache_dirty

    while True:
        try:
            stream_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
            outflow_direction_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.int8))
            outflow_weights_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
            distance_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
            cache_tag = (
                numpy.empty((CACHE_ROWS,), dtype=numpy.int32))
            cache_dirty = (
                numpy.zeros((CACHE_ROWS,), dtype=numpy.int8))
            break
        except MemoryError as e:
            LOGGER.warn(
                'Warning a cache row size of %d was too large, ' % CACHE_ROWS +
                'reducing by half')
            CACHE_ROWS /= 2
            if CACHE_ROWS < 3:
                LOGGER.error(
                    'The cache size is too small now, '
                    "don't know what to do.  Failing.")
                raise e
    
    #initially nothing is loaded in the cache, use -1 to indicate that as a tag
    cache_tag[:] = -1
    cache_dirty[:] = 0
    
    #build up the stream pixel indexes
    for row_index in range(n_rows):
        stream_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1,
            buf_obj=stream_cache[0].reshape((1,n_cols)))
        for col_index in range(n_cols):
            if stream_cache[0, col_index] == 1:
                #it's a stream, remember that
                visit_stack.push(row_index * n_cols + col_index)
                
    LOGGER.info('number of stream pixels %d' % (visit_stack.size()))
    
    cdef int current_index, cache_row_offset, neighbor_row_index
    cdef int cache_row_index, row_tag
    cdef int neighbor_outflow_direction, neighbor_index, outflow_direction
    cdef int neighbor_col_index
    cdef float neighbor_outflow_weight, current_distance, cell_travel_distance
    cdef float outflow_weight, neighbor_distance, step_size
    cdef int it_flows_here
    cdef int step_count = 0
    cdef int downstream_index, downstream_uncalculated

    while visit_stack.size() > 0:
        current_index = visit_stack.top()
        visit_stack.pop()
        
        row_index = current_index / n_cols
        col_index = current_index % n_cols
        step_count += 1
        if step_count % 1000000 == 0:
            LOGGER.info(
                'visit_stack on stream distance size: %d (reports every 1000000 steps)' %
                (visit_stack.size()))
        #see if we need to update the row cache
        for cache_row_offset in range(-1, 2):
            neighbor_row_index = row_index + cache_row_offset
            #see if that row is out of bounds
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                continue
            #otherwise check if the cache needs an update
            cache_row_index = neighbor_row_index % CACHE_ROWS
            row_tag = neighbor_row_index / CACHE_ROWS
            
            if cache_tag[cache_row_index] == row_tag:
                #cache is up to date, so skip
                continue
                
            #see if we need to save the cache
            if cache_dirty[cache_row_index]:
                old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
                distance_band.WriteArray(
                    distance_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                cache_dirty[cache_row_index] = 0
                
            #load a new row
            distance_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=distance_cache[cache_row_index].reshape((1,n_cols)))
            outflow_direction_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=outflow_direction_cache[cache_row_index].reshape((1,n_cols)))
            outflow_weights_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=outflow_weights_cache[cache_row_index].reshape((1,n_cols)))
            stream_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols, 
                win_ysize=1, buf_obj=stream_cache[cache_row_index].reshape((1,n_cols)))
            cache_tag[cache_row_index] = row_tag

        cache_row_index = row_index % CACHE_ROWS
        current_distance = distance_cache[cache_row_index, col_index]

        if current_distance != distance_nodata:
            #if cell is already defined, then skip
            continue
        
        outflow_weight = outflow_weights_cache[cache_row_index, col_index]
        
        if stream_cache[cache_row_index, col_index] == 1 or outflow_weight == outflow_nodata:
            #it's a stream, set distance to zero
            distance_cache[cache_row_index, col_index] = 0
            cache_dirty[cache_row_index] = 1
        else:
            #check to see if downstream neighbors are processed
            downstream_uncalculated = False
            for downstream_index in range(2):
                outflow_weight = outflow_weights_cache[cache_row_index, col_index]
                outflow_direction = outflow_direction_cache[cache_row_index, col_index]
                if downstream_index == 1:
                    outflow_weight = 1.0 - outflow_weight
                    outflow_direction = (outflow_direction + 1) % 8

                if outflow_weight > 0.0:
                    neighbor_row_index = row_index + row_offsets[outflow_direction]
                    if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                        #out of bounds
                        continue

                    neighbor_col_index = col_index + col_offsets[outflow_direction]
                    if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                        #out of bounds
                        continue

                    cache_neighbor_row_index = (
                        cache_row_index + row_offsets[outflow_direction]) % CACHE_ROWS
                    neighbor_distance = distance_cache[
                        cache_neighbor_row_index, neighbor_col_index]
                    neighbor_outflow_weight = (
                        outflow_weights_cache[cache_neighbor_row_index, col_index])
                    
                    #make sure that downstream neighbor isn't processed and
                    #isn't a nodata pixel for some reason
                    if (neighbor_distance == distance_nodata and
                        neighbor_outflow_weight != outflow_nodata):
                        visit_stack.push(neighbor_row_index * n_cols + neighbor_col_index)
                        downstream_uncalculated = True

            if downstream_uncalculated:
                #need to process downstream first
                continue
                
            #calculate current
            distance_cache[cache_row_index, col_index] = 0
            cache_dirty[cache_row_index] = 1
            outflow_weight = outflow_weights_cache[cache_row_index, col_index]
            outflow_direction = outflow_direction_cache[cache_row_index, col_index]
            for downstream_index in range(2):
                
                if downstream_index == 1:
                    outflow_weight = 1.0 - outflow_weight
                    outflow_direction = (outflow_direction + 1) % 8

                if outflow_weight > 0.0:
                    neighbor_row_index = row_index + row_offsets[outflow_direction]
                    if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                        #out of bounds
                        continue

                    neighbor_col_index = col_index + col_offsets[outflow_direction]
                    if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                        #out of bounds
                        continue

                    cache_neighbor_row_index = (
                        cache_row_index + row_offsets[outflow_direction]) % CACHE_ROWS
                    neighbor_distance = distance_cache[
                        cache_neighbor_row_index, neighbor_col_index]
                        
                    if outflow_direction % 2 == 1:
                        #increase distance by a square root of 2 for diagonal
                        step_size = cell_size * 1.41421356237
                    else:
                        step_size = cell_size

                    if neighbor_distance != distance_nodata:
                        distance_cache[cache_row_index, col_index] += (
                            neighbor_distance * outflow_weight + step_size)

        #push any upstream neighbors that inflow onto the stack
        for neighbor_index in range(8):
            neighbor_row_index = row_index + row_offsets[neighbor_index]
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                #out of bounds
                continue
            neighbor_col_index = col_index + col_offsets[neighbor_index]
            if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                #out of bounds
                continue

            cache_neighbor_row_index = (
                cache_row_index + row_offsets[neighbor_index]) % CACHE_ROWS
            neighbor_outflow_direction = outflow_direction_cache[
                cache_neighbor_row_index, neighbor_col_index]
            #if the neighbor is no data, don't try to set that
            if neighbor_outflow_direction == outflow_direction_nodata:
                continue

            neighbor_outflow_weight = outflow_weights_cache[
                cache_neighbor_row_index, neighbor_col_index]
            
            it_flows_here = False
            if neighbor_outflow_direction == inflow_offsets[neighbor_index]:
                #the neighbor flows into this cell
                it_flows_here = True

            if (neighbor_outflow_direction + 1) % 8 == inflow_offsets[neighbor_index]:
                #the offset neighbor flows into this cell
                it_flows_here = True
                neighbor_outflow_weight = 1.0 - neighbor_outflow_weight
            
            if (it_flows_here and neighbor_outflow_weight > 0.0 and
                distance_cache[cache_neighbor_row_index, neighbor_col_index] ==
                distance_nodata):
                #not touched yet, set distance push on the visit stack
                visit_stack.push(
                    neighbor_row_index * n_cols + neighbor_col_index)
            
    #see if we need to save the cache
    for cache_row_index in range(CACHE_ROWS):
        if cache_dirty[cache_row_index]:
            old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
            distance_band.WriteArray(
                distance_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
            cache_dirty[cache_row_index] = 0        
    
    for dataset in [outflow_weights_ds, outflow_direction_ds]:
        gdal.Dataset.__swig_destroy__(dataset)
    for dataset_uri in [outflow_weights_uri, outflow_direction_uri]:
        pass#os.remove(dataset_uri)

        
def calculate_d_dn(flow_direction_uri, stream_uri, ws_factor_uri, d_dn_uri):
    """This function calculates the flow downhill distance to the stream layers
    
        flow_direction_uri - a raster with d-infinity flow directions
        stream_uri - a raster where 1 indicates a stream all other values
            ignored must be same dimensions and projection as
            flow_direction_uri)
        distance_uri - an output raster that will be the same dimensions as
            the input rasters where each pixel is in linear units the drainage
            from that point to a stream.
            
        returns nothing"""
    
    cdef float d_dn_nodata = -9999.0
    raster_utils.new_raster_from_base_uri(
        flow_direction_uri, d_dn_uri, 'GTiff', d_dn_nodata,
        gdal.GDT_Float32, fill_value=d_dn_nodata)

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]
    
    cdef int row_index, col_index, n_rows, n_cols
    n_rows, n_cols = raster_utils.get_row_col_from_uri(
        flow_direction_uri)
        
    cdef stack[int] visit_stack
    
    stream_ds = gdal.Open(stream_uri)
    stream_band = stream_ds.GetRasterBand(1)
    cdef float cell_size = raster_utils.get_cell_size_from_uri(stream_uri)
    
    d_dn_ds = gdal.Open(d_dn_uri, gdal.GA_Update)
    d_dn_band = d_dn_ds.GetRasterBand(1)
    
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
    
    ws_factor_ds = gdal.Open(ws_factor_uri)
    ws_factor_band = ws_factor_ds.GetRasterBand(1)
    
    cdef int outflow_direction_nodata = raster_utils.get_nodata_from_uri(
        outflow_direction_uri)
    
    cdef int CACHE_ROWS = n_rows
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] stream_cache
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_cache
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights_cache
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] d_dn_cache
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] ws_factor_cache  
    cdef numpy.ndarray[numpy.npy_int32, ndim=1] cache_tag
    cdef numpy.ndarray[numpy.npy_byte, ndim=1] cache_dirty
    
    while True:
        try:
            stream_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
            outflow_direction_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.int8))
            outflow_weights_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
            d_dn_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
            ws_factor_cache = (
                numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))    
            cache_tag = (
                numpy.empty((CACHE_ROWS,), dtype=numpy.int32))
            cache_dirty = (
                numpy.zeros((CACHE_ROWS,), dtype=numpy.int8))
            break
        except MemoryError as e:
            LOGGER.warn(
                'Warning a cache row size of %d was too large, ' % CACHE_ROWS +
                'reducing by half')
            CACHE_ROWS /= 2
            if CACHE_ROWS < 3:
                LOGGER.error(
                    'The cache size is too small now, '
                    "don't know what to do.  Failing.")
                raise e
    
    #initially nothing is loaded in the cache, use -1 to indicate that as a tag
    cache_tag[:] = -1
    cache_dirty[:] = 0
    
    #build up the stream pixel indexes
    for row_index in range(n_rows):
        stream_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1,
            buf_obj=stream_cache[0].reshape((1,n_cols)))
        for col_index in range(n_cols):
            if stream_cache[0, col_index] == 1:
                #it's a stream, remember that
                visit_stack.push(row_index * n_cols + col_index)
                
    LOGGER.info('number of stream pixels %d' % (visit_stack.size()))
    
    cdef int current_index, cache_row_offset, neighbor_row_index
    cdef int cache_row_index, row_tag
    cdef int neighbor_outflow_direction, neighbor_index, outflow_direction
    cdef int neighbor_col_index
    cdef float neighbor_outflow_weight, current_d_dn
    cdef float outflow_weight, neighbor_d_dn, step_size, ws_factor
    cdef int it_flows_here
    cdef int step_count = 0
    cdef int downstream_index, downstream_uncalculated

    while visit_stack.size() > 0:
        current_index = visit_stack.top()
        visit_stack.pop()
        
        row_index = current_index / n_cols
        col_index = current_index % n_cols
        step_count += 1
        if step_count % 1000000 == 0:
            LOGGER.info(
                'visit_stack on stream distance size: %d (reports every 1000000 steps)' %
                (visit_stack.size()))
        #see if we need to update the row cache
        for cache_row_offset in range(-1, 2):
            neighbor_row_index = row_index + cache_row_offset
            #see if that row is out of bounds
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                continue
            #otherwise check if the cache needs an update
            cache_row_index = neighbor_row_index % CACHE_ROWS
            row_tag = neighbor_row_index / CACHE_ROWS
            
            if cache_tag[cache_row_index] == row_tag:
                #cache is up to date, so skip
                continue
                
            #see if we need to save the cache
            if cache_dirty[cache_row_index]:
                old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
                d_dn_band.WriteArray(
                    d_dn_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                cache_dirty[cache_row_index] = 0
                
            #load a new row
            d_dn_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=d_dn_cache[cache_row_index].reshape((1,n_cols)))
            outflow_direction_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=outflow_direction_cache[cache_row_index].reshape((1,n_cols)))
            outflow_weights_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=outflow_weights_cache[cache_row_index].reshape((1,n_cols)))
            ws_factor_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=ws_factor_cache[cache_row_index].reshape((1,n_cols)))                    
            stream_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols, 
                win_ysize=1, buf_obj=stream_cache[cache_row_index].reshape((1,n_cols)))
            cache_tag[cache_row_index] = row_tag

        cache_row_index = row_index % CACHE_ROWS
        current_d_dn = d_dn_cache[cache_row_index, col_index]

        if current_d_dn != d_dn_nodata:
            #if cell is already defined, then skip
            continue
        
        outflow_weight = outflow_weights_cache[cache_row_index, col_index]
        
        if stream_cache[cache_row_index, col_index] == 1 or outflow_weight == outflow_nodata:
            #it's a stream, set distance to zero
            d_dn_cache[cache_row_index, col_index] = 0
            cache_dirty[cache_row_index] = 1
        else:
            #check to see if downstream neighbours are processed
            downstream_uncalculated = False
            for downstream_index in range(2):
                outflow_weight = outflow_weights_cache[cache_row_index, col_index]
                outflow_direction = outflow_direction_cache[cache_row_index, col_index]
                if downstream_index == 1:
                    outflow_weight = 1.0 - outflow_weight
                    outflow_direction = (outflow_direction + 1) % 8

                if outflow_weight > 0.0:
                    neighbor_row_index = row_index + row_offsets[outflow_direction]
                    if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                        #out of bounds
                        continue

                    neighbor_col_index = col_index + col_offsets[outflow_direction]
                    if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                        #out of bounds
                        continue

                    cache_neighbor_row_index = (
                        cache_row_index + row_offsets[outflow_direction]) % CACHE_ROWS
                    neighbor_d_dn = d_dn_cache[
                        cache_neighbor_row_index, neighbor_col_index]
                    neighbor_outflow_weight = (
                        outflow_weights_cache[cache_neighbor_row_index, col_index])
                    
                    #make sure that downstream neighbor isn't processed and
                    #isn't a nodata pixel for some reason
                    if (neighbor_d_dn == d_dn_nodata and
                        neighbor_outflow_weight != outflow_nodata):
                        visit_stack.push(neighbor_row_index * n_cols + neighbor_col_index)
                        downstream_uncalculated = True

            if downstream_uncalculated:
                #need to process downstream first
                continue
                
            #calculate current
            d_dn_cache[cache_row_index, col_index] = 0
            cache_dirty[cache_row_index] = 1
            outflow_weight = outflow_weights_cache[cache_row_index, col_index]
            outflow_direction = outflow_direction_cache[cache_row_index, col_index]
            ws_factor = ws_factor_cache[cache_row_index, col_index]
            for downstream_index in range(2):
                
                if downstream_index == 1:
                    outflow_weight = 1.0 - outflow_weight
                    outflow_direction = (outflow_direction + 1) % 8

                if outflow_weight > 0.0:
                    neighbor_row_index = row_index + row_offsets[outflow_direction]
                    if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                        #out of bounds
                        continue

                    neighbor_col_index = col_index + col_offsets[outflow_direction]
                    if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                        #out of bounds
                        continue

                    cache_neighbor_row_index = (
                        cache_row_index + row_offsets[outflow_direction]) % CACHE_ROWS
                    neighbor_d_dn = d_dn_cache[
                        cache_neighbor_row_index, neighbor_col_index]

                    if outflow_direction % 2 == 1:
                        #increase distance by a square root of 2 for diagonal
                        step_size = cell_size * 1.41421356237
                    else:
                        step_size = cell_size

                    if neighbor_d_dn != d_dn_nodata:
                        d_dn_cache[cache_row_index, col_index] += (
                            (neighbor_d_dn + step_size/ws_factor) * 
                            outflow_weight)

        #push any upstream neighbors that inflow onto the stack
        for neighbor_index in range(8):
            neighbor_row_index = row_index + row_offsets[neighbor_index]
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                #out of bounds
                continue
            neighbor_col_index = col_index + col_offsets[neighbor_index]
            if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                #out of bounds
                continue

            cache_neighbor_row_index = (
                cache_row_index + row_offsets[neighbor_index]) % CACHE_ROWS
            neighbor_outflow_direction = outflow_direction_cache[
                cache_neighbor_row_index, neighbor_col_index]
            #if the neighbor is no data, don't try to set that
            if neighbor_outflow_direction == outflow_direction_nodata:
                continue

            neighbor_outflow_weight = outflow_weights_cache[
                cache_neighbor_row_index, neighbor_col_index]
            
            it_flows_here = False
            if neighbor_outflow_direction == inflow_offsets[neighbor_index]:
                #the neighbor flows into this cell
                it_flows_here = True

            if (neighbor_outflow_direction + 1) % 8 == inflow_offsets[neighbor_index]:
                #the offset neighbor flows into this cell
                it_flows_here = True
                neighbor_outflow_weight = 1.0 - neighbor_outflow_weight
            
            if (it_flows_here and neighbor_outflow_weight > 0.0 and
                d_dn_cache[cache_neighbor_row_index, neighbor_col_index] ==
                d_dn_nodata):
                #not touched yet, set distance push on the visit stack
                visit_stack.push(
                    neighbor_row_index * n_cols + neighbor_col_index)
            
    #see if we need to save the cache
    for cache_row_index in range(CACHE_ROWS):
        if cache_dirty[cache_row_index]:
            old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
            d_dn_band.WriteArray(
                d_dn_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
            cache_dirty[cache_row_index] = 0        
    
    for dataset in [outflow_weights_ds, outflow_direction_ds]:
        gdal.Dataset.__swig_destroy__(dataset)
    for dataset_uri in [outflow_weights_uri, outflow_direction_uri]:
        pass#os.remove(dataset_uri)

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
    last_time = time.time()

    for global_block_row in xrange(int(numpy.ceil(float(n_rows) / block_row_size))):
        current_time = time.time()
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
