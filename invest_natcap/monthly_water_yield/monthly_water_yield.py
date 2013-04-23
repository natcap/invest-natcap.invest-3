"""InVEST Monthly Water Yield model module"""
import math
import os.path
import logging

from osgeo import osr
from osgeo import gdal
from osgeo import ogr
import numpy as np
#required for py2exe to build
from scipy.sparse.csgraph import _validation

from invest_natcap import raster_utils
LOGGER = logging.getLogger('monthly_water_yield')


def execute(args):
    """Doc string for the purpose of the model and the inputs packaged in 'args'
    
    """
    LOGGER.debug('Start Executing Model')

    # Get input URIS



    # Process data from time_step_data
        # Read precip data into a dictionary
        # 

    # Make point shapefiles based on the current time step

    # Use vectorize points to construct rasters based on points and fields

    # Calculate Evapotranspiration

    # Calculate Direct Flow (Runoff)

    # Calculate Interflow

    # Calculate Baseflow

    # Calculate Streamflow

    # Calculate Soil Moisture for current time step, to be used as previous time
    # step in the next iteration

    # Add values to output table

    # Move on to next month
