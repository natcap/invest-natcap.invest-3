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

from invest_natcap import raster_utils

from libcpp.stack cimport stack
from libcpp.queue cimport queue
from libc.math cimport atan
from libc.math cimport atan2
from libc.math cimport tan
from libc.math cimport sqrt

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing cython core')

cdef double PI = 3.141592653589793238462643383279502884
cdef double EPS = 1e-6


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

        returns sink_cell_set, source_cell_set
            where these sets indicate the cells with only inflow (sinks) or
            only outflow (source)"""

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

    #These will be used to determine inflow and outflow later

    inflow_cell_set = set()
    outflow_cell_set = set()

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

                    #Something flows out of this cell, remember that
                    outflow_cell_set.add(current_index)

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
                    inflow_cell_set.add(outflow_index)

                    #if there is non-zero flow to the next cell clockwise then
                    #add it to the inflow set
                    if outflow_weight != 1.0:
                        next_outflow_index = current_index + \
                            diagonal_offsets[(neighbor_direction_index + 1) % 8]
                        inflow_cell_set.add(next_outflow_index)

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
    sink_cell_set = inflow_cell_set.difference(outflow_cell_set)
    source_cell_set = outflow_cell_set.difference(inflow_cell_set)

    LOGGER.debug('n_cols n_rows %s %s' % (n_cols, n_rows))

    LOGGER.info('Done calculating flow path elapsed time %ss' % \
                    (time.clock()-start))
    return sink_cell_set, source_cell_set


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
              

cdef int _is_sink(int row_index, int col_index, int n_rows, int n_cols, int* row_offsets, int *col_offsets, float[:, :] dem_array, float nodata_value):
    cdef int neighbor_row_index, neighbor_col_index
    if dem_array[row_index, col_index] == nodata_value: return 0
            
    if _is_flat(row_index, col_index, n_rows, n_cols, row_offsets, col_offsets, dem_array, nodata_value):
        return 0
    
    for neighbor_index in xrange(8):
        neighbor_row_index = row_index + row_offsets[neighbor_index]
        if neighbor_row_index < 0 or neighbor_row_index >= n_rows:
            continue
        neighbor_col_index = col_index + col_offsets[neighbor_index]
        if neighbor_col_index < 0 or neighbor_col_index >= n_cols:
            continue
        
        if (dem_array[neighbor_row_index, neighbor_col_index] == dem_array[row_index, col_index] and
                _is_flat(neighbor_row_index, neighbor_col_index, n_rows, n_cols, row_offsets, col_offsets, dem_array, nodata_value)):
            return 1
    return 0              
        
        
def resolve_flat_regions_for_drainage(dem_python_array, float nodata_value):
    """This function resolves the flat regions on a DEM that cause undefined
        flow directions to occur during routing.  The algorithm is the one
        presented in "The assignment of drainage direction over float surfaces
        in raster digital elevation models by Garbrecht and Martz (1997)
        
        dem_array - a numpy floating point array that represents a digital
            elevation model.  Any flat regions that would cause an undefined
            flow direction will be adjusted in height so that every pixel
            on the dem has a local defined slope.

        nodata_value - this value will be ignored on the DEM as a valid height
            value
            
        returns nothing"""

    
    cdef float[:, :] dem_array = dem_python_array
    cdef int *row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    cdef int *col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]
    cdef int n_rows = dem_array.shape[0]
    cdef int n_cols = dem_array.shape[1]
    cdef queue[Row_Col_Weight_Tuple] sink_queue
    cdef int row_index, col_index


    

    #Identify sink cells
    LOGGER.info('identify sink cells')
    sink_cell_list = []
    cdef Row_Col_Weight_Tuple t
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            if _is_sink(row_index, col_index, n_rows, n_cols, row_offsets, col_offsets, dem_array, nodata_value):
                t = Row_Col_Weight_Tuple(row_index, col_index, 0)
                sink_queue.push(t)

    LOGGER.info('calculate distances from sinks to other flat cells')
    dem_sink_offset_data_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_sink_offset = numpy.memmap(dem_sink_offset_data_file, dtype=numpy.float32, mode='w+',
                              shape=(n_rows, n_cols))
    dem_offset_data_file = tempfile.TemporaryFile()
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_offset = numpy.memmap(dem_offset_data_file, dtype=numpy.float32, mode='w+',
                              shape=(n_rows, n_cols))                              
    dem_sink_offset[:] = numpy.inf

    LOGGER.info('sink queue size %s' % (sink_queue.size()))
    cdef Row_Col_Weight_Tuple current_cell_tuple
    while sink_queue.size() > 0:
        current_cell_tuple = sink_queue.front()
        sink_queue.pop()
        if dem_sink_offset[current_cell_tuple.row_index, current_cell_tuple.col_index] <= current_cell_tuple.weight:
            continue
        dem_sink_offset[current_cell_tuple.row_index, current_cell_tuple.col_index] = current_cell_tuple.weight

        for neighbor_index in xrange(8):
            neighbor_row_index = current_cell_tuple.row_index + row_offsets[neighbor_index]
            neighbor_col_index = current_cell_tuple.col_index + col_offsets[neighbor_index]
            if _is_flat(neighbor_row_index, neighbor_col_index, n_rows, n_cols, row_offsets, col_offsets, dem_array, nodata_value) and dem_sink_offset[neighbor_row_index, neighbor_col_index] > current_cell_tuple.weight + 1 and dem_array[current_cell_tuple.row_index, current_cell_tuple.col_index] == dem_array[neighbor_row_index, neighbor_col_index]:
                t = Row_Col_Weight_Tuple(neighbor_row_index, neighbor_col_index, current_cell_tuple.weight + 1)
                sink_queue.push(t)

    dem_sink_offset[dem_sink_offset == numpy.inf] = 0
    numpy.multiply(dem_sink_offset, 2.0, dem_offset)
    cdef numpy.ndarray[numpy.npy_float, ndim=2] dem_edge_offset = dem_sink_offset
    cdef int max_distance
    
    LOGGER.info('calculate distances from edge to center of flat regions')
    edge_cell_list = []
    cdef queue[Row_Col_Weight_Tuple] edge_queue

    for row_index in range(1, n_rows - 1):
        for col_index in range(1, n_cols - 1):
            #only consider flat cells
            if not _is_flat(row_index, col_index, n_rows, n_cols, row_offsets, col_offsets, dem_array, nodata_value): continue
            for neighbor_index in xrange(8):
                neighbor_row_index = row_index + row_offsets[neighbor_index]
                neighbor_col_index = col_index + col_offsets[neighbor_index]
                if (dem_array[neighbor_row_index, neighbor_col_index] != nodata_value) and (dem_array[row_index, col_index] < dem_array[neighbor_row_index, neighbor_col_index]):
                    t = Row_Col_Weight_Tuple(row_index, col_index, 0)
                    edge_queue.push(t)
                    break
                    
    if edge_queue.size() > 0:
        LOGGER.info('edge cell queue size %s' % (edge_queue.size()))
        dem_edge_offset[:] = numpy.inf
        
        while edge_queue.size() > 0:
            current_cell_tuple = edge_queue.front()
            edge_queue.pop()
            if dem_edge_offset[current_cell_tuple.row_index, current_cell_tuple.col_index] <= current_cell_tuple.weight:
                continue
            dem_edge_offset[current_cell_tuple.row_index, current_cell_tuple.col_index] = current_cell_tuple.weight

            for neighbor_index in xrange(8):
                neighbor_row_index = current_cell_tuple.row_index + row_offsets[neighbor_index]
                neighbor_col_index = current_cell_tuple.col_index + col_offsets[neighbor_index]
                if _is_flat(neighbor_row_index, neighbor_col_index, n_rows, n_cols, row_offsets, col_offsets, dem_array, nodata_value) and dem_edge_offset[neighbor_row_index, neighbor_col_index] > current_cell_tuple.weight + 1 and dem_array[current_cell_tuple.row_index, current_cell_tuple.col_index] == dem_array[neighbor_row_index, neighbor_col_index]:
                    t = Row_Col_Weight_Tuple(neighbor_row_index, neighbor_col_index, current_cell_tuple.weight + 1)
                    edge_queue.push(t)

        max_distance = numpy.max(dem_edge_offset[dem_edge_offset != numpy.inf])
        dem_edge_offset = max_distance + 1 - dem_edge_offset
        dem_edge_offset[dem_edge_offset == -numpy.inf] = 0
        dem_offset += dem_edge_offset
    
    dem_python_array += dem_offset * numpy.float(1.0/10000.0)
    return dem_offset, dem_sink_offset, dem_edge_offset

    
def flow_direction_inf(dem_uri, flow_direction_uri):
    """Calculates the D-infinity flow algorithm.  The output is a float
        raster whose values range from 0 to 2pi.
        Algorithm from: Tarboton, "A new method for the determination of flow
        directions and upslope areas in grid digital elevation models," Water
        Resources Research, vol. 33, no. 2, pages 309 - 319, February 1997.

       dem - (input) a single band GDAL Dataset with elevation values
       bounding_box - (input) a 4 element array defining the GDAL read window
           for dem and output on flow
       flow - (output) a single band float raster of same dimensions as
           dem.  After the function call it will have flow direction in it 
       
       returns nothing"""

    cdef int col_index, row_index, n_cols, n_rows, max_index, facet_index
    cdef double e_0, e_1, e_2, s_1, s_2, d_1, d_2, flow_direction, slope, \
        flow_direction_max_slope, slope_max, dem_nodata, nodata_flow

    dem_dataset = gdal.Open(dem_uri)

    flow_nodata = -1.0
    raster_utils.new_raster_from_base(
        dem_dataset, flow_direction_uri, 'GTiff', flow_nodata,
        gdal.GDT_Float32, fill_value=flow_nodata)

    LOGGER.debug("flow_direction_uri %s" % flow_direction_uri)
    flow_direction_dataset = gdal.Open(flow_direction_uri, gdal.GA_Update)
    if dem_dataset.GetRasterBand(1).GetNoDataValue() != None:
        dem_nodata = dem_dataset.GetRasterBand(1).GetNoDataValue()
    else:
        #we don't have a nodata value, just make something small
        dem_nodata = -1e6
    flow_band = flow_direction_dataset.GetRasterBand(1)

    LOGGER.info("loading DEM")
    dem_data_file = tempfile.TemporaryFile()
    flow_data_file = tempfile.TemporaryFile()

    dem_data_uri = raster_utils.temporary_filename()
    dem_carray = raster_utils.load_dataset_to_carray(
        dem_uri, dem_data_uri)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_array = (dem_carray[:]).astype(numpy.float32)

    #these outputs should become carrays
    dem_offset, sink_offset,edge_offset = resolve_flat_regions_for_drainage(dem_array, dem_nodata)

    raster_utils.new_raster_from_base(
        dem_dataset, flow_direction_uri + 'dem_offest.tif', 'GTiff', flow_nodata,
        gdal.GDT_Float32, fill_value=flow_nodata)
    dem_offset_dataset = gdal.Open(flow_direction_uri + 'dem_offest.tif', gdal.GA_Update)
    dem_offset_band = dem_offset_dataset.GetRasterBand(1)
    dem_offset_band.WriteArray(dem_offset)
    raster_utils.new_raster_from_base(
        dem_dataset, flow_direction_uri + 'sink_offest.tif', 'GTiff', flow_nodata,
        gdal.GDT_Float32, fill_value=flow_nodata)
    sink_offset_dataset = gdal.Open(flow_direction_uri + 'sink_offest.tif', gdal.GA_Update)
    sink_offset_band = sink_offset_dataset.GetRasterBand(1)
    sink_offset_band.WriteArray(sink_offset)
    raster_utils.new_raster_from_base(
        dem_dataset, flow_direction_uri + 'edge_offest.tif', 'GTiff', flow_nodata,
        gdal.GDT_Float32, fill_value=flow_nodata)
    edge_offset_dataset = gdal.Open(flow_direction_uri + 'edge_offest.tif', gdal.GA_Update)
    edge_offset_band = edge_offset_dataset.GetRasterBand(1)
    edge_offset_band.WriteArray(edge_offset)
    
    n_rows = dem_dataset.RasterYSize
    n_cols = dem_dataset.RasterXSize

    #This matrix holds the flow direction value, initialize to flow_nodata
    flow_data_uri = raster_utils.temporary_filename()
    flow_carray = raster_utils.load_dataset_to_carray(
        flow_direction_uri, flow_data_uri)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flow_array = flow_carray[:]
#        raster_utils.load_memory_mapped_array(flow_direction_uri, flow_data_file, array_type=numpy.float32)

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

    #Get pixel sizes
    d_1 = abs(dem_dataset.GetGeoTransform()[1])
    d_2 = abs(dem_dataset.GetGeoTransform()[5])
    cdef float max_r = numpy.pi / 4.0
    LOGGER.info("calculating d-inf per pixel flows")
    #loop through each cell and skip any edge pixels
    for col_index in range(1, n_cols - 1):
        for row_index in range(1, n_rows - 1):

            #If we're on a nodata pixel, set the flow to nodata and skip
            if dem_array[row_index, col_index] == dem_nodata:
                flow_array[row_index, col_index] = flow_nodata
                continue

            if flow_array[row_index, col_index] != flow_nodata:
                continue

            #Calculate the flow flow_direction for each facet
            slope_max = 0 #use this to keep track of the maximum down-slope
            flow_direction_max_slope = 0 #flow direction on max downward slope
            max_index = 0 #index to keep track of max slope facet
            
            for facet_index in range(8):
                #This defines the three height points
                e_0 = dem_array[e_0_offsets[facet_index*2+0] + row_index,
                                e_0_offsets[facet_index*2+1] + col_index]
                e_1 = dem_array[e_1_offsets[facet_index*2+0] + row_index,
                                e_1_offsets[facet_index*2+1] + col_index]
                e_2 = dem_array[e_2_offsets[facet_index*2+0] + row_index,
                                e_2_offsets[facet_index*2+1] + col_index]
                
                #avoid calculating a slope on nodata values
                if e_1 == dem_nodata or e_2 == dem_nodata:
                    #If any neighbors are nodata, it's contaminated
                    flow_array[row_index, col_index] = flow_nodata
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
                    flow_array[row_index, col_index] = \
                        a_f[max_index] * flow_direction_max_slope + \
                        a_c[max_index] * 3.14159265 / 2.0

    LOGGER.info("writing flow data to raster")
    flow_band.WriteArray(flow_array)
    flow_band = None
    gdal.Dataset.__swig_destroy__(flow_direction_dataset)
    flow_direction_dataset = None
    raster_utils.calculate_raster_stats_uri(flow_direction_uri)
