"""This file contains functions to simulate overland flow on GIS rasters
    defined by DEM raster datasets.  Here are some conventions of this model:

    A single pixel defines its neighbors as follows:

    3 2 1
    4 p 0
    5 6 7

    The 'p' refers to 'pixel' since the flow model is pixel centric.

    One of the outputs from this model will be a flow graph represented as a
    sparse matrix.  The rows in the matrix are the originating nodes and the 
    columns represent the outflow, thus G[i,j]'s value is the fraction of flow
    from node 'i' to node 'j'.  The following expresses how to calculate the 
    matrix indexes from the pixels original row,column position in the raster.
    Given that the raster's dimension is 'n_rows' by 'n_columns', pixel located
    at row 'r' and colunn 'c' has index

        (r,c) -> r * n_columns + c = index

    Likewise given 'index' r and c can be derived as:

        (index) -> (index div n_columns, index mod n_columns) where 'div' is 
            the integer division operator and 'mod' is the integer remainder
            operation."""

import os
import logging
import collections
import time
import tempfile

from osgeo import gdal
import numpy

from invest_natcap import raster_utils
import invest_cython_core


logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing')

def route_flux(
    dem_uri, source_uri, absorption_rate_uri, loss_uri, flux_uri, workspace_dir, aoi_uri = None):

    """This function will route flux across a landscape given a dem to
        guide flow from a d-infinty flow algorithm, and a custom function
        that will operate on input flux and other user defined arguments
        to determine nodal output flux.

        dem_uri - a URI to a DEM raster
        source_uri - a GDAL dataset that has source flux per pixel
        absorption_rate_uri - a GDAL floating point dataset that has a percent
            of flux absorbed per pixel
        loss_uri - an output URI to to the dataset that will output the
            amount of flux absorbed by each pixel
        flux_uri - a URI to an output dataset that records the amount of flux
            traveling through each pixel
        workspace_dir - a URI to an existing directory that can be used to
            write intermediate files to
        aoi_uri - an OGR datasource for an area of interest polygon.
            the routing flux calculation will only occur on those pixels
            and neighboring pixels will either be raw outlets or 
            non-contibuting inputs depending on the orientation of the DEM.

        returns nothing"""

    flow_direction_uri = os.path.join(workspace_dir, 'flow_direction.tif')
    inflow_direction_uri = os.path.join(workspace_dir, 'inflow_direction.tif')
    outflow_weights_uri = os.path.join(workspace_dir, 'outflow_weights.tif')
    outflow_direction_uri = os.path.join(workspace_dir, 'outflow_directions.tif')

    calculate_flow_direction(dem_uri, flow_direction_uri)
    sink_cell_set, source_cell_set = calculate_flow_graph(
        flow_direction_uri, outflow_weights_uri, outflow_direction_uri)
    calculate_transport(outflow_direction_uri, outflow_weights_uri, sink_cell_set, source_uri, absorption_rate_uri, loss_uri, flux_uri)



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

    #We need to open the dem so we can create the dataset to hold the output
    #flow direction raster
    dem_dataset = gdal.Open(dem_uri)
    dem_band, dem_nodata = raster_utils.extract_band_and_nodata(dem_dataset)
    n_rows, n_cols = dem_band.YSize, dem_band.XSize

    d_inf_dir_nodata = -1.0
    flow_direction_dataset = raster_utils.new_raster_from_base(
        dem_dataset, flow_direction_uri, 'GTiff', d_inf_dir_nodata,
        gdal.GDT_Float32)

    #Calcualte the d infinity flow direction
    bounding_box = [0, 0, n_cols, n_rows]
    invest_cython_core.flow_direction_inf(
        dem_dataset, bounding_box, flow_direction_dataset)

    LOGGER.info('Done calculating d-infinity elapsed time %ss' % (time.clock()-start))

def calculate_flow_graph(flow_direction_uri, outflow_weights_uri, outflow_direction_uri):
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

        returns sink_cell_set, source_cell_set
            where these sets indicate the cells with only inflow (sinks) or
            only outflow (source)"""

    LOGGER.info('Calculating flow graph')
    start = time.clock()

    #This is the array that's used to keep track of the connections of the
    #current cell to those *inflowing* to the cell, thus the 8 directions
    flow_direction_dataset = gdal.Open(flow_direction_uri)
    flow_direction_band, flow_direction_nodata = raster_utils.extract_band_and_nodata(flow_direction_dataset)
    n_cols, n_rows = flow_direction_band.XSize, flow_direction_band.YSize
    n_elements = n_cols * n_rows


    outflow_weights = numpy.empty(n_elements, dtype = numpy.float32)
    outflow_weights_nodata = -1.0
    outflow_weights[:] = outflow_weights_nodata

    outflow_direction = numpy.empty(n_elements, dtype = numpy.byte)
    outflow_direction_nodata = 9
    outflow_direction[:] = outflow_direction_nodata

    #These will be used to determine inflow and outflow later

    inflow_cell_set = set()
    outflow_cell_set = set()

    #Diagonal offsets are based off the following index notation for neighbors
    #    3 2 1
    #    4 p 0
    #    5 6 7

    #diagonal offsets index is 0, 1, 2, 3, 4, 5, 6, 7 from the figure above
    diagonal_offsets = \
        [1, -n_cols+1, -n_cols, -n_cols-1, -1, n_cols-1, n_cols, n_cols+1]

    #The number of diagonal offsets defines the neighbors, angle between them
    #and the actual angle to point to the neighbor
    n_neighbors = 8
    angle_between_neighbors = 2.0 * numpy.pi / n_neighbors
    angle_to_neighbor = \
        [i * angle_between_neighbors for i in range(n_neighbors)]

    flow_direction_memory_file = tempfile.TemporaryFile()
    flow_direction_array = raster_utils.load_memory_mapped_array(flow_direction_uri, flow_direction_memory_file)

    #Iterate over flow directions
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            flow_direction = flow_direction_array[row_index, col_index]
            #make sure the flow direction is defined, if not, skip this cell
            if flow_direction == flow_direction_nodata:
                continue
            current_index = row_index * n_cols + col_index
            for neighbor_offset in range(n_neighbors):
                flow_angle_to_neighbor = numpy.abs(
                    angle_to_neighbor[neighbor_offset] - flow_direction)
                if flow_angle_to_neighbor < angle_between_neighbors:
                    #There's flow from the current cell to the neighbor
                    #Get the flat indexes for the current and outflow cell
                    outflow_index = \
                        current_index + diagonal_offsets[neighbor_offset]

                    #Something flows out of this cell, remember that
                    outflow_cell_set.add(current_index)

                    #Determine if the direction we're on is oriented at 90
                    #degrees or 45 degrees.  Given our orientation even number
                    #neighbor indexes are oriented 90 degrees and odd are 45
                    if neighbor_offset % 2 == 0:
                        outflow_weights[outflow_index] = \
                            1.0 - numpy.tan(flow_angle_to_neighbor)
                    else:
                        outflow_weights[outflow_index] = \
                            numpy.tan(numpy.pi/4.0 - flow_angle_to_neighbor)

                    #Update outflow neighbor
                    outflow_direction[outflow_index] = neighbor_offset

                    inflow_cell_set.add(outflow_index)
                    
                    #we found the outflow direction
                    break

    #write outflow direction and weights
    outflow_weights_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, outflow_weights_uri, 'GTiff', outflow_weights_nodata,
        gdal.GDT_Float32)
    outflow_weights_band, _ = raster_utils.extract_band_and_nodata(outflow_weights_dataset)
    outflow_weights_band.WriteArray(numpy.memmap.reshape(outflow_weights, (n_rows, n_cols)))
    
    outflow_direction_dataset = raster_utils.new_raster_from_base(
        flow_direction_dataset, outflow_direction_uri, 'GTiff', outflow_direction_nodata,
        gdal.GDT_Byte)
    outflow_direction_band, _ = raster_utils.extract_band_and_nodata(outflow_direction_dataset)
    outflow_direction_band.WriteArray(numpy.memmap.reshape(outflow_direction, (n_rows, n_cols)))

    LOGGER.debug("Calculating sink and source cells")
    sink_cell_set = inflow_cell_set.difference(outflow_cell_set)
    source_cell_set = outflow_cell_set.difference(inflow_cell_set)

    LOGGER.info('Done calculating flow path elapsed time %s' % (time.clock()-start))
    return sink_cell_set, source_cell_set

def calculate_transport(
    outflow_direction_uri, outflow_weights_uri, sink_cell_set, source_uri, absorption_rate_uri, loss_uri, flux_uri):
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
    outflow_weights_dataset = gdal.Open(outflow_weights_uri)
    source_dataset = gdal.Open(source_uri)
    absorption_rate_dataset = gdal.Open(absorption_rate_uri)

    #Extract nodata values
    _, outflow_weights_nodata = raster_utils.extract_band_and_nodata(outflow_weights_dataset)
    _, source_nodata = raster_utils.extract_band_and_nodata(source_dataset)
    _, absorption_rate_nodata = raster_utils.extract_band_and_nodata(absorption_rate_dataset)

    #Create memory mapped lookup arrays
    outflow_direction_data_file = tempfile.TemporaryFile()
    outflow_weights_data_file = tempfile.TemporaryFile()
    source_data_file = tempfile.TemporaryFile()
    absorption_rate_data_file = tempfile.TemporaryFile()

    outflow_direction_array = raster_utils.load_memory_mapped_array(outflow_direction_uri, outflow_direction_data_file)
    outflow_weights_array = raster_utils.load_memory_mapped_array(outflow_weights_uri, outflow_weights_data_file)
    source_array = raster_utils.load_memory_mapped_array(source_uri, source_data_file)
    absorption_rate_array = raster_utils.load_memory_mapped_array(absorption_rate_uri, absorption_rate_data_file)


    loss_dataset = raster_utils.new_raster_from_base(
        flow_direction, loss_uri, 'GTiff', transport_nodata,
        gdal.GDT_Float32)
    flux_dataset = raster_utils.new_raster_from_base(
        flow_direction, flux_uri, 'GTiff', transport_nodata,
        gdal.GDT_Float32)


    loss_band, _ = raster_utils.extract_band_and_nodata(loss_dataset)
    flux_band, _ = raster_utils.extract_band_and_nodata(flux_dataset)

    visited_cells = set(sink_cells)
    cells_to_process = collections.deque(sink_cells)
    
    while len(cells_to_process) > 0:
        current_index = cells_to_process.popleft()
        current_row = current_index / n_cols
        current_col = current_index % n_cols

        parents_calculated = True
        for offset in range(8):
            parent_index = flow_graph_neighbor_indexes[current_index, offset]
            if parent_index == out_nodata_value:
                continue
            if parent_index not in visited_cells:
                if parents_calculated:
                    cells_to_process.appendleft(current_index)
                cells_to_process.appendleft(parent_index)
                visited_cells.add(parent_index)
                parents_calculated = False
            continue

        #all parents calculated so loop over them and calculate current flow
        current_flow = 1.0
        for offset in range(8):
            parent_index = flow_graph_neighbor_indexes[current_index, offset]
            if parent_index == out_nodata_value:
                continue
            parent_row = parent_index / n_cols
            parent_col = parent_index % n_cols
            parent_percent = flow_graph_edge_weights[current_index, offset]
            current_flow += parent_percent * raster_out_array[parent_row, parent_col]

        raster_out_array[current_row, current_col] = current_flow


    raster_out_band.WriteArray(raster_out_array, 0, 0)
    LOGGER.info('Done processing flow elapsed time %s' % (time.clock()-start))

    #This is for debugging
    sink_uri = os.path.join(workspace_dir, 'sink.tif')
    sink_nodata = -1.0
    sink_dataset = raster_utils.new_raster_from_base(
        dem_dataset, sink_uri, 'GTiff', d_inf_dir_nodata,
        gdal.GDT_Int32)
    sink_band, _, sink_array = raster_utils.extract_band_and_nodata(sink_dataset, get_array = True)
    sink_array[:] = sink_nodata

    source_uri = os.path.join(workspace_dir, 'source.tif')
    source_nodata = -1.0
    source_dataset = raster_utils.new_raster_from_base(
        dem_dataset, source_uri, 'GTiff', d_inf_dir_nodata,
        gdal.GDT_Int32)
    source_band, _, source_array = raster_utils.extract_band_and_nodata(source_dataset, get_array = True)
    source_array[:] = source_nodata

    for cell_index in sink_cells:
        cell_row = cell_index / n_cols
        cell_col = cell_index % n_cols
        sink_array[cell_row, cell_col] = 1

    for cell_index in source_cells:
        cell_row = cell_index / n_cols
        cell_col = cell_index % n_cols
        source_array[cell_row, cell_col] = 1

    sink_band.WriteArray(sink_array, 0, 0)
    source_band.WriteArray(source_array, 0, 0)

    LOGGER.debug("number of sinks %s number of sources %s" % (len(sink_cells), len(source_cells)))



    pass
