"""InVEST Hydropower Valuation module at the "uri" level"""

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
        URI inputs of files. It will do file handling and open/create
        appropriate objects to pass to the core hydropower valuation
        processing function.  It may write log, warning, or error messages to 
        stdout.
        
        args - a python dictionary with at least the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['cyield_uri'] - a uri to a Gdal raster of the calibrated
            water yield volume per sub-watershed, generated as an output
            of the water scarcity model (cubic meters) (required)
            NOTE: This input is currently only being used to get a pixel size
            for output rasters. It is not needed otherwise unless we later
            want to add in per pixel applications.  All calculations are being
            taken from the water_scarcity_tables.
        args['consump_uri'] - a uri to a Gdal raster of the total water
            consumptive use for each sub-watershed, generated as an output
            of the water scarcity model (cubic meters) (required)
            NOTE: This input is currently only being used to get a pixel size
            for output rasters. It is not needed otherwise unless we later
            want to add in per pixel applications.  All calculations are being
            taken from the water_scarcity_tables.
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds_uri'] - a uri to an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['watershed_scarcity_table_uri'] - a uri to an input CSV table,
            generated as an output of the water scarcity model, that holds
            relevant values for each watershed. (required)
        args['subwatershed_scarcity_table_uri'] - a uri to an input CSV table,
            generated as an output of the water scarcity model, that holds
            relevant values for each sub watershed. (required)
        args['valuation_table_uri'] - a uri to an input CSV table of 
            hydropower stations with the following fields (required):
            ('ws_id', 'time_span', 'discount', 'efficiency', 'fraction',
            'cost', 'height', 'kw_price')
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional)
               
        returns - nothing"""
    
    LOGGER.info('Starting Hydropower Valuation File Handling')
    
    #Set up the file directories
    workspace_dir = args['workspace_dir']
    val_args = {}
    val_args['workspace_dir'] = workspace_dir
    
    #Create the output directories
    for folder_name in ['Output', 'Service', 'Intermediate']:
        folder_path = workspace_dir + os.sep + folder_name
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
    
    #Open gdal raster files and pass to the arguments
    val_args['cyield_vol'] = gdal.Open(args['cyield_uri'])
    val_args['consump_vol'] = gdal.Open(args['consump_uri'])
    
    #Open ogr shapefiles and pass to new dicitonary
    val_args['watersheds'] = ogr.Open(args['watersheds_uri'])
    val_args['sub_watersheds'] = ogr.Open(args['sub_watersheds_uri'])
    
    #Open csv tables and add to the arguments
    valuation_table_map = {}
    valuation_table_file = open(args['valuation_table_uri'])
    reader = csv.DictReader(valuation_table_file)
    for row in reader:
        valuation_table_map[int(row['ws_id'])] = row
    
    val_args['valuation_table'] = valuation_table_map
    valuation_table_file.close()
    
    water_scarcity_map = {}
    water_scarcity_table_file = open(args['watershed_scarcity_table_uri'])
    reader = csv.DictReader(water_scarcity_table_file)
    for row in reader:
        water_scarcity_map[int(row['ws_id'])] = row
    
    val_args['watershed_scarcity_table'] = water_scarcity_map
    water_scarcity_table_file.close()

    subwater_scarcity_map = {}
    subwater_scarcity_table_file = open(args['subwatershed_scarcity_table_uri'])
    reader = csv.DictReader(subwater_scarcity_table_file)
    for row in reader:
        subwater_scarcity_map[int(row['subws_id'])] = row
    
    val_args['subwatershed_scarcity_table'] = subwater_scarcity_map
    subwater_scarcity_table_file.close()    
    
    #Add the suffix string to arguments
    val_args['results_suffix'] = args['results_suffix']
    
    #Call hydropower_core.valuation
    hydropower_core.valuation(val_args)
    LOGGER.info('Hydropower Valuation Completed')
