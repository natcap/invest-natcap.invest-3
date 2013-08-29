import logging
import numpy

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
    for row_index in range(1, flat_cells.shape[0] - 1):
        for col_index in range(1, flat_cells.shape[1] - 1):
            #If the cell is flat, it's not a drain
            if flat_cells[row_index, col_index]: continue
            
            for neighbor_row, neighbor_col in [(0, 1), (1, 1), (1, 0), (1, -1),
                (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
            
                if (dem_array[row_index + neighbor_row, col_index + neighbor_col] == dem_array[row_index, col_index] and
                    flat_cells[row_index + neighbor_row, col_index + neighbor_col]):
                    
                    sink_cells[row_index, col_index] = True
                    break
    LOGGER.debug(sink_cells)

    
    #Iterate out from sink increasing along the way
    #Identify edge increasing cells
    #Iterate out from increasing cells

    
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
