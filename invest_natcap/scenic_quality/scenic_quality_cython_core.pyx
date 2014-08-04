
import math
cimport numpy as np
import numpy as np

import cython
from cython.operator import dereference as deref
from libc.math cimport atan2
from libc.math cimport sin

cdef extern from "stdlib.h":
    void* malloc(size_t size)
    void free(void* ptr)

cdef extern from "math.h":
    double atan2(double x, double x)

def list_extreme_cell_angles(array_shape, viewpoint_coords, max_dist):
    """List the minimum and maximum angles spanned by each cell of a
        rectangular raster if scanned by a sweep line centered on
        viewpoint_coords.
    
        Inputs:
            -array_shape: a shape tuple (rows, cols) as is created from
                calling numpy.ndarray.shape()
            -viewpoint_coords: a 2-tuple of coordinates similar to array_shape
            where the sweep line originates
            -max_dist: maximum viewing distance
            
        returns a tuple (min, center, max, I, J) with min, center and max 
        Nx1 numpy arrays of each raster cell's minimum, center, and maximum 
        angles and coords as two Nx1 numpy arrays of row and column of the 
        coordinate of each point.
    """
    cdef:
        # constants
        double pi = 3.141592653589793238462643
        double two_pi = 2. * pi
        double max_dist_sq = max_dist**2 if max_dist >= 0 else 1000000000
        # viewpoint coordinates
        int viewpoint_row = viewpoint_coords[0]
        int viewpoint_col = viewpoint_coords[1]
        # vector from viewpoint to currently processed cell
        int viewpoint_to_cell_row
        int viewpoint_to_cell_col
        # array sizes
        int array_rows = array_shape[0]
        int array_cols = array_shape[1]
        # Number of cells processed
        int cell_count = 0
        # This array stores the offset coordinates to recover the first 
        # and last corners of a cell reached by the sweep line. Since the 
        # line sweeps from angle 0 to angle 360, the first corner 
        # is associated with the lowest sweep line angle (min angle), and the
        # last corner with the highest angle (max angle). 
        # Each group of 4 values correspond to a sweep line-related angular 
        # sector:
        # -row 0: cell centers at angle a = 0 (east of viewpoint)
        # -row 1: cell centers at angle 0 < a < 90
        # -row 2: cell centers at angle a = 90 (north of viewpoint)
        # -row 3: cell centers at angle 90 < a < 180
        # -row 4: cell centers at angle a = 180 (west of viewpoint)
        # -row 5: cell centers at angle 180 < a < 270
        # -row 6: cell centers at angle a = 270 (south of viewpoint)
        # -row 7: cell centers at angle 270 < a < 360
        # The 4 values encode 2 pairs of offsets:
        #   -first 2 values: [row, col] first corner offset coordinates 
        #   -last 2 values: [row, col] last corner offset coordinates 
        double *extreme_cell_points = [ \
        0.5, -0.5, -0.5, -0.5, \
        0.5, 0.5, -0.5, -0.5, \
        0.5, 0.5, 0.5, -0.5, \
        -0.5, 0.5, 0.5, -0.5, \
        -0.5, 0.5, 0.5, 0.5, \
        -0.5, -0.5, 0.5, 0.5, \
        -0.5, -0.5, -0.5, 0.5, \
        0.5, -0.5, -0.5, 0.5]
        # constants for fast axess of extreme_cell_points
        size_t SECTOR_SIZE = 4 # 4 values in a row
        size_t POINT_SIZE = 2 # 2 coordinates per point per point
        size_t min_point_id # first corner base index
        size_t max_point_id # last corner base index
        # row of the first corner met by the sweep line
        double min_corner_row
        double min_corner_col
        # row of the last corner met by the sweep line
        double max_corner_row
        double max_corner_col
        # offset from the cell center to the first corner
        double min_corner_offset_row
        double min_corner_offset_col
        # offset from the cell center to the last corner
        double max_corner_offset_row
        double max_corner_offset_col
        # C array that will be used in the loop
        # pointer to min angle values
        double *min_a_ptr = NULL
        # pointer to cell center angle values
        double *a_ptr = NULL
        # pointer to max angle values
        double *max_a_ptr = NULL
        # pointer to the cells row number
        long *I_ptr = NULL
        # pointer to the cells column number
        long *J_ptr = NULL
        # variables used in the loop
        int cell_id = 0 # processed cell counter
        int row # row counter
        int col # column counter
        int sector # current sector

    # Count sixe of arrays before allocating
    # Loop through the rows
    for row in range(array_rows):
        viewpoint_to_cell_row = row - viewpoint_row
        # Loop through the columns    
        for col in range(array_cols):
            viewpoint_to_cell_col = col - viewpoint_col
            # Skip if cell is too far
            d = viewpoint_to_cell_row**2 + viewpoint_to_cell_col**2
            if d > max_dist_sq:
                continue
            # Skip if cell falls on the viewpoint
            if (row == viewpoint_row) and (col == viewpoint_col):
                continue
            cell_count += 1
    # Allocate the arrays
    min_a_ptr = <double *>malloc((cell_count) * sizeof(double))
    a_ptr = <double *>malloc((cell_count) * sizeof(double))
    max_a_ptr = <double *>malloc((cell_count) * sizeof(double))
    I_ptr = <long *>malloc((cell_count) * sizeof(long))
    J_ptr = <long *>malloc((cell_count) * sizeof(long))

    # Fill out the arrays
    # Loop through the rows
    for row in range(array_rows):
        viewpoint_to_cell_row = row - viewpoint_row
        # Loop through the columns    
        for col in range(array_cols):
            viewpoint_to_cell_col = col - viewpoint_col
            # Skip if cell is too far
            d = viewpoint_to_cell_row**2 + viewpoint_to_cell_col**2
            if d > max_dist_sq:
                continue
            # Skip if cell falls on the viewpoint
            if (row == viewpoint_row) and (col == viewpoint_col):
                continue
            # cell coordinates
            # Update list of rows and list of cols
            I_ptr[cell_id] = row
            J_ptr[cell_id] = col
            # Compute the angle of the cell center
            angle = atan2(-(row - viewpoint_row), col - viewpoint_col)
            a_ptr[cell_id] = (angle + two_pi) % two_pi
            # find index in extreme_cell_points that corresponds to the current
            # angle to compute the offset from cell center
            # This line only discriminates between 4 axis-aligned angles
            sector = <int>(4. * a_ptr[cell_id] / two_pi) * 2
            # The if statement adjusts for all the 8 angles
            if abs(viewpoint_to_cell_row * viewpoint_to_cell_col) > 0:
                sector += 1
            # compute extreme corners
            min_point_id = sector * SECTOR_SIZE # Beginning of a row
            max_point_id = min_point_id + POINT_SIZE # Skip a point
            # offset from current cell center to first corner
            min_corner_offset_row = extreme_cell_points[min_point_id]
            min_corner_offset_col = extreme_cell_points[min_point_id + 1]
            # offset from current cell center to last corner
            max_corner_offset_row = extreme_cell_points[max_point_id]
            max_corner_offset_col = extreme_cell_points[max_point_id + 1]
            # Compute the extreme corners from the offsets
            min_corner_row = viewpoint_to_cell_row + min_corner_offset_row
            min_corner_col = viewpoint_to_cell_col + min_corner_offset_col
            max_corner_row = viewpoint_to_cell_row + max_corner_offset_row
            max_corner_col = viewpoint_to_cell_col + max_corner_offset_col
            # Compute the angles associated with the extreme corners
            min_angle = atan2(-min_corner_row, min_corner_col)
            max_angle = atan2(-max_corner_row, max_corner_col)
            # Save the angles in the fast C arrays
            min_a_ptr[cell_id] = (min_angle + two_pi) % two_pi 
            max_a_ptr[cell_id] = (max_angle + two_pi) % two_pi
            cell_id += 1
    # Copy C-array contents to numpy arrays:
    # TODO: use memcpy if possible (or memoryviews?)
    min_angles = np.ndarray(cell_count, dtype = np.float)
    angles = np.ndarray(cell_count, dtype = np.float)
    max_angles = np.ndarray(cell_count, dtype = np.float)
    I = np.ndarray(cell_count, dtype = np.int32)
    J = np.ndarray(cell_count, dtype = np.int32)

    for i in range(cell_count):
        min_angles[i] = min_a_ptr[i]
        angles[i] = a_ptr[i]
        max_angles[i] = max_a_ptr[i]
        I[i] = I_ptr[i]
        J[i] = J_ptr[i]
    # clean-up
    free(I_ptr)
    free(J_ptr)
    free(min_a_ptr)
    free(a_ptr)
    free(max_a_ptr)

    return (min_angles, angles, max_angles, I, J)

# Cython versions of aesthetic_quality_core's active_pixel helper functions
# I'm trying to avoid cythonizing the more efficient version with skip lists,
# because they are much more complicated to design and maintain.

# struct that mimics python's dictionary implementation
cdef struct ActivePixel:
    long is_active # Indicate if the pixel is active
    long index # long is python's default int type
    double distance # double is python's float type
    double visibility
    double offset
    ActivePixel *next

def print_python_pixel(pixel):
    print('pixel', pixel['distance'], 'next', \
    None if pixel['next'] is None else pixel['next']['distance'])

def print_sweep_line(sweep_line):
    if 'closest' not in sweep_line:
        print('empty sweep line')
    else:
        pixel = sweep_line['closest']
        while pixel is not None:
            print_python_pixel(pixel)
            pixel = pixel['next']

cdef print_active_pixel(ActivePixel *pixel):
    print('pixel', 'NULL' if pixel is NULL else deref(pixel).distance, \
    'next', 'NULL' if pixel is NULL or deref(pixel).next is NULL else \
    deref(deref(pixel).next).distance)
    

cdef print_active_pixels(ActivePixel *active_pixels):
    cdef ActivePixel *pixel

    if active_pixels is not NULL:
        # extract data from the closest distance first
        pixel = active_pixels
        print_active_pixel(pixel)
        # Proceed to the next entry as long as there are valid pixels
        while pixel.next is not NULL:
            # get the next pixel
            pixel = deref(pixel).next
            print_active_pixel(pixel)
    else:
        print('active pixels is empty')

def dict_to_active_pixels_to_dict(sweep_line):
    """Converts a sweep_line to an ActivePixel array and back and return it.
    
    Inputs: 
        -sweep_line: a sweep line creatd with add_active_pixel in 
        aesthetic_quality_core.

    Returns a new sweep_line after being converted to ActivePixel 
    and back. For debug purposes to see if the conversion functions work
    """
    original_sweep_line_size = len(sweep_line)
    # Retreive the active pixels
    cdef ActivePixel *active_pixels = dict_to_active_pixels(sweep_line)
    # Converts the active pixels back to a python dictionary and return it
    sweep_line = active_pixels_to_dict(active_pixels)
    message = 'dict_to_active_pixels_to_dict: original sweep line size ' + \
    str(original_sweep_line_size) + " is different from new sweep line's " + \
    str(len(sweep_line))
    assert len(sweep_line) == original_sweep_line_size, message
    pixels_deleted = delete_active_pixels(active_pixels)
    message = "dict_to_active_pixels_to_dict: deleted pixel count " + \
    str(pixels_deleted) + " doesn't agree with sweep line length " + \
    str(max(0, len(sweep_line) -1))
    assert pixels_deleted == max(0, (len(sweep_line)-1)), message

    return sweep_line

cdef active_pixel_to_dict(ActivePixel active_pixel):
    """Convert a single ActivePixel object to a dictionary"""    
    pixel = {}
    pixel['index'] = active_pixel.index
    pixel['visibility'] = active_pixel.visibility
    pixel['distance'] = active_pixel.distance
    pixel['next'] = None # might be overridden later

    return pixel

cdef active_pixels_to_dict(ActivePixel *active_pixels):
    """Convert a python dictionary of active pixels to a C ActivePixel*"""
    sweep_line = {}
    cdef ActivePixel pixel

    if active_pixels is not NULL:
        # extract data from the closest distance first
        pixel = deref(active_pixels)
        # create the first distance in sweep_line
        sweep_line[pixel.distance] = active_pixel_to_dict(pixel)
        # Make 'closest' point to the first distance
        sweep_line['closest'] = sweep_line[pixel.distance]
        # We'll need this later to update the 'next' field if necessary
        last_distance = pixel.distance
        # Proceed to the next entry as long as there are valid pixels
        while pixel.next is not NULL:
            # get the next pixel
            pixel = deref(pixel.next)
        # Fill up the sweep_line with pixels
        sweep_line[pixel.distance] = active_pixel_to_dict(pixel)
        # Update the last pixel's 'next' field
        sweep_line[last_distance]['next'] = sweep_line[pixel.distance]
        # Update last_distance for next loop
        last_distance = pixel.distance

    return sweep_line

cdef ActivePixel *dict_to_active_pixels(sweep_line):
    """Convert a python dictionary of active pixels to a C ActivePixel*"""
    cdef ActivePixel *active_pixel = NULL # New pixel being created
    cdef ActivePixel *previous = NULL # previous pixel that needs an update
    cdef ActivePixel *first_pixel = NULL # closest pixel in the sweep line

    if 'closest' in sweep_line:
     # Construct the active pixel list with values from sweep_line
     pixel = sweep_line['closest']
     while pixel is not None:
         # Dynamically allocate the active pixels individually
         active_pixel =<ActivePixel*>malloc(sizeof(ActivePixel))
         assert active_pixel is not NULL, "can't allocate new active pixel"
         # Keep the first pixel's address around
         if first_pixel is NULL:
              first_pixel = active_pixel
         # set up the values in active_pixels
         active_pixel.index = pixel['index']
         active_pixel.visibility = pixel['visibility']
         active_pixel.distance = pixel['distance']
         # Set the 'next' field to NULL for the moment
         active_pixel.next = NULL
         # Update the 'next' field if it's possible
         if previous is not NULL:
             deref(previous).next = active_pixel
         # Move on to the next pixel
         pixel = pixel['next']
         previous = active_pixel

    return first_pixel

cdef int delete_active_pixels(ActivePixel *first_pixel):
    """Delete every pixel in the active_pixel linked list"""
    deleted_pixels = 0 # Keep a count of how many pixels have been deleted
    cdef ActivePixel *pixel_to_delete = NULL # The pixel to be deleted
    # Iterate through the linked list and delete every pixel on the way
    while first_pixel is not NULL:
        pixel_to_delete = first_pixel
        first_pixel = deref(first_pixel).next # new first pixel
        free(pixel_to_delete)
        deleted_pixels += 1

    return deleted_pixels

def find_active_pixel(sweep_line, distance):
    """Python wrapper for the cython find_active_pixel_cython function"""
    cdef: 
        ActivePixel *active_pixels
        ActivePixel *active_pixel
        
    result = None
        
    if 'closest' in sweep_line:
        # Convert sweep_line to ActivePixel *. Need to delete active_pixels.
        active_pixels = dict_to_active_pixels(sweep_line)
        # Invoke the low-level function to find the right value
        active_pixel = find_active_pixel_cython(active_pixels, distance)
        # Convert C-style pixel to python dictionary if possible
        if active_pixel is not NULL:
            result = active_pixel_to_dict(deref(active_pixel))
        # clean-up
        pixels_deleted = delete_active_pixels(active_pixels)
        # Try to keep track of memory leaks
        message = "find_active_pixels: deleted pixel count " + \
        str(pixels_deleted) + " doesn't agree with sweep line length " + \
        str(max(0, len(sweep_line) -1))
        assert pixels_deleted == max(0, len(sweep_line)-1), message

    return result

# Find an active pixel based on distance. Return None if it can't be found
cdef ActivePixel* find_active_pixel_cython(ActivePixel *closest, double distance):
    cdef ActivePixel *pixel = NULL
    if closest is not NULL:
        # Get information about first pixel in the list
        pixel = closest
        # Move on to next pixel if we can (not a NULL pointer)
        while pixel is not NULL and deref(pixel).distance < distance:
            pixel = deref(pixel).next

        if (pixel is not NULL) and (deref(pixel).distance != distance):
            return NULL

    return pixel


def add_active_pixel(sweep_line, index, distance, visibility, offset):
    """Python wrapper for the cython find_active_pixel_cython function"""
    #print('adding ' + str(distance) + ' to cython list')
    #print_sweep_line(sweep_line)
    # Make sure we're not creating any duplicate
    message = 'Duplicate entry: the value ' + str(distance) + ' already exist'
    assert distance not in sweep_line, message

    cdef ActivePixel *active_pixels = dict_to_active_pixels(sweep_line)
    active_pixels = \
    add_active_pixel_cython(active_pixels, index, distance, visibility, offset)
    sweep_line = active_pixels_to_dict(active_pixels)
    pixels_deleted = delete_active_pixels(active_pixels)
    message = "add_active_pixels: deleted pixel count " + \
    str(pixels_deleted) + " doesn't agree with sweep line length " + \
    str(max(0, len(sweep_line) -1))
    assert pixels_deleted == max(0, len(sweep_line)-1), message

    return sweep_line

# What is needed: 
#   -maintain a pool of available pixels
#   -figure out how to deallocate the active pixels
cdef inline ActivePixel *add_active_pixel_cython(ActivePixel *closest, \
    int index, double distance, double visibility, double offset):
    """Add a pixel to the sweep line in O(n) using a linked_list of
    linked_cells."""

    cdef:
        ActivePixel *previous = NULL
        ActivePixel *pixel = closest
        ActivePixel *new_pixel = NULL
    if pixel is not NULL:
        while deref(pixel).next is not NULL and \
            deref(pixel).distance < distance:
            previous = pixel
            pixel = deref(pixel).next
        if deref(pixel).next is not NULL:
            message = "won't override existing distance " + str(distance)
            assert deref(pixel).distance != distance, message

        new_pixel = <ActivePixel*>malloc(sizeof(ActivePixel))
        assert new_pixel is not NULL, 'new pixel assignment failed'
        deref(new_pixel).next = NULL
        deref(new_pixel).index = index
        deref(new_pixel).distance = distance
        deref(new_pixel).visibility = visibility
        deref(new_pixel).offset = offset

        # Found something
        if deref(pixel).distance < distance:
            # insert at the end
            deref(pixel).next = new_pixel
        elif previous is NULL:
            # insert at the beginning
            deref(new_pixel).next = closest
            closest = new_pixel
        else:
            # insert between the ends
            deref(previous).next = new_pixel # previous points to new
            deref(new_pixel).next = pixel # new points to next pixel
    # Closest is NULL: just make it point to the new pixel
    else:
        closest = <ActivePixel*>malloc(sizeof(ActivePixel))
        deref(closest).next = NULL
        deref(closest).index = index
        deref(closest).distance = distance
        deref(closest).visibility = visibility
        deref(closest).offset = offset

    return closest

def remove_active_pixel(sweep_line, distance):
    """Python wrapper for the cython remove_active_pixel_cython function"""
    #print('removing ' + str(distance) + ' from cython list')
    #print_sweep_line(sweep_line)
    cdef ActivePixel *active_pixels = dict_to_active_pixels(sweep_line)
    sweep_line_length = len(sweep_line)
    active_pixels = \
    remove_active_pixel_cython(active_pixels, distance)
    sweep_line = active_pixels_to_dict(active_pixels)
    pixels_deleted = delete_active_pixels(active_pixels)
    if pixels_deleted == 0 and sweep_line_length == 0: # Empty list?
        pixels_deleted = -1 # Adjust so the assertion subtraction is still 0
    message = "remove_active_pixels: deleted pixel count " + \
    str(pixels_deleted) + " doesn't agree with sweep line length " + \
    str(max(0, len(sweep_line) -1))
    assert pixels_deleted == max(0, len(sweep_line)-1), message

    return sweep_line

cdef inline ActivePixel *remove_active_pixel_cython(ActivePixel *closest, \
    double distance):
    """Remove a pixel based on distance. Do nothing if can't be found."""
    cdef ActivePixel *previous = NULL
    cdef ActivePixel *pixel = NULL
    cdef ActivePixel *next = NULL

    if closest is not NULL:
        # Initialize to first pixel in the list
        pixel = closest
    # Move on to next pixel if we're not done
    while (pixel is not NULL) and \
        (deref(pixel).distance < distance):
        #print('moving to next pixel')
        previous = pixel
        pixel = deref(pixel).next
    # We reached the end and didn't find anything
    if pixel is NULL:
        return closest
    # We didn't reach the end: either pixel doesn't exist:
    if deref(pixel).distance != distance:
        return closest
    # Or we found the value we want to delete
    # Make the previous element point to the next
    # We're at the beginning of the list: update the list's first element
    if previous is NULL:
        next = deref(pixel).next
        # No next pixel: we have to delete 'closest'
        if next is NULL:
            free(closest) # same as free(pixel)
            closest = NULL
        # Otherwise, update it
        else:
            free(closest) # same as free(pixel)
            closest = next
    # We're not at the beginning of the list: only update previous
    else:
        deref(previous).next = deref(pixel).next
        free(pixel)

    return closest


def update_visible_pixels(active_pixels, I, J, d, visibility_map):
    """Python wrapper for the cython function update_visible_pixels"""
    # Update visibility and create a binary map of visible pixels
    # -Look at visibility from closer pixels out, keep highest visibility
    # -A pixel is not visible if its visibility <= highest visibility so far
    if not active_pixels:
        return

    active_pixels_length = max(0, len(active_pixels) -1)
    cdef ActivePixel *closest = dict_to_active_pixels(active_pixels)

    update_visible_pixels_cython(closest, I, J, d, visibility_map)

    pixels_deleted = delete_active_pixels(closest)

    message = 'update_visible_pixels: deleted pixel count (' + \
    str(pixels_deleted) + ') differs from original active pixel count ' + \
    str(active_pixels_length)
    assert active_pixels_length == pixels_deleted, message


cdef void update_visible_pixels_fast(ActivePixel *active_pixel_array, \
    np.ndarray[int, ndim = 1] I, np.ndarray[int, ndim = 1] J, \
    int pixel_count, \
    np.ndarray[np.float64_t, ndim = 2] visibility_map):
        
    cdef ActivePixel p

    print('update_visible_pixels_fast')
    for pixel_id in range(pixel_count):
        p = active_pixel_array[pixel_id]
        print('pixel', pixel_id, 'visible', p.is_active)
    # Pixel is visible
    #if p.offset > max_visibility:
    #    visibility = 1.
    #    visibility = p.offset - max_visibility
    #else:
    #    visibility = 0.
    #    visibility = p.offset - max_visibility
    #if p.visibility > max_visibility:
    #    max_visibility = p.visibility

    # Update the visibility map for this pixel
    #index = p.index
    #if visibility_map[I[index], J[index]] == 0:
    #    visibility_map[I[index], J[index]] = visibility
    #pixel = p.next

cdef void update_visible_pixels_cython(ActivePixel *closest, \
    np.ndarray[int, ndim = 1] I, np.ndarray[int, ndim = 1] J, \
    np.float64_t d, \
    np.ndarray[np.float64_t, ndim = 2] visibility_map):
    """Update the array of visible pixels from the active pixel's visibility
        
        Inputs:
        -closest: an ActivePixel pointer to a linked list 
        of ActivePixel. These are nums with the following fields:
        -distance: distance between pixel center and viewpoint
        -visibility: an elevation/distance ratio used by the
        algorithm to determine what pixels are bostructed
        -index: pixel index in the event stream, used to find the
        pixel's coordinates 'i' and 'j'.
        -next: points to the next pixel, or is None if at the end
        The linked list is implemented with a dictionary where the
        pixels distance is the key. The closest pixel is also
        referenced by the key 'closest'.
        -I: the array of pixel rows indexable by pixel['index']
        -J: the array of pixel columns indexable by pixel['index']
        -visibility_map: a python array the same size as the DEM
        with 1s for visible pixels and 0s otherwise. Viewpoint is
        always visible.
            
    Returns nothing"""
    cdef ActivePixel *pixel = NULL
    cdef ActivePixel p
    cdef double max_visibility = -1000000.
    cdef double visibility = 0
    cdef int index = -1
     
    # Update visibility and create a binary map of visible pixels
    # -Look at visibility from closer pixels out, keep highest visibility
    # -A pixel is not visible if its visibility <= highest visibility so far
    if closest is NULL:
        return

    pixel = closest
    while pixel is not NULL:
        p = deref(pixel)
        # Pixel is visible
        if p.offset > max_visibility:
            visibility = 1.
            visibility = p.offset - max_visibility
        else:
            visibility = 0.
            visibility = p.offset - max_visibility
        if p.visibility > max_visibility:
            max_visibility = p.visibility

        # Update the visibility map for this pixel
        index = p.index
        if visibility_map[I[index], J[index]] == 0:
            visibility_map[I[index], J[index]] = visibility
        pixel = p.next

def _active_pixel_index(O, P, E):
    O = [float(O[0]), float(O[1])]
    P = [float(P[0]), float(P[1])]
    E = [float(E[0]), float(E[1])]
    # Compute the long and short components
    if abs(E[0]-O[0]) > abs(E[1]-O[1]):
        l = 0 # Long component is along the 'i' axis (rows)
        s = 1 # Short component is along the 'j' axis (cols)
    else:
        l = 1 # Long component is along the 'j' axis (cols)
        s = 0 # Short component is along the 'i' axis (rows)

    Os = O[s]
    Ol = O[l]
    Es = E[s]
    El = E[l]

    Sl = -1 if (Ol>El) else 1
    Ss = -1 if (Os>Es) else 1

    slope = 0 if El==Ol else (Es-Os) / (El-Ol)
    #if El!=Ol:
    #    print('Os', Os, 'Ol', Ol, 'Es', Es, 'El', El, 'Ps', P[s], 'Pl', P[l])
    #    print('Es-Os', Es-Os, ' / El-Ol', El-Ol, 'slope', slope)

    return active_pixel_index(Ol, Os, P[l], P[s], El, Es, Sl, Ss, slope)

cdef int active_pixel_index(double Ol, double Os, \
                        double Pl, double Ps, \
                        double El, double Es, \
                        double Sl, double Ss,
                        double slope):
    cdef double Dl = Pl-Ol # Distance along the long component
    cdef double Ds = Ps-Os # Distance along the short component
    
    if not Ds and not Dl: # P == O => index is 0 by convention
        return 0
    else:
        #print('')
        #print('O', (Ol, Os), 'P', (Pl, Ps), 'E', (El, Es))
        #print('Signs', (Sl, Ss), 'Distances', (Dl, Ds), 'slope', slope)
        #print('base index', Sl*2*Dl, 'offset', (Ss*Ds-Ss*int(Ss*slope*(Dl-Sl*.5)+.5)))
        #print('pixel elev.', Ds*Ss, 'distance', Dl-Sl*.5, 'slope', slope, \
        #    'boundary elev.', slope*(Dl-Sl*.5), \
        #    'rounded', int(Ss*slope*(Dl-Sl*.5)+.5), \
        #    'diff', Ss*Ds-int(Ss*slope*(Dl-Sl*.5)+.5))
        return int(Sl*2*Dl+(Ss*Ds-int(Ss*slope*(Dl-Sl*.5)+.5)))


#@cython.boundscheck(False)
def sweep_through_angles( \
    np.ndarray[np.int64_t, ndim = 1, mode="c"] viewpoint, \
    np.ndarray[np.int64_t, ndim = 2, mode="c"] perimeter, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] angles, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] add_events, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] center_events, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] remove_events, \
    np.ndarray[np.int32_t, ndim = 2, mode="c"] coord, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] distances, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] offset_visibility, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] visibility, \
    np.ndarray[np.float64_t, ndim = 2, mode="c"] visibility_map):
    """Update the active pixels as the algorithm consumes the sweep angles"""
    cdef int angle_count = len(angles)
    cdef int max_line_length = angle_count/2
    cdef int a = 0
    cdef int i = 0
    cdef int c = 0
    cdef double d = 0
    cdef double v = 0
    # Variables for fast update of the active line
    # The active line is a segment between the points O and E:
    #  -O is the origin, i.e. the cell on which the viewpoint is
    #  -E is the end point, a cell on the viewshed's bounding box
    # The active line's long axis is the axis (either 0 for I or 1 for J) where 
    # the active line is the longest: 
    #    long_axis = argmax(abs([E[0]-O[0], E[1]-O[1]]))
    # Conversely, the line's short axis is the axis where the active line is
    # the shortest: 
    #    short_axis = argmin(abs([E[0]-O[0], E[1]-O[1]]))
    cdef double sign[2] # used to account for the inverted row coordinates
    sign[0] = -1. # row coordinates (i) are negated (inverted)
    sign[1] = 1. # col coordinates (j) are kept as is
    cdef int s = 0 # Active line's short axis (set to I)
    cdef int l = 1 # Active line's long axis (set to J)
    cdef double Os = -viewpoint[s] # Origin's coordinate along short axis O[s]
    cdef double Ol = viewpoint[l] # Origin's coordinate along long axis O[l]
    cdef double Es = -perimeter[s][0] # End point's coord. along short axis E[s]
    cdef double El = perimeter[l][0] # End point's coord. along long axis E[l]
    cdef double Sl = -1 if Ol>El else 1 # Sign of the direction from O to E
    cdef double Ss = -1 if Os>Es else 1 # Sign of the direction from O to E
    cdef double slope = (Es-Os)/(El-Ol)
    cdef int ID = 0 # active pixel index
    # Active line container: an array that can contain twice the pixels in
    # a straight unobstructed line of sight aligned with the I or J axis.
    cdef ActivePixel *active_pixel_array = \
        <ActivePixel*>malloc(max_line_length*sizeof(ActivePixel))
    assert active_pixel_array is not NULL
    cdef ActivePixel active_pixel
    # Deactivate every pixel in the active line
    for index in range(max_line_length):
        active_pixel_array[index].is_active = False
    # 4- build event lists
    cdef int add_event_id = 0
    cdef int add_event_count = add_events.size
    cdef int center_event_id = 0
    cdef int center_event_count = center_events.size
    cdef int remove_event_id = 0
    cdef int remove_event_count = remove_events.size
    # 5- Sort event lists
    print('sorting the events')
    cdef np.ndarray[np.int32_t, ndim=1, mode="c"] arg_min = \
        np.argsort(add_events).astype(np.int32)
    cdef np.ndarray[np.int32_t, ndim=1, mode="c"] arg_center = \
        np.argsort(center_events).astype(np.int32)
    cdef np.ndarray[np.int32_t, ndim=1, mode="c"] arg_max = \
        np.argsort(remove_events).astype(np.int32)
    # Updating active cells
    active_line = {}
    cdef ActivePixel *active_pixels = NULL
    cdef int *cell_events = <int*>malloc(max_line_length*sizeof(int))
    assert cell_events is not NULL

    cdef ActivePixel px

    # 1- add cells at angle 0
    print('Creating cython event stream')
    # Collect cell_center events
    while (center_event_id < center_event_count) and \
        (center_events[arg_center[center_event_id]] < angles[1]):
        i = arg_center[center_event_id]
        d = distances[i]
        v = visibility[i]
        o = offset_visibility[i]
        active_pixels = add_active_pixel_cython(active_pixels, i, d, v, o)
        center_event_id += 1
        Pl = coord[l][i] * sign[l]
        Ps = coord[s][i] * sign[s]
        ID = active_pixel_index(Ol, Os, Pl, Ps, El, Es, Sl, Ss, slope)
        #print('Initialized pixel at ', ID)
        active_pixel_array[ID].is_active = True
        active_pixel_array[ID].index = i
        active_pixel_array[ID].distance = d
        active_pixel_array[ID].visibility = v
        active_pixel_array[ID].offset = o
        # The sweep line is current, now compute pixel visibility
        update_visible_pixels_cython( \
            active_pixels, coord[0], coord[1], d, visibility_map)
        update_visible_pixels_fast( \
            active_pixel_array, coord[0], coord[1], \
            max_line_length, visibility_map)        
        #for p in range(max_line_length):
        #    active_pixel = active_pixel_array[p]
        #    print('ID', p, 'is_active', active_pixel.is_active, \
        #        'distance', active_pixel.distance)

    # 2- loop through line sweep angles:
    for a in range(angle_count-2):
        print('')
        print('----- Angle', a, angles[a+1], '-----')
        #for p in range(max_line_length):
        #    print('ID', p, 'is_active', active_pixel_array[p].is_active, \
        #        'distance', active_pixel_array[p].distance)
        # New angle: recompute constants for fast pixel update algorithm
        if abs(perimeter[0][a]-viewpoint[0])>abs(perimeter[1][a]-viewpoint[1]):
            l = 0 # Long component is I (lines)
            s = 1 # Short component is J (columns)
        else:
            l = 1 # Long component is J (columns)
            s = 0 # Short component is I (lines)
          
        Os = viewpoint[s] * sign[s]
        Ol = viewpoint[l] * sign[l]
        Es = perimeter[s][a] * sign[s]
        El = perimeter[l][a] * sign[l]

        Sl = -1 if Ol>El else 1
        Ss = -1 if Os>Es else 1

        slope = (Es-Os)/(El-Ol)

        # 2.2- remove cells
        while (remove_event_id < remove_event_count) and \
            (remove_events[arg_max[remove_event_id]] <= angles[a+1]):
            i = arg_max[remove_event_id]
            d = distances[i]
            active_pixels = remove_active_pixel_cython(active_pixels, d)
            Pl = coord[l][i]*sign[l]
            Ps = coord[s][i]*sign[s]
            row = coord[0][i] - viewpoint[0]
            col = coord[1][i] - viewpoint[1]
            ID = active_pixel_index(Ol, Os, Pl, Ps, El, Es, Sl, Ss, slope)
            #print('Removed pixel', (-row, col), ' from', ID, remove_events[i])
            # Expecting valid pixel: is_active and distance == distances[i]
            # Move other pixel over otherwise
            if not active_pixel_array[ID].is_active or \
                active_pixel_array[ID].distance != distances[i]:
                for p in range(max_line_length):
                    print('expected distance', distances[i])
                    print('actual', p, 'is_active', active_pixel_array[p].is_active, \
                        'distance', active_pixel_array[p].distance)
            #    print('pixel', ID)
            #    print('is_active', active_pixel_array[ID].is_active)
            #    print('expected dist', distances[i], 'actual', \
            #        active_pixel_array[ID].distance, 'diff', \
            #        active_pixel_array[ID].distance-distances[i])
            #    print('old ID', ID)
            #    if (ID/2)*2 == ID: # even index: other pixel is the next one
            #        active_pixel_array[ID] = active_pixel_array[ID+1]
            #        active_pixel_array[ID+1].is_active = False
            #        print('new ID', ID + 1)
            #    else: # odd index: other pixel is the one just before
            #        active_pixel_array[ID] = active_pixel_array[ID-1]
            #        active_pixel_array[ID-1].is_active = False
            #        print('new ID', ID - 1)
            #    active_pixel_array[ID].is_active = False
            #    for p in range(max_line_length):
            #        print('after swap: ID', p, 'is_active', active_pixel_array[p].is_active, \
            #            'distance', active_pixel_array[p].distance)
            # Making sure that after the switch, we get the right pixel
            message = 'Is active ' + str(active_pixel_array[ID].is_active) + \
                ', expected distance ' + str(distances[i]) + \
                ', actual distance ' + str(active_pixel_array[ID].distance)
            assert active_pixel_array[ID].is_active and \
                active_pixel_array[ID].distance == distances[i], message
            active_pixel_array[ID].is_active = False

            arg_max[remove_event_id] = 0
            remove_event_id += 1
        # 2.1- add cells
        while (add_event_id < add_event_count) and \
            (add_events[arg_min[add_event_id]] < angles[a+1]):
            # The active cell list is initialized with those at angle 0.
            # Make sure to remove them from the cell_addition events to
            # avoid duplicates, but do not remove them from remove_cell events,
            # because they still need to be removed
            i = arg_min[add_event_id]
            d = distances[i]
            v = visibility[i]
            o = offset_visibility[i]
            active_pixels = add_active_pixel_cython(active_pixels, i, d, v, o)

            if abs(perimeter[0][a+1]-viewpoint[0])>abs(perimeter[1][a+1]-viewpoint[1]):
                l = 0 # Long component is I (lines)
                s = 1 # Short component is J (columns)
            else:
                l = 1 # Long component is J (columns)
                s = 0 # Short component is I (lines)
          
            Os = viewpoint[s] * sign[s]
            Ol = viewpoint[l] * sign[l]
            Es = perimeter[s][a+1] * sign[s]
            El = perimeter[l][a+1] * sign[l]

            Sl = -1 if Ol>El else 1
            Ss = -1 if Os>Es else 1

            slope = (Es-Os)/(El-Ol)

            Pl = coord[l][i] * sign[l]
            Ps = coord[s][i] * sign[s]
            row = coord[0][i] - viewpoint[0]
            col = coord[1][i] - viewpoint[1]
            ID = active_pixel_index(Ol, Os, Pl, Ps, El, Es, Sl, Ss, slope)
            #print('Added pixel', (-row, col), 'to', ID, add_events[i])
            # Active pixels could collide. If so, compute offset
            if active_pixel_array[ID].is_active:
                print('Pixel ' + str(ID) + ' is already active', \
                    active_pixel_array[ID].is_active)
            #    if (ID/2)*2 == ID: # even index: other pixel is the next one
            #        print('changing ID to ' + str(ID+1))
            #        if active_pixel_array[ID].is_active:
            #            for p in range(max_line_length):
            #                print('Sanity check: ID', p, 'is_active', \
            #                    active_pixel_array[p].is_active, \
            #                    'distance', active_pixel_array[p].distance)
            #        message = 'Other pixel is also active'
            #        assert not active_pixel_array[ID+1].is_active, message
            #        active_pixel_array[ID] = active_pixel_array[ID+1]
            #    else: # odd index: other pixel is the one just before
            #        print('changing ID to ' + str(ID-1))
            #        if active_pixel_array[ID].is_active:
            #            for p in range(max_line_length):
            #                print('Sanity check: ID', p, 'is_active', \
            #                    active_pixel_array[p].is_active, \
            #                    'distance', active_pixel_array[p].distance)
            #        message = 'Other pixel is also active'
            #        assert not active_pixel_array[ID-1].is_active, message
            #        active_pixel_array[ID] = active_pixel_array[ID-1]
            # Make sure that all is good:
            message = "Can't add to already active pixel " + str((Pl, Ps)) + \
                ' (' + str(ID) + ')'
            assert not active_pixel_array[ID].is_active, message
            active_pixel_array[ID].is_active = True
            active_pixel_array[ID].index = i
            active_pixel_array[ID].distance = d
            active_pixel_array[ID].visibility = v
            active_pixel_array[ID].offset = o

            arg_min[add_event_id] = 0
            add_event_id += 1
        # The sweep line is current, now compute pixel visibility
        update_visible_pixels_cython( \
            active_pixels, coord[0], coord[1], d, visibility_map)
        update_visible_pixels_fast( \
            active_pixel_array, coord[0], coord[1], \
            max_line_length, visibility_map)        

    # clean up
    free(cell_events)

    return visibility_map

