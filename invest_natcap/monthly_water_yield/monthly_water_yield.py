"""InVEST Monthly Water Yield model module"""
import math
import os.path
import logging
import csv
import datetime
import re

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
    
    data_dict = construct_time_step_data(time_step_data_uri)
    LOGGER.debug('Constructed DATA : %s', data_dict)

    list_of_months = data_dict.keys()
    list_of_months = sorted(
            list_of_months, 
            key=lambda x: datetime.datetime.strptime(x, '%m/%Y'))

    for cur_month in list_of_months:
        
        cur_step_dict = data_dict[cur_month]
        cur_field_name = re.sub('\/', '_', cur_month)
        cur_month_name = cur_field_name + '.shp'
        cur_point_uri = os.path.join(intermediate_dir, cur_month_name)

        # Make point shapefiles based on the current time step
        raster_utils.dictionary_to_point_shapefile(
                cur_step_dict, cur_field_name, cur_point_uri)
    
    
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
    unique_id = 0

    for row in data_handler:
        
        try:
            data_dict[row['date']][unique_id] = row
            unique_id+=1
        except KeyError:
            unique_id = 0
            data_dict[row['date']] = {}
            data_dict[row['date']][unique_id] = row
            unique_id+=1

    data_file.close()
    return data_dict
