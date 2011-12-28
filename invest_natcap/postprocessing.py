"""This is a collection of postprocessing functions that are useful for some
    of the InVEST models."""

import logging

import numpy as np
import pylab

LOGGER = logging.getLogger('postprocessing')

def plot_flow_direction(flow_matrix):
    """Generates a quiver plot (arrows on a grid) of a flow matrix
    
    flow_matrix - a raster of floats indicating the direciton of flow out of
        each pixel.  Values are given in radians
        
    returns nothing"""

    LOGGER.info('Starting plot of flow direction')
    pylab.figure()
    pylab.quiver(np.cos(flow_matrix), np.sin(flow_matrix),
                 units='xy',
                 pivot='middle',
                 scale=1)
    pylab.tight_layout()
    pylab.savefig('flow.png', dpi=3200)
    LOGGER.info('Done with plot of flow direction')
