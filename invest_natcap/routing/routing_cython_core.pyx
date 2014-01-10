import collections
import tempfile
import time
import logging
import sys
import tables

import numpy
cimport numpy
import scipy.sparse
import osgeo
from osgeo import gdal
from cython.operator cimport dereference as deref

from libcpp.stack cimport stack
from libcpp.queue cimport queue
from libc.math cimport atan
from libc.math cimport atan2
from libc.math cimport tan
from libc.math cimport sqrt

from invest_natcap import raster_utils



logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing cython core')

cdef double PI = 3.141592653589793238462643383279502884
cdef double EPS = 1e-6

cdef int MAX_WINDOW_SIZE = 2**13

def calculate_transport(
    outflow_direction_uri, outflow_weights_uri, sink_cell_set, source_uri,
    absorption_rate_uri, loss_uri, flux_uri, absorption_mode):
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
            traveling through each pixel
        absorption_mode - either 'flux_only' or 'source_and_flux'. For
            'flux_only' the outgoing flux is (in_flux * absorption + source).
            If 'source_and_flux' then the output flux 
            is (in_flux + source) * absorption.

        returns nothing"""

    #Calculate flow graph

    #Pass transport
    LOGGER.info('Processing transport through grid')
    start = time.clock()

    #Extract input datasets
    outflow_direction_dataset = gdal.Open(outflow_direction_uri)

    #Create memory mapped lookup arrays
    outflow_direction_data_file = tempfile.TemporaryFile()
    outflow_weights_data_file = tempfile.TemporaryFile()
    source_data_file = tempfile.TemporaryFile()
    absorption_rate_data_file = tempfile.TemporaryFile()

    outflow_direction_data_uri = raster_utils.temporary_filename()
    outflow_direction_carray = raster_utils.load_dataset_to_carray(
        outflow_direction_uri, outflow_direction_data_uri)        
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_array = (
        outflow_direction_carray[:])
    
    cdef int outflow_direction_nodata = raster_utils.get_nodata_from_uri(outflow_direction_uri)

    outflow_weights_data_uri = raster_utils.temporary_filename()
    outflow_weights_carray = raster_utils.load_dataset_to_carray(
        outflow_weights_uri, outflow_weights_data_uri)        
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights_array = (
        outflow_weights_carray[:])
    
    cdef float source_nodata = raster_utils.get_nodata_from_uri(source_uri)
    source_data_uri = raster_utils.temporary_filename()
    source_carray = raster_utils.load_dataset_to_carray(
        source_uri, source_data_uri)        
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] source_array = source_carray[:]
    
    cdef float absorption_nodata = raster_utils.get_nodata_from_uri(absorption_rate_uri)
    absorption_rate_data_uri = raster_utils.temporary_filename()
    absorption_rate_carray = raster_utils.load_dataset_to_carray(
        absorption_rate_uri, absorption_rate_data_uri)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] absorption_rate_array = absorption_rate_carray[:]
    
    #Create output arrays for loss and flux
    cdef int n_cols = outflow_direction_dataset.RasterXSize
    cdef int n_rows = outflow_direction_dataset.RasterYSize
    transport_nodata = -1.0

    loss_data_file = tempfile.TemporaryFile()
    flux_data_file = tempfile.TemporaryFile()

    
    loss_data_uri = raster_utils.temporary_filename()
    loss_carray = raster_utils.create_carray(loss_data_uri, tables.Float32Atom(), (n_rows, n_cols))
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] loss_array = loss_carray[:]
    
    flux_data_uri = raster_utils.temporary_filename()
    flux_carray = raster_utils.create_carray(flux_data_uri, tables.Float32Atom(), (n_rows, n_cols))
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flux_array = flux_carray[:]

    loss_array[:] = transport_nodata
    flux_array[:] = transport_nodata

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
    cdef int current_row
    cdef int current_col
    cdef int neighbor_direction
    cdef int neighbor_row
    cdef int neighbor_col
    cdef double absorption_rate
    cdef double outflow_weight
    cdef double in_flux

    cdef int absorb_source = (absorption_mode == 'source_and_flux')

    while cells_to_process.size() > 0:
        current_index = cells_to_process.top()
        cells_to_process.pop()
        current_row = current_index / n_cols
        current_col = current_index % n_cols

        #Ensure we are working on a valid pixel
        if (source_array[current_row, current_col] == source_nodata):
            flux_array[current_row, current_col] = 0.0
            loss_array[current_row, current_col] = 0.0

        #We have real data that make the absorption array nodata sometimes
        #right now the best thing to do is treat it as 0.0 so everything else
        #routes
        if (absorption_rate_array[current_row, current_col] == 
            absorption_nodata):
            absorption_rate_array[current_row, current_col] = 0.0

        if flux_array[current_row, current_col] == transport_nodata:
            flux_array[current_row, current_col] = source_array[
                current_row, current_col]
            loss_array[current_row, current_col] = 0.0
            if absorb_source:
                absorption_rate = (
                    absorption_rate_array[current_row, current_col])
                loss_array[current_row, current_col] = (
                    absorption_rate * flux_array[current_row, current_col])
                flux_array[current_row, current_col] *= (1 - absorption_rate)

        current_neighbor_index = cell_neighbor_to_process.top()
        cell_neighbor_to_process.pop()
        for direction_index in xrange(current_neighbor_index, 8):
            #get percent flow from neighbor to current cell

            neighbor_row = current_row+row_offsets[direction_index]
            neighbor_col = current_col+col_offsets[direction_index]

            #See if neighbor out of bounds
            if 0 < neighbor_row < 0 or neighbor_row >= n_rows or \
                    neighbor_col < 0 or neighbor_col >= n_cols:
                continue

            #if neighbor inflows
            neighbor_direction = \
                outflow_direction_array[neighbor_row, neighbor_col]
            if neighbor_direction == outflow_direction_nodata:
                continue

            if inflow_offsets[direction_index] != neighbor_direction and \
               inflow_offsets[direction_index] != (neighbor_direction - 1) % 8:
                #then neighbor doesn't inflow into current cell
                continue

            #Calculate the outflow weight
            outflow_weight = outflow_weights_array[neighbor_row, neighbor_col]
            if inflow_offsets[direction_index] == (neighbor_direction - 1) % 8:
                outflow_weight = 1.0 - outflow_weight

            #TODO: Make sure that there is outflow from the neighbor cell to the current one before processing
            if abs(outflow_weight) < 0.001:
                continue

            in_flux = flux_array[neighbor_row, neighbor_col]
            if in_flux != transport_nodata:
                absorption_rate = \
                    absorption_rate_array[current_row, current_col]

                flux_array[current_row, current_col] += (
                    outflow_weight * in_flux * (1.0 - absorption_rate))

                loss_array[current_row, current_col] += (
                    outflow_weight * in_flux * absorption_rate)
            else:
                #we need to process the neighbor, remember where we were
                #then add the neighbor to the process stack
                cells_to_process.push(current_index)
                cell_neighbor_to_process.push(direction_index)

                #Calculating the flat index for the neighbor and starting
                #at it's neighbor index of 0
                cells_to_process.push(neighbor_row * n_cols + neighbor_col)
                cell_neighbor_to_process.push(0)
                break

    LOGGER.info('Writing results to disk')
    #Write results to disk
    loss_dataset = raster_utils.new_raster_from_base(
        outflow_direction_dataset, loss_uri, 'GTiff', transport_nodata,
        gdal.GDT_Float32)
    flux_dataset = raster_utils.new_raster_from_base(
        outflow_direction_dataset, flux_uri, 'GTiff', transport_nodata,
        gdal.GDT_Float32)

    loss_band, _ = raster_utils.extract_band_and_nodata(loss_dataset)
    flux_band, _ = raster_utils.extract_band_and_nodata(flux_dataset)

    loss_band.WriteArray(loss_array)
    flux_band.WriteArray(flux_array)

    LOGGER.info('Done processing transport elapsed time %ss' %
                (time.clock() - start))


def calculate_flow_graph(
    flow_direction_uri, outflow_weights_uri, outflow_direction_uri,
    dem_uri=None):
    """This function calculates the flow graph from a d-infinity based
        flow algorithm to include including source/sink cells
        as well as a data structures to assist in walking up the flow graph.

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

        dem_uri - (optional) if present, returns a sink cell list sorted by
            "lowest" height to highest.  useful for flow accumulation sorting

        returns nothing"""

    LOGGER.info('Calculating flow graph')
    start = time.clock()

    #This is the array that's used to keep track of the connections of the
    #current cell to those *inflowing* to the cell, thus the 8 directions
    flow_direction_dataset = gdal.Open(flow_direction_uri)
    cdef double flow_direction_nodata
    flow_direction_band, flow_direction_nodata = \
        raster_utils.extract_band_and_nodata(flow_direction_dataset)

    cdef int n_cols, n_rows
    n_cols, n_rows = flow_direction_band.XSize, flow_direction_band.YSize

    outflow_weight_data_file = tempfile.TemporaryFile()
    
    outflow_weights_data_uri = raster_utils.temporary_filename()
    outflow_weights_carray = raster_utils.create_carray(
        outflow_weights_data_uri, tables.Float32Atom(), (n_rows, n_cols))
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights = (
        outflow_weights_carray[:])
    outflow_weights_nodata = -1.0
    outflow_weights[:] = outflow_weights_nodata

    outflow_direction_data_file = tempfile.TemporaryFile()

    outflow_direction_data_uri = raster_utils.temporary_filename()
    outflow_direction_carray = raster_utils.create_carray(
        outflow_direction_data_uri, tables.Int8Atom(), (n_rows, n_cols))
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction = outflow_direction_carray[:]
    outflow_direction_nodata = 9
    outflow_direction[:] = outflow_direction_nodata

    #The number of diagonal offsets defines the neighbors, angle between them
    #and the actual angle to point to the neighbor
    cdef int n_neighbors = 8
    cdef double *angle_to_neighbor = [0.0, 0.7853981633974483, 1.5707963267948966, 2.356194490192345, 3.141592653589793, 3.9269908169872414, 4.71238898038469, 5.497787143782138]

    flow_direction_memory_file = tempfile.TemporaryFile()
    flow_direction_data_uri = raster_utils.temporary_filename()
    flow_direction_carray = raster_utils.load_dataset_to_carray(
        flow_direction_uri, flow_direction_data_uri)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flow_direction_array = (
        flow_direction_carray[:])
    
    #diagonal offsets index is 0, 1, 2, 3, 4, 5, 6, 7 from the figure above
    cdef int *diagonal_offsets = \
        [1, -n_cols+1, -n_cols, -n_cols-1, -1, n_cols-1, n_cols, n_cols+1]

    #Iterate over flow directions
    cdef int row_index, col_index, neighbor_direction_index
    cdef long current_index
    cdef double flow_direction, flow_angle_to_neighbor, outflow_weight
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            flow_direction = flow_direction_array[row_index, col_index]
            #make sure the flow direction is defined, if not, skip this cell
            if flow_direction == flow_direction_nodata:
                continue
            current_index = row_index * n_cols + col_index
            found = False
            for neighbor_direction_index in range(n_neighbors):
                flow_angle_to_neighbor = abs(
                    angle_to_neighbor[neighbor_direction_index] -
                    flow_direction)
                if flow_angle_to_neighbor < PI/4.0:
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

                    outflow_direction[row_index, col_index] = \
                        neighbor_direction_index
                    outflow_weights[row_index, col_index] = outflow_weight

                    #There's flow from the current cell to the neighbor
                    #so figure out the neighbor then add to inflow set
                    outflow_index = current_index + \
                        diagonal_offsets[neighbor_direction_index]

                    #if there is non-zero flow to the next cell clockwise then
                    #add it to the inflow set
                    if outflow_weight != 1.0:
                        next_outflow_index = current_index + \
                            diagonal_offsets[(neighbor_direction_index + 1) % 8]

                    #we found the outflow direction
                    break
            if not found:
                LOGGER.debug('no flow direction found for %s %s' % \
                                 (row_index, col_index))

    #write outflow direction and weights
    outflow_weights_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, outflow_weights_uri, 'GTiff',
        outflow_weights_nodata, gdal.GDT_Float32)
    outflow_weights_band = outflow_weights_dataset.GetRasterBand(1)
    outflow_weights_band.WriteArray(outflow_weights)

    outflow_direction_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, outflow_direction_uri, 'GTiff',
        outflow_direction_nodata, gdal.GDT_Byte)
    outflow_direction_band = outflow_direction_dataset.GetRasterBand(1)
    outflow_direction_band.WriteArray(outflow_direction)

    LOGGER.debug("Calculating sink and source cells")

    LOGGER.debug('n_cols n_rows %s %s' % (n_cols, n_rows))

    LOGGER.info('Done calculating flow path elapsed time %ss' % \
                    (time.clock()-start))


def calculate_flow_direction(dem_uri, flow_direction_uri):
    """Calculates the flow direction of a landscape given its dem

        dem_uri - a URI to a GDAL dataset to the DEM that will be used to
            determine flow direction.
        flow_direction_uri - a URI to create a dataset that will be used
            to store the flow direction.
        inflow_direction_uri - a URI to a byte GDAL raster that's used
            to determine which neighbors inflow into the current cell

        returns nothing"""

    LOGGER.info('Calculate flow direction')
    start = time.clock()

    #Calcualte the d infinity flow direction
    flow_direction_inf(dem_uri, flow_direction_uri)

    LOGGER.info(
        'Done calculating d-infinity elapsed time %ss' % (time.clock() - start))
    

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
            eminating per pixel that will reach any sink pixel

        returns nothing"""

    LOGGER.info("calculating percent to sink")
    start_time = time.clock()

    sink_pixels_dataset = gdal.Open(sink_pixels_uri)

    cdef float effect_nodata = -1.0
    effect_dataset = raster_utils.new_raster_from_base(
        sink_pixels_dataset, effect_uri, 'GTiff', effect_nodata,
        gdal.GDT_Float32)

    cdef int n_cols = sink_pixels_dataset.RasterXSize
    cdef int n_rows = sink_pixels_dataset.RasterYSize

    sink_pixels_data_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] sink_pixels_array = raster_utils.load_memory_mapped_array(
        sink_pixels_uri, sink_pixels_data_file)

    outflow_direction_data_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_array = raster_utils.load_memory_mapped_array(
        outflow_direction_uri, outflow_direction_data_file)
    outflow_direction_dataset = gdal.Open(outflow_direction_uri)

    cdef int outflow_direction_nodata
    _, outflow_direction_nodata = raster_utils.extract_band_and_nodata(
        outflow_direction_dataset)

    outflow_weights_data_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights_array = raster_utils.load_memory_mapped_array(
        outflow_weights_uri, outflow_weights_data_file)
    outflow_weights_dataset = gdal.Open(outflow_weights_uri)

    cdef float outflow_weights_nodata
    _, outflow_weights_nodata = raster_utils.extract_band_and_nodata(
        outflow_weights_dataset)

    export_rate_data_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] export_rate_array = raster_utils.load_memory_mapped_array(
        export_rate_uri, export_rate_data_file)
    export_rate_dataset = gdal.Open(export_rate_uri)
    
    cdef float export_rate_nodata
    _, export_rate_nodata = raster_utils.extract_band_and_nodata(
        export_rate_dataset)

    effect_band, _ = raster_utils.extract_band_and_nodata(
        effect_dataset)

    effect_data_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] effect_array = numpy.memmap(
        effect_data_file, dtype=numpy.float32, mode='w+',
        shape=(n_rows, n_cols))
    effect_array[:] = effect_nodata

    #Diagonal offsets are based off the following index notation for neighbors
    #    3 2 1
    #    4 p 0
    #    5 6 7

    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    cdef int *inflow_offsets = [4, 5, 6, 7, 0, 1, 2, 3]

    process_stack = collections.deque()

    cdef int loop_col_index, loop_row_index, index, row_index, col_index, neighbor_row_index, neighbor_col_index, offset, outflow_direction, neighbor_index, neighbor_outflow_direction
    cdef float total_effect, outflow_weight, neighbor_outflow_weight, neighbor_effect, neighbor_export
    cdef float outflow_percent_list[2]

    process_queue = collections.deque()
    #Queue the sinks
    for col_index in xrange(n_cols):
        for row_index in xrange(n_rows):
            if sink_pixels_array[row_index, col_index] == 1:
                effect_array[row_index, col_index] = 1.0
                process_queue.appendleft(row_index * n_cols + col_index)

    while len(process_queue) > 0:
        index = process_queue.pop()
        row_index = index / n_cols
        col_index = index % n_cols

        if export_rate_array[row_index, col_index] == export_rate_nodata:
            continue

        #if the outflow weight is nodata, then not a valid pixel
        outflow_weight = outflow_weights_array[row_index, col_index]
        if outflow_weight == outflow_weights_nodata:
            continue

        for neighbor_index in range(8):
            neighbor_row_index = row_index + row_offsets[neighbor_index]
            if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
                #out of bounds
                continue

            neighbor_col_index = col_index + col_offsets[neighbor_index]
            if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
                #out of bounds
                continue

            if sink_pixels_array[neighbor_row_index, neighbor_col_index] == 1:
                #it's already a sink
                continue

            neighbor_outflow_direction = \
                outflow_direction_array[neighbor_row_index, neighbor_col_index]
            #if the neighbor is no data, don't try to set that
            if neighbor_outflow_direction == outflow_direction_nodata:
                continue

            neighbor_outflow_weight = outflow_weights_array[neighbor_row_index, neighbor_col_index]
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

            if abs(neighbor_outflow_weight) < EPS:
                #it doesn't flow here
                continue
                
            if it_flows_here:
                #If we haven't processed that effect yet, set it to 0 and append to the queue
                if effect_array[neighbor_row_index, neighbor_col_index] == effect_nodata:
                    process_queue.appendleft(neighbor_row_index * n_cols + neighbor_col_index)
                    effect_array[neighbor_row_index, neighbor_col_index] = 0.0

                effect_array[neighbor_row_index, neighbor_col_index] += \
                    effect_array[row_index, col_index] * \
                    neighbor_outflow_weight * \
                    export_rate_array[row_index, col_index]

    effect_band.WriteArray(effect_array, 0, 0)
    LOGGER.info('Done calculating percent to sink elapsed time %ss' % \
                    (time.clock() - start_time))


cdef struct Row_Col_Weight_Tuple:
    int row_index
    int col_index
    int weight

    
cdef int _is_flat(int row_index, int col_index, int n_rows, int n_cols, int* row_offsets, int *col_offsets, float[:, :] dem_array, float nodata_value):
    cdef int neighbor_row_index, neighbor_col_index
    if row_index <= 0 or row_index >= n_rows - 1 or col_index <= 0 or col_index >= n_cols - 1:
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
    int *col_offsets, float[:, :] dem_array, float nodata_value):

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

    
    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]

    dem_ds = gdal.Open(dem_uri, gdal.GA_ReadOnly)

    cdef int n_rows = dem_ds.RasterYSize
    cdef int n_cols = dem_ds.RasterXSize
    cdef queue[Row_Col_Weight_Tuple] sink_queue
    cdef int row_index, col_index, current_row_index, current_n_rows

    cdef float nodata_value = raster_utils.get_nodata_from_uri(dem_uri)

    #Identify sink cells
    LOGGER.info('identify sink cells')
    sink_cell_list = []
    cdef Row_Col_Weight_Tuple t
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_array

    cdef int weight, w_row_index, w_col_index
    cdef int row_window_size, col_window_size, ul_row_index, ul_col_index
    cdef int lr_col_index, lr_row_index, hits, misses, steps
    cdef int old_ul_row_index, old_ul_col_index, old_lr_row_index, old_lr_col_index
    
    row_window_size = 7
    col_window_size = n_cols
    ul_row_index = 0
    ul_col_index = 0
    lr_row_index = row_window_size
    lr_col_index = col_window_size

    #copy the dem to a copy so we know the type
    dem_band = dem_ds.GetRasterBand(1)
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_out_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        numpy.inf)
    dem_out_ds = gdal.Open(dem_out_uri, gdal.GA_Update)
    dem_out_band = dem_out_ds.GetRasterBand(1)
    for row_index in range(n_rows):
        dem_out_array = dem_band.ReadAsArray(
            xoff=0, yoff=row_index, win_xsize=n_cols, win_ysize=1)
        dem_out_band.WriteArray(dem_out_array, xoff=0, yoff=row_index)

    dem_array = numpy.empty((row_window_size, col_window_size), dtype=numpy.float32)
    dem_out_band.ReadAsArray(
        xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
        win_ysize=row_window_size, buf_obj=dem_array)

    hits = 0
    misses = 0

    col_index = 0
    for row_index in range(n_rows):
        if _update_window(
            row_index, col_index, &ul_row_index, &ul_col_index,
            &lr_row_index, &lr_col_index, n_rows, n_cols,
            row_window_size, col_window_size, 2):
            #need to reload the window
            misses += 1
            dem_out_band.ReadAsArray(
                xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
                win_ysize=row_window_size, buf_obj=dem_array)
        else:
            hits += 1
        w_row_index = row_index - ul_row_index
        for col_index in range(n_cols):
            w_col_index = col_index - ul_col_index
            if _is_sink(
                w_row_index, w_col_index, row_window_size, col_window_size,
                row_offsets, col_offsets, dem_array, nodata_value):
                t = Row_Col_Weight_Tuple(row_index, col_index, 0)
                sink_queue.push(t)

    LOGGER.info('calculate distances from sinks to other flat cells')
    LOGGER.info('sink queue size %s' % (sink_queue.size()))
    cdef Row_Col_Weight_Tuple current_cell_tuple
    
    #This is as big as the window will get
    row_window_size = MAX_WINDOW_SIZE
    col_window_size = row_window_size
    if row_window_size > n_rows:
        row_window_size = n_rows
    if col_window_size > n_cols:
        col_window_size = n_cols

    ul_row_index = 0
    ul_col_index = 0
    lr_row_index = row_window_size
    lr_col_index = col_window_size

    #Load the dem_offset raster/band/array
    dem_sink_offset_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_sink_offset_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        numpy.inf)
    dem_sink_offset_ds = gdal.Open(dem_sink_offset_uri, gdal.GA_Update)
    dem_sink_offset_band = dem_sink_offset_ds.GetRasterBand(1)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_sink_offset = (
        dem_sink_offset_band.ReadAsArray(
            xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
            win_ysize=row_window_size))
    dem_array = dem_out_band.ReadAsArray(
        xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
        win_ysize=row_window_size)

    hits = 0
    misses = 0
    steps = 0
    while sink_queue.size() > 0:
        if steps % 10000 == 0:
            LOGGER.debug("sink queue size: %d" % (sink_queue.size()))
        steps += 1
        current_cell_tuple = sink_queue.front()
        sink_queue.pop()
        row_index = current_cell_tuple.row_index
        col_index = current_cell_tuple.col_index
        weight = current_cell_tuple.weight

        old_ul_row_index = ul_row_index
        old_ul_col_index = ul_col_index
        old_lr_row_index = lr_row_index
        old_lr_col_index = lr_col_index
        
        if _update_window(
            row_index, col_index, &ul_row_index, &ul_col_index,
            &lr_row_index, &lr_col_index, n_rows, n_cols,
            row_window_size, col_window_size, 2):
            #need to reload the window
            misses += 1
            LOGGER.debug('miss')

            #write back the old window
            dem_sink_offset_band.WriteArray(
                dem_sink_offset, xoff=old_ul_col_index, yoff=old_ul_row_index)
            
            #load the new windows
            dem_out_band.ReadAsArray(
                xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
                win_ysize=row_window_size, buf_obj=dem_array)
            dem_sink_offset_band.ReadAsArray(
                xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
                win_ysize=row_window_size, buf_obj=dem_sink_offset)
        else:
            hits += 1

        w_row_index = row_index - ul_row_index
        w_col_index = col_index - ul_col_index

        if dem_sink_offset[w_row_index, w_col_index] < weight:
            continue
        dem_sink_offset[w_row_index, w_col_index] = weight

        for neighbor_index in xrange(8):
            neighbor_row_index = row_index + row_offsets[neighbor_index]
            neighbor_col_index = col_index + col_offsets[neighbor_index]

            w_neighbor_row_index = w_row_index + row_offsets[neighbor_index]
            w_neighbor_col_index = w_col_index + col_offsets[neighbor_index]

            if not _is_flat(
                w_neighbor_row_index, w_neighbor_col_index, row_window_size, col_window_size,
                row_offsets, col_offsets, dem_array, nodata_value):
                continue

            if (dem_sink_offset[w_neighbor_row_index, w_neighbor_col_index] <=
                weight + 1):
                continue
            if (dem_array[w_row_index, w_col_index] == 
                dem_array[w_neighbor_row_index, w_neighbor_col_index]):
                t = Row_Col_Weight_Tuple(
                    neighbor_row_index, neighbor_col_index, weight + 1)
                sink_queue.push(t)
                dem_sink_offset[w_neighbor_row_index, w_neighbor_col_index] = weight + 1

    #write back the remaning open window
    dem_sink_offset_band.WriteArray(
        dem_sink_offset, xoff=ul_col_index, yoff=ul_row_index)
    if hits+misses != 0:
        LOGGER.info("hits/misses %d/%d miss percent %.2f%%" %
                    (hits, misses, 100.0*misses/float(hits+misses)))

    LOGGER.info('calculate distances from edge to center of flat regions')
    edge_cell_list = []
    cdef queue[Row_Col_Weight_Tuple] edge_queue

    row_window_size = 5
    col_window_size = n_cols
    ul_row_index = 0
    ul_col_index = 0
    lr_row_index = row_window_size
    lr_col_index = col_window_size
    dem_array = dem_out_band.ReadAsArray(
        xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
        win_ysize=row_window_size)

    hits = 0
    misses = 0
    for row_index in range(1, n_rows - 1):
        if _update_window(
            row_index, col_index, &ul_row_index, &ul_col_index,
            &lr_row_index, &lr_col_index, n_rows, n_cols,
            row_window_size, col_window_size, 2):
            #need to reload the window
            misses += 1
            dem_out_band.ReadAsArray(
                xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
                win_ysize=row_window_size, buf_obj=dem_array)
        else:
            hits += 1
        w_row_index = row_index - ul_row_index

        for col_index in range(1, n_cols - 1):
            w_col_index = col_index - ul_col_index

            #only consider flat cells
            if w_col_index >= n_cols:
                LOGGER.error("warning w_col_index > n_cols %d %d" % (w_col_index, n_cols))
            if w_row_index >= n_rows:
                LOGGER.error("warning w_row_index > n_rows %d %d" % (w_row_index, n_rows))

            if not _is_flat(
                w_row_index, w_col_index, row_window_size, col_window_size,
                row_offsets, col_offsets, dem_array, nodata_value):
                continue
            for neighbor_index in xrange(8):
                w_neighbor_row_index = w_row_index + row_offsets[neighbor_index]
                w_neighbor_col_index = w_col_index + col_offsets[neighbor_index]

                if ((dem_array[w_neighbor_row_index, w_neighbor_col_index] != 
                    nodata_value) and
                    (dem_array[w_row_index, w_col_index] <
                     dem_array[w_neighbor_row_index, w_neighbor_col_index])):

                    t = Row_Col_Weight_Tuple(row_index, col_index, 0)
                    edge_queue.push(t)
                    break
    if hits+misses != 0:
        LOGGER.info("hits/misses %d/%d miss percent %.2f%%" %
                    (hits, misses, 100.0*misses/float(hits+misses)))

    #This is as big as the window will get
    row_window_size = MAX_WINDOW_SIZE
    col_window_size = row_window_size
    if row_window_size > n_rows:
        row_window_size = n_rows
    if col_window_size > n_cols:
        col_window_size = n_cols

    ul_row_index = 0
    ul_col_index = 0
    lr_row_index = row_window_size
    lr_col_index = col_window_size
 
    dem_edge_offset_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(
        dem_uri, dem_edge_offset_uri, 'GTiff', nodata_value, gdal.GDT_Float32,
        numpy.inf)
    dem_edge_offset_ds = gdal.Open(dem_edge_offset_uri, gdal.GA_Update)
    dem_edge_offset_band = dem_edge_offset_ds.GetRasterBand(1)
    cdef numpy.ndarray[numpy.npy_float, ndim=2] dem_edge_offset = (
        dem_edge_offset_band.ReadAsArray(
            xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
            win_ysize=row_window_size))
    dem_array = dem_out_band.ReadAsArray(
        xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
        win_ysize=row_window_size)
   
    hits = 0
    misses = 0
    steps = 0
    while edge_queue.size() > 0:
        if steps % 10000 == 0:
            LOGGER.debug("edge queue size: %d" % (edge_queue.size()))
        steps += 1
        current_cell_tuple = edge_queue.front()
        edge_queue.pop()
        row_index = current_cell_tuple.row_index
        col_index = current_cell_tuple.col_index
        weight = current_cell_tuple.weight

        if (((row_index < ul_row_index + 2) and (ul_row_index > 0))  or
            ((row_index >= lr_row_index - 2) and (lr_row_index < n_rows - 1)) or
            ((col_index < ul_col_index + 2) and (ul_col_index > 0)) or
            ((col_index >= lr_col_index - 2) and (lr_col_index < n_cols - 1))):

            #need to reload the window
            misses += 1
            LOGGER.debug('miss')

            #save edge offset off
            dem_edge_offset_band.WriteArray(
                dem_edge_offset, xoff=old_ul_col_index, yoff=old_ul_row_index)

            #Get a window centered on the current pixel
            ul_row_index = row_index-(row_window_size/2)
            lr_row_index = row_index+row_window_size/2+row_window_size%2
            ul_col_index = col_index-(col_window_size/2)
            lr_col_index = col_index+col_window_size/2+col_window_size%2

            if ul_row_index < 0:
                lr_row_index += -ul_row_index
                ul_row_index = 0
            if ul_col_index < 0:
                lr_col_index += -ul_col_index
                ul_col_index = 0
            if lr_row_index > n_rows:
                ul_row_index -= (lr_row_index - n_rows)
                lr_row_index = n_rows
            if lr_col_index > n_cols:
                ul_col_index -= (lr_col_index - n_cols)
                lr_col_index = n_cols

            dem_out_band.ReadAsArray(
                xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
                win_ysize=row_window_size, buf_obj=dem_array)
            dem_edge_offset_band.ReadAsArray(
                xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
                win_ysize=row_window_size, buf_obj=dem_edge_offset)
        else:
            hits += 1

        w_row_index = row_index - ul_row_index
        w_col_index = col_index - ul_col_index

        if dem_edge_offset[w_row_index, w_col_index] <= weight:
            continue
        dem_edge_offset[w_row_index, w_col_index] = weight

        for neighbor_index in xrange(8):
            neighbor_row_index = row_index + row_offsets[neighbor_index]
            neighbor_col_index = col_index + col_offsets[neighbor_index]

            w_neighbor_row_index = w_row_index + row_offsets[neighbor_index]
            w_neighbor_col_index = w_col_index + col_offsets[neighbor_index]

            if (_is_flat(
                    w_neighbor_row_index, w_neighbor_col_index, row_window_size, col_window_size,
                    row_offsets, col_offsets, dem_array, nodata_value) and
                dem_edge_offset[w_neighbor_row_index, w_neighbor_col_index] > weight + 1 and
                dem_array[w_row_index, w_col_index] == dem_array[w_neighbor_row_index, w_neighbor_col_index]):

                t = Row_Col_Weight_Tuple(neighbor_row_index, neighbor_col_index, weight + 1)
                edge_queue.push(t)

    #save final dem edge offset off
    dem_edge_offset_band.WriteArray(
        dem_edge_offset, xoff=ul_col_index, yoff=ul_row_index)
    
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
                max_distance, numpy.max(row_array[row_array!=numpy.inf]))
        except ValueError:
            #no non-infinity elements, that's normal
            pass
    
    #Add the final offsets to the dem array
    dem_array = numpy.empty((1, n_cols), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float, ndim=2]dem_sink_offset_array = (
        numpy.empty((1, n_cols), dtype=numpy.float32))
    cdef numpy.ndarray[numpy.npy_float, ndim=2]dem_edge_offset_array = (
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
        mask_array = ((dem_sink_offset_array != numpy.inf) &
                      (dem_edge_offset_array != numpy.inf))
        dem_array[mask_array] = (dem_array[mask_array] + 
                                 (dem_sink_offset_array[mask_array] * 2.0 +
                                  (max_distance+1-dem_edge_offset_array[mask_array])) / 10000.0)
        dem_out_band.WriteArray(dem_array, xoff=0, yoff=row_index)
    
    
def flow_direction_inf(dem_uri, flow_direction_uri, dem_offset_uri):
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
        dem_carray - (optional) a CArray the same dimensions as dem_uri that
            will contain the flat region resolved regions of the dem_carray
       
       returns nothing"""

    cdef int col_index, row_index, n_cols, n_rows, max_index, facet_index
    cdef double e_0, e_1, e_2, s_1, s_2, d_1, d_2, flow_direction, slope, \
        flow_direction_max_slope, slope_max, dem_nodata, nodata_flow

    #need this if statement because dem_nodata is statically typed
    if raster_utils.get_nodata_from_uri(dem_uri) != None:
        dem_nodata = raster_utils.get_nodata_from_uri(dem_uri)
    else:
        #we don't have a nodata value, traditional one
        dem_nodata = -9999
    
    #Load DEM and resolve plateaus
    resolve_flat_regions_for_drainage(dem_uri, dem_offset_uri)
    dem_data_uri = raster_utils.temporary_filename()
    dem_carray = raster_utils.load_dataset_to_carray(
        dem_offset_uri, dem_data_uri, array_type=gdal.GDT_Float32)

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

    n_rows, n_cols = raster_utils.get_row_col_from_uri(dem_uri)
    d_1 = raster_utils.get_cell_size_from_uri(dem_uri)
    d_2 = d_1
    cdef float max_r = numpy.pi / 4.0
    
    #Create a flow carray and respective dataset
    flow_nodata = -9999
    raster_utils.new_raster_from_base_uri(
        dem_uri, flow_direction_uri, 'GTiff', flow_nodata,
        gdal.GDT_Float32, fill_value=flow_nodata)
    flow_direction_dataset = gdal.Open(flow_direction_uri, gdal.GA_Update)
    flow_band = flow_direction_dataset.GetRasterBand(1)
    #we'll write into this array and save every row
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flow_array = numpy.empty(
        (1, n_cols), dtype=numpy.float32)
    
    LOGGER.info("calculating d-inf per pixel flows")
    #This array will be a 3 row window for the whole dem carray so we
    #don't need to hold it in memory, loading 3 rows at a time is almost as 
    #fast as loading the entire array in memory (I timed it)
    cdef float[:, :] dem_window
    
    cdef int row_offset, col_offset

    cdef int weight, w_row_index, w_col_index
    cdef int row_window_size, col_window_size, ul_row_index, ul_col_index
    cdef int lr_col_index, lr_row_index, hits, misses
    cdef int old_ul_row_index, old_ul_col_index, old_lr_row_index, old_lr_col_index, window_buffer
    cdef int e_0_row_index, e_0_col_index, e_1_row_index, e_1_col_index, e_2_row_index, e_2_col_index
    
    row_window_size = 3
    col_window_size = n_cols
    window_buffer = 1
    ul_row_index = 0
    ul_col_index = 0
    lr_row_index = row_window_size
    lr_col_index = col_window_size

    dem_window = dem_carray[ul_row_index:lr_row_index, ul_col_index:lr_col_index]
    hits = 0
    misses = 0

    for row_index in range(n_rows):
        #We load 3 rows at a time

        if _update_window(
            row_index, col_index, &ul_row_index, &ul_col_index,
            &lr_row_index, &lr_col_index, n_rows, n_cols,
            row_window_size, col_window_size, window_buffer):
            #need to reload the window
            misses += 1
            dem_window = dem_carray[ul_row_index:lr_row_index,
                                   ul_col_index:lr_col_index]
        else:
            hits += 1

        #clear out the flow array from the previous loop
        flow_array[:] = flow_nodata
        for col_index in range(n_cols):
            #If we're on a nodata pixel, set the flow to nodata and skip
            if dem_window[1, col_index] == dem_nodata:
                continue
            
            #Calculate the flow flow_direction for each facet
            slope_max = 0 #use this to keep track of the maximum down-slope
            flow_direction_max_slope = 0 #flow direction on max downward slope
            max_index = 0 #index to keep track of max slope facet

            w_row_index = row_index - ul_row_index
            w_col_index = col_index - ul_col_index

            for facet_index in range(8):
                #This defines the three points the facet
                e_0_row_index = e_0_offsets[facet_index * 2 + 0] + w_row_index
                e_0_col_index = e_0_offsets[facet_index * 2 + 1] + w_col_index
                e_1_row_index = e_1_offsets[facet_index * 2 + 0] + w_row_index
                e_1_col_index = e_1_offsets[facet_index * 2 + 1] + w_col_index
                e_2_row_index = e_2_offsets[facet_index * 2 + 0] + w_row_index
                e_2_col_index = e_2_offsets[facet_index * 2 + 1] + w_col_index

                if (e_0_row_index < 0 or e_0_col_index < 0 or
                    e_1_row_index < 0 or e_1_col_index < 0 or
                    e_2_row_index < 0 or e_2_col_index < 0):
                    continue

                try:
                    e_0 = dem_window[e_0_row_index, e_0_col_index]
                    e_1 = dem_window[e_1_row_index, e_1_col_index]
                    e_2 = dem_window[e_2_row_index, e_2_col_index]

                except IndexError:
                    #This facet isn't defined because it's on the edge
                    continue
                #avoid calculating a slope on nodata values
                if e_1 == dem_nodata or e_2 == dem_nodata:
                    #If any neighbors are nodata, it's contaminated
                    break

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
            else: 
                # This is the fallthrough condition for the for loop, we reach
                # it only if we haven't encountered an invalid slope or pixel
                # that caused the above algorithm to break out 
                #Calculate the global angle depending on the max slope facet
                if slope_max > 0:
                    flow_array[0, col_index] = (
                        a_f[max_index] * flow_direction_max_slope +
                        a_c[max_index] * 3.14159265 / 2.0)
        #save the current flow row
        flow_band.WriteArray(flow_array, 0, row_index)

    flow_band = None
    gdal.Dataset.__swig_destroy__(flow_direction_dataset)
    flow_direction_dataset = None
    raster_utils.calculate_raster_stats_uri(flow_direction_uri)


cdef inline  int _update_window(
    int row_index, int col_index, int *ul_row_index, int *ul_col_index,
    int *lr_row_index, int *lr_col_index, int n_rows, int n_cols,
    int row_window_size, int col_window_size, int window_buffer):
#    if (((row_index <  ul_row_index[0] + 2) and (ul_row_index[0] >= 0))  or
#        ((row_index >= lr_row_index[0] - 2) and (lr_row_index[0] < n_rows - 1)) or
#        ((col_index <  ul_col_index[0] + 2) and (ul_col_index[0] > 0)) or
#        ((col_index >= lr_col_index[0] - 2) and (lr_col_index[0] < n_cols - 1))):
    if ((row_index <  ul_row_index[0] + window_buffer) or
        (row_index >= lr_row_index[0] - window_buffer) or
        (col_index <  ul_col_index[0] + window_buffer) or
        (col_index >= lr_col_index[0] - window_buffer)):

        ul_row_index[0] = row_index-(row_window_size/2)
        lr_row_index[0] = row_index+row_window_size/2+row_window_size%2
        ul_col_index[0] = col_index-(col_window_size/2)
        lr_col_index[0] = col_index+col_window_size/2+col_window_size%2

        if ul_row_index[0] < 0:
            lr_row_index[0] += -ul_row_index[0]
            ul_row_index[0] = 0
        if ul_col_index[0] < 0:
            lr_col_index[0] += -ul_col_index[0]
            ul_col_index[0] = 0
        if lr_row_index[0] > n_rows:
            ul_row_index[0] -= lr_row_index[0] - n_rows
            lr_row_index[0] = n_rows
        if lr_col_index[0] > n_cols:
            ul_col_index[0] -= lr_col_index[0] - n_cols
            lr_col_index[0] = n_cols
        return 1
    else:
        return 0

        
def find_sinks(dem_uri):
    """Discover and return the sinks in the dem array
    
        dem_carray - a uri to a gdal dataset
        
        returns a set of flat integer index indicating the sinks in the region"""
        
    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    
    cdef int w_row_index, w_col_index
    cdef int row_window_size, col_window_size, ul_row_index, ul_col_index
    cdef int lr_col_index, lr_row_index, hits, misses, neighbor_index
    cdef int neighbor_row_index, neighbor_col_index, w_neighbor_row_index, w_neighbor_col_index

    dem_ds = gdal.Open(dem_uri)
    dem_band = dem_ds.GetRasterBand(1)
    cdef int n_cols = dem_band.XSize
    cdef int n_rows = dem_band.YSize
    cdef float nodata_value = raster_utils.get_nodata_from_uri(dem_uri)
    
    LOGGER.debug("n_cols, n_rows %d %d" % (n_cols, n_rows))

    row_window_size = 3
    col_window_size = n_cols
    ul_row_index = 0
    ul_col_index = 0
    lr_row_index = row_window_size
    lr_col_index = col_window_size

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_array = dem_band.ReadAsArray(
        xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
        win_ysize=row_window_size)
    hits = 0
    misses = 0

    col_index = 0
    cdef int sink_set_index = 0
    sink_set = numpy.empty((10,), dtype=numpy.int32)
    for row_index in range(n_rows):
        #the col index will be 0 since we go row by row
        if _update_window(
            row_index, 0, &ul_row_index, &ul_col_index,
            &lr_row_index, &lr_col_index, n_rows, n_cols,
            row_window_size, col_window_size, 1):
            #need to reload the window
            misses += 1
            dem_band.ReadAsArray(
                xoff=ul_col_index, yoff=ul_row_index, win_xsize=col_window_size,
                win_ysize=row_window_size, buf_obj=dem_array)
        else:
            hits += 1
        w_row_index = row_index - ul_row_index
        for col_index in range(n_cols):
            w_col_index = col_index - ul_col_index
            if dem_array[w_row_index, w_col_index] == nodata_value:
                continue
            for neighbor_index in range(8):
                neighbor_row_index = row_index + row_offsets[neighbor_index]
                if neighbor_row_index < ul_row_index or neighbor_row_index >= lr_row_index:
                    continue
                neighbor_col_index = col_index + col_offsets[neighbor_index]
                if neighbor_col_index < ul_col_index or neighbor_col_index >= lr_col_index:
                    continue

                w_neighbor_row_index = w_row_index + row_offsets[neighbor_index]
                w_neighbor_col_index = w_col_index + col_offsets[neighbor_index]

                if dem_array[w_neighbor_row_index, w_neighbor_col_index] == nodata_value:
                    continue
                
                if (dem_array[w_neighbor_row_index, w_neighbor_col_index] < dem_array[w_row_index, w_col_index]):
                    #this cell can drain into another
                    break
            else: #else for the for loop
                #every cell we encountered was nodata or higher than current
                #cell, must be a sink
                if sink_set_index >= sink_set.shape[0]:
                    sink_set.resize((sink_set.shape[0] * 2,))
                sink_set[sink_set_index] = row_index * n_cols + col_index
                sink_set_index += 1

    LOGGER.info("hit ratio %d %d %f" % (misses, hits, hits/float(misses+hits)))
    sink_set.resize((sink_set_index,))
    return sink_set
