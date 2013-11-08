
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

def list_extreme_cell_angles_cython(array_shape, viewpoint_coords):
    """List the minimum and maximum angles spanned by each cell of a
        rectangular raster if scanned by a sweep line centered on
        viewpoint_coords.
    
        Inputs:
            -array_shape: a shape tuple (rows, cols) as is created from
                calling numpy.ndarray.shape()
            -viewpoint_coords: a 2-tuple of coordinates similar to array_shape
            where the sweep line originates
            
        returns a tuple (min, center, max, I, J) with min, center and max 
        Nx1 numpy arrays of each raster cell's minimum, center, and maximum 
        angles and coords as two Nx1 numpy arrays of row and column of the 
        coordinate of each point.
    """
    cdef:
        # constants
        double pi = 3.141592653589793238462643
        double two_pi = 2. * pi
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
        int cell_count = array_rows * array_cols
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
        size_t SECTOR_SIZE = 4 # values per sector
        size_t POINT_SIZE = 2 # values per point
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
        double *min_a_ptr = <double *>malloc((cell_count-1) * sizeof(double))
        # pointer to cell center angle values
        double *a_ptr = <double *>malloc((cell_count-1) * sizeof(double))
        # pointer to max angle values
        double *max_a_ptr = <double *>malloc((cell_count-1) * sizeof(double))
        # pointer to the cells row number
        long *I_ptr = <long *>malloc((cell_count-1) * sizeof(long))
        # pointer to the cells column number
        long *J_ptr = <long *>malloc((cell_count-1) * sizeof(long))
        # variables used in the loop
        int cell_id = 0 # processed cell counter
        int row # row counter
        int col # column counter
        int sector # current sector

    # Loop through the rows
    for row in range(array_rows):
        viewpoint_to_cell_row = row - viewpoint_row
        # Loop through the columns    
        for col in range(array_cols):
            viewpoint_to_cell_col = col - viewpoint_col
            # Show progress in 0.1% increment
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
            min_point_id = sector * SECTOR_SIZE
            max_point_id = min_point_id + POINT_SIZE
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
    min_angles = np.ndarray(cell_count -1, dtype = np.float)
    angles = np.ndarray(cell_count -1, dtype = np.float)
    max_angles = np.ndarray(cell_count -1, dtype = np.float)
    I = np.ndarray(cell_count -1, dtype = np.int32)
    J = np.ndarray(cell_count -1, dtype = np.int32)

    for i in range(cell_count-1):
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
    long index # long is python's default int type
    double distance # double is python's float type
    double visibility
    ActivePixel *next

cdef ActivePixel *dict_to_active_pixels(sweep_line):
    """Convert a python dictionary of active pixels to a C ActivePixels*"""
    cdef ActivePixel *active_pixels = NULL
    
    if 'closest' in sweep_line:
        # Have to create the whole linked list, since we're going to search
        # into it
        pixel = sweep_line['closest']
        element_count = 1
        # Find out how long the sweep_line is
        while pixel['next'] is not None:
            pixel = pixel['next']
            element_count += 1
        # Dynamically allocate the active_pixels list
        active_pixels =<ActivePixel*>malloc(element_count*sizeof(ActivePixel))
        # Fill it up with values from sweep_line
        pixel = sweep_line['closest']
        for e in range(element_count):
            active_pixels[e].index = pixel['index']
            active_pixels[e].visibility = pixel['visibility']
            active_pixels[e].distance = pixel['distance']
            active_pixels[e].next = &(active_pixels[e+1])
            pixel = pixel['next']

    return active_pixels

def find_active_pixel(sweep_line, distance):
    """Python wrapper for the cython find_active_pixel_cython function"""
    cdef ActivePixel *active_pixels
    
    if 'closest' in sweep_line:
        # Convert sweep_line to ActivePixel *
        ActivePixel = dict_to_active_pixels(sweep_line)
        # Invoke the low-level function to find the right value
        value = find_active_pixel_cython(active_pixels, distance)
        # clean-up
        free(active_pixels)
        return value
    else:
        return None

# Find an active pixel based on distance. Return None if it can't be found
cdef find_active_pixel_cython(ActivePixel *closest, double distance):
    cdef ActivePixel *pixel
    if closest is not NULL:
        # Get information about first pixel in the list
        pixel = closest
        # Move on to next pixel if we're not done
        while (pixel is not NULL) and \
            (deref(pixel).distance < distance):
            pixel = deref(pixel).next
        # We reached the end and didn't find anything
        if pixel is NULL:
            return None
        # We didn't reach the end: either pixel doesn't exist...
        if deref(pixel).distance != distance:
            return None
        # ...or we found it
        else:
            return deref(pixel).distance
    else:
        return None



def remove_active_pixel(sweep_line, distance):
    """Remove a pixel based on distance. Do nothing if can't be found."""
    if 'closest' in sweep_line:
        # Get information about first pixel in the list
        previous = None
        pixel = sweep_line[sweep_line['closest']['distance']] # won't change
        # Move on to next pixel if we're not done
        while (pixel is not None) and \
            (pixel['distance'] < distance):
            previous = pixel
            pixel = pixel['next']
        # We reached the end and didn't find anything
        if pixel is None:
            return sweep_line
        # We didn't reach the end: either pixel doesn't exist:
        if pixel['distance'] != distance:
            return sweep_line
        # Or we found the value we want to delete
        # Make the previous element point to the next
        # We're at the beginning of the list: update the list's first element
        if previous is None:
            # No next pixel: we have to delete 'closest'
            if pixel['next'] is None:
                del sweep_line['closest']
            # Otherwise, update it
            else:
                sweep_line['closest'] = pixel['next']
        # We're not at the beginning of the list: only update previous
        else:
            previous['next'] = sweep_line[distance]['next']
        # Remove the value from the list
        del sweep_line[distance]
    return sweep_line


def add_active_pixel(sweep_line, index, distance, visibility):
    """Add a pixel to the sweep line in O(n) using a linked_list of
    linked_cells."""
    # Make sure we're not creating any duplicate
    message = 'Duplicate entry: the value ' + str(distance) + ' already exist'
    assert distance not in sweep_line, message
    new_pixel = \
    {'next':None, 'index':index, 'distance':distance, 'visibility':visibility}
    if 'closest' in sweep_line:
        # Get information about first pixel in the list
        previous = None
        pixel = sweep_line[sweep_line['closest']['distance']] # won't change
        # Move on to next pixel if we're not done
        while (pixel is not None) and \
            (pixel['distance'] < distance):
            previous = pixel
            pixel = pixel['next']
        # 1- Make the current pixel points to the next one
        new_pixel['next'] = pixel
        # 2- Insert the current pixel in the sweep line:
        sweep_line[distance] = new_pixel
        # 3- Make the preceding pixel point to the current one
        if previous is None:
            sweep_line['closest'] = new_pixel
        else:
            sweep_line[previous['distance']]['next'] = sweep_line[distance]
    else:
        sweep_line[distance] = new_pixel
        sweep_line['closest'] = new_pixel
    return sweep_line


