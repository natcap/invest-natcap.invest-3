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
    
    
    cdef int CACHE_ROWS = 2**10
    if CACHE_ROWS > n_rows:
        CACHE_ROWS = n_rows
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.int8))
    cdef numpy.ndarray[numpy.npy_float, ndim=2] outflow_weights_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] source_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_float, ndim=2] absorption_rate_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] loss_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))   
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flux_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] stream_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.int8))
    
    cdef int stream_nodata = 0
    if stream_uri != None:
        stream_dataset = gdal.Open(stream_uri)
        stream_band = stream_dataset.GetRasterBand(1)
        stream_nodata = raster_utils.get_nodata_from_uri(stream_uri)
    else:
        stream_band = None
    
        

    cdef numpy.ndarray[numpy.npy_int32, ndim=1] cache_tag = (
        numpy.empty((CACHE_ROWS,), dtype=numpy.int32))
    #initially nothing is loaded in the cache, use -1 to indicate that as a tag
    cache_tag[:] = -1
    cdef numpy.ndarray[numpy.npy_byte, ndim=1] cache_dirty = (
        numpy.zeros((CACHE_ROWS,), dtype=numpy.int8))
    cache_dirty[:] = 0
    outflow_direction_dataset = gdal.Open(outflow_direction_uri)
    outflow_direction_band = outflow_direction_dataset.GetRasterBand(1)
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

    cdef int current_index
    cdef int old_row_index
    cdef int current_row
    cdef int current_col
    cdef int neighbor_direction
    cdef int neighbor_row
    cdef int neighbor_col
    cdef double absorption_rate
    cdef double outflow_weight
    cdef double in_flux
    cdef int cache_row_offset, neighbor_row_index, cache_row_index, cache_row_tag

    cdef int absorb_source = (absorption_mode == 'source_and_flux')

    cdef int n_steps = 0
    while cells_to_process.size() > 0:
        n_steps += 1
        if n_steps % 100000 == 0:
            LOGGER.debug('Reporting every 100000 steps cells_to_process.size() = %d' % (cells_to_process.size()))
    
        current_index = cells_to_process.top()
        cells_to_process.pop()
        current_row = current_index / n_cols
        current_col = current_index % n_cols
        #see if we need to update the row cache
        for cache_row_offset in range(-1, 2):
            neighbor_row_index = current_row + cache_row_offset
            #see if that row is out of bounds
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                continue
            #otherwise check if the cache needs an update
            cache_row_index = neighbor_row_index % CACHE_ROWS
            cache_row_tag = neighbor_row_index / CACHE_ROWS
            
            if cache_tag[cache_row_index] == cache_row_tag:
                #cache is up to date, so skip
                continue
                
            #see if we need to save the cache
            if cache_dirty[cache_row_index]:
                old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
                loss_band.WriteArray(
                    loss_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                flux_band.WriteArray(
                    flux_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                cache_dirty[cache_row_index] = 0
                
            #load a new row
            flux_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=flux_cache[cache_row_index].reshape((1,n_cols)))
            loss_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=loss_cache[cache_row_index].reshape((1,n_cols)))
            absorption_rate_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=absorption_rate_cache[cache_row_index].reshape((1,n_cols)))
            source_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=source_cache[cache_row_index].reshape((1,n_cols)))
            outflow_direction_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=outflow_direction_cache[cache_row_index].reshape((1,n_cols)))
            outflow_weights_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=outflow_weights_cache[cache_row_index].reshape((1,n_cols)))
            if stream_band != None:
                stream_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=stream_cache[cache_row_index].reshape((1,n_cols)))
            else:
                stream_cache[:] = 0
            cache_tag[cache_row_index] = cache_row_tag
                
        cache_row_index = current_row % CACHE_ROWS
        
        #Ensure we are working on a valid pixel
        if (source_cache[cache_row_index, current_col] == source_nodata):
            flux_cache[cache_row_index, current_col] = 0.0
            loss_cache[cache_row_index, current_col] = 0.0
            cache_dirty[cache_row_index] = 1

        #We have real data that make the absorption array nodata sometimes
        #right now the best thing to do is treat it as 0.0 so everything else
        #routes
        if (absorption_rate_cache[cache_row_index, current_col] == 
            absorption_rate_nodata):
            absorption_rate_cache[cache_row_index, current_col] = 0.0

        if flux_cache[cache_row_index, current_col] == transport_nodata:
            if stream_cache[cache_row_index, current_col] == 0:
                flux_cache[cache_row_index, current_col] = source_cache[
                    cache_row_index, current_col]
            else:
                flux_cache[cache_row_index, current_col] = 0.0
            loss_cache[cache_row_index, current_col] = 0.0
            cache_dirty[cache_row_index] = 1
            if absorb_source:
                absorption_rate = (
                    absorption_rate_cache[cache_row_index, current_col])
                loss_cache[cache_row_index, current_col] = (
                    absorption_rate * flux_cache[cache_row_index, current_col])
                flux_cache[cache_row_index, current_col] *= (1 - absorption_rate)

        current_neighbor_index = cell_neighbor_to_process.top()
        cell_neighbor_to_process.pop()
        for direction_index in xrange(current_neighbor_index, 8):
            #get percent flow from neighbor to current cell
            cache_cache_neighbor_row = (
                cache_row_index+row_offsets[direction_index]) % CACHE_ROWS
            neighbor_row = current_row+row_offsets[direction_index]
            neighbor_col = current_col+col_offsets[direction_index]

            #See if neighbor out of bounds
            if (neighbor_row < 0 or neighbor_row >= n_rows or
                neighbor_col < 0 or neighbor_col >= n_cols):
                continue

            #if neighbor inflows
            neighbor_direction = (
                outflow_direction_cache[cache_cache_neighbor_row, neighbor_col])
            if neighbor_direction == outflow_direction_nodata:
                continue

            if (inflow_offsets[direction_index] != neighbor_direction and
                inflow_offsets[direction_index] != (neighbor_direction - 1) % 8):
                #then neighbor doesn't inflow into current cell
                continue

            #Calculate the outflow weight
            outflow_weight = outflow_weights_cache[cache_cache_neighbor_row, neighbor_col]
            
            if inflow_offsets[direction_index] == (neighbor_direction - 1) % 8:
                outflow_weight = 1.0 - outflow_weight

            if outflow_weight < 0.001:
                continue
            in_flux = flux_cache[cache_cache_neighbor_row, neighbor_col]

            if in_flux != transport_nodata:
                absorption_rate = (
                    absorption_rate_cache[cache_row_index, current_col])

                #If it's not a stream, route the flux normally
                if stream_cache[cache_row_index, current_col] == 0:
                    flux_cache[cache_row_index, current_col] += (
                        outflow_weight * in_flux * (1.0 - absorption_rate))

                    loss_cache[cache_row_index, current_col] += (
                        outflow_weight * in_flux * absorption_rate)
                else:
                    #Otherwise if it is a stream, all flux routes to the outlet
                    #we don't want it absorbed later
                    flux_cache[cache_row_index, current_col] = 0.0
                    loss_cache[cache_row_index, current_col] = 0.0
                cache_dirty[cache_row_index] = 1
            else:
                #we need to process the neighbor, remember where we were
                #then add the neighbor to the process stack
                cells_to_process.push(current_index)
                cell_neighbor_to_process.push(direction_index)

                #Calculating the flat index for the neighbor and starting
                #at it's neighbor index of 0
                #a global neighbor row needs to be calculated
                cells_to_process.push((current_row+row_offsets[direction_index]) * n_cols + neighbor_col)
                cell_neighbor_to_process.push(0)
                break

    LOGGER.info('Flushing remaining dirty cache to disk')
    #Write results to disk
    for cache_row_index in range(CACHE_ROWS):
        if cache_dirty[cache_row_index]:
            old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
            flux_band.WriteArray(
                flux_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
            loss_band.WriteArray(
                loss_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
            cache_dirty[cache_row_index] = 0

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
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flow_direction_window
    
    #This is the array that's used to keep track of the connections of the
    #current cell to those *inflowing* to the cell, thus the 8 directions
    cdef int n_cols, n_rows
    n_cols, n_rows = flow_direction_band.XSize, flow_direction_band.YSize
    
    cdef int outflow_direction_nodata = 9
    outflow_direction_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, outflow_direction_uri, 'GTiff',
        outflow_direction_nodata, gdal.GDT_Byte)
    outflow_direction_band = outflow_direction_dataset.GetRasterBand(1)
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_window = (
        numpy.empty((1, n_cols), dtype=numpy.int8))
    
    cdef double outflow_weights_nodata = -1.0
    outflow_weights_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, outflow_weights_uri, 'GTiff',
        outflow_weights_nodata, gdal.GDT_Float32)
    outflow_weights_band = outflow_weights_dataset.GetRasterBand(1)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights_window = (
        numpy.empty((1, n_cols), dtype=numpy.float32))

    #The number of diagonal offsets defines the neighbors, angle between them
    #and the actual angle to point to the neighbor
    cdef int n_neighbors = 8
    cdef double *angle_to_neighbor = [0.0, 0.7853981633974483, 1.5707963267948966, 2.356194490192345, 3.141592653589793, 3.9269908169872414, 4.71238898038469, 5.497787143782138]
    
    #diagonal offsets index is 0, 1, 2, 3, 4, 5, 6, 7 from the figure above
    cdef int *diagonal_offsets = [
        1, -n_cols+1, -n_cols, -n_cols-1, -1, n_cols-1, n_cols, n_cols+1]

    #Iterate over flow directions
    cdef int row_index, col_index, neighbor_direction_index
    cdef long current_index
    cdef double flow_direction, flow_angle_to_neighbor, outflow_weight
    
    for row_index in range(n_rows):
        
        outflow_direction_window[:] = outflow_direction_nodata
        outflow_weights_window[:] = outflow_weights_nodata
        
        flow_direction_window = flow_direction_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1)
    
        for col_index in range(n_cols):
            flow_direction = flow_direction_window[0, col_index]
            #make sure the flow direction is defined, if not, skip this cell
            if flow_direction == flow_direction_nodata:
                continue
            found = False
            for neighbor_direction_index in range(n_neighbors):
                flow_angle_to_neighbor = abs(
                    angle_to_neighbor[neighbor_direction_index] -
                    flow_direction)
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
                        neighbor_direction_index = \
                            (neighbor_direction_index + 1) % 8

                    outflow_direction_window[0, col_index] = neighbor_direction_index
                    outflow_weights_window[0, col_index] = outflow_weight

                    #we found the outflow direction
                    break
            if not found:
                LOGGER.debug('no flow direction found for %s %s' % \
                                 (row_index, col_index))
        outflow_weights_band.WriteArray(outflow_weights_window, xoff=0, yoff=row_index)
        outflow_direction_band.WriteArray(outflow_direction_window, xoff=0, yoff=row_index)

    LOGGER.info('Done calculating flow weights elapsed time %ss' % \
                    (time.clock()-start))


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
    start_time = time.clock()

    cdef double effect_nodata = -1.0
    raster_utils.new_raster_from_base_uri(
        sink_pixels_uri, effect_uri, 'GTiff', effect_nodata,
        gdal.GDT_Float32, fill_value=effect_nodata)
    effect_dataset = gdal.Open(effect_uri, gdal.GA_Update)
    effect_band = effect_dataset.GetRasterBand(1)

    cdef int n_cols = effect_dataset.RasterXSize
    cdef int n_rows = effect_dataset.RasterYSize
    
    cdef int CACHE_ROWS = 2**12
    if CACHE_ROWS > n_rows:
        CACHE_ROWS = n_rows

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] effect_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] sink_pixels_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.int8))
    sink_pixels_dataset = gdal.Open(sink_pixels_uri)
    sink_pixels_band = sink_pixels_dataset.GetRasterBand(1)
    cdef int sink_pixels_nodata = raster_utils.get_nodata_from_uri(
        sink_pixels_uri)
    
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] export_rate_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    export_rate_dataset = gdal.Open(export_rate_uri)
    export_rate_band = export_rate_dataset.GetRasterBand(1)
    cdef double export_rate_nodata = raster_utils.get_nodata_from_uri(
        export_rate_uri)
    
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.int8))
    outflow_direction_dataset = gdal.Open(outflow_direction_uri)
    outflow_direction_band = outflow_direction_dataset.GetRasterBand(1)
    cdef int outflow_direction_nodata = raster_utils.get_nodata_from_uri(
        outflow_direction_uri)
    
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    outflow_weights_dataset = gdal.Open(outflow_weights_uri)
    outflow_weights_band = outflow_weights_dataset.GetRasterBand(1)
    cdef double outflow_weights_nodata = raster_utils.get_nodata_from_uri(
        outflow_weights_uri)
    
    #Diagonal offsets are based off the following index notation for neighbors
    #    3 2 1
    #    4 p 0
    #    5 6 7

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]

    cdef int index, row_index, col_index, cache_row_index, neighbor_row_index, cache_neighbor_row_index, neighbor_col_index, neighbor_index, neighbor_outflow_direction, cache_row_offset, old_row_index
    cdef double outflow_weight, neighbor_outflow_weight
    
    cdef numpy.ndarray[numpy.npy_int32, ndim=1] cache_tag = (
        numpy.empty((CACHE_ROWS,), dtype=numpy.int32))
    #initially nothing is loaded in the cache, use -1 to indicate that as a tag
    cache_tag[:] = -1
    cdef numpy.ndarray[numpy.npy_byte, ndim=1] cache_dirty = (
        numpy.zeros((CACHE_ROWS,), dtype=numpy.int8))
    cache_dirty[:] = 0
    
    
    cdef queue[int] process_queue
    #Queue the sinks
    for row_index in xrange(n_rows):
        effect_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols,
            win_ysize=1, buf_obj=effect_cache[0].reshape((1,n_cols)))
        sink_pixels_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols,
            win_ysize=1, buf_obj=sink_pixels_cache[0].reshape((1,n_cols)))
        for col_index in xrange(n_cols):
            if sink_pixels_cache[0, col_index] == 1:
                effect_cache[0, col_index] = 1.0
                process_queue.push(row_index * n_cols + col_index)
        effect_band.WriteArray(
            effect_cache[0].reshape((1,n_cols)), xoff=0, yoff=row_index)

    while process_queue.size() > 0:
        index = process_queue.front()
        process_queue.pop()
        row_index = index / n_cols
        col_index = index % n_cols

        for cache_row_offset in range(-1, 2):
            neighbor_row_index = row_index + cache_row_offset
            #see if that row is out of bounds
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                continue
            #otherwise check if the cache needs an update
            cache_row_index = neighbor_row_index % CACHE_ROWS
            cache_row_tag = neighbor_row_index / CACHE_ROWS
            
            if cache_tag[cache_row_index] == cache_row_tag:
                #cache is up to date, so skip
                continue
                
            #see if we need to save the cache
            if cache_dirty[cache_row_index]:
                old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
                effect_band.WriteArray(
                    effect_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                cache_dirty[cache_row_index] = 0
                
            #load a new row
            sink_pixels_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=sink_pixels_cache[cache_row_index].reshape((1,n_cols)))
            export_rate_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=export_rate_cache[cache_row_index].reshape((1,n_cols)))
            outflow_direction_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=outflow_direction_cache[cache_row_index].reshape((1,n_cols)))
            outflow_weights_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=outflow_weights_cache[cache_row_index].reshape((1,n_cols)))
            effect_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=effect_cache[cache_row_index].reshape((1,n_cols)))
            cache_tag[cache_row_index] = cache_row_tag
                
        cache_row_index = row_index % CACHE_ROWS
        
        if export_rate_cache[cache_row_index, col_index] == export_rate_nodata:
            continue

        #if the outflow weight is nodata, then not a valid pixel
        outflow_weight = outflow_weights_cache[cache_row_index, col_index]
        if outflow_weight == outflow_weights_nodata:
            continue

        for neighbor_index in range(8):
            cache_neighbor_row_index = (cache_row_index + row_offsets[neighbor_index]) % CACHE_ROWS
            neighbor_row_index = row_index + row_offsets[neighbor_index]
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                #out of bounds
                continue

            neighbor_col_index = col_index + col_offsets[neighbor_index]
            if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                #out of bounds
                continue

            if sink_pixels_cache[cache_neighbor_row_index, neighbor_col_index] == 1:
                #it's already a sink
                continue

            neighbor_outflow_direction = (
                outflow_direction_cache[cache_neighbor_row_index, neighbor_col_index])
            #if the neighbor is no data, don't try to set that
            if neighbor_outflow_direction == outflow_direction_nodata:
                continue

            neighbor_outflow_weight = (
                outflow_weights_cache[cache_neighbor_row_index, neighbor_col_index])
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
                if effect_cache[cache_neighbor_row_index, neighbor_col_index] == effect_nodata:
                    process_queue.push(neighbor_row_index * n_cols + neighbor_col_index)
                    effect_cache[cache_neighbor_row_index, neighbor_col_index] = 0.0

                #the percent of the pixel upstream equals the current percent 
                #times the percent flow to that pixels times the 
                effect_cache[cache_neighbor_row_index, neighbor_col_index] += (
                    effect_cache[cache_row_index, col_index] *
                    neighbor_outflow_weight *
                    export_rate_cache[cache_row_index, col_index])
                cache_dirty[cache_neighbor_row_index] = 1

    for cache_row_index in range(CACHE_ROWS):
        if cache_dirty[cache_row_index]:
            old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
            effect_band.WriteArray(
                effect_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
            cache_dirty[cache_row_index] = 0
                
    LOGGER.info('Done calculating percent to sink elapsed time %ss' % \
                    (time.clock() - start_time))


cdef struct Row_Col_Weight_Tuple:
    int row_index
    int col_index
    int weight

    
cdef int _is_flat(int row_index, int col_index, int n_rows, int n_cols, int* row_offsets, int *col_offsets, numpy.ndarray[numpy.npy_float32, ndim=2] dem_array, float nodata_value):
    cdef int neighbor_row_index, neighbor_col_index
    if (row_index <= 0 or row_index >= n_rows - 1 or 
        col_index <= 0 or col_index >= n_cols - 1):
        return 0
    if dem_array[row_index, col_index] == nodata_value: return 0    
    for neighbor_index in xrange(8):
        neighbor_row_index = row_index + row_offsets[neighbor_index]            
        neighbor_col_index = col_index + col_offsets[neighbor_index]            
        
        if dem_array[neighbor_row_index, neighbor_col_index] == nodata_value:
            return 0
        if dem_array[neighbor_row_index, neighbor_col_index] < dem_array[row_index, col_index]:
            return 0
    return 1
              

cdef int _is_sink(
    int row_index, int col_index, int n_rows, int n_cols, int* row_offsets,
    int *col_offsets, numpy.ndarray[numpy.npy_float32, ndim=2] dem_array, float nodata_value):

    cdef int neighbor_row_index, neighbor_col_index
    if dem_array[row_index, col_index] == nodata_value: return 0
    
    if _is_flat(row_index, col_index, n_rows, n_cols, row_offsets,
                col_offsets, dem_array, nodata_value):
        return 0
    
    for neighbor_index in xrange(8):
        neighbor_row_index = row_index + row_offsets[neighbor_index]
        if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
            continue
        neighbor_col_index = col_index + col_offsets[neighbor_index]
        if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
            continue
            
        if (dem_array[neighbor_row_index, neighbor_col_index] ==
            dem_array[row_index, col_index] and
            _is_flat(neighbor_row_index, neighbor_col_index,
                     n_rows, n_cols, row_offsets, col_offsets,
                     dem_array, nodata_value)):
            return 1
    return 0

    
cdef void _build_flat_set(
    band, float nodata_value, int n_rows, int n_cols,
    int *row_offsets, int *col_offsets, c_set[int] *flat_set):

    cdef double dem_value, neighbor_dem_value
    #get the ceiling of the integer division
    cdef int *allowed_neighbor = [1, 1, 1, 1, 1, 1, 1, 1]

    cdef int row_index, col_index
    cdef int ul_row_index = 0, ul_col_index = 0
    cdef int lr_col_index = n_cols, lr_row_index = 3
    

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_array = band.ReadAsArray(
        xoff=ul_col_index, yoff=ul_row_index, win_xsize=n_cols,
        win_ysize=3)
    cdef int y_offset, local_y_offset
    
    #not flat on the edges of the raster, could be a sink
    for row_index in range(1, n_rows-1):
        #Grab three rows at a time and be careful of the top and bottom edge
        y_offset = row_index - 1
            
        band.ReadAsArray(
            xoff=0, yoff=y_offset, win_xsize=n_cols,
            win_ysize=3, buf_obj=dem_array)

        #not flat on the edges of the raster
        for col_index in range(1, n_cols - 1):
            dem_value = dem_array[1, col_index]
            if dem_value == nodata_value:
                continue

            #check all the neighbors, if nodata or lower, this isn't flat
            for neighbor_index in xrange(8):
                neighbor_row_index = 1 + row_offsets[neighbor_index]
                neighbor_col_index = col_index + col_offsets[neighbor_index]
                
                neighbor_dem_value = dem_array[neighbor_row_index, neighbor_col_index]
                if neighbor_dem_value < dem_value or neighbor_dem_value == nodata_value:
                    break
            else:
                #This is a flat element
                deref(flat_set).insert(row_index * n_cols + col_index)
    
    cdef int w_row_index, w_col_index

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

    dem_ds = gdal.Open(dem_uri, gdal.GA_ReadOnly)
    cdef int n_rows = dem_ds.RasterYSize
    cdef int n_cols = dem_ds.RasterXSize
        
    #copy the dem to a different dataset so we know the type
    dem_band = dem_ds.GetRasterBand(1)
    cdef double nodata_value = raster_utils.get_nodata_from_uri(dem_uri)
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_out_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        INF)
    dem_out_ds = gdal.Open(dem_out_uri, gdal.GA_Update)
    dem_out_band = dem_out_ds.GetRasterBand(1)
    cdef int row_index, col_index
    for row_index in range(n_rows):
        dem_out_array = dem_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1)
        dem_out_band.WriteArray(dem_out_array, xoff=0, yoff=row_index)

    LOGGER.info('identify flat cells')
    
    #search for flat cells
    #search for flat areas, iterate through the array 3 rows at a time
    cdef c_set[int] flat_set
    cdef c_set[int] flat_set_for_looping
    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    _build_flat_set(dem_out_band, nodata_value, n_rows, n_cols, row_offsets, col_offsets, &flat_set)
    LOGGER.debug("flat_set size %d" % (flat_set.size()))
    cdef int flat_index
    #make a copy of the flat index so we can break it down for iteration but
    #keep the old one for rapid testing of flat cells
    for flat_index in flat_set:
        flat_set_for_looping.insert(flat_set_for_looping.end(), flat_index)

    LOGGER.info('finished flat cell detection, now identify plateaus')

    dem_sink_offset_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_sink_offset_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        INF)
    dem_sink_offset_ds = gdal.Open(dem_sink_offset_uri, gdal.GA_Update)
    dem_sink_offset_band = dem_sink_offset_ds.GetRasterBand(1)

    dem_edge_offset_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_edge_offset_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        INF)
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
    
    cdef int CACHE_ROWS = 2**12
    if CACHE_ROWS > n_rows:
        CACHE_ROWS = n_rows
    cdef numpy.ndarray[numpy.npy_float, ndim=2] dem_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_float, ndim=2] dem_sink_offset_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_float, ndim=2] dem_edge_offset_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_int32, ndim=1] cache_tag = (
        numpy.empty((CACHE_ROWS,), dtype=numpy.int32))
    #initially nothing is loaded in the cache, use -1 to indicate that as a tag
    cache_tag[:] = -1
    cdef numpy.ndarray[numpy.npy_byte, ndim=1] cache_dirty = (
        numpy.zeros((CACHE_ROWS,), dtype=numpy.int8))

    cdef Row_Col_Weight_Tuple current_cell_tuple
    cdef int cache_row_offset, cache_row_index, cache_row_tag
    cdef int neighbor_cache_row_index, neighbor_row_index, neighbor_col_index
    
    cdef Row_Col_Weight_Tuple t
    cdef int weight, region_count = 0

    while flat_set_for_looping.size() > 0:
        #This pulls the flat index out for looping
        flat_index = deref(flat_set_for_looping.begin())
        flat_set_for_looping.erase(flat_index)
        
        row_index = flat_index / n_cols
        
        #see if we need to update the row cache
        for cache_row_offset in range(-1, 2):
            neighbor_row_index = row_index + cache_row_offset
            #see if that row is out of bounds
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                continue
            #otherwise check if the cache needs an update
            cache_row_index = neighbor_row_index % CACHE_ROWS
            cache_row_tag = neighbor_row_index / CACHE_ROWS
            
            if cache_tag[cache_row_index] == cache_row_tag:
                #cache is up to date, so skip
                continue
            
            #see if we need to save the cache
            if cache_dirty[cache_row_index]:
                old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
                dem_sink_offset_band.WriteArray(
                    dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                dem_edge_offset_band.WriteArray(
                    dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                cache_dirty[cache_row_index] = 0
                
            #load a new row
            cache_tag[cache_row_index] = cache_row_tag
            dem_out_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=dem_cache[cache_row_index].reshape((1,n_cols)))
            dem_sink_offset_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)))
            dem_edge_offset_band.ReadAsArray(
                xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                win_ysize=1, buf_obj=dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)))
        
        cache_row_index = row_index % CACHE_ROWS
        col_index = flat_index % n_cols
        if dem_cache[cache_row_index, col_index] == nodata_value:
            continue

        #see if we already processed this cell looking for edges and sinks
        if dem_sink_offset_cache[cache_row_index, col_index] != INF:
            continue

        #mark the cell as visited
        dem_sink_offset_cache[cache_row_index, col_index] = MAX_DISTANCE
        cache_dirty[cache_row_index] = 1 #just changed dem_sink_offset, we're dirty
        flat_region_queue.push(flat_index)
        region_count += 1
        if region_count % 100000 == 0:
            LOGGER.info('working on plateau #%d (reports every 100000 plateaus) number of flat cells remaining %d' % (region_count, flat_set_for_looping.size()))
        
        #Visit a flat region and search for sinks and edges
        while flat_region_queue.size() > 0:
            flat_index = flat_region_queue.front()
            flat_set_for_looping.erase(flat_index)
            flat_region_queue.pop()
            
            row_index = flat_index / n_cols
            
            #see if we need to update the row cache
            for cache_row_offset in range(-1, 2):
                neighbor_row_index = row_index + cache_row_offset
                #see if that row is out of bounds
                if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                    continue
                #otherwise check if the cache needs an update
                cache_row_index = neighbor_row_index % CACHE_ROWS
                cache_row_tag = neighbor_row_index / CACHE_ROWS
                
                if cache_tag[cache_row_index] == cache_row_tag:
                    #cache is up to date, so skip
                    continue
                    
                #see if we need to save the cache
                if cache_dirty[cache_row_index]:
                    old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
                    dem_sink_offset_band.WriteArray(
                        dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                    dem_edge_offset_band.WriteArray(
                        dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                    cache_dirty[cache_row_index] = 0
                    
                #load a new row
                cache_tag[cache_row_index] = cache_row_tag
                dem_out_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_cache[cache_row_index].reshape((1,n_cols)))
                dem_sink_offset_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)))
                dem_edge_offset_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)))

            cache_row_index = row_index % CACHE_ROWS
            col_index = flat_index % n_cols

            #test if this point is an edge
            #if it's flat it could be an edge
            if flat_set.find(flat_index) != flat_set.end():
                for neighbor_index in xrange(8):
                    neighbor_row_index = row_index + row_offsets[neighbor_index]
                    neighbor_col_index = col_index + col_offsets[neighbor_index]
                    
                    if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                        continue
                    if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                        continue

                    neighbor_cache_row_index = neighbor_row_index % CACHE_ROWS
                    
                    #ignore nodata
                    if (dem_cache[neighbor_cache_row_index, neighbor_col_index] ==
                        nodata_value):
                        continue

                    #if we don't abut a higher pixel then skip
                    if (dem_cache[neighbor_cache_row_index, neighbor_col_index] <=
                        dem_cache[cache_row_index, col_index]):
                        continue

                    #otherwise we're next to an uphill pixel, that means we're an edge
                    t = Row_Col_Weight_Tuple(row_index, col_index, 0)
                    edge_queue.push(t)
                    dem_edge_offset_cache[cache_row_index, col_index] = 0
                    cache_dirty[cache_row_index] = 1
                    break
            else:
                #it's been pushed onto the plateau queue, so we know it's in the same
                #region, but it's not flat, so it must be a sink
                t = Row_Col_Weight_Tuple(row_index, col_index, 0)
                sink_queue.push(t)
                dem_sink_offset_cache[cache_row_index, col_index] = 0
                cache_dirty[cache_row_index] = 1

            #loop neighbor and test to see if we can extend
            for neighbor_index in xrange(8):
                neighbor_row_index = row_index + row_offsets[neighbor_index]                
                if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                    continue
                    
                neighbor_col_index = col_index + col_offsets[neighbor_index]
                if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                    continue

                neighbor_cache_row_index = neighbor_row_index % CACHE_ROWS
                    
                #skip if we're not on the same plateau
                if (dem_cache[neighbor_cache_row_index, neighbor_col_index] !=
                    dem_cache[cache_row_index, col_index]):
                    continue

                #ignore if we've already visited the neighbor
                if dem_sink_offset_cache[neighbor_cache_row_index, neighbor_col_index] != INF:
                    continue

                #otherwise extend our search
                flat_region_queue.push(
                    (row_index + row_offsets[neighbor_index]) * n_cols +
                    col_index + col_offsets[neighbor_index])
                dem_sink_offset_cache[neighbor_cache_row_index, neighbor_col_index] = MAX_DISTANCE
                cache_dirty[neighbor_cache_row_index] = 1

        #process sink offsets for region
        while sink_queue.size() > 0:
            sink_cell_hits += 1
            current_cell_tuple = sink_queue.front()
            sink_queue.pop()
            
            row_index = current_cell_tuple.row_index
            col_index = current_cell_tuple.col_index
            weight = current_cell_tuple.weight

            #see if we need to update the row cache
            for cache_row_offset in range(-1, 2):
                neighbor_row_index = row_index + cache_row_offset
                #see if that row is out of bounds
                if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                    continue
                #otherwise check if the cache needs an update
                cache_row_index = neighbor_row_index % CACHE_ROWS
                cache_row_tag = neighbor_row_index / CACHE_ROWS
                
                if cache_tag[cache_row_index] == cache_row_tag:
                    #cache is up to date, so skip
                    continue
                    
                #see if we need to save the cache
                if cache_dirty[cache_row_index]:
                    old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
                    dem_sink_offset_band.WriteArray(
                        dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                    dem_edge_offset_band.WriteArray(
                        dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                    cache_dirty[cache_row_index] = 0
                    
                #load a new row
                cache_tag[cache_row_index] = cache_row_tag
                dem_out_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_cache[cache_row_index].reshape((1,n_cols)))
                dem_sink_offset_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)))
                dem_edge_offset_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)))

            cache_row_index = row_index % CACHE_ROWS

            for neighbor_index in xrange(8):
                neighbor_row_index = row_index + row_offsets[neighbor_index]
                if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                    continue
                neighbor_col_index = col_index + col_offsets[neighbor_index]
                if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                    continue
                
                flat_index = neighbor_row_index * n_cols + neighbor_col_index
                #If the neighbor is not flat then skip
                if flat_set.find(flat_index) == flat_set.end():
                    continue

                neighbor_cache_row_index = neighbor_row_index % CACHE_ROWS
                
                #If the neighbor is at a different height, then skip
                if (dem_cache[cache_row_index, col_index] != 
                    dem_cache[neighbor_cache_row_index, neighbor_col_index]):
                    continue

                #if the neighbor's weight is less than the weight we'd project to it
                #no need to update it, we're done w/ that direction
                if (dem_sink_offset_cache[neighbor_cache_row_index, neighbor_col_index] <=
                    weight + 1):
                    continue

                #otherwise, project onto the neighbor
                t = Row_Col_Weight_Tuple(
                    neighbor_row_index, neighbor_col_index, weight + 1)
                sink_queue.push(t)
                dem_sink_offset_cache[neighbor_cache_row_index, neighbor_col_index] = weight + 1
                cache_dirty[neighbor_cache_row_index] = 1

        #process edge offsets for region
        while edge_queue.size() > 0:
            edge_cell_hits += 1
            current_cell_tuple = edge_queue.front()
            edge_queue.pop()
            
            row_index = current_cell_tuple.row_index
            col_index = current_cell_tuple.col_index
            weight = current_cell_tuple.weight

            #see if we need to update the row cache
            for cache_row_offset in range(-1, 2):
                neighbor_row_index = row_index + cache_row_offset
                #see if that row is out of bounds
                if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                    continue
                #otherwise check if the cache needs an update
                cache_row_index = neighbor_row_index % CACHE_ROWS
                cache_row_tag = neighbor_row_index / CACHE_ROWS
                
                if cache_tag[cache_row_index] == cache_row_tag:
                    #cache is up to date, so skip
                    continue
                    
                #see if we need to save the cache
                if cache_dirty[cache_row_index]:
                    old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
                    dem_sink_offset_band.WriteArray(
                        dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                    dem_edge_offset_band.WriteArray(
                        dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
                    cache_dirty[cache_row_index] = 0
                    
                #load a new row
                cache_tag[cache_row_index] = cache_row_tag
                dem_out_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_cache[cache_row_index].reshape((1,n_cols)))
                dem_sink_offset_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)))
                dem_edge_offset_band.ReadAsArray(
                    xoff=0, yoff=neighbor_row_index, win_xsize=n_cols,
                    win_ysize=1, buf_obj=dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)))

            cache_row_index = row_index % CACHE_ROWS

            for neighbor_index in xrange(8):
                neighbor_row_index = row_index + row_offsets[neighbor_index]
                neighbor_col_index = col_index + col_offsets[neighbor_index]
                if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                    continue
                if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                    continue
                
                neighbor_cache_row_index = neighbor_row_index % CACHE_ROWS
                
                #If the neighbor is not at the same height, skip
                if (dem_cache[cache_row_index, col_index] !=
                    dem_cache[neighbor_cache_row_index, neighbor_col_index]):
                    continue

                flat_index = neighbor_row_index * n_cols + neighbor_col_index
                #If the neighbor is not flat then skip
                if flat_set.find(flat_index) == flat_set.end():
                    continue

                #if the neighbors weight is less than the weight we'll project, skip
                if dem_edge_offset_cache[neighbor_cache_row_index, neighbor_col_index] <= weight + 1:
                    continue

                dem_edge_offset_cache[neighbor_cache_row_index, neighbor_col_index] = weight + 1
                cache_dirty[neighbor_cache_row_index] = 1
                #otherwise project the current weight to the neighbor
                t = Row_Col_Weight_Tuple(neighbor_row_index, neighbor_col_index, weight + 1)
                edge_queue.push(t)
                
    LOGGER.info('saving back the dirty cache')
    
    #see if we need to save the cache
    for cache_row_index in range(CACHE_ROWS):
        if cache_dirty[cache_row_index]:
            old_row_index = cache_tag[cache_row_index] * CACHE_ROWS + cache_row_index
            dem_sink_offset_band.WriteArray(
                dem_sink_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
            dem_edge_offset_band.WriteArray(
                dem_edge_offset_cache[cache_row_index].reshape((1,n_cols)), xoff=0, yoff=old_row_index)
            cache_dirty[cache_row_index] = 0
                
                
    LOGGER.debug('region_count: %d' % region_count)
    LOGGER.info('edge cell hits %d' % edge_cell_hits)
    LOGGER.info('sink cell hits %d' % sink_cell_hits)
    
    #Find max distance
    LOGGER.debug('calculating max distance')
    cdef numpy.ndarray[numpy.npy_float, ndim=2] row_array = (
        numpy.empty((1, n_cols), dtype=numpy.float32))
    cdef int max_distance = -1
    
    for row_index in range(n_rows):
        dem_edge_offset_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1,
            buf_obj=row_array)
        try:
            max_distance = max(
                max_distance, numpy.max(row_array[row_array!=INF]))
        except ValueError:
            #no non-infinity elements, that's normal
            pass
    
    #Add the final offsets to the dem array
    dem_array = numpy.empty((1, n_cols), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float, ndim=2] dem_sink_offset_array = (
        numpy.empty((1, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_float, ndim=2] dem_edge_offset_array = (
        numpy.empty((1, n_cols), dtype=numpy.float32))
    for row_index in range(n_rows):
        dem_out_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1,
            buf_obj=dem_array)
        dem_sink_offset_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1,
            buf_obj=dem_sink_offset_array)
        dem_edge_offset_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1,
            buf_obj=dem_edge_offset_array)
        mask_array = ((dem_sink_offset_array != INF) &
                      (dem_edge_offset_array != INF))
        dem_array[mask_array] = (dem_array[mask_array] + 
                                 (dem_sink_offset_array[mask_array] * 2.0 +
                                  (max_distance+1-dem_edge_offset_array[mask_array])) / 10000.0)
        dem_out_band.WriteArray(dem_array, xoff=0, yoff=row_index)

    
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
        flow_direction_max_slope, slope_max, dem_nodata, nodata_flow

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
    #we'll write into this array and save every row
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flow_array = numpy.empty(
        (1, n_cols), dtype=numpy.float32)
    
    LOGGER.info("calculating d-inf per pixel flows")
    
    cdef int row_offset, col_offset

    cdef int e_0_row_index, e_0_col_index, e_1_row_index, e_1_col_index, e_2_row_index, e_2_col_index
    cdef float[:, :] dem_window
    cdef int y_offset, local_y_offset
    cdef int max_downhill_facet
    cdef double lowest_dem, dem_value, flow_direction_value
    cdef queue[int] unresolved_cells
    
    #flow not defined on the edges, so just go 1 row in 
    for row_index in range(n_rows):
        #We load 3 rows at a time
        y_offset = row_index - 1
        local_y_offset = 1
        
        if row_index == 0:
            y_offset = 0
            local_y_offset = 0
        if row_index == n_rows - 1:
            y_offset = n_rows - 3
            local_y_offset = 2
        
        dem_window = dem_band.ReadAsArray(
            xoff=0, yoff=y_offset, win_xsize=n_cols, win_ysize=3)
        
        #clear out the flow array from the previous loop
        flow_array[:] = flow_nodata
        #flow not defined on the edges, so just go 1 col in 
        for col_index in range(n_cols):

            e_0_row_index = e_0_offsets[0] + local_y_offset
            e_0_col_index = e_0_offsets[1] + col_index
            e_0 = dem_window[e_0_row_index, e_0_col_index]

            #If we're on a nodata pixel, set the flow to nodata and skip
            if dem_window[local_y_offset, col_index] == dem_nodata:
                continue
                
            max_downhill_facet = -1
            lowest_dem = e_0
            #we have a special case if we're on the border of the raster
            if (col_index == 0 or col_index == n_cols - 1 or 
                row_index == 0 or row_index == n_rows - 1):
                #loop through the neighbor edges, and manually set a direction
                for facet_index in range(8):
                    e_1_row_index = row_offsets[facet_index] + local_y_offset
                    e_1_col_index = col_offsets[facet_index] + col_index
                    if (e_1_col_index == -1 or e_1_col_index == n_cols or
                        e_1_row_index == -1 or e_1_row_index == 3):
                        continue
                    e_1 = dem_window[e_1_row_index, e_1_col_index]
                    if e_1 == dem_nodata:
                        continue
                    if e_1 < lowest_dem:
                        lowest_dem = e_1
                        max_downhill_facet = facet_index
                        
                if max_downhill_facet != -1:
                    flow_array[0, col_index] = (
                        3.14159265 / 4.0 * max_downhill_facet)
                else:
                    #we need to point to the left or right
                    if col_index == 0:
                        flow_array[0, col_index] = (
                            3.14159265 / 2.0 * 2)
                    elif col_index == n_cols - 1:
                        flow_array[0, col_index] = (
                            3.14159265 / 2.0 * 0)
                    elif row_index == 0:
                        flow_array[0, col_index] = (
                            3.14159265 / 2.0 * 1)
                    elif row_index == n_rows - 1:
                        flow_array[0, col_index] = (
                            3.14159265 / 2.0 * 3)
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
                e_1_row_index = e_1_offsets[facet_index * 2 + 0] + local_y_offset
                e_1_col_index = e_1_offsets[facet_index * 2 + 1] + col_index
                e_2_row_index = e_2_offsets[facet_index * 2 + 0] + local_y_offset
                e_2_col_index = e_2_offsets[facet_index * 2 + 1] + col_index

                e_1 = dem_window[e_1_row_index, e_1_col_index]
                e_2 = dem_window[e_2_row_index, e_2_col_index]

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
                    flow_array[0, col_index] = (
                        a_f[max_index] * flow_direction_max_slope +
                        a_c[max_index] * 3.14159265 / 2.0)
                else:
                    unresolved_cells.push(col_index + row_index * n_cols)
                #just in case we set 2pi rather than 0
                #if abs(flow_array[0, col_index] - 3.14159265 * 2.0) < 1e-10:
                #    flow_array[0, col_index]  = 0.0
            else:
                if max_downhill_facet != -1:
                    flow_array[0, col_index] = (
                        3.14159265 / 4.0 * max_downhill_facet)
                else:
                    unresolved_cells.push(col_index + row_index * n_cols)
        #save the current flow row
        flow_band.WriteArray(flow_array, 0, row_index)
    
    y_offset = -1
    cdef int dirty_cache = 0
    cdef queue[int] unresolved_cells_defer
    cdef int previous_unresolved_size = unresolved_cells.size()
    while unresolved_cells.size() > 0:
        flat_index = unresolved_cells.front()
        unresolved_cells.pop()
    
        row_index = flat_index / n_cols
        col_index = flat_index % n_cols
            
        #We load 3 rows at a time and we know unresolved directions can only
        #occur in the middle of the raster
        if row_index == 0 or row_index == n_rows - 1 or col_index == 0 or col_index == n_cols - 1:
            raise Exception('When resolving unresolved direction cells, encountered a pixel on the edge (%d, %d)' % (row_index, col_index))
        if y_offset != row_index - 1:
            if dirty_cache:
                flow_band.WriteArray(flow_array, 0, y_offset)
                dirty_cache = 0
            local_y_offset = 1
            y_offset = row_index - 1
            dem_window = dem_band.ReadAsArray(
                xoff=0, yoff=y_offset, win_xsize=n_cols, win_ysize=3)
            flow_array = flow_band.ReadAsArray(
                xoff=0, yoff=y_offset, win_xsize=n_cols, win_ysize=3)
                
        dem_value = dem_window[1, col_index]
        flow_direction_value = flow_array[1, col_index]
        
        for facet_index in range(8):
            e_1_row_index = row_offsets[facet_index] + local_y_offset
            e_1_col_index = col_offsets[facet_index] + col_index
            if (dem_window[e_1_row_index, e_1_col_index] == dem_value and
                flow_array[e_1_row_index, e_1_col_index] != flow_nodata):
                flow_array[1, col_index] = facet_index * 3.14159265 / 4.0
                dirty_cache = 1
                break
        else:        
            #maybe we can drain to nodata
            for facet_index in range(8):
                e_1_row_index = row_offsets[facet_index] + local_y_offset
                e_1_col_index = col_offsets[facet_index] + col_index
                if dem_window[e_1_row_index, e_1_col_index] == dem_nodata:
                    flow_array[1, col_index] = facet_index * 3.14159265 / 4.0
                    dirty_cache = 1
                    break
            else:
                #we couldn't resolve it, try again later
                unresolved_cells_defer.push(flat_index)
                
        if unresolved_cells.size() == 0:
            LOGGER.info('previous_unresolved_size %d' % previous_unresolved_size)
            LOGGER.info('unresolved_cells_defer.size() = %d' % unresolved_cells_defer.size())
            if unresolved_cells_defer.size() < previous_unresolved_size:
                previous_unresolved_size = unresolved_cells_defer.size()
                while unresolved_cells_defer.size() > 0:
                    unresolved_cells.push(unresolved_cells_defer.front())
                    unresolved_cells_defer.pop()

    while unresolved_cells_defer.size() > 0:
        flat_index = unresolved_cells_defer.front()
        unresolved_cells_defer.pop()
    
        row_index = flat_index / n_cols
        col_index = flat_index % n_cols
        #We load 3 rows at a time and we know unresolved directions can only
        #occur in the middle of the raster
        if row_index == 0 or row_index == n_rows - 1 or col_index == 0 or col_index == n_cols - 1:
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


        
    flow_band = None
    gdal.Dataset.__swig_destroy__(flow_direction_dataset)
    flow_direction_dataset = None
    raster_utils.calculate_raster_stats_uri(flow_direction_uri)


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
        
    cdef queue[int] visit_queue
    
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] buffer_array = (
        numpy.empty((1, n_cols), dtype=numpy.float32))
    
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
    outflow_direction_ds = gdal.Open(outflow_direction_uri)
    outflow_direction_band = outflow_direction_ds.GetRasterBand(1)
    
    cdef int outflow_direction_nodata = raster_utils.get_nodata_from_uri(
        outflow_direction_uri)
    
    cdef int CACHE_ROWS = 2**10
    if CACHE_ROWS > n_rows:
        CACHE_ROWS = n_rows
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.int8))
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] distance_cache = (
        numpy.empty((CACHE_ROWS, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_int32, ndim=1] cache_tag = (
        numpy.empty((CACHE_ROWS,), dtype=numpy.int32))
    #initially nothing is loaded in the cache, use -1 to indicate that as a tag
    cache_tag[:] = -1
    cdef numpy.ndarray[numpy.npy_byte, ndim=1] cache_dirty = (
        numpy.zeros((CACHE_ROWS,), dtype=numpy.int8))
    cache_dirty[:] = 0
    
    #build up the stream pixel indexes
    for row_index in range(n_rows):
        stream_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1,
            buf_obj=buffer_array)
        distance_cache[0, :] = distance_nodata
        for col_index in range(n_cols):
            if buffer_array[0, col_index] == 1:
                #it's a stream, remember that
                visit_queue.push(row_index * n_cols + col_index)
                distance_cache[0, col_index] = 0.0
        distance_band.WriteArray(
            distance_cache[0].reshape((1,n_cols)), xoff=0, yoff=row_index)
        
    LOGGER.info('number of stream pixels %d' % (visit_queue.size()))
    
    cdef int current_index, cache_row_offset, neighbor_row_index
    cdef int cache_row_index, cache_row_tag
    cdef int neighbor_outflow_direction, neighbor_index
    cdef int neighbor_col_index
    cdef float neighbor_outflow_weight, current_distance, cell_travel_distance
    cdef int it_flows_here
    cdef int step_count = 0
    while visit_queue.size() > 0:
        if step_count % 100000 == 0:
            LOGGER.info(
                'visit_queue on stream distance size: %d (reports every 100,000 steps)' %
                visit_queue.size())
        step_count += 1
        current_index = visit_queue.front()
        visit_queue.pop()
        
        row_index = current_index / n_cols
        col_index = current_index % n_cols
        #see if we need to update the row cache
        for cache_row_offset in range(-1, 2):
            neighbor_row_index = row_index + cache_row_offset
            #see if that row is out of bounds
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                continue
            #otherwise check if the cache needs an update
            cache_row_index = neighbor_row_index % CACHE_ROWS
            cache_row_tag = neighbor_row_index / CACHE_ROWS
            
            if cache_tag[cache_row_index] == cache_row_tag:
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
            cache_tag[cache_row_index] = cache_row_tag
                
        cache_row_index = row_index % CACHE_ROWS
        current_distance = distance_cache[cache_row_index, col_index]
        for neighbor_index in range(8):
            cache_neighbor_row_index = (
                cache_row_index + row_offsets[neighbor_index]) % CACHE_ROWS
            neighbor_row_index = row_index + row_offsets[neighbor_index]
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                #out of bounds
                continue

            neighbor_col_index = col_index + col_offsets[neighbor_index]
            if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                #out of bounds
                continue

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

            if (neighbor_outflow_direction - 1) % 8 == inflow_offsets[neighbor_index]:
                #the offset neighbor flows into this cell
                it_flows_here = True
                neighbor_outflow_weight = 1.0 - neighbor_outflow_weight
                
            if it_flows_here:
                if distance_cache[cache_neighbor_row_index, neighbor_col_index] == distance_nodata:
                    distance_cache[cache_neighbor_row_index, neighbor_col_index] = 0
                    visit_queue.push(
                        neighbor_row_index * n_cols + neighbor_col_index)
                cell_travel_distance = cell_size
                if neighbor_index % 2 == 1:
                    #it's a diagonal direction multiply by square root of 2
                    cell_travel_distance *= 1.4142135623730951
                
                distance_cache[cache_neighbor_row_index, neighbor_col_index] += (
                    current_distance + cell_travel_distance) * neighbor_outflow_weight
                cache_dirty[cache_neighbor_row_index] = 1
            
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
        os.remove(dataset_uri)
