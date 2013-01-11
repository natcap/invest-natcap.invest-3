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
import osgeo.gdalconst
import numpy

from invest_natcap import raster_utils
import invest_cython_core
import routing_cython_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('routing')

def route_flux(
    dem_uri, source_uri, absorption_rate_uri, loss_uri, flux_uri,
    workspace_dir, aoi_uri=None):

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
    outflow_weights_uri = os.path.join(workspace_dir, 'outflow_weights.tif')
    outflow_direction_uri = os.path.join(
        workspace_dir, 'outflow_directions.tif')

    calculate_flow_direction(dem_uri, flow_direction_uri)
    sink_cell_set, _ = routing_cython_core.calculate_flow_graph(
        flow_direction_uri, outflow_weights_uri, outflow_direction_uri)
    routing_cython_core.calculate_transport(
        outflow_direction_uri, outflow_weights_uri, sink_cell_set,
        source_uri, absorption_rate_uri, loss_uri, flux_uri)


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
    dem_band = dem_dataset.GetRasterBand(1)
    n_rows, n_cols = dem_band.YSize, dem_band.XSize

    #Calcualte the d infinity flow direction
    routing_cython_core.flow_direction_inf(
        dem_uri, flow_direction_uri)

    resolve_undefined_flow_directions(dem_uri, flow_direction_uri)

    LOGGER.info(
        'Done calculating d-infinity elapsed time %ss' % (time.clock() - start))


def resolve_undefined_flow_directions(dem_uri, flow_direction_uri):
    """Take a raster that has flow directions already defined and fill in
        the undefined ones.

        dem_uri - the path to a DEM GDAL dataset
        flow_direction_uri - the path to a flow direction dataset whose
            flow directions have already been defined, but may have undefined
            flow directions due to plateaus.  The value of this raster will
            be modified where flow directions that were previously undefined
            will be resolved.

        returns nothing"""

    dem_dataset = gdal.Open(dem_uri)
    dem_band, dem_nodata, dem_array = raster_utils.extract_band_and_nodata(
        dem_dataset, get_array=True)

    flow_direction_dataset = gdal.Open(flow_direction_uri, osgeo.gdalconst.GA_Update)
    flow_direction_band, flow_direction_nodata, flow_direction_array = \
        raster_utils.extract_band_and_nodata(
        flow_direction_dataset, get_array=True)

    n_cols = dem_dataset.RasterXSize
    n_rows = dem_dataset.RasterYSize


    ### Grid cell direction reference
    # 3 2 1
    # 4 x 0
    # 5 6 7

    row_offsets = [0, -1, -1, -1,  0,  1, 1, 1]
    col_offsets = [1,  1,  0, -1, -1, -1, 0, 1]


    cells_to_process = collections.deque()

    #Build an initial list of cells to depth first search through to find
    #minimum distances
    LOGGER.info('Building initial list of edge plateau pixels')
    for row_index in xrange(n_rows):
        for col_index in xrange(n_cols):
            dem_value = dem_array[row_index, col_index]
            if dem_value == dem_nodata:
                continue

            flow_direction_value = flow_direction_array[row_index, col_index]
            if flow_direction_value != flow_direction_nodata:
                continue
            
            dem_neighbors_valid = True
            flow_direction_neighbors_valid = False

            for neighbor_index in xrange(8):
                neighbor_row = row_index + row_offsets[neighbor_index]
                neighbor_col = col_index + col_offsets[neighbor_index]
                
                if neighbor_row < 0 or neighbor_row >= n_rows or \
                        neighbor_col < 0 or neighbor_col >= n_cols:
                    #we're out of range, no way is the dem valid
                    dem_neighbors_valid = False
                    break

                dem_neighbor_value = dem_array[neighbor_row, neighbor_col]

                if dem_neighbor_value == dem_nodata:
                    dem_neighbors_valid = False
                    break

                if flow_direction_array[neighbor_row, neighbor_col] != \
                        flow_direction_nodata and dem_neighbor_value <= dem_value:
                    #Here we found a flow direction that is valid
                    #we can build from here
                    flow_direction_neighbors_valid = True
                
            if dem_neighbors_valid and flow_direction_neighbors_valid:
                #Then we can define a valid direction
                cells_to_process.append(row_index * n_cols + col_index)


    angle_to_neighbor = [0.0, 0.7853981633974483, 1.5707963267948966, 2.356194490192345, 3.141592653589793, 3.9269908169872414, 4.71238898038469, 5.497787143782138]

    LOGGER.info('resolving directions')
    while len(cells_to_process) > 0:
        current_index = cells_to_process.pop()

        row_index = current_index / n_cols
        col_index = current_index % n_cols

        flow_direction_value = flow_direction_array[row_index, col_index]
        if flow_direction_value != flow_direction_nodata:
            continue
        
        for neighbor_index in xrange(8):
            neighbor_row = row_index + row_offsets[neighbor_index]
            neighbor_col = col_index + col_offsets[neighbor_index]
            
            if neighbor_row < 0 or neighbor_row >= n_rows or \
                    neighbor_col < 0 or neighbor_col >= n_cols:
                #we're out of range, no way is the dem valid
                continue

            neighbor_flow_direction = flow_direction_array[neighbor_row, neighbor_col]

            if neighbor_flow_direction == flow_direction_nodata:
                #if the neighbor is undefined it needs it
                cells_to_process.appendleft(neighbor_row * n_cols + neighbor_col)
            else:
                flow_direction_array[row_index, col_index] = angle_to_neighbor[neighbor_index]

    flow_direction_band.WriteArray(flow_direction_array)
