import math

import numpy as np
import collections
import logging

#LOGGER = logging.get('aesthetic_quality_core')
#logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
#    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def list_extreme_cell_angles(array_shape, viewpoint_coords):
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

    pi = math.pi
    two_pi = 2. * pi
    rad_to_deg = 180.0 / pi
    deg_to_rad = 1.0 / rad_to_deg

    extreme_cell_points = [ \
    {'min_angle':[0.5, -0.5], 'max_angle':[-0.5, -0.5]}, \
    {'min_angle':[0.5, 0.5], 'max_angle':[-0.5, -0.5]}, \
    {'min_angle':[0.5, 0.5], 'max_angle':[0.5, -0.5]}, \
    {'min_angle':[-0.5, 0.5], 'max_angle':[0.5, -0.5]}, \
    {'min_angle':[-0.5, 0.5], 'max_angle':[0.5, 0.5]}, \
    {'min_angle':[-0.5, -0.5], 'max_angle':[0.5, 0.5]}, \
    {'min_angle':[-0.5, -0.5], 'max_angle':[-0.5, 0.5]}, \
    {'min_angle':[0.5, -0.5], 'max_angle':[-0.5, 0.5]}]

    min_angles = []
    angles = []
    max_angles = []
    I = []
    J = []
    for row in range(array_shape[0]):
        for col in range(array_shape[1]):
            # Skip if cell falls on the viewpoint
            if (row == viewpoint[0]) and (col == viewpoint[1]):
                continue
            cell = np.array([row, col])
            I.append(row)
            J.append(col)
            viewpoint_to_cell = cell - viewpoint
            # Compute the angle of the cell center
            angle = np.arctan2(-viewpoint_to_cell[0], viewpoint_to_cell[1])
            angles.append((angle + two_pi) % two_pi)
            # find index in extreme_cell_points that corresponds to the current
            # angle to compute the offset from cell center
            sector = int(4. * angles[-1] / two_pi) * 2
            if np.amin(np.absolute(viewpoint_to_cell)) > 0:
                sector += 1
            min_corner_offset = \
                np.array(extreme_cell_points[sector]['min_angle'])
            max_corner_offset = \
                np.array(extreme_cell_points[sector]['max_angle'])
            # Use the offset to compute extreme angles
            min_corner = viewpoint_to_cell + min_corner_offset
            min_angle = np.arctan2(-min_corner[0], min_corner[1])
            min_angles.append((min_angle + two_pi) % two_pi) 
            
            max_corner = viewpoint_to_cell + max_corner_offset
            max_angle = np.arctan2(-max_corner[0], max_corner[1])
            max_angles.append((max_angle + two_pi) % two_pi)
    # Create a tuple of ndarray angles before returning
    min_angles = np.array(min_angles)
    angles = np.array(angles)
    max_angles = np.array(max_angles)
    I = np.array(I)
    J = np.array(J)

    return (min_angles, angles, max_angles, I, J)

# Linked cells used for the active pixels
linked_cell_factory = collections.namedtuple('linked_cell', \
    ['previous', 'next', 'distance', 'visibility'])

# Links to the cells
cell_link_factory = collections.namedtuple('cell_link', \
    ['top', 'right', 'bottom', 'level', 'distance'])

def find_active_pixel_fast(sweep_line, skip_nodes, distance):
    """Find an active pixel based on distance. Return None if can't be found"""
    if 'closest' in sweep_line:
        print('closest exist in sweep_line')
        if len(skip_nodes) > 0:
            print('Skip nodes non empty: pick the one at [' + \
                str(len(skip_nodes) - 1) + '][0]')
            # Get information about first pixel in the list
            pixel = skip_nodes[-1][0]
        else:
            print("skip nodes empty, use sweep_line['closest']")
            pixel = sweep_line['closest']
        previous = pixel

        # go right until distance is passed
        while (pixel['distance'] < distance):
            print('pixel distance ' + str(pixel['distance']) + ' < ' + \
                str(distance) + ', moving on to next pixel')
            previous = pixel
            pixel = pixel['next']
        print('stopped at pixel', pixel['distance'])
        if pixel['distance'] == distance:
            print('found the value we wanted.')
            while (pixel['down'] is not None):
                print('We have to go down')
                pixel = pixel['down']
            print('done, returning pixel', pixel['distance'])
            return pixel
        
        # Go down 1 level
        print(pixel['distance'], "is too far.")
        if previous['down'] is None:
            print("can't go further down: value doesn't exist. Return None.")
            return None
        print("Going down from", previous['distance'])
        pixel = previous['down']
        print('max span is', span)
        span = previous['span']
        iteration = 0
        while (iteration < span) and (pixel['distance'] < distance):
            print('pixel distance is too small', pixel['distance'], \
                'moving forward')
            pixel = pixel['next']
            iteration += 1
            print('moved forward', iteration, 'times')
        print('Done moving forward')
        if pixel['distance'] == distance:
            print('Found the value we wanted.')
            while (pixel['down'] is not None):
                print('Not down enough. Going further down.')
                pixel = pixel['down']
            print('Found the pixel on sweep_line, returning it.')
            return pixel
        if pixel['distance'] > distance:
            print('Pixel distance', pixel['distance'], \
                'is too high, returning None')
            return None
        return pixel
    else:
        print('list is empty: returning None')
        return None

def find_active_pixel(sweep_line, distance):
    """Find an active pixel based on distance. Return None if can't be found"""
    if 'closest' in sweep_line:
        # Get information about first pixel in the list
        pixel = sweep_line[sweep_line['closest']['distance']] # won't change
        # Move on to next pixel if we're not done
        while (pixel is not None) and \
            (pixel['distance'] < distance):
            pixel = pixel['next']
        # We reached the end and didn't find anything
        if pixel is None:
            return None
        # We didn't reach the end: either pixel doesn't exist...
        if pixel['distance'] != distance:
            return None
        # ...or we found it
        else:
            return pixel
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


def add_active_pixel_fast(sweep_line, distance, visibility):
    """Add a pixel to the sweep line in O(log n) using a skip list."""
    # Make sure we're not creating any duplicate
    message = 'Duplicate entry: the value ' + str(distance) + ' already exist'
    assert distance not in sweep_line, message
    new_pixel = \
    {'next':None, 'up':None, 'distance':distance, 'visibility':visibility}
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

def add_active_pixel(sweep_line, distance, visibility):
    """Add a pixel to the sweep line in O(n) using a linked_list of
    linked_cells."""
    # Make sure we're not creating any duplicate
    message = 'Duplicate entry: the value ' + str(distance) + ' already exist'
    assert distance not in sweep_line, message
    new_pixel = {'next':None, 'distance':distance, 'visibility':visibility}
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

def viewshed(input_uri, output_uri, coordinates, obs_elev=1.75, tgt_elev=0.0, \
max_dist=-1., refraction_coeff=None):
    """Viewshed computation function
        
        Inputs: 
            -input_uri: uri of the input elevation raster map
            -output_uri: uri of the output raster map
            -coordinates: tuple (east, north) of coordinates of viewing
                position
            -obs_elev: observer elevation above the raster map.
            -tgt_elev: offset for target elevation above the ground. Applied to
                every point on the raster
            -max_dist: maximum visibility radius. By default infinity (-1), 
                not used yet
            -refraction_coeff: refraction coefficient (0.0-1.0), not used yet"""
    add_cell_events = []
    delete_cell_events = []
    cell_center_events = []

    in_raster = gdal.Open(input_uri)
    in_array = in_raster.GetRasterBand(1).ReadAsArray()

    extreme_angles

def execute(args):
    """Entry point for aesthetic quality core computation.
    
        Inputs:
        
        Returns
    """
    pass
