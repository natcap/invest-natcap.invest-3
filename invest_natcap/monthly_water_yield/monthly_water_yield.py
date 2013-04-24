"""InVEST Monthly Water Yield model module"""
import math
import os.path
import logging
import csv

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

        args[workspace_dir] - a uri to the workspace directory where outputs
            will be written to disk
        args[time_step_data] - a uri to a CSV file

    """
    LOGGER.debug('Start Executing Model')
    
    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')
    raster_utils.create_directories([intermediate_dir, output_dir])

    # Get input URIS
    time_step_data_uri = args['time_step_data_uri']


    # Process data from time_step_data
        # Read precip data into a dictionary
        
    time_step_data_handler = fileio.TableHandler(time_step_data_uri)
    time_step_data_list = time_step_data_handler.get_table()
    LOGGER.debug('Time Step Handler : %s', time_step_data_list)
    
    data_dict = construct_time_step_data(time_step_data_uri)
    LOGGER.debug('Constructed DATA : %s', data_dict)

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

def construct_time_step_data(data_uri):
    """Parse the CSV data file and construct a dictionary using the time step
        dates as keys. Each unique date will then have a dictionary of the
        points.

        data_uri - a URI path to a CSV file

        returns - a dictionary"""

    data_file = open(data_uri)
    data_handler = csv.DictReader(data_file)
    LOGGER.debug('Original Fieldnames : %s', data_handler.fieldnames)
    # Make the fielnames lowercase
    data_handler.fieldnames = [f.lower() for f in data_handler.fieldnames]
    LOGGER.debug('Lowercase Fieldnames : %s', data_handler.fieldnames)
    
    data_dict = {}

    for row in data_handler:
        try:
            data_dict[row['date']][(
                float(row['lati']), float(row['long']))] = float(row['p'])
        except KeyError:
            data_dict[row['date']] = {}
            data_dict[row['date']][(
                float(row['lati']), float(row['long']))] = float(row['p'])

    data_file.close()
    return data_dict
