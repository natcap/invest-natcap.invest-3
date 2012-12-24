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

from osgeo import gdal
import numpy

from invest_natcap import raster_utils
import invest_cython_core


logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing')

def calculate_routing(
    dem_uri, dataset_uri_list, mass_balance_op, workspace_dir, raster_out_uri,
    out_nodata_value, aoi_uri = None):

    """This function will route flux across a landscape given a dem to
        guide flow from a d-infinty flow algorithm, and a custom function
        that will operate on input flux and other user defined arguments
        to determine nodal output flux.

        dem_uri - a URI to a DEM raster
        dataset_uri_list - a list of GDAL readable rasters that will be
            used as input to the 'mass_balance_op' operation.  These datasets
            must be aligned with themselves and dem_uri.
        mass_balance_op - a len(dataset_uri_list)+1 function that operates per
            pixel on the aligned pixel stack from dataset_uri_list where the
            first input is the incoming flux from other contributing 
            nodes.
        workspace_dir - a directory that can be used for intermediate
            file generation.  The contents of this directory are not safe
            for preseveration if files already exist in it.
        raster_out_uri - the name/uri of the output raster?  TODO: WHAT OUTPUTS?
        out_nodata_value - the nodata value of the ouput raster TODO: RASTERS?
        aoi_uri - an OGR datasource for an area of interest polygon.
            the routing flux calculation will only occur on those pixels
            and neighboring pixels will either be raw outlets or 
            non-contibuting inputs depending on the orientation of the DEM.

        returns nothing"""

    dem_dataset = gdal.Open(dem_uri)
    dem_band, dem_nodata = raster_utils.extract_band_and_nodata(dem_dataset)
    n_rows, n_cols = dem_band.YSize, dem_band.XSize
    n_elements = n_rows * n_cols

    #Create AOI mask raster
    aoi_mask_uri = os.path.join(workspace_dir, 'aoi_mask.tif')

    #Calculate d-infinity flow direction
    d_inf_dir_uri = os.path.join(workspace_dir, 'd_inf_dir.tif')
    d_inf_dir_nodata = -1.0

    flow_direction_dataset = raster_utils.new_raster_from_base(
        dem_dataset, d_inf_dir_uri, 'GTiff', d_inf_dir_nodata,
        gdal.GDT_Float32)

    bounding_box = [0, 0, n_cols, n_rows]
    invest_cython_core.flow_direction_inf(
        dem_dataset, bounding_box, flow_direction_dataset)
    flow_band, flow_nodata = raster_utils.extract_band_and_nodata(
        flow_direction_dataset)

    #get a memory mapped flow direction array
    flow_direction_filename = os.path.join(workspace_dir, 'flow_direction.dat')
    flow_direction_array = numpy.memmap(
        flow_direction_filename, dtype='float32', mode='w+',
        shape = (n_rows, n_cols))
    LOGGER.info('load flow dataset into array')
    for row_index in range(n_rows):
        row_array = flow_band.ReadAsArray(0, row_index, n_cols, 1)
        flow_direction_array[row_index, :] = row_array

    #This is the array that's used to keep track of the connections. With dinf
    #there are only two cells that can recieve flow, hence the 2 as the second
    #element in the size
    flow_graph_edge_weights = numpy.zeros((n_elements, 2), dtype=numpy.float)
    flow_graph_neighbor_indexes = numpy.zeros((n_elements, 2), dtype = numpy.int)

    #These will be used to determine inflow and outflow later
    inflow_cell_set = set()
    outflow_cell_set = set()

    LOGGER.info('Calculating flow path')
    calculate_flow_path(
        flow_direction_array, flow_nodata,
        flow_graph_edge_weights, flow_graph_neighbor_indexes, outflow_cell_set,
        inflow_cell_set)

    LOGGER.debug("Calculating sink and source cells")

    sink_cells = inflow_cell_set.difference(outflow_cell_set)
    source_cells = outflow_cell_set.difference(inflow_cell_set)

    LOGGER.info('Processing flow through the grid')

    raster_out_dataset = raster_utils.new_raster_from_base(
        dem_dataset, raster_out_uri, 'GTiff', out_nodata_value,
        gdal.GDT_Float32)
    raster_out_band, _, raster_out_array = raster_utils.extract_band_and_nodata(raster_out_dataset, get_array = True)
    raster_out_array[:] = out_nodata_value

    visited_cells = set(source_cells)
    cells_to_process = collections.deque(source_cells)
    
    while len(cells_to_process) > 0:
        cell_index = cells_to_process.popleft()
        cell_row = cell_index / n_cols
        cell_col = cell_index % n_cols

        #if any contributing neighbors aren't processed yet, push back on queue and wait

        if raster_out_array[cell_row, cell_col] == out_nodata_value:
            raster_out_array[cell_row, cell_col] = 1

        for offset in [0, 1]:
            neighbor_index = flow_graph_neighbor_indexes[cell_index, offset]
            neighbor_row = neighbor_index / n_cols
            neighbor_col = neighbor_index % n_cols
            flow_percent = flow_graph_edge_weights[cell_index, offset]

            #propagate flux to neighbors
            if raster_out_array[neighbor_row, neighbor_col] == out_nodata_value:
                raster_out_array[neighbor_row, neighbor_col] = 1 + raster_out_array[cell_row, cell_col] * flow_percent
            else:
                raster_out_array[neighbor_row, neighbor_col] += raster_out_array[cell_row, cell_col] * flow_percent

            if neighbor_index not in visited_cells:
                cells_to_process.append(neighbor_index)
                visited_cells.add(neighbor_index)

    raster_out_band.WriteArray(raster_out_array,0,0)

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

    sink_band.WriteArray(sink_array,0,0)
    source_band.WriteArray(source_array,0,0)

    LOGGER.debug("number of sinks %s number of sources %s" % (len(sink_cells), len(source_cells)))

def calculate_flow_path(
    flow_direction_array, flow_nodata, flow_graph_edge_weights,
    flow_graph_neighbor_indexes, outflow_cell_set, inflow_cell_set):
    """Calculates the graph flow path given a d-infinity flow direction array

        flow_direction_array - numpy 2D array of float with elements that
            describe the d infinity outflow direction from the center of
            that cell.
        
        flow_nodata - the value that represents an undefined value in 
            flow_direction_array

        flow_graph_edge_weights - an output value whose initial state is
            a 2D numpy array of as many rows as there are values in 
            flow_direction_array and two columns.  The two columns indicate
            the two outflow neighbor weights determined by the d infinity
            algorithm which should sum to 1.0.

        flow_graph_neighbor_indexes - an output value whose initial state is
            a 2D numpy array of as many rows as there are values in 
            flow_direction_array and two columns.  The two columns indicate
            the flat indexes of the two outflow neighbor cells.

        outflow_cell_set - an output value whose initial state is an empty
            set.  The output value contains all flat indexes that have
            outflow in the simulation.

        inflow_cell_set - an output value whose initial state is an empty
            set.  The output value contains all flat indexes that have
            inflow in the simulation.

    returns nothing"""

    n_rows, n_cols = flow_direction_array.shape

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

    #Iterate over flow directions
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            flow_direction = flow_direction_array[row_index, col_index]
            #make sure the flow direction is defined, if not, skip this cell
            if flow_direction == flow_nodata:
                continue
            for neighbor_index in range(n_neighbors):
                flow_angle_to_neighbor = numpy.abs(
                    angle_to_neighbor[neighbor_index] - flow_direction)
                if flow_angle_to_neighbor < angle_between_neighbors:
                    #There's flow from the current cell to the neighbor
                    flat_index = row_index * n_cols + col_index
                    outflow_cell_set.add(flat_index)
                    #Determine if the direction we're on is oriented at 90
                    #degrees or 45 degrees.  Given our orientation even number
                    #neighbor indexes are oriented 90 degrees and odd are 45
                    if neighbor_index % 2 == 0:
                        flow_graph_edge_weights[flat_index, 0] = \
                            1.0 - numpy.tan(flow_angle_to_neighbor)
                    else:
                        flow_graph_edge_weights[flat_index, 0] = \
                            numpy.tan(numpy.pi/4.0 - flow_angle_to_neighbor)

                    #Whatever's left will flow into the next clockwise pixel
                    flow_graph_edge_weights[flat_index, 1] = \
                        1.0 - flow_graph_edge_weights[flat_index, 0]
                    
                    #set the edge weight for the current and next edge
                    for edge_index in [0, 1]:
                        #This lets the current index wrap around if we're at 
                        #the last index and we we need to go to 0
                        offset_index = \
                            (neighbor_index + edge_index) % n_neighbors
                        
                        outflow_flat_index = \
                            flat_index + diagonal_offsets[offset_index]

                        flow_graph_neighbor_indexes[flat_index, edge_index] = \
                            outflow_flat_index

                        inflow_cell_set.add(outflow_flat_index)
                    #We don't need to check any more edges
                    break
