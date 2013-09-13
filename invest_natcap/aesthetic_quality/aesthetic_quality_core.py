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
