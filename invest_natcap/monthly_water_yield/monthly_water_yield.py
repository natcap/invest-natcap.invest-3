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
    dem_uri = args['dem_uri']

    # Get DEM WKT
    dem_wkt = raster_utils.get_dataset_projection_wkt_uri(dem_uri)

    # Set out_nodata value
    float_nodata = float(np.finfo(np.float32).min) + 1.0

    # Construct a dictionary from the time step data
    data_dict = construct_time_step_data(time_step_data_uri)
    # A list of the fields from the time step table we are interested in and
    # need.
    data_fields = ['p']
    LOGGER.debug('Constructed DATA : %s', data_dict)

    # Get the keys from the time step dictionary, which will be the month/year
    # signature
    list_of_months = data_dict.keys()
    # Sort the list of months chronologically. 
    list_of_months = sorted(
            list_of_months, 
            key=lambda x: datetime.datetime.strptime(x, '%m/%Y'))

    for cur_month in list_of_months:
        # Get the dictionary for the current time step month
        cur_step_dict = data_dict[cur_month]
        # Since the time step signature has a 'slash' we need to replace it with
        # an underscore so that we don't run into issues with file naming
        cur_field_name = re.sub('\/', '_', cur_month)
        cur_month_name = cur_field_name + '_points.shp'
        cur_point_uri = os.path.join(intermediate_dir, cur_month_name)

        # Make point shapefiles based on the current time step
        raster_utils.dictionary_to_point_shapefile(
                cur_step_dict, cur_field_name, cur_point_uri)
   
        projected_point_name = cur_month_name + '_proj_points.shp'
        projected_point_uri = os.path.join(
                intermediate_dir, projected_point_name)
        # Project point shapefile
        raster_utils.reproject_datasource_uri(
                cur_point_uri, dem_wkt, projected_point_uri) 

        raster_uri_list = []
        # Use vectorize points to construct rasters based on points and fields
        for field in data_fields:
            out_uri_name = cur_month_name + '_' + field + '.tif'
            output_uri = os.path.join(intermediate_dir, out_uri_name)
            raster_uri_list.append(output_uri)
            
            _ = raster_utils.new_raster_from_base_uri(
                    dem_uri, output_uri, 'GTIFF', float_nodata,
                    gdal.GDT_Float32, fill_value=float_nodata)

            raster_utils.vectorize_points_uri(cur_point_uri, field, output_uri)


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

        returns - a dictionary with the following structure:
            {
                '01/1988':{
                    0:{'date':'01/1988','lati':'44.5','long':'-123.3','p':'10'},
                    1:{'date':'01/1988','lati':'44.5','long':'-123.5','p':'5'},
                    2:{'date':'01/1988','lati':'44.3','long':'-123.3','p':'0'}
                    },
                '02/1988':{
                    0:{'date':'02/1988','lati':'44.5','long':'-123.3','p':'10'},
                    1:{'date':'02/1988','lati':'44.5','long':'-123.4','p':'6'},
                    2:{'date':'02/1988','lati':'44.6','long':'-123.5','p':'7'}
                    }...
            }
    """
    data_file = open(data_uri)
    data_handler = csv.DictReader(data_file)
    
    # Make the fieldnames lowercase
    data_handler.fieldnames = [f.lower() for f in data_handler.fieldnames]
    LOGGER.debug('Lowercase Fieldnames : %s', data_handler.fieldnames)
    
    data_dict = {}
    # An ID variable that will be assigned as the unique key for the sub
    # dictionary of each time step.
    unique_id = 0

    for row in data_handler:
        # Try/except block helps to properly set each monthly time step as a
        # unique key. These monthly keys map to a sub dictionary where the
        # points for the data are held. This block trys to assign those points
        # to the sub dictionary, however if the monthly time step has not been
        # added as an outer unique key, it is created in the except block.
        try:
            # Try to assign unique point to monthly time step
            data_dict[row['date']][unique_id] = row
            unique_id+=1
        except KeyError:
            # If this is a new monthly time step then set the unique_id to 0
            unique_id = 0
            # Initialize the new monthly time step
            data_dict[row['date']] = {}
            # Add the first point for the monthly time step
            data_dict[row['date']][unique_id] = row
            unique_id+=1

    data_file.close()
    return data_dict
