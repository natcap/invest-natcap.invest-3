'''Using hybrid approach of cut/fill from Pierre Soille's paper 
"Optimal removal of spuriois pits in grid digital elevation models." The
implementation of it was originally done in C++ by Stephen Jackson at
https://github.com/crwr/OptimizedPitRemoval/blob/master/C%2B%2B%20Code/OptimizedPitRemoval.cpp'''

import os
import sys
import heapq
import logging
import numpy as np

from osgeo import gdal
from invest_natcap import raster_utils

LOGGER = logging.getLogger('PIT FILL')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
   %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

#A handy way of getting the above square as a flow direction
#This way we are checking all cells around the middle one, and 
#then can just write that direction to the numpy array
#in charge of holding all of those.
ROW_OFFSET = [-1, -1, -1, 0, 1, 1, 1, 0]
COL_OFFSET = [-1, 0, 1, 1, 1, 0, -1, -1] 
#TODO: Change this out for getting the nodata value from the raster
nodata = -1000

class NegativeFlowDirection(Exception):
    '''This should come into play when we are looking at an outlet, and
    therefore have no flow direction.'''
    pass

def initialize_pixel_queue(base, direction, flooded):
    '''Input:
        base- numpy array which contains elevation information.
        direction- array which holds the direction from which water comes, 
            using a 8-direction int indicator.
        flooded- 0 = unflooded, 1= flooded, 2 = flooded with confirmed descending
            path to outlet.
    '''
    num_rows, num_cols = base.shape
    
    #Case where it's on the edge of the map
    def is_border(row, col):
        if row == 0 or row == num_rows - 1:
            return True
        elif col == 0 or col == num_cols - 1:
            return True
        else:
            return False
    
    heap = []

    for row in range(num_rows):
        for col in range(num_cols):

            has_nodata_neighbor = False
            for direction_index in range(8):
                try:
                    neighbor_row = row + ROW_OFFSET[direction_index] 
                    neighbor_col = col + COL_OFFSET[direction_index]
                    #print("Currently looking at row: %s, col: %s" % (neighbor_row, neighbor_col))
                    if base[neighbor_row, neighbor_col] == nodata:

                        #Want to set the direction of that pixel to be the direction
                        #FROM which it was flooded
                        direction[col, row] = direction_index
                        has_nodata_neighbor = True
                        break
                #Along the edges, there won't be a full cadre of directions, but we
                #do want to check the rest. 
                except IndexError:
                    continue

            if is_border(row, col) or has_nodata_neighbor:
                #array[x,y] will give the value of the pixel at that coordinate
                heapq.heappush(heap, (base[row, col], (row, col)))
                flooded[row, col] = 2   
   
                #TODO: Need to check that this is an okay thing to do. What
                #should the default direction be in an outlet?
                direction[row, col] = -1

    return heap

def is_local_min(coords, base, flooded):
    
    row, col = coords
    
    #If the cell is in the PQ, it has either been flooded with a 2 or a 1.
    if flooded[row, col] == 2:
        return False

    #Else case is if flooded == 1
    else:
        for direction_index in range(8):
            try:
                neighbor_row = row + ROW_OFFSET[direction_index] 
                neighbor_col = col + COL_OFFSET[direction_index]
               
                #1. If we're less than a neighbor
                #2. if we are the same height as our neighbors, but they're
                #unflooded.
                if base[neighbor_row, neighbor_col] < base[row, col] or \
                    (base[neighbor_row, neighbor_col] == base[row, col] and \
                        flooded[neighbor_row, neighbor_col] == 0):
                    
                    return False
            
            except IndexError:
                continue
    
    #If we haven't returned out of one of the loops up to this point, want to
    #return true for the function.
    return True

def trace_flow(row, col, direction):

    #Want to follow flow direction to an adjacent cell
    flow_direction = direction[row, col]
    
    LOGGER.debug("R: %s, C: %s, Dir: %s" % (row, col, flow_direction))
    if flow_direction == -1:
        raise NegativeFlowDirection

    #Get the row and column coordiates for the cell specified for flow direction
    adj_row = row + ROW_OFFSET[flow_direction]
    adj_col = col + COL_OFFSET[flow_direction]

    return adj_row, adj_col

def find_crest_elev(coords, base, direction, flooded):
    
    reached_outlet = False

    curr_row, curr_col = coords

    while not reached_outlet:

        try:
            adj_row, adj_col = trace_flow(curr_row, curr_col, direction)
        #Flow direction of -1 is code for "this is an outlet itself."
        except NegativeFlowDirection:
            reached_outlet = True
            break
        
        curr_crest = base[curr_row, curr_col] 
        adj_elev = base[adj_row, adj_col]

        #If our neighbor is nodata, we've reached an outlet
        if adj_elev == nodata:
            reached_outlet = True
        #Or if the neighbor is lower, but has a path to the outlet, we've
        #reached an outlet
        elif curr_crest > adj_elev and flooded[adj_row, adj_col] == 2:
            reached_outlet = True
        
        #Otherwise, move to the neighbor, and follow flow direction again.
        else:
            curr_row, curr_col = adj_row, adj_col
            curr_crest = adj_elev

    return curr_crest

def get_depression_extent(coords, base, crest_elev):
    '''Should return a list of the (x,y) of all pixels which are included in
    depression for the point specified by coords.'''
    
    x, y = coords

    #Used to hold the origin pit, as well as the neighbors that have yet to be
    #check if part of the depression extent.
    depress_queue = []
    origin_elev = base[x, y]
    heapq.heappush(depress_queue, (origin_elev, (x, y)))

    depress_extent = []
    #We know the origin pit is part of the depression. So add it.
    depress_extent.append((x, y))

    while depress_queue:
        
        curr_elev, curr_coords = heapq.heappop(depress_queue)
        curr_row, curr_col = curr_coords

        for direction_index in range(8):
            try:
                neighbor_row = curr_row + ROW_OFFSET[direction_index] 
                neighbor_col = curr_col + COL_OFFSET[direction_index]
                #LOGGER.debug("Depression, Neighbor: %s, %s" % (neighbor_row, neighbor_col)) 
                neighbor_elev = base[neighbor_row, neighbor_col]

                #If a neighbor cell is greater than the present cell, but lower
                #than crest elevation, want to add it to the queue.
                if curr_elev <= neighbor_elev < crest_elev and \
                        (neighbor_row, neighbor_col) not in depress_extent:

                    #Add the neighbor to both the queue and our to check its 
                    #neighbors and the list to track known parts of the depression.
                    heapq.heappush(depress_queue, (neighbor_elev, (neighbor_row, neighbor_col)))
                    depress_extent.append((neighbor_row, neighbor_col))
            except IndexError:
                continue

    return depress_extent

def create_cut_function(pit_coords, base, direction, flooded, step):
    
    curr_row, curr_col = pit_coords
    pit_elev = base[curr_row, curr_col]
    reached_outlet = False

    cut_volume = {}

    while not reached_outlet:
       
        try:
            adj_row, adj_col = trace_flow(curr_row, curr_col, direction)
            #LOGGER.debug("AdjR: %s, AdjC: %s" % (adj_row, adj_col))
        #Flow direction of -1 is code for "this is an outlet itself."
        except NegativeFlowDirection:
            LOGGER.debug("This is actually raising an exception!")
            reached_outlet = True
            break

        if base[adj_row, adj_col] == nodata or \
            (base[adj_row, adj_col] < pit_elev and flooded[adj_row, adj_col] == 2):
            reached_outlet = True
        
        else:
            curr_step = pit_elev
            #While the step we're looking at is less than the neighbor elevation.
            while curr_step < base[adj_row, adj_col]:
                
                old_cut = cut_volume[curr_step] if curr_step in cut_volume else 0

                #the old amount we were removing plus the difference between the
                #elevation of the next cell, and the elevation step we're on.
                cut_volume[curr_step] = old_cut + (base[adj_row, adj_col] - curr_step)

                curr_step += step

        #Move to the next cell in flow direction.
        curr_row, curr_col = adj_row, adj_col

    return cut_volume

def create_fill_function(pit_coords, base, depress_coords, crest_elev, step):
    
    fill_volume = {}

    pit_row, pit_col = pit_coords

    for curr_row, curr_col in depress_coords:
        
        #Initialize to the lowest point in the depression.
        curr_elev = base[curr_row, curr_col]
        #Initialize to teh pit elevation, since we'll work up from there.
        curr_step = base[pit_row, pit_col]
        
        while curr_step < crest_elev:
            if curr_step > curr_elev:
                
                old_fill = fill_volume[curr_step] if curr_step in fill_volume else 0
                
                fill_volume[curr_step] = old_fill + curr_step - curr_elev
            
            curr_step += step
        
        #When curr_step is at crest elevation, or happens to go over.
        else:
            #TODO: Ascertain whether there could be more than one pixel which would
            #twig this condition. So we would be rewriting the udeal fill level for
            #the crest more than once.
            old_fill = fill_volume[crest_elev] if crest_elev in fill_volume else 0
            fill_volume[crest_elev] = old_fill + crest_elev - curr_elev

    return fill_volume

def get_ideal_fill_level(pit_elev, crest_elev, cut_volume, fill_volume, step_size):

    best_min_cost = sys.maxint
    best_cost_step = None

    #If the steps should go up to the crest, want to make sure that it's added
    #to the steps we'll be checking.
    step_range = range(pit_elev, crest_elev, step_size)
    step_range = step_range + [crest_elev] if crest_elev % step_size == 0 else step_range
    LOGGER.debug("Step range: %s" % step_range)
    LOGGER.debug("Pit Elev: %s, Crest_Elev: %s" % (pit_elev, crest_elev))

    for level in step_range:
       
        #This allows us to not have to instantiate all levels for the dictionaries,
        #since we know we would just be setting them to 0.
        cut_cost = cut_volume[level] if level in cut_volume else 0
        fill_cost = fill_volume[level] if level in fill_volume else 0

        difference = abs(fill_cost-cut_cost)
        LOGGER.debug("Difference: %s " % difference)

        if difference < best_min_cost:
            best_min_cost = abs(fill_cost - cut_cost)
            best_cost_step = level

    return best_cost_step

def fill_to_elev(pit_coords, depress_coords, de_pit, elev):
    
    #Fill the pit
    pit_row, pit_col = pit_coords
    de_pit[pit_row, pit_col] = elev

    #Fill the rest of the depression
    for dep_row, dep_col in depress_coords:
       
        if de_pit[dep_row, dep_col] < elev:
            de_pit[dep_row, dep_col] = elev

def cut_to_elev(pit_coords, base, direction, flooded, de_pit, elev):
    
    reached_outlet = False
    curr_row, curr_col = pit_coords

    while not reached_outlet:
        
        try:
            adj_row, adj_col = trace_flow(curr_row, curr_col, direction)
        #Flow direction of -1 is code for "this is an outlet itself."
        except NegativeFlowDirection:
            reached_outlet = True
            break
        
        if base[adj_row, adj_col] == nodata or \
            (base[adj_row, adj_col] < elev and flooded[adj_row, adj_col] == 2):
            reached_outlet = True
        else:
            #TODO: Make sure that we really need an if statement here. What happens if
            #we don't have it?
            if base[adj_row, adj_col] > elev:
                de_pit[adj_row, adj_col] = elev

            #TODO: Check if this is really necessary.
            #Shouldn't this already be true?
            flooded[adj_row, adj_col] = 2

        #Move to the next cell in flow direction.
        curr_row, curr_col = adj_row, adj_col

def hybrid_pit_removal(coords, base, direction, flooded, de_pit, step_size):

    row, col = coords
    pit_elev = base[row, col]

    crest_elev = find_crest_elev(coords, base, direction, flooded)

    #Returns an elevation ordered list of the coordinates that make up the
    #current depression. These are less than the crest elevation, but greater 
    #than or equal to the original pit.
    depress_coords = get_depression_extent(coords, base, crest_elev)
    
    #Returns dictionary which maps elevation steps to their corresponding cut
    #amount.
    #TODO: step size should be passed in as an argument
    LOGGER.debug("Pit at : %s, Depress_Extent: %s" % (coords, depress_coords))
    LOGGER.debug("pre-error Direction is: %s" % direction[12,162])
    cut_volume = create_cut_function(coords, base, direction, flooded, step_size)

    fill_volume = create_fill_function(coords, base, depress_coords, crest_elev, step_size)
    LOGGER.debug("Row %s, Col: %s" % (row, col))
    LOGGER.debug("Elev is: %s" % pit_elev)
    LOGGER.debug("Flooded: %s" % flooded[row, col])
    ideal_level = get_ideal_fill_level(pit_elev, crest_elev, cut_volume, fill_volume, step_size)
    
    #Now, fix it.
    fill_to_elev(coords, depress_coords, de_pit, ideal_level)
    cut_to_elev(coords, base, direction, flooded, de_pit, ideal_level)

    #TODO: Do we actually need to set the pit to flooded here, or would it have
    #happened organically within cut/fill?
    flooded[row, col] = 2

def main():
    '''All the initializations. We assume that these would come from the params
    being passed into the function call.'''
    base_uri = 'smaller_clipped_dem.tif'
    raster = gdal.Open(base_uri)
    band = raster.GetRasterBand(1)
    
    #ALL THE NUMPY ARRAYS
    base_array = band.ReadAsArray()
    direction_array = np.empty_like(base_array)
    flooded_array = np.zeros_like(base_array)
    de_pit_array = np.copy(base_array)
    
    #Initialization of the priority queue
    pixel_queue = initialize_pixel_queue(base_array, direction_array, flooded_array)

    #Var that will come from the user.
    step_size = 100

    print('Initialization done.')

    #Running through currently queued items and doing the stuff.
    while pixel_queue:
        
        #print('In the queue. Still moving')

        curr_elev, curr_coords = heapq.heappop(pixel_queue)
        row, col = curr_coords

        #We know that we are looking at the coordinates of a pit,
        #now want to take the hybrid approach to filling.
        if is_local_min(curr_coords, base_array, flooded_array):
            
            #DO THE THINGS! WITH THE STUFF!
            hybrid_pit_removal(
                curr_coords, base_array, direction_array,
                flooded_array, de_pit_array, step_size)
        
        #We're not looking at a pit for the current cell
        else:
            #Correcting places where pits were removed, but they remain 
            #classified as flooded = 1.
            if flooded_array[row, col] == 1:
                for direction_index in range(8):
                    try:
                        neighbor_row = row + ROW_OFFSET[direction_index]
                        neighbor_col = col + COL_OFFSET[direction_index]

                        #If our neighbor is flooded with a confirmed path to outlet,
                        #and their terrain le less than ours
                        if (flooded_array[neighbor_row, neighbor_col] == 2 and
                            base_array[neighbor_row, neighbor_col] < curr_elev):
                            flooded_array[row, col] = 2
                            break
                    except IndexError:
                        continue

        #Now, go through the neighbors of the current cell which have yet to
        #be flooded, set flooding direction for them as coming from us, 
        #check whether they should be counted as having a path to outlet or not.
        for direction_index in range(8):
            try:
                neighbor_row = row + ROW_OFFSET[direction_index]
                neighbor_col = col + COL_OFFSET[direction_index]

                #Want only those neighbors who are "dry" (flooded == 0)
                if flooded_array[neighbor_row, neighbor_col] == 0:
                    
                    #If neighbor is higher than us, and we're on a confirmed
                    #path to the outlet.
                    if (base_array[neighbor_row, neighbor_col] >= base_array[row, col] and
                        flooded_array[row, col] == 2):
                        flooded_array[neighbor_row, neighbor_col] = 2
                    #If we know that we're lower than neighbor (since we're first in the PQ),
                    #but don't know if confirmed to outlet.
                    else:
                        flooded_array[neighbor_row, neighbor_col] = 1

                    #Add neighbor to PQ
                    heapq.heappush(
                        pixel_queue, (base_array[neighbor_row, neighbor_col], 
                                      (neighbor_row, neighbor_col)))
                    
                    #Set flow direction for the neighbor as being from original cell.
                    #In terms of direction, want to get the index that will be
                    #opposite of the side of the square that we're currently in.
                    #Adding + mod 8 takes us to the number opposite the current
                    #direction in the square.
                    index_rel_to_neighbor = (direction_index + 4) % 8
                    direction_array[neighbor_row, neighbor_col] = index_rel_to_neighbor
            
            except IndexError:
                continue

    print('Writing de-pitted array back to raster.')

    #Write back to a raster
    de_pit_uri = 'attempt_to_de_pit.tif'
    
    new_dataset = raster_utils.new_raster_from_base(
        raster, de_pit_uri, 'GTiff', nodata, gdal.GDT_Float32)
    
    n_band, n_nodata = raster_utils.extract_band_and_nodata(new_dataset)
    n_band.Fill(n_nodata)
    
    n_band.WriteArray(de_pit_array)



import cProfile
import pstats
cProfile.runctx('main()', globals(), locals(), 'fillstats')
p = pstats.Stats('fillstats')
p.sort_stats('time').print_stats(20)
p.sort_stats('cumulative').print_stats(20)
end = time.time()

#main()
