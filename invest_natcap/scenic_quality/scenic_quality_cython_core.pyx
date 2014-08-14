import sys
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

cdef void update_visible_pixels_fast(ActivePixel *active_pixel_array, \
    np.ndarray[np.int32_t, ndim = 1] I, \
    np.ndarray[np.int32_t, ndim = 1] J, \
    int pixel_count, np.ndarray[np.float64_t, ndim = 2] visibility_map):
        
    cdef ActivePixel p
    cdef double max_visibility = -1000000.
    cdef double visibility = 0
    cdef int index = -1
    cdef int pixel_id

    for pixel_id in range(2, pixel_count):
        p = active_pixel_array[pixel_id]
        # Inactive pixel: either we skip or we exit
        if not p.is_active:
            # No more pixels to check if 2nd inactive pixel beyond position 2
            if not active_pixel_array[pixel_id-1].is_active and \
                not active_pixel_array[pixel_id-2].is_active:
                break
            # Just an inactive pixel, skip it
            else:
                continue
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
    #if El!=Ol:
    #    print('Os', Os, 'Ol', Ol, 'Es', Es, 'El', El, 'Ps', P[s], 'Pl', P[l])
    #    print('Es-Os', Es-Os, ' / El-Ol', El-Ol, 'slope', slope)

    return active_pixel_index(Ol, Os, P[l], P[s], El, Es, Dl, Ds, Sl, Ss, slope)

cdef int active_pixel_index(double Ol, double Os, \
                        double Pl, double Ps, \
                        double El, double Es, \
                        double Dl, double Ds, \
                        double Sl, double Ss,
                        double slope):
    
    return int(Sl*2*Dl+(Ss*Ds-int(Ss*slope*(Dl-Sl*.5)+.5))) if Ds or Dl else 0


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
    np.ndarray[np.float64_t, ndim = 2, mode="c"] visibility_map):
    """Update the active pixels as the algorithm consumes the sweep angles"""
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
    cdef np.int32_t Pl = 0
    cdef np.int32_t Ps = 0
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
    for index in range(max_line_length):
        active_pixel_array[index].is_active = False
    # 4- build event lists
    cdef int add_event_id = 0
    cdef int add_event_count = add_events.size
    cdef int center_event_id = 0
    cdef int center_event_count = center_events.size
    cdef int remove_event_id = 0
    cdef int remove_event_count = remove_events.size

    cdef np.int32_t [:] coordL = coord[l]
    cdef np.int32_t [:] coordS = coord[s]

    # 1- add cells at angle 0
    # Collect cell_center events
    while (center_event_id < center_event_count) and \
        (center_events[arg_center[center_event_id]] < angles[1]):
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
        assert ID>=0 and ID<max_line_length
        active_pixel_array[ID].is_active = True
        active_pixel_array[ID].index = i
        active_pixel_array[ID].distance = d
        active_pixel_array[ID].visibility = v
        active_pixel_array[ID].offset = o
        center_event_id += 1
    # The sweep line is current, now compute pixel visibility
    update_visible_pixels_fast( \
        active_pixel_array, coord[0], coord[1], \
        max_line_length, visibility_map)

    # 2- loop through line sweep angles:
    for a in range(angle_count-2):
        # 2.2- remove cells
        if abs(perimeter[0][a]-viewpoint[0])>abs(perimeter[1][a]-viewpoint[1]):
            l = 0 # Long component is I (lines)
            s = 1 # Short component is J (columns)
        else:
            l = 1 # Long component is J (columns)
            s = 0 # Short component is I (lines)
          
        coordL = coord[l]
        coordS = coord[s]

        Os = viewpoint[s] * sign[s]
        Ol = viewpoint[l] * sign[l]
        Es = perimeter[s][a] * sign[s]
        El = perimeter[l][a] * sign[l]

        Sl = -1 if Ol>El else 1
        Ss = -1 if Os>Es else 1

        slope = (Es-Os)/(El-Ol)

        while (remove_event_id < remove_event_count) and \
            (remove_events[arg_max[remove_event_id]] <= angles[a+1]):
            i = arg_max[remove_event_id]
            d = distances[i]
            Pl = coordL[i]*sign[l]
            Ps = coordS[i]*sign[s]
            Dl = Pl-Ol
            Ds = Ps-Os
            ID = <int>(Sl*2*Dl+(Ss*Ds-(<int>(Ss*slope*(Dl-Sl*.5)+.5)))) \
                if Ds or Dl else 0
            # Expecting valid pixel: is_active and distance == distances[i]
            # Move other pixel over otherwise
            if not active_pixel_array[ID].is_active or \
                active_pixel_array[ID].distance != distances[i]:
                ID = ID+1 if (ID/2)*2 == ID else ID-1
            assert ID>=0 and ID<max_line_length
            active_pixel_array[ID].is_active = False

            arg_max[remove_event_id] = 0
            remove_event_id += 1
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

        while (add_event_id < add_event_count) and \
            (add_events[arg_min[add_event_id]] < angles[a+1]):
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
            # Active pixels could collide. If so, compute offset
            if active_pixel_array[ID].is_active:
                alternate_ID = ID+1 if (ID/2)*2 == ID else ID-1
                # Move existing pixel over
                active_pixel_array[alternate_ID] = active_pixel_array[ID]
            # Add new pixel
            assert ID>=0 and ID<max_line_length
            active_pixel_array[ID].is_active = True
            active_pixel_array[ID].index = i
            active_pixel_array[ID].distance = d
            active_pixel_array[ID].visibility = v
            active_pixel_array[ID].offset = o

            arg_min[add_event_id] = 0
            add_event_id += 1
        # The sweep line is current, now compute pixel visibility
        update_visible_pixels_fast( \
            active_pixel_array, coord[0], coord[1], \
            max_line_length, visibility_map) 

    # clean up
    free(active_pixel_array)

    return visibility_map

