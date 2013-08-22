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
    extreme_cell_angles = []
    x_range = np.array(range(array_shape[0]))
    y_range = np.array(range(array_shape[1]))

    print(x_range)
    print(y_range)

    #xx = np.meshgrid()

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
