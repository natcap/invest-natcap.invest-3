"""InVEST Hydropower Valuation module at the "uri" level"""

import sys
import os
import logging
import csv

from osgeo import gdal
from osgeo import ogr

from invest_natcap.hydropower import hydropower_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('hydropower_valuation')

def execute(args):
    """This function invokes the valuation model for hydropower given
        URI inputs of files. It will do filehandling and open/create
        appropriate objects to pass to the core sediment biophysical 
        processing function.  It may write log, warning, or error messages to 
        stdout.
        
        args - a python dictionary with at the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['cal_water_yield'] - 
        args['water_consump'] - 
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds_uri'] - a uri to an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['watershed_scarcity_table'] - 
        args['subwatershed_scarcity_table'] - 
        args['valuation_table_uri'] - a uri to an input CSV table of 
            land use/land cover classes, containing data on biophysical 
            coefficients such as root_depth and etk. NOTE: these data are 
            attributes of each LULC class rather than attributes of individual 
            cells in the raster map (required)
        args['seasonality_constant'] - floating point value between 1 and 10 
            corresponding to the seasonal distribution of precipitation 
            (required)
            
        returns - nothing"""
        
    #Set up the file directories
    workspace_dir = args['workspace_dir']
    val_args = {}
    val_args['workspace_dir'] = workspace_dir
    
    #Create the output directories
    for folder_name in ['Output', 'Service', 'Intermediate']:
        folder_path = workspace_dir + os.sep + folder_name
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
    
    #Open gdal raster files and pass to new dictionary
        
    #Open ogr shapefiles and pass to new dicitonary
        
    #Open csv tables and store in dictionaries
        
    #Call hydropower_core.valuation
        
#    hydropower_core.valuation(val_args)