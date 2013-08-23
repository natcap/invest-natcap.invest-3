import math

import numpy as np
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
            
        returns a tuple of 2 arrays (min, max) as does numpy.where() with min
            and max the minimum and maximum angles spanned by each raster pixel
    """
    viewpoint = np.array(viewpoint_coords)

    pi = math.pi
    two_pi = 2. * pi
    rad_to_deg = 180.0 / pi
    deg_to_rad = 1.0 / rad_to_deg

    extreme_cell_points = [ \
    [{'min_angle':[0.5, -0.5]}, {'max_angle':[-0.5,-0.5]}], \
    [{'min_angle':[0.5, 0.5]}, {'max_angle':[-0.5, -0.5]}], \
    [{'min_angle':[0.5, 0.5]}, {'max_angle':[0.5, -0.5]}], \
    [{'min_angle':[-0.5, 0.5]}, {'max_angle':[0.5, -0.5]}], \
    [{'min_angle':[-0.5, 0.5]}, {'max_angle':[0.5, 0.5]}], \
    [{'min_angle':[-0.5, -0.5]}, {'max_angle':[0.5, 0.5]}], \
    [{'min_angle':[-0.5, -0.5]}, {'max_angle':[-0.5, 0.5]}], \
    [{'min_angle':[0.5, -0.5]}, {'max_angle':[-0.5, 0.5]}]]

    extreme_cell_angles = []
    x_range = np.array(range(array_shape[0]))
    y_range = np.array(range(array_shape[1]))

    print(x_range)
    print(y_range)

    for entry in extreme_cell_points:
        print(entry)

    for row in range(array_shape[0]):
        for col in range(array_shape[1]):
            # Skip if cell falls on the viewpoint
            if (row == viewpoint[0]) and (col == viewpoint[1]):
                continue
            cell = np.array([row, col])
            viewpoint_to_cell = cell - viewpoint
            angle = np.arctan2(-viewpoint_to_cell[0], viewpoint_to_cell[1])
            angle = (angle + two_pi) % two_pi 
            print(cell, viewpoint_to_cell, angle * rad_to_deg)
            extreme_cell_angles.append(np.array([angle, angle]))
            # find index in extreme_cell_points that corresponds to the current
            # angle:
            index = int(4. * angle / two_pi) * 2
            if np.amin(np.absolute(viewpoint_to_cell)) > 0:
                index += 1
            print(index)
    
    extreme_cell_angles = np.array(extreme_cell_angles) 

    return extreme_cell_angles

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
    pass

def execute(args):
    """Entry point for aesthetic quality core computation.
    
        Inputs:
        
        Returns
    """
    pass
