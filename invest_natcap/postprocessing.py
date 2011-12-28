"""This is a collection of postprocessing functions that are useful for some
    of the InVEST models."""

import numpy as np
import pylab

def plot_flow_direction(flow_matrix):
    """Generates a quiver plot (arrows on a grid) of a flow matrix
    
    flow_matrix - a raster of floats indicating the direciton of flow out of
        each pixel.  Values are given in radians
        
    returns nothing"""

    pylab.figure()
    pylab.quiver(np.cos(flow_matrix), np.sin(flow_matrix))
    pylab.show()
