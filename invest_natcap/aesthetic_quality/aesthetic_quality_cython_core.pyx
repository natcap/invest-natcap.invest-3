from libc.math cimport atan2
from libc.math cimport sin
import math
cimport numpy as np
import numpy as np

import cython

cdef extern from "math.h":
    double atan2(double x, double x)

#cdef extern from "math.h":
#    int abs(int x)


cdef inline int int_round(float x): return <int>(x) if x-<int>x <= 0.5  else <int>(x+1)

class NotAtSea(Exception): pass
@cython.boundscheck(False)
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
    viewpoint = np.array(viewpoint_coords)

    pi = 3.1415926535897932384626433852
    two_pi = 2. * pi
    rad_to_deg = 180.0 / pi
    deg_to_rad = 1.0 / rad_to_deg

    cdef:
        int min_angle_id = 0
        int max_angle_id = 1
        #float viewpoint[2] = {viewpoint_coords[0], viewpoint_coords[1]}

    extreme_cell_points = np.array([ \
    [[0.5, -0.5], [-0.5, -0.5]], \
    [[0.5, 0.5], [-0.5, -0.5]], \
    [[0.5, 0.5], [0.5, -0.5]], \
    [[-0.5, 0.5], [0.5, -0.5]], \
    [[-0.5, 0.5], [0.5, 0.5]], \
    [[-0.5, -0.5], [0.5, 0.5]], \
    [[-0.5, -0.5], [-0.5, 0.5]], \
    [[0.5, -0.5], [-0.5, 0.5]]], dtype = float)

    print('listing extreme cell angles')
    cell_count = array_shape[0]*array_shape[1]

    min_angles = np.ndarray(cell_count -1, dtype = np.float)
    angles = np.ndarray(cell_count -1, dtype = np.float)
    max_angles = np.ndarray(cell_count -1, dtype = np.float)
    I = np.ndarray(cell_count -1, dtype = np.int32)
    J = np.ndarray(cell_count -1, dtype = np.int32)

    # Loop through the rows
    cdef:
        #int array_size[2] = {array_shape[0], array_shape[1]}
        int cell_id = 0
        int row = 0
        int col = 0
        #int cell[2] = {0, 0}
        #int viewpoint_to_cell[2] = {0, 0}

    for row in range(array_shape[0]):
        # Loop through the columns    
        for col in range(array_shape[1]):
            # Show progress in 0.1% increment
            if (cell_count > 1000) and \
                (cell_id % (cell_count/1000)) == 0:
                progress = round(float(cell_id) / cell_count * 100.,1)
                print(str(progress) + '%')
            # Skip if cell falls on the viewpoint
            if (row == viewpoint[0]) and (col == viewpoint[1]):
                continue
            # cell coordinates
            cell = np.array([row, col])
            # Update list of rows and list of cols
            #I.append(row)
            I[cell_id] = row
            #J.append(col)
            J[cell_id] = col
            viewpoint_to_cell = cell - viewpoint
            # Compute the angle of the cell center
            angle = atan2(-viewpoint_to_cell[0], viewpoint_to_cell[1])
            #angles.append((angle + two_pi) % two_pi)
            angles[cell_id] = (angle + two_pi) % two_pi
            # find index in extreme_cell_points that corresponds to the current
            # angle to compute the offset from cell center
            # This line only discriminates between 4 axis-aligned angles
            sector = int(4. * angles[cell_id] / two_pi) * 2
            # The if statement adjusts for all the 8 angles
            #if abs(viewpoint_to_cell[0] * viewpoint_to_cell[1]) > 0:
            if np.amin(np.absolute(viewpoint_to_cell)) > 0:
                sector += 1
            # adjust wrt 8 angles
            min_corner_offset = \
                np.array(extreme_cell_points[sector][min_angle_id])
            max_corner_offset = \
                np.array(extreme_cell_points[sector][max_angle_id])
            # Use the offset to compute extreme angles
            min_corner = viewpoint_to_cell + min_corner_offset
            min_angle = atan2(-min_corner[0], min_corner[1])
            #min_angles.append((min_angle + two_pi) % two_pi) 
            min_angles[cell_id] = (min_angle + two_pi) % two_pi 
            
            max_corner = viewpoint_to_cell + max_corner_offset
            max_angle = atan2(-max_corner[0], max_corner[1])
            #max_angles.append((max_angle + two_pi) % two_pi)
            max_angles[cell_id] = (max_angle + two_pi) % two_pi
            cell_id += 1
    print('done listing extreme cell angles, storing results')
    # Create a tuple of ndarray angles before returning
    min_angles = np.array(min_angles)
    angles = np.array(angles)
    max_angles = np.array(max_angles)
    I = np.array(I)
    J = np.array(J)
    print('done storing result. Returning.')
    return (min_angles, angles, max_angles, I, J)


