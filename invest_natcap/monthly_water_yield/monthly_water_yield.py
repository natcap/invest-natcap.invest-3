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
from invest_natcap.invest_core import fileio

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('monthly_water_yield')


def execute(args):
    """Doc string for the purpose of the model and the inputs packaged in 'args'
   
        args -

        args[time_step_data] - a uri to a CSV file

    """
    LOGGER.debug('Start Executing Model')

    # Get input URIS
    time_step_data_uri = args['time_step_data_uri']


    # Process data from time_step_data
        # Read precip data into a dictionary
        
    time_step_data_handler = fileio.TableHandler(time_step_data_uri)
    time_step_data_list = time_step_data_handler.get_table()
    LOGGER.debug('Time Step Handler : %s', time_step_data_list)


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
