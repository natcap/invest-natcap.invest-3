import collections
import tempfile
import time
import logging

import numpy
cimport numpy
from osgeo import gdal

from invest_natcap import raster_utils

from libcpp.stack cimport stack


logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing cython core')

def calculate_transport(
    outflow_direction_uri, outflow_weights_uri, sink_cell_set, source_uri,
    absorption_rate_uri, loss_uri, flux_uri):
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

    cdef numpy.ndarray[numpy.npy_byte, ndim=2] outflow_direction_array = raster_utils.load_memory_mapped_array(
        outflow_direction_uri, outflow_direction_data_file)

    #TODO: This is hard-coded because load memory mapped array doesn't return a nodata value
    cdef int outflow_direction_nodata = 9
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] outflow_weights_array = raster_utils.load_memory_mapped_array(
        outflow_weights_uri, outflow_weights_data_file)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] source_array = raster_utils.load_memory_mapped_array(
        source_uri, source_data_file)
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] absorption_rate_array = raster_utils.load_memory_mapped_array(
        absorption_rate_uri, absorption_rate_data_file)

    #Create output arrays for loss and flux
    cdef int n_cols = outflow_direction_dataset.RasterXSize
    cdef int n_rows = outflow_direction_dataset.RasterYSize
    transport_nodata = -1.0

    loss_data_file = tempfile.TemporaryFile()
    flux_data_file = tempfile.TemporaryFile()

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] loss_array = numpy.memmap(loss_data_file, dtype=numpy.float32, mode='w+',
                              shape=(n_rows, n_cols))
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flux_array = numpy.memmap(flux_data_file, dtype=numpy.float32, mode='w+',
                              shape=(n_rows, n_cols))
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

    while cells_to_process.size() > 0:
        current_index = cells_to_process.top()
        cells_to_process.pop()
        current_row = current_index / n_cols
        current_col = current_index % n_cols

        if flux_array[current_row, current_col] == transport_nodata:
            flux_array[current_row, current_col] = source_array[
                current_row, current_col]
            loss_array[current_row, current_col] = 0.0

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

                flux_array[current_row, current_col] += \
                    outflow_weight * in_flux * (1.0 - absorption_rate)

                loss_array[current_row, current_col] += \
                    in_flux * absorption_rate
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

    cdef int col_index, row_index, col_max, row_max, max_index, facet_index
    cdef double e_0, e_1, e_2, s_1, s_2, d_1, d_2, flow_direction, slope, \
        flow_direction_max_slope, slope_max, nodata_dem, nodata_flow

    dem_dataset = gdal.Open(dem_uri)

    flow_nodata = -1.0
    flow_direction_dataset = raster_utils.new_raster_from_base(
        dem_dataset, flow_direction_uri, 'GTiff', flow_nodata,
        gdal.GDT_Float64)

    dem_nodata = dem_dataset.GetRasterBand(1).GetNoDataValue()
    flow_band = flow_direction_dataset.GetRasterBand(1)

    LOGGER.info("loading DEM")
    dem_data_file = tempfile.TemporaryFile()
    flow_data_file = tempfile.TemporaryFile()

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] dem_array = \
        raster_utils.load_memory_mapped_array(dem_uri, dem_data_file, array_type=numpy.float32)

    n_rows = dem_dataset.RasterYSize
    n_cols = dem_dataset.RasterXSize

    #This matrix holds the flow direction value, initialize to flow_nodata
    cdef numpy.ndarray[numpy.npy_float32, ndim=2] flow_array = \
        numpy.memmap(flow_data_file, dtype=numpy.float32, mode='w+',
                     shape=(n_rows, n_cols))
    flow_array[:] = flow_nodata

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

    LOGGER.info("calculating d-inf per pixel flows")
    #loop through each cell and skip any edge pixels
    for col_index in range(1, n_cols - 1):
        for row_index in range(1, n_rows - 1):

            #If we're on a nodata pixel, set the flow to nodata and skip
            if dem_array[row_index, col_index] == dem_nodata:
                flow_array[row_index, col_index] = flow_nodata
                continue

            #Calculate the flow flow_direction for each facet
            slope_max = 0 #use this to keep track of the maximum down-slope
            flow_direction_max_slope = 0 #flow direction on max downward slope
            max_index = 0 #index to keep track of max slope facet
            
            #Initialize flow matrix to nod_data flow so the default is to 
            #calculate with D8.
            flow_array[row_index, col_index] = flow_nodata
            
            for facet_index in range(8):
                #This defines the three height points
                e_0 = dem_array[e_0_offsets[facet_index*2+0] + row_index,
                                e_0_offsets[facet_index*2+1] + col_index]
                e_1 = dem_array[e_1_offsets[facet_index*2+0] + row_index,
                                e_1_offsets[facet_index*2+1] + col_index]
                e_2 = dem_array[e_2_offsets[facet_index*2+0] + row_index,
                                e_2_offsets[facet_index*2+1] + col_index]
                
                #LOGGER.debug('facet %s' % (facet_index+1))
                #LOGGER.debug('e_1_offsets %s %s' %(e_1_offsets[facet_index*2+1],
                #                                   e_1_offsets[facet_index*2+0]))
                #LOGGER.debug('e_0 %s e_1 %s e_2 %s' % (e_0, e_1, e_2))
                
                #avoid calculating a slope on nodata values
                if e_1 == dem_nodata or e_2 == dem_nodata: 
                    break #fallthrough to D8
                 
                #s_1 is slope along straight edge
                s_1 = (e_0 - e_1) / d_1 #Eqn 1
                
                #slope along diagonal edge
                s_2 = (e_1 - e_2) / d_2 #Eqn 2
                
                if s_1 <= 0 and s_2 <= 0:
                    #uphill slope or flat, so skip, D8 resolve 
                    continue 
                
                #Default to pi/2 in case s_1 = 0 to avoid divide by zero cases
                flow_direction = 3.14159262/2.0
                if s_1 != 0:
                    flow_direction = numpy.arctan(s_2 / s_1) #Eqn 3

                if flow_direction < 0: #Eqn 4
                    #LOGGER.debug("flow direciton negative")
                    #If the flow direction goes off one side, set flow
                    #direction to that side and the slope to the straight line
                    #distance slope
                    flow_direction = 0
                    slope = s_1
                    #LOGGER.debug("flow direction < 0 slope=%s"%slope)
                elif flow_direction > numpy.arctan(d_2 / d_1): #Eqn 5
                    #LOGGER.debug("flow direciton greater than 45 degrees")
                    #If the flow direciton goes off the diagonal side, figure
                    #out what its value is and
                    flow_direction = numpy.arctan(d_2 / d_1)
                    slope = (e_0 - e_2) / numpy.sqrt(d_1 ** 2 + d_2 ** 2)
                    #LOGGER.debug("flow direction > 45 slope=%s"%slope)
                else:
                    #LOGGER.debug("flow direciton in bounds")
                    slope = numpy.sqrt(s_1 ** 2 + s_2 ** 2) #Eqn 3
                    #LOGGER.debug("flow direction in middle slope=%s"%slope)

                #LOGGER.debug("slope %s" % slope)
                if slope > slope_max:
                    flow_direction_max_slope = flow_direction
                    slope_max = slope
                    max_index = facet_index
            else: 
                # This is the fallthrough condition for the for loop, we reach
                # it only if we haven't encountered an invalid slope or pixel
                # that caused the above algorithm to break out
                 
                #Calculate the global angle depending on the max slope facet
                #LOGGER.debug("slope_max %s" % slope_max)
                #LOGGER.debug("max_index %s" % (max_index+1))
                if slope_max > 0:
                    flow_array[row_index, col_index] = \
                        a_f[max_index] * flow_direction_max_slope + \
                        a_c[max_index] * 3.14159265 / 2.0

    #Calculate D8 flow to resolve undefined flows in D-inf
#    d8_flow_direction_dataset = raster_utils.new_raster_from_base(flow, '', 'MEM', -5.0, gdal.GDT_Float32)
#    LOGGER.info("calculating D8 flow")
#    flowDirectionD8(dem, bounding_box, d8_flow_direction_dataset)
#    d8_flow_matrix = d8_flow_direction_dataset.ReadAsArray(*bounding_box).transpose()
    
#    nodata_d8 = d8_flow_direction_dataset.GetRasterBand(1).GetNoDataValue()

#    d8_to_radians = {0: -1.0,
#                     1: 0.0,
#                     2: 5.497787144,
#                     4: 4.71238898,
#                     8: 3.926990817,
#                     16: 3.141592654,
#                     32: 2.35619449,
#                     64: 1.570796327,
#                     128: 0.785398163,
#                     nodata_d8: flow_nodata
#                     }
    
#    for col_index in range(1, col_max - 1):
#        for row_index in range(1, row_max - 1):
#            if flow_matrix[row_index, col_index] == flow_nodata:
#                flow_matrix[row_index, col_index] = \
#                    d8_to_radians[d8_flow_matrix[row_index, col_index]]

    LOGGER.info("writing flow data to raster")
    flow_band.WriteArray(flow_array)
    raster_utils.calculate_raster_stats(flow_direction_dataset)
