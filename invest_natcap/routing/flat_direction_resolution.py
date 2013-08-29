import logging
import numpy
import scipy.sparse

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('plateau resolution')


def resolve_flat_regions_for_drainage(dem_array, nodata_value):
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

    def calc_flat_index(row_index, col_index):
        """Helper function to calculate a flat index"""
        return row_index * dem_array.shape[0] + col_index
    
    #Identify flat regions
    LOGGER.info('identifying flat pixels')
    flat_cells = numpy.zeros(dem_array.shape, dtype=numpy.bool)	 
    for row_index in range(1, flat_cells.shape[0] - 1):
        for col_index in range(1, flat_cells.shape[1] - 1):
            flat_cells[row_index, col_index] = (dem_array[row_index-1:row_index+2, col_index-1:col_index+2] >= dem_array[row_index, col_index]).all()
    LOGGER.debug(flat_cells)

    #Identify sink cells
    LOGGER.info('identify sink cells')
    sink_cells = numpy.zeros(dem_array.shape, dtype=numpy.bool)
    sink_cell_list = []
    for row_index in range(1, flat_cells.shape[0] - 1):
        for col_index in range(1, flat_cells.shape[1] - 1):
            #If the cell is flat, it's not a drain
            if flat_cells[row_index, col_index]: continue
            
            for neighbor_row, neighbor_col in [(0, 1), (1, 1), (1, 0), (1, -1),
                (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
            
                if (dem_array[row_index + neighbor_row, col_index + neighbor_col] == dem_array[row_index, col_index] and
                    flat_cells[row_index + neighbor_row, col_index + neighbor_col]):
                    
                    sink_cells[row_index, col_index] = True
                    sink_cell_list.append(calc_flat_index(row_index, col_index))
                    break
    LOGGER.debug(sink_cells)

    LOGGER.info('construct connectivity path for sinks and flat regions')
    connectivity_matrix = scipy.sparse.lil_matrix(
        (dem_array.size, dem_array.size))

        
    edge_cell_list = []
    for row_index in range(1, flat_cells.shape[0] - 1):
        for col_index in range(1, flat_cells.shape[1] - 1):
            if not flat_cells[row_index, col_index] and not sink_cells[row_index, col_index]: continue
            
            #Loop through each cell and visit the neighbors.  If two flat cells
            #touch each other, connect them.
            current_index = calc_flat_index(row_index, col_index)
            for neighbor_row, neighbor_col in [(0, 1), (1, 1), (1, 0),
                (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
                if (flat_cells[row_index + neighbor_row, col_index + neighbor_col] or
                    sink_cells[row_index + neighbor_row, col_index + neighbor_col]):
                    neighbor_index = calc_flat_index(
                        row_index + neighbor_row, col_index + neighbor_col)
                    connectivity_matrix[current_index, neighbor_index] = 1
                if flat_cells[row_index, col_index] and dem_array[row_index, col_index] < dem_array[row_index + neighbor_row, col_index + neighbor_col]:
                    edge_cell_list.append(current_index)
                    
    LOGGER.info('find distances from sinks to flat cells')
    sink_distance_row = numpy.min(scipy.sparse.csgraph.dijkstra(
        connectivity_matrix, directed=True, indices=sink_cell_list, 
        return_predecessors=False, unweighted=True), axis=0)
        
    #Compress rows of distance matrix into a single row that contains the min
    #distance of all the distances
    LOGGER.debug(sink_distance_row.reshape(flat_cells.shape))
    
    #Identify edge increasing cells
    edge_distance_row = numpy.min(scipy.sparse.csgraph.dijkstra(
        connectivity_matrix, directed=True, indices=edge_cell_list, 
        return_predecessors=False, unweighted=True), axis=0)
    
    max_distance = numpy.max(edge_distance_row[edge_distance_row != numpy.inf])
    
    LOGGER.debug(max_distance)
    edge_distance_row = max_distance + 1 - edge_distance_row    
    LOGGER.debug(edge_distance_row.reshape(flat_cells.shape))
    
    LOGGER.info('resolve any cells that don\'t drain')
    dem_offset = (edge_distance_row + sink_distance_row).reshape(flat_cells.shape)
    for row_index in range(1, flat_cells.shape[0] - 1):
        for col_index in range(1, flat_cells.shape[1] - 1):
            min_offset = numpy.min(dem_offset[row_index-1:row_index+2, col_index-1:col_index+2])
            if min_offset == dem_offset[row_index, col_index]:
                dem_offset[row_index, col_index] += 0.5
                
    LOGGER.debug(dem_offset)

    
    
if __name__ == "__main__":
    dem_array = numpy.array(
        [[9,9,9,9,9,9,9],
         [9,6,6,6,6,6,9],
         [8,6,6,6,6,6,9],
         [8,6,6,6,6,6,9],
         [7,6,6,6,6,6,8],
         [7,6,6,6,6,6,8],
         [7,7,5,7,7,8,8]])

    resolve_flat_regions_for_drainage(dem_array, -1)
