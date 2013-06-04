"""InVEST Water Scarcity module at the "uri" level"""

import os
import logging
import csv

from osgeo import gdal
from osgeo import ogr

from invest_natcap.hydropower import hydropower_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('water_scarcity')

def execute(args):
    """This function invokes the water scarcity model given
        URI inputs of files. It will do file handling and open/create
        appropriate objects to pass to the core water scarcity
        processing function.  It may write log, warning, or error messages to 
        stdout.
        
        args - a python dictionary with at least the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['lulc_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexes in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape.  (required)
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds_uri'] - a uri to an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['watershed_yield_table_uri'] - a uri to an input CSV table, 
            generated from the water_yield model, containing values for mean 
            precipitation, potential and actual evapotranspiration and water
            yield per watershed
        args['subwatershed_yield_table_uri'] - a uri to an input CSV table, 
            generated from the water_yield model, containing values for mean 
            precipitation, potential and actual evapotranspiration and water
            yield per sub watershed
        args['demand_table_uri'] - a uri to an input CSV table of LULC classes,
            showing consumptive water use for each landuse / land-cover type
            (cubic meters per year) (required)
        args['hydro_calibration_table_uri'] - a  uri to an input CSV table of 
            hydropower stations with associated calibration values (required)
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional)
           
        returns nothing"""
    
    LOGGER.info('Starting Water Scarcity File Handling')
    
   # workspace_dir = args['workspace_dir']
    #Create the output directories
#   for folder_name in ['Output', 'Service', 'Intermediate']:
#       folder_path = workspace_dir + os.sep + folder_name
#       if not os.path.isdir(folder_path):
#           os.makedirs(folder_path)
    
  #  water_scarcity_args = {}
 #   water_scarcity_args['workspace_dir'] = args['workspace_dir']
    
    #Open all of the gdal files and add to the arguments
#    water_scarcity_args['lulc'] = args['lulc_uri']
    
    #Open all the shapefiles and add to the arguments
#    water_scarcity_args['watersheds'] = args['watersheds_uri']
#    water_scarcity_args['sub_watersheds'] = args['sub_watersheds_uri']
    
    #Open/read in the csv files into a dictionary and add to arguments
#   watershed_yield_table_map = {}
#   watershed_yield_table_file = open(args['watershed_yield_table_uri'])
#   reader = csv.DictReader(watershed_yield_table_file)
#   for row in reader:
#       watershed_yield_table_map[int(row['ws_id'])] = row
#   
#   water_scarcity_args['watershed_yield_table'] = watershed_yield_table_map
#   watershed_yield_table_file.close()
#   
#   subwatershed_yield_table_map = {}
#   subwatershed_yield_table_file = open(args['subwatershed_yield_table_uri'])
#   reader = csv.DictReader(subwatershed_yield_table_file)
#   for row in reader:
#       subwatershed_yield_table_map[int(row['subws_id'])] = row
#   
#   water_scarcity_args['subwatershed_yield_table'] = \
#       subwatershed_yield_table_map
#   subwatershed_yield_table_file.close()
#   
#   demand_table_map = {}
#   demand_table_file = open(args['demand_table_uri'])
#   reader = csv.DictReader(demand_table_file)
#   for row in reader:
#       demand_table_map[int(row['lucode'])] = int(row['demand'])
#   
#   LOGGER.debug('Demand_Dict : %s', demand_table_map)
#   water_scarcity_args['demand_table'] = demand_table_map
#   demand_table_file.close()
#   
#   hydro_cal_table_map = {}
#   hydro_cal_table_file = open(args['hydro_calibration_table_uri'])
#   reader = csv.DictReader(hydro_cal_table_file)
#   for row in reader:
#       hydro_cal_table_map[int(row['ws_id'])] = float(row['calib'])
#       
#   water_scarcity_args['hydro_calibration_table'] = hydro_cal_table_map
#   hydro_cal_table_file.close()
    
    #Add the suffix string to the arguments
#    water_scarcity_args['results_suffix'] = args['results_suffix']
    
    #Call water_scarcity_core.py
    hydropower_core.water_scarcity(args)
    LOGGER.info('Water Scarcity Completed')
