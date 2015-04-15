import sys
import os
import csv
import math
import h5py
import copy

cimport numpy as np
import numpy as np

import cython
from cython.operator import dereference as deref
from libc.math cimport atan2
from libc.math cimport sin
from libc.math cimport sqrt
from libc.math cimport log

cdef extern from "stdlib.h":
    void* malloc(size_t size)
    void free(void* ptr)

def memory_efficient_event_stream(array_shape, viewpoint_coords, max_dist):
    """Create a memory efficient event stream for cell addition/removal.
    
        Inputs:
            -array_shape: a shape tuple (rows, cols) as is created from
                calling numpy.ndarray.shape()
            -viewpoint_coords: a 2-tuple of coordinates similar to array_shape
            where the sweep line originates
            -max_dist: maximum viewing distance in pixels
            
        returns a uri to an hdf5 file that contains the cell addition/removal
            event stream.
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
        # Each group of 4 values is the coordinate of a pair of points 
        # that sit on the cell corners associated to the lowest and highest 
        # angles. These corners change depending on the quadrant 
        # (angular sector) the point is in:
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
        np.float64_t angle = 0.
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
        
        # variables used in the loop
        int cell_id = 0 # processed cell counter
        np.int32_t row # row counter
        np.int32_t col # column counter
        int sector # current sector

        # pixel addition/removal event
        size_t add = 0
        size_t drop = 1


        # Upper bound of the array size of the largest possible viewshed area
        int *max_size = \
            [2*min(max_dist, array_shape[0]), \
            2*min(max_dist, array_shape[1])]

        int *center = [array_shape[0]/2, array_shape[1]/2]

    # Create an hdf5 intermediate file to store the line's active pixels:
#    print('------------------- CWD:', os.getcwd(), '-------------------------')
    active_pixels_file_path = 'active_pixels.h5'
    f = h5py.File(active_pixels_file_path, 'w')
    # Active pixels array size: 
    # active_pixels[angle][x/y][add/drop][pixel_id]
    active_pixels = f.create_dataset('active_pixels', \
        (2*(max_size[0] + max_size[1]), 2, 2, 2*max_dist), \
        compression = 'gzip', fillvalue = -1.0)

    pixel_map_file_path = 'pixel_map.h5'
    g = h5py.File(pixel_map_file_path, 'w')
    pixel_map = g.create_dataset('pixel_map', \
        (max_size[0], max_size[1]), \
        compression = 'gzip', fillvalue = -1.0)

    # Enumerate perimeter pixels + compute their angles
    i_min = 0
    i_max = max_size[0]
    j_min = 0
    j_max = max_size[1]
    # list all perimeter cell center angles
    row_count = i_max - i_min 
    col_count = j_max - j_min
    # Create top row, except cell (0,0)
    rows = np.zeros(col_count - 1)
    cols = np.array(range(col_count-1, 0, -1))
    # Create left side, avoiding repeat from top row
    rows = np.concatenate((rows, np.array(range(row_count -1))))
    cols = np.concatenate((cols, np.zeros(row_count - 1)))
    # Create bottom row, avoiding repat from left side
    rows = np.concatenate((rows, np.ones(col_count - 1) * (row_count -1)))
    cols = np.concatenate((cols, np.array(range(col_count - 1))))
    # Create last part of the right side, avoiding repeat from bottom row
    rows = np.concatenate((rows, np.array(range(row_count - 1, 0, -1))))
    cols = np.concatenate((cols, np.ones(row_count - 1) * (col_count - 1)))
    # Roll the arrays so the first point's angle at (rows[0], cols[0]) is 0
    rows = np.roll(rows, viewpoint_row - i_min).astype(np.int64)
    cols = np.roll(cols, viewpoint_col - i_min).astype(np.int64)

    p_rows = np.zeros_like(rows)
    p_cols = np.zeros_like(p_rows)

    for r in range(len(rows)):
        p_rows[r] = rows[r] - viewpoint_row
        p_cols[r] = cols[r] - viewpoint_col

    angles = (np.arctan2(-p_rows, p_cols) + two_pi) % two_pi
    

#    I, J = np.meshgrid(range(3), range(3), indexing='ij')
    
    # 1-Draw horizontal line from center to edge of visible area
    for p in range(max_dist):
        pixel_map[center[0], center[1] + p] = 0.0
        active_pixels[0, 0, add, p] = center[0]
        active_pixels[0, 1, add, p] = center[1] + p

    # 2-Add fringe line above it
    for p in range(1, max_dist):
        pixel_map[center[0]+1, center[1] + p] = angles[1]
        active_pixels[1, 0, add, p] = center[0]+1
        active_pixels[1, 1, add, p] = center[1] + p

    cdef int iteration = 1

    # 3-Until there are no more angles to process:
    for i in range(angles.size-1):
        print('i', i)
        a = angles[i]
        # 4-Find fringe pixel from focal point
        pixel_mask = \
            pixel_map[center[0]-1:center[0]+2, center[1]-1:center[1]+2]

        fringe_pixel = np.where(pixel_mask > 0)

        assert fringe_pixel[0].size == 1, 'Unexpected fringe pixel count: ' + \
            str(fringe_pixel[0].size)

        fringe_pixel = \
            (fringe_pixel[0][0] + center[0] - 1, \
            fringe_pixel[1][0] + center[1] - 1)

        # 5-Until there are no more fringe pixels:
        pixel = 0
        while fringe_pixel[0].size == 1:
            # Compute the angle of the cell center
            row = fringe_pixel[0]
            col = fringe_pixel[1]

            center_angle = \
                <np.float64_t>(atan2(-p_rows[i], p_cols[i]) +two_pi) %two_pi
            
            #   5.1-Check if fringe pixel should be an active pixel
            # find index in extreme_cell_points that corresponds to the current
            # angle to compute the offset from cell center
            # This line only discriminates between 4 axis-aligned angles
            sector = <int>(4. * a / two_pi) * 2
            # The if statement adjusts for all the 8 angles
            if abs(p_rows[i] * p_cols[i]) > 0:
                sector += 1

            # Compute offset
            # Compute offset ID
            min_point_id = sector * SECTOR_SIZE # Beginning of a row
            max_point_id = min_point_id + POINT_SIZE # Skip a point
            # Compute offset from current cell center to first corner
            min_corner_offset_row = extreme_cell_points[min_point_id]
            min_corner_offset_col = extreme_cell_points[min_point_id + 1]
            # Compute corner angle
            min_corner_row = row + min_corner_offset_row
            min_corner_col = col + min_corner_offset_col
            # Compute the angles associated with the extreme corners
            min_angle = atan2(-min_corner_row, min_corner_col)

            
            # 5.2-If fringe pixel should be an active pixel:
            if min_angle < angles[i+1]:
                # Mark fringe pixel as active pixel
                pixel_map[row, col] = 0.0
                active_pixels[1, 0, add, pixel] = row
                active_pixels[1, 1, add, pixel] = col

                # 5.2.1-Extract neighboring pixels
                pixel_mask = pixel_map[row-1:row+2, col-1:col+2]
                fringe_pixels = \
                    np.where((pixel_mask > 0) & (pixel_mask < angles[i]))

                # 5.2.2-Mark fringe pixels (if not too far)
                for i in range(fringe_pixels[0].size):
                    new_row = fringe_pixels[0][i] + row - 1
                    new_col = fringe_pixels[1][i] + col - 1
                    
                    distance = \
                        ((viewpoint_row-new_row)**2 + \
                        (viewpoint_col-new_col)**2)**.5
                    
                    if distance < max_dist:
                        pixel_map[row, col] = angles[i]

            # 5.3-Move to next fringe pixel + see if not too far
            pixel_mask = pixel_map[row-1:row+2, col-1:col+2]

            fringe_pixel = np.where((pixel_mask > 0) & (pixel_mask < angles[i]))

            # No more fringe pixels, move on to next angle
            if fringe_pixel[0].size == 0:
                break

            fringe_pixel = \
                (fringe_pixel[0][0] + row - 1, \
                fringe_pixel[1][0] + col - 1)

            break

        # 6-Move on to next angle
        iteration += 1


    f.close()
    g.close()

    os.remove(active_pixels_file_path)
    os.remove(pixel_map_file_path)

    return

    # Count size of arrays before allocating
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
    min_angles = np.ndarray(cell_count, dtype = np.float64)
    angles = np.ndarray(cell_count, dtype = np.float64)
    max_angles = np.ndarray(cell_count, dtype = np.float64)
    I = np.ndarray(cell_count, dtype = np.int32)
    J = np.ndarray(cell_count, dtype = np.int32)


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
            I[cell_id] = row
            J[cell_id] = col
            # Compute the angle of the cell center
            angle = <np.float64_t>(atan2(-(row - viewpoint_row), col - viewpoint_col) + \
                two_pi) % two_pi
            angles[cell_id] = angle
            # find index in extreme_cell_points that corresponds to the current
            # angle to compute the offset from cell center
            # This line only discriminates between 4 axis-aligned angles
            sector = <int>(4. * angle / two_pi) * 2
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
            min_angles[cell_id] = (min_angle + two_pi) % two_pi 
            max_angles[cell_id] = (max_angle + two_pi) % two_pi
            cell_id += 1

    return (min_angles, angles, max_angles, I, J)

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
        # Each group of 4 values is the coordinate of a pair of points 
        # that sit on the cell corners associated to the lowest and highest 
        # angles. These corners change depending on the quadrant 
        # (angular sector) the point is in:
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
        np.float64_t angle = 0.
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
        # variables used in the loop
        int cell_id = 0 # processed cell counter
        np.int32_t row # row counter
        np.int32_t col # column counter
        int sector # current sector

    # Count size of arrays before allocating
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
    min_angles = np.ndarray(cell_count, dtype = np.float64)
    angles = np.ndarray(cell_count, dtype = np.float64)
    max_angles = np.ndarray(cell_count, dtype = np.float64)
    I = np.ndarray(cell_count, dtype = np.int32)
    J = np.ndarray(cell_count, dtype = np.int32)


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
            I[cell_id] = row
            J[cell_id] = col
            # Compute the angle of the cell center
            angle = <np.float64_t>(atan2(-(row - viewpoint_row), col - viewpoint_col) + \
                two_pi) % two_pi
            angles[cell_id] = angle
            # find index in extreme_cell_points that corresponds to the current
            # angle to compute the offset from cell center
            # This line only discriminates between 4 axis-aligned angles
            sector = <int>(4. * angle / two_pi) * 2
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
            min_angles[cell_id] = (min_angle + two_pi) % two_pi 
            max_angles[cell_id] = (max_angle + two_pi) % two_pi
            cell_id += 1

    return (min_angles, angles, max_angles, I, J)

def compute_distances(int vi, int vj, double cell_size, \
    np.ndarray[np.int32_t, ndim = 1] I, \
    np.ndarray[np.int32_t, ndim = 1] J, \
    np.ndarray[np.float64_t, ndim = 1] distance_sq, \
    np.ndarray[np.float64_t, ndim = 1] distance):

    cdef:
        int index_count = I.shape[0]

        double cell_size_sq = cell_size * cell_size

    for i in range(index_count):
        distance_sq[i] = ((vi - I[i])**2 + (vj - J[i])**2) * cell_size_sq
        distance[i] = sqrt(distance_sq[i])
 

# Function that computes the polynomial valuation function 
def polynomial(double a, double b, double c, double d, \
    int max_valuation_radius, int vi, int vj, double cell_size, \
    double coeff, \
    np.ndarray[np.int32_t, ndim = 1] I, \
    np.ndarray[np.int32_t, ndim = 1] J, \
    np.ndarray[np.float64_t, ndim = 1] distance, \
    np.ndarray[np.float64_t, ndim = 2] mask, \
    np.ndarray[np.float64_t, ndim = 2] accum):

    cdef:
        double C1 = (a+b*1000+c*1000**2+d*1000**3) * coeff
        double C2 = (b+2*c*1000+3*d*1000**2) * coeff
        double x
        int row, col
    a *= coeff
    b *= coeff
    c *= coeff
    d *= coeff
 
    index_count = I.shape[0]

    for i in range(index_count):
        row = I[i]
        col = J[i]
        if mask[row, col] > 0.:
            x = distance[i]
            if x < 1000:
                accum[row, col] += C1 - C2 * (1000 - x)
            elif x <= max_valuation_radius:
                accum[row, col] += a + b*x + c*x**2 + d*x**3

def logarithmic(double a, double b, double c, double d, \
    int max_valuation_radius, int vi, int vj, double cell_size, \
    double coeff, \
    np.ndarray[np.int32_t, ndim = 1] I, \
    np.ndarray[np.int32_t, ndim = 1] J, \
    np.ndarray[np.float64_t, ndim = 1] distance, \
    np.ndarray[np.float64_t, ndim = 2] mask, \
    np.ndarray[np.float64_t, ndim = 2] accum):

    cdef:
        double C1 = (a + b*log(1000)) * coeff
        double C2 = (b/1000) * coeff
        double x
        int row, col
    a *= coeff
    b *= coeff
    c *= coeff
    d *= coeff
 
    index_count = I.shape[0]

    for i in range(index_count):
        row = I[i]
        col = J[i]
        if mask[row, col] > 0.:
            x = distance[i]
            if x < 1000:
                accum[row, col] += C1 - C2*(1000-x)
            elif x <= max_valuation_radius:
                accum[row, col] += a + b*log(x)

# struct that mimics python's dictionary implementation
cdef struct ActivePixel:
    long is_active # Indicate if the pixel is active
    long index # long is python's default int type
    double distance # double is python's float type
    double visibility
    double offset

cdef int update_visible_pixels_fast(ActivePixel *active_pixel_array, \
    np.ndarray[np.int32_t, ndim = 1] I, \
    np.ndarray[np.int32_t, ndim = 1] J, \
    int pixel_count, np.ndarray[np.float64_t, ndim = 2] visibility_map, int a):
        
    cdef ActivePixel p
    cdef double max_visibility = -1000000.
    cdef double visibility = 0
    cdef int index = active_pixel_array[0].index
    cdef int pixel_id
    cdef int active_pixel_count = 0
    cdef int last_active_pixel = 1

    for pixel_id in range(pixel_count):
        p = active_pixel_array[pixel_id]
        # Inactive pixel: either we skip or we exit
        if not p.is_active:
            # More than 2 pixels gap? -> end of active pixels, exit loop
            if pixel_id - last_active_pixel > 3:
                break
            # Just an inactive pixel, skip it
            continue
        # Pixel is visible
        if p.offset > max_visibility:
            visibility = p.offset - max_visibility
        else:
            visibility = p.offset - max_visibility
        if p.visibility > max_visibility:
            max_visibility = p.visibility

        # Update the visibility map for this pixel
        index = p.index
        if visibility_map[I[index], J[index]] == 0:
            visibility_map[I[index], J[index]] = visibility
        active_pixel_count += 1
        last_active_pixel = pixel_id 

    #visibility_map[I[index], J[index]] = a # Debug purposes only!!!!

    return active_pixel_count

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
    Dl = P[l]-Ol
    Ds = P[s]-Os

    Sl = -1 if (Ol>El) else 1
    Ss = -1 if (Os>Es) else 1

    slope = 0 if El==Ol else (Es-Os) / (El-Ol)

    return active_pixel_index(Ol, Os, P[l], P[s], El, Es, Dl, Ds, Sl, Ss, slope)

cdef int active_pixel_index(double Ol, double Os, \
                        double Pl, double Ps, \
                        double El, double Es, \
                        double Dl, double Ds, \
                        double Sl, double Ss,
                        double slope):
    
    return <int>(Sl*2*Dl+(Ss*Ds-(<int>(Ss*slope*(Dl-Sl*.5)+.5)))) \
        if Ds or Dl else 0


#@cython.boundscheck(False)
def sweep_through_angles( \
    np.ndarray[np.int64_t, ndim = 1, mode="c"] viewpoint, \
    np.ndarray[np.int64_t, ndim = 2, mode="c"] perimeter, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] angles, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] add_events, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] center_events, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] remove_events, \
    np.ndarray[np.int64_t, ndim = 1, mode="c"] arg_min, \
    np.ndarray[np.int64_t, ndim = 1, mode="c"] arg_center, \
    np.ndarray[np.int64_t, ndim = 1, mode="c"] arg_max, \
    np.ndarray[np.int32_t, ndim = 2, mode="c"] coord, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] distances, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] offset_visibility, \
    np.ndarray[np.float64_t, ndim = 1, mode="c"] visibility, \
    np.ndarray[np.float64_t, ndim = 2, mode="c"] visibility_map, \
    char * path, \
    int index):
    """Update the active pixels as the algorithm consumes the sweep angles"""

#    # Save viewshed function arguments in HDF5
#    # Inputs to save:
#    #   -add_events, center_events, remove_events
#    #   -arg_min, arg_center, arg_max
#    #   -distances, distances_sq
#    #   -visibility, offset_visibility
#    #
#    # Create the paths to the debug data
#    debug_uri = os.path.join(path, 'debug_data_' + index + '.h5')
#
#    debug_data = h5py.File(debug_uri, 'w')
#
#
#    add_events_dataset = debug_data.create_dataset('add_events', 
#        (add_events.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#
#    center_events_dataset = debug_data.create_dataset('center_events', 
#        (center_events.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#    
#    remove_events_dataset = debug_data.create_dataset('remove_events', 
#        (remove_events.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#    
#
#    arg_min_dataset = debug_data.create_dataset('arg_min', 
#        (arg_min.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#
#    arg_center_dataset = debug_data.create_dataset('arg_center', 
#        (arg_center.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#
#    arg_max_dataset = debug_data.create_dataset('arg_max', 
#        (arg_max.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#
#
#    distances_dataset = debug_data.create_dataset('distances', 
#        (distances.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#
#    visibility_dataset = debug_data.create_dataset('visibility', 
#        (visibility.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#
#    offset_visibility_dataset = debug_data.create_dataset('offset_visibility', 
#        (offset_visibility.shape[0],), \
#        compression = 'gzip', fillvalue = -1)
#
#
#    # Store data in the file
#    add_events_dataset[...] = add_events[...]
#    center_events_dataset[...] = center_events[...]
#    remove_events_dataset[...] = remove_events[...]
#    
#    arg_min_dataset[...] = arg_min[...]
#    arg_center_dataset[...] = arg_center[...]
#    arg_max_dataset[...] = arg_max[...]
#
#    distances_dataset[...] = distances[...]
#    visibility_dataset[...] = visibility[...]
#    offset_visibility_dataset[...] = offset_visibility[...]
#
#    # Close the files
#    debug_data.close()


    cdef double epsilon = 1e-8

    cdef int angle_count = len(angles)
    cdef int max_line_length = angle_count/2
    cdef int a = 0
    cdef int i = 0
    cdef int c = 0
    cdef double d = 0
    cdef double v = 0
    cdef double o = 0
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
    cdef np.int32_t sign[2] # used to account for the inverted row coordinates
    sign[0] = -1 # row coordinates (i) are negated (inverted)
    sign[1] = 1 # col coordinates (j) are kept as is
    cdef int s = 0 # Active line's short axis (set to I)
    cdef int l = 1 # Active line's long axis (set to J)
    cdef double Os = -viewpoint[s] # Origin's coordinate along short axis O[s]
    cdef double Ol = viewpoint[l] # Origin's coordinate along long axis O[l]
    cdef np.int32_t Pl = 0 # Coordinate of the point being processed in a loop
    cdef np.int32_t Ps = 0 # Other coordinate
    cdef double Es = -perimeter[s][0] # End point's coord. along short axis E[s]
    cdef double El = perimeter[l][0] # End point's coord. along long axis E[l]
    cdef double Dl = 0 # Distance along the long component
    cdef double Ds = 0 # Distance along the short component
    cdef double Sl = -1 if Ol>El else 1 # Sign of the direction from O to E
    cdef double Ss = -1 if Os>Es else 1 # Sign of the direction from O to E
    cdef double slope = (Es-Os)/(El-Ol)
    cdef double dbl = 0
    cdef int ID = 0 # active pixel index
    cdef int alternate_ID = 0
    
    # Active line container: an array that can contain twice the pixels in
    # a straight unobstructed line of sight aligned with the I or J axis.
    cdef ActivePixel *active_pixel_array = \
        <ActivePixel*>malloc(max_line_length*sizeof(ActivePixel))
    assert active_pixel_array is not NULL
    # Deactivate every pixel in the active line
    for pixel in range(max_line_length):
        active_pixel_array[pixel].is_active = False
    # 4- build event lists
    cdef int add_event_id = 0
    cdef int add_event_count = add_events.size
    cdef int center_event_id = 0
    cdef int center_event_count = center_events.size
    cdef int remove_event_id = 0
    cdef int remove_event_count = remove_events.size

    cdef np.int32_t [:] coordL = coord[l]
    cdef np.int32_t [:] coordS = coord[s]

    # internal consistency check
    cdef int active_pixel_count = 0
    cdef int previous_pixel_count = 0
    cdef int add_pixel_count = 0
    cdef int remove_pixel_count = 0
    cdef int total_active_pixel_count = 0
    cdef int last_active_pixel = 0

    # Used to test the active line consistency. Debug only.
    cdef int active_pixels_per_location = 0
    cdef int max_active_ID = 0

    cdef ActivePixel temporary_pixel # Used when swapping pixels

    
#    # ----------------------------------------------------------------
#    # Track pixel addition/removal history only for debug purposes
#    # ----------------------------------------------------------------
#
#    # Open file to save debug data
#    try:
#        filename = os.path.join(path, 'history_' + str(index) + '.txt')
#        fp = open(filename, 'w')
#        print('Saving file to', filename)
#    except IOError as err:
#        print("Can't open file " + fp)
#        raise err
#
#    csv_writer = csv.writer(fp)
#
#    cdef np.ndarray history = np.zeros([max_line_length/2 +1, 2]).astype(int)
#
#    row = []
#    while (center_event_id < center_event_count) and \
#        (center_events[arg_center[center_event_id]] < angles[1] + epsilon):
#        i = arg_center[center_event_id]
#        Pl = coordL[i] * sign[l]
#        Ps = coordS[i] * sign[s]
#        Dl = Pl-Ol
#        Ds = Ps-Os
#        ID = <int>(Sl*2*Dl+(Ss*Ds-(<int>(Ss*slope*(Dl-Sl*.5)+.5)))) \
#            if Ds or Dl else 0
#        
#        assert history[ID/2][0] + history[ID/2][1] == 0
#
#        history[ID/2][ID%2] += 1
##        row.append(ID)
##        row.append((ID, history[ID/2][ID%2]))
#        row.append((ID, history[ID/2][0], history[ID/2][1]))
##        row.append((ID, center_events[arg_center[center_event_id]]))
#        center_event_id += 1
##    csv_writer.writerow(['initialisation']+sorted(row))
#    csv_writer.writerow(['initialisation']+row)
#
#
##    print('')
#
#
#    for a in range(angle_count-2):
##        print('angle', a, [angles[a], angles[a+1]])
#        row = ['angle ' + str(a) + ', ' + str(angles[a]) + ':']
##        row = ['angle', a, [angles[a], angles[a+1]]]
#        csv_writer.writerow(row)
#
#        # Removals
#        if abs(perimeter[0][a]-viewpoint[0])>abs(perimeter[1][a]-viewpoint[1]):
#            l = 0 # Long component is I (lines)
#            s = 1 # Short component is J (columns)
#        else:
#            l = 1 # Long component is J (columns)
#            s = 0 # Short component is I (lines)
#          
#        coordL = coord[l]
#        coordS = coord[s]
#        Os = viewpoint[s] * sign[s]
#        Ol = viewpoint[l] * sign[l]
#        Es = perimeter[s][a] * sign[s]
#        El = perimeter[l][a] * sign[l]
#        Sl = -1 if Ol>El else 1
#        Ss = -1 if Os>Es else 1
#        slope = (Es-Os)/(El-Ol)
#
#        row = []
#        while (remove_event_id < remove_event_count) and \
#            (remove_events[arg_max[remove_event_id]] <= \
#                angles[a+1] + epsilon):
#            i = arg_max[remove_event_id]
#            Pl = coordL[i]*sign[l]
#            Ps = coordS[i]*sign[s]
#            Dl = Pl-Ol
#            Ds = Ps-Os
#            ID = <int>(Sl*2*Dl+(Ss*Ds-(<int>(Ss*slope*(Dl-Sl*.5)+.5)))) \
#                if Ds or Dl else 0
#            
#
#            assert history[ID/2][0] + history[ID/2][1] > 0
#
#            if history[ID/2][ID%2] == 0:
#                ID = ID+1 if ID%2==0 else ID-1
##                print("Trying to remove from other ID")
#
#            assert history[ID/2][ID%2] == 1
#
#            history[ID/2][ID%2] -= 1
##            print '('+str(ID)+', '+str(history[ID/2])+')',
#
#            remove_event_id += 1
#
#            row = []
#            row.append((ID, history[ID/2][0], history[ID/2][1]))
#            csv_writer.writerow(['removal:']+row)
#
##            row.append((ID, history[ID/2][0], history[ID/2][1]))
##        csv_writer.writerow(['removal:']+row)
#
#
##        print('')
#
#
#        # Additions
#        if abs(perimeter[0][a+1]-viewpoint[0])>abs(perimeter[1][a+1]-viewpoint[1]):
#            l = 0 # Long component is I (lines)
#            s = 1 # Short component is J (columns)
#        else:
#            l = 1 # Long component is J (columns)
#            s = 0 # Short component is I (lines)
#
#        coordL = coord[l]
#        coordS = coord[s]
#        Os = viewpoint[s] * sign[s]
#        Ol = viewpoint[l] * sign[l]
#        Es = perimeter[s][a+1] * sign[s]
#        El = perimeter[l][a+1] * sign[l]
#        Sl = -1 if Ol>El else 1
#        Ss = -1 if Os>Es else 1
#        slope = (Es-Os)/(El-Ol)
#
#        row = []
#        max_active_ID = 0
##        print('Adding', add_event_id, 'pixels')
#        while (add_event_id < add_event_count) and \
#            (add_events[arg_min[add_event_id]] < \
#                angles[a+1] - epsilon):
#            i = arg_min[add_event_id]
#            Pl = coordL[i] * sign[l]
#            Ps = coordS[i] * sign[s]
#            Dl = Pl-Ol
#            Ds = Ps-Os
#            ID = <int>(Sl*2*Dl+(Ss*Ds-(<int>(Ss*slope*(Dl-Sl*.5)+.5)))) \
#                if Ds or Dl else 0
#
#            assert history[ID/2][0] + history[ID/2][1] < 2
#
#            if history[ID/2][ID%2] == 1:
#                ID = ID+1 if ID%2==0 else ID-1
##                print("Trying to add to other ID")
#
#            assert history[ID/2][ID%2] == 0
#
#            history[ID/2][ID%2] += 1
#
#            add_event_id += 1
#            max_active_ID = ID if ID > max_active_ID else max_active_ID
#
#            row = []
#            row.append((ID, history[ID/2][0], history[ID/2][1]))
#            csv_writer.writerow(['additions:']+row)
##            row.append((ID, history[ID/2][0], history[ID/2][1]))
##        csv_writer.writerow(['additions:']+row)
#
#
#
##        print('')
##        print('Final:')
##        for p in range(1, history.size):
##            if history[p] == 0:
##                break
##            print (p, history[p]),
##        print('')
#
#
##        row = []
##        for ID in range(2, max_line_length):
##            print(max_line_length, ID, history.shape[0])
##            row.append((ID, history[ID/2]))
##        csv_writer.writerow(['final:']+row)
#
#    center_event_id = 0
#    add_event_id = 0
#    remove_event_id = 0
#
#    sys.exit(0)


    # ----------------------------------------------------------------
    # Updating active pixel line + keep track of add/remove history
    # ----------------------------------------------------------------

    # Open file to save debug data
    try:
        filename = os.path.join(path, 'active_pixels_' + str(index) + '.txt') 
        fp = open(filename, 'w')
        print('Saving file to', filename)
    except IOError as err:
        print("Can't open file " + fp)
        raise err

    csv_writer = csv.writer(fp)

    cdef np.ndarray history = np.zeros([max_line_length/2 +1, 2]).astype(int)

#    row = ['Initialization:']

    # 1- add cells at angle 0
    # Collect cell_center events
    row = []
    while (center_event_id < center_event_count) and \
        (center_events[arg_center[center_event_id]] < angles[1] - epsilon):
        i = arg_center[center_event_id]
        d = distances[i]
        v = visibility[i]
        o = offset_visibility[i]
        Pl = coordL[i] * sign[l]
        Ps = coordS[i] * sign[s]
        Dl = Pl-Ol
        Ds = Ps-Os
        ID = <int>(Sl*2*Dl+(Ss*Ds-(<int>(Ss*slope*(Dl-Sl*.5)+.5)))) \
            if Ds or Dl else 0

        
        #print 'ID', ID, '(first, second)', \
        #    (history[ID/2][0], history[ID/2][1]), \
        #    '(I, J)', (coord[0][i], coord[1][i]), \
        #    center_events[arg_center[center_event_id]], \
        #    ' - ', angles[1], '=', \
        #    center_events[arg_center[center_event_id]] - angles[1], \
        #    ' < ', -epsilon

        assert history[ID/2][0] + history[ID/2][1] == 0

        history[ID/2][ID%2] += 1

        #assert ID>=0 and ID<max_line_length
        active_pixel_array[ID].is_active = True
        active_pixel_array[ID].index = i
        active_pixel_array[ID].distance = d
        active_pixel_array[ID].visibility = v
        active_pixel_array[ID].offset = o
        center_event_id += 1
        add_pixel_count += 1

    print('')

#        row.append((ID, history[ID/2][0], history[ID/2][1]))
#    csv_writer.writerow(['initialisation']+row)


    for p in range(2, center_event_id):
        assert history[p][0] + history[p][1] == 1


    # Test that the line has exactly 1 active pixel per possible location
    # There are two possible locations for pixel 'p' to be active: 2p, 2p+1
    for p in range(max_line_length):
        if active_pixel_array[p].is_active:
            max_active_ID = p

    for pixel_id in range(2, max_active_ID):
        
        # Moving to a new location: reset the active pixel counter 
        if pixel_id % 2 == 0:
            active_pixels_per_location = 0

        if active_pixel_array[pixel_id].is_active:
            active_pixels_per_location += 1

        if pixel_id % 2 == 1:
            if active_pixels_per_location != 1:
                for p in range(max_line_length):
                    if active_pixel_array[p].is_active:
                        print (p),

            assert active_pixels_per_location == 1, \
                "Invalid initialized array: wrong active pixel count (" + \
                    str(active_pixels_per_location) + \
                    ") at location " + str(pixel_id)

    # The sweep line is current, now compute pixel visibility
    active_pixel_count = update_visible_pixels_fast( \
        active_pixel_array, coord[0], coord[1], \
        max_line_length, visibility_map, 1)

    #if active_pixel_count != \
    #        previous_pixel_count + add_pixel_count - remove_pixel_count:
    #    print 'Active pixels'
    #    for pixel_id in range(2, max_line_length):
    #        # Inactive pixel: either we skip or we exit
    #        if active_pixel_array[pixel_id].is_active:
    #            print pixel_id, 
    #    print('')

    #message = \
    #    str(active_pixel_count) + ' = ' + str(previous_pixel_count) + ' + ' + \
    #    str(add_pixel_count) + ' - ' + str(remove_pixel_count)
    assert active_pixel_count == \
            previous_pixel_count + add_pixel_count - remove_pixel_count#, message

    previous_pixel_count = active_pixel_count

    # 2- loop through line sweep angles:
    #print('sweeping through', angle_count, 'angles')
    for a in range(angle_count-2):
#        print('angle', a, angles[a])
#        row = ['angle ' + str(a) + ', ' + str(angles[a]) + ':']
#        csv_writer.writerow(row)

        # 2.2- remove cells
        if abs(perimeter[0][a]-viewpoint[0])>abs(perimeter[1][a]-viewpoint[1]):
            l = 0 # Long component is I (lines)
            s = 1 # Short component is J (columns)
        else:
            l = 1 # Long component is J (columns)
            s = 0 # Short component is I (lines)
          
        coordL = coord[l]
        coordS = coord[s]

        # Coordinates at the Origin (O)
        Os = viewpoint[s] * sign[s]
        Ol = viewpoint[l] * sign[l]
        
        # Coordinates at the End point (E)
        Es = perimeter[s][a] * sign[s]
        El = perimeter[l][a] * sign[l]

        # Sign for the long and short components
        Sl = -1 if Ol>El else 1
        Ss = -1 if Os>Es else 1

        slope = (Es-Os)/(El-Ol)


        row = [] 
        remove_pixel_count = 0
        while (remove_event_id < remove_event_count) and \
            (remove_events[arg_max[remove_event_id]] <= \
                angles[a+1] + epsilon):
            i = arg_max[remove_event_id]
            d = distances[i]
            Pl = coordL[i]*sign[l]
            Ps = coordS[i]*sign[s]
            Dl = Pl-Ol
            Ds = Ps-Os
            ID = <int>(Sl*2*Dl+(Ss*Ds-(<int>(Ss*slope*(Dl-Sl*.5)+.5)))) \
                if Ds or Dl else 0
            
            # Check the column has at least 1 pixel available to remove
            assert history[ID/2][0] + history[ID/2][1] > 0


            # Expecting location with valid pixel, i.e.: 
            #   -is_active == True
            #   -distance == distances[i]
            #
            # If not, look at the other location:
            #   - ID += 1 if ID is even (ID % 2 == 0)
            #   - ID -= 1 if ID is odd
            #
            if history[ID/2][ID%2] == 0:
                # Make sure history and active_pixel_array are consistent
                assert active_pixel_array[ID].is_active == False

                ID = ID+1 if ID%2==0 else ID-1
#                print("Trying to remove from other ID")

            # After moving to other ID, look if it is an active pixel
            assert history[ID/2][ID%2] == 1, \
                'ID slots already empty (ID, #): ' + str(ID) + ', ' + \
                str(history[ID/2][ID%2])


            # Sanity check
            assert ID>=0 and ID<max_line_length

            history[ID/2][ID%2] -= 1

            active_pixel_array[ID].is_active = False

            arg_max[remove_event_id] = 0
            remove_event_id += 1
            remove_pixel_count += 1

#            row = []
#            row.append((ID, history[ID/2][0], history[ID/2][1]))
#            csv_writer.writerow(['removal:']+row)

#            row.append((ID, history[ID/2][0], history[ID/2][1]))
#        csv_writer.writerow(['removal:']+row)

        for p in range(history.shape[0]):
            assert (history[p][0] + history[p][1] >= 0) and \
                (history[p][0] + history[p][1] <= 2)

#        row = []
        # 2.1- add cells
        if abs(perimeter[0][a+1]-viewpoint[0])>abs(perimeter[1][a+1]-viewpoint[1]):
            l = 0 # Long component is I (lines)
            s = 1 # Short component is J (columns)
        else:
            l = 1 # Long component is J (columns)
            s = 0 # Short component is I (lines)

        coordL = coord[l]
        coordS = coord[s]

        Os = viewpoint[s] * sign[s]
        Ol = viewpoint[l] * sign[l]
        Es = perimeter[s][a+1] * sign[s]
        El = perimeter[l][a+1] * sign[l]

        Sl = -1 if Ol>El else 1
        Ss = -1 if Os>Es else 1

        slope = (Es-Os)/(El-Ol)

        add_pixel_count = 0
        while (add_event_id < add_event_count) and \
            (add_events[arg_min[add_event_id]] < \
                angles[a+1] - epsilon):
            i = arg_min[add_event_id]
            d = distances[i]
            v = visibility[i]
            o = offset_visibility[i]

            Pl = coordL[i] * sign[l]
            Ps = coordS[i] * sign[s]
            Dl = Pl-Ol
            Ds = Ps-Os
            ID = <int>(Sl*2*Dl+(Ss*Ds-(<int>(Ss*slope*(Dl-Sl*.5)+.5)))) \
                if Ds or Dl else 0
            
            if history[ID/2][ID%2] == 1:
                # Make sure history and active_pixel_array are consistent
                assert active_pixel_array[ID].is_active

                # Check there is some space left
                assert history[ID/2][0] + history[ID/2][1] < 2, \
                    'ID slots already full (ID, #): ' + str(ID) + ', ' + \
                    str(history[ID/2][0]) + ', ' + str(history[ID/2][1])

                ID = ID+1 if ID%2==0 else ID-1
#                print("Trying to add to other ID")

            history[ID/2][ID%2] += 1
            
            # Add new pixel
            assert ID>=0 and ID<max_line_length
            active_pixel_array[ID].is_active = True
            active_pixel_array[ID].index = i
            active_pixel_array[ID].distance = d
            active_pixel_array[ID].visibility = v
            active_pixel_array[ID].offset = o

            arg_min[add_event_id] = 0
            add_event_id += 1
            add_pixel_count += 1

#            row = []
#            row.append((ID, history[ID/2][0], history[ID/2][1]))
#            csv_writer.writerow(['additions:']+row)

#            row.append((ID, history[ID/2][0], history[ID/2][1]))
#        csv_writer.writerow(['additions:']+row)

        for p in range(history.shape[0]):
            assert (history[p][0] + history[p][1] >= 0) and \
                (history[p][0] + history[p][1] <= 2)

        # The sweep line is current, now compute pixel visibility
        active_pixel_count = update_visible_pixels_fast( \
            active_pixel_array, coord[0], coord[1], \
            max_line_length, visibility_map, a+1)

#        print(str(active_pixel_count) + ' = ' + str(previous_pixel_count) + \
#            ' + ' + str(add_pixel_count) + ' - ' + str(remove_pixel_count))

#        row = ['final:']
#        for pixel_id in range(max_line_length):
#            if active_pixel_array[pixel_id].is_active:
#                row.append(pixel_id)
#        csv_writer.writerow(row)


#        row = []
#        for ID in range(2, max_line_length):
#            row.append((ID, history[ID/2]))
#        csv_writer.writerow(['final:']+row)



#        if active_pixel_count != \
#                previous_pixel_count + add_pixel_count - remove_pixel_count:
#            print 'Active pixels'
#            total_active_pixel_count = 0
#            last_active_pixel = 0
#            for pixel_id in range(max_line_length):
#                # Inactive pixel: either we skip or we exit
#                if active_pixel_array[pixel_id].is_active:
#                    total_active_pixel_count += 1
#                    print (pixel_id, pixel_id - last_active_pixel),
#                    last_active_pixel = pixel_id
#            print('count', total_active_pixel_count, active_pixel_count)
#
#        message = str(active_pixel_count) + ' = ' + \
#            str(previous_pixel_count) + ' + ' + \
#            str(add_pixel_count) + ' - ' + str(remove_pixel_count)
#
#        assert active_pixel_count == \
#            previous_pixel_count + add_pixel_count - remove_pixel_count, message
#
#        previous_pixel_count = active_pixel_count

#    sys.exit(0)

    # clean up
    free(active_pixel_array)

    return visibility_map

