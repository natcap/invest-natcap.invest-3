"""InVEST Water Yield module at the "uri" level"""

import os
import logging
import csv

from osgeo import gdal
from osgeo import ogr

from invest_natcap.hydropower import hydropower_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('water_yield')

def execute(args):
    """This function invokes the water yield model given
        URI inputs of files. It will do file handling and open/create
        appropriate objects to pass to the core water yield processing 
        function.  It may write log, warning, or error messages to 
        stdout.
        
        args - a python dictionary with at least the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['lulc_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexes in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape. (required)
        args['soil_depth_uri'] - a uri to an input raster describing the 
            average soil depth value for each cell (mm) (required)
        args['precipitation_uri'] - a uri to an input raster describing the 
            average annual precipitation value for each cell (mm) (required)
        args['pawc_uri'] - a uri to an input raster describing the 
            plant available water content value for each cell. Plant Available
            Water Content fraction (PAWC) is the fraction of water that can be
            stored in the soil profile that is available for plants' use. 
            PAWC is a fraction from 0 to 1 (required)
        args['eto_uri'] - a uri to an input raster describing the 
            annual average evapotranspiration value for each cell. Potential
            evapotranspiration is the potential loss of water from soil by
            both evaporation from the soil and transpiration by healthy Alfalfa
            (or grass) if sufficient water is available (mm) (required)
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        args['sub_watersheds_uri'] - a uri to an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['biophysical_table_uri'] - a uri to an input CSV table of 
            land use/land cover classes, containing data on biophysical 
            coefficients such as root_depth (mm) and etk, which are required. 
            NOTE: these data are attributes of each LULC class rather than 
            attributes of individual cells in the raster map (required)
        args['seasonality_constant'] - floating point value between 1 and 10 
            corresponding to the seasonal distribution of precipitation 
            (required)
        args['results_suffix'] - a string that will be concatenated onto the
           end of file names (optional)
           
        returns - nothing"""
    
    LOGGER.info('Starting Water Yield File Handling')
    
    water_yield_args = {}
    workspace_dir = args['workspace_dir']
    water_yield_args['workspace_dir'] = workspace_dir
    
#   #Create the output directories
#   for folder_name in ['Output', 'Service', 'Intermediate']:
#       folder_path = workspace_dir + os.sep + folder_name
#       if not os.path.isdir(folder_path):
#           os.makedirs(folder_path)
#           
#   pixel_dir = workspace_dir + os.sep + 'Output/Pixel'
#   
#   if not os.path.isdir(pixel_dir):
#       os.makedirs(pixel_dir)
    
    #Open all of the gdal files and add to the arguments
    water_yield_args['precipitation_uri'] = args['precipitation_uri']
    water_yield_args['soil_depth_uri'] = args['soil_depth_uri']
    water_yield_args['lulc_uri'] = args['lulc_uri']
    water_yield_args['pawc_uri'] = args['pawc_uri']
    water_yield_args['eto_uri'] = args['eto_uri']
    
    #Open all the shapefiles and add to the arguments
    water_yield_args['watersheds_uri'] = args['watersheds_uri']
    water_yield_args['sub_watersheds_uri'] = args['sub_watersheds_uri']
    
#   #Open/read in the csv files into a dictionary and add to arguments
#   biophysical_table_map = {}
#   biophysical_table_file = open(args['biophysical_table_uri'])
#   reader = csv.DictReader(biophysical_table_file)
#   for row in reader:
#       biophysical_table_map[int(row['lucode'])] = \
#           {'etk':float(row['etk']), 'root_depth':float(row['root_depth'])}
    
    water_yield_args['biophysical_table_uri'] = args['biophysical_table_uri'] 

    #Add seasonality_constant and suffix to the arguments
    water_yield_args['seasonality_constant'] = args['seasonality_constant']
    water_yield_args['suffix'] = args['results_suffix']
    
    #Call water_yield in hydropower_core.py
    hydropower_core.water_yield(water_yield_args)
    LOGGER.info('Water Yield Completed')
