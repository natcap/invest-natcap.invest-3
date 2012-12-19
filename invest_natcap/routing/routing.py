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

from osgeo import gdal
import numpy
import scipy.sparse

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


    #1a) create AOI mask raster
    aoi_mask_uri = os.path.join(workspace_dir, 'aoi_mask.tif')


    #1b) calculate d-infinity flow direction
    d_inf_dir_uri = os.path.join(workspace_dir, 'd_inf_dir.tif')
    d_inf_dir_nodata = -1.0

    bounding_box = [0, 0, n_cols, n_rows]

    flow_direction_dataset = raster_utils.new_raster_from_base(
        dem_dataset, d_inf_dir_uri, 'GTiff', d_inf_dir_nodata,
        gdal.GDT_Float32)

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

    #2)  calculate the flow graph

    #Diagonal offsets are based off the following index notation for neighbors
    #    3 2 1
    #    4 p 0
    #    5 6 7
    #i.e. the node to the right of p is index '0', the one to the lower right
    #is '5' etc.
    #diagonal offsets index is 0, 1, 2, 3, 4, 5, 6, 7 from the figure above
    diagonal_offsets = [
        1, -n_cols+1, -n_cols, -n_cols-1, -1, n_cols-1, n_cols, n_cols+1]
    
    #The number of diagonal offsets defines the neighbors, angle between them
    #and the actual angle to point to the neighbor
    n_neighbors = len(diagonal_offsets)
    angle_between_neighbors = 2.0 * numpy.pi / n_neighbors
    angle_to_neighbor = [
        i * angle_between_neighbors for i in range(n_neighbors)]

    #This is the array that's used to keep track of the connections. It's the
    #diagonals of the matrix stored row-wise.  We add an additional
    flow_graph_diagonals = numpy.zeros((n_neighbors, n_elements+n_neighbors))

    #Iterate over flow directions
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            for neighbor_index in range(n_neighbors):
                flow_angle_to_neighbor = numpy.abs(
                    angle_to_neighbor[neighbor_index] - 
                    flow_direction_array[row_index, col_index])
                if flow_angle_to_neighbor < angle_between_neighbors:
                    #There's flow from the current cell to the neighbor
                    flat_index = row_index * n_cols + col_index
                    
                    #TODO: calculate percent flow
                    percent_flow = 1.0
                    
                    #set the edge weight
                    flow_graph_diagonals[neighbor_index, flat_index+diagonal_offsets[neighbor_index]] = percent_flow

    #This builds the sparse adjaency matrix
    adjacency_matrix = scipy.sparse.spdiags(
        flow_graph_diagonals, diagonal_offsets, n_elements, n_elements)

    LOGGER.debug(flow_graph_diagonals)
