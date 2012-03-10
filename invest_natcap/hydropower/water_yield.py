"""InVEST Water Yield module at the "uri" level"""

import sys
import os
import logging

from osgeo import gdal
from osgeo import ogr

#from invest_natcap.hydropower import hydropower_core

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('water_yield')

def execute(args):
    """This function invokes the water yield model given
        URI inputs of files. It will do filehandling and open/create
        appropriate objects to pass to the core sediment biophysical 
        processing function.  It may write log, warning, or error messages to 
        stdout.
        
        args - a python dictionary with at the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['lulc_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexs in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape.  (required)
        args['soil_depth_uri'] - a uri to an input raster describing the 
            average soil depth value for each cell (mm) (required)
        args['precipitaion_uri'] - a uri to an input raster describing the 
            average annual precipitation value for each cell (mm) (required)
        args['pawc_uri'] - a uri to an input raster describing the 
            plant available water content value for each cell. Plant Available
            Water Content fraction (PAWC) is the fraction of water that can be
            stored in the soil profile that is available for plants' use. 
            PAWC is a fraction from 0 to 1 (required)
        args['ape_uri'] - a uri to an input raster describing the 
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
            coefficients such as root_depth and etk. NOTE: these data are 
            attributes of each LULC class rather than attributes of individual 
            cells in the raster map (required)
        args['zhang'] - floating point value between 1 and 10 corresponding
            to the seasonal distribution of precipitation
            
        returns - nothing"""
    
    workspace_dir = args['workspace_dir']
    
    #Create the output directories
    for folder_name in ['Output', 'Service', 'Intermediate']:
        folder_path = workspace_dir + os.sep + folder_name
        if not os.path.isdir(folder_path):
            os.path.mkdir(folder_path)
            
    #Open all of the gdal files and place in dictionary
    args['precipitation'] = gdal.Open(args['precipitation_uri'])
    args['soil_depth'] = gdal.Open(args['soil_depth_uri'])
    args['lulc'] = gdal.Open(args['lulc_uri'])
    args['pawc'] = gdal.Open(args['pawc_uri'])
    args['ape'] = gdal.Open(args['ape_uri'])
    
    
    #Open all the shapefiles and place in dictionary
    args['watersheds'] = ogr.Open(args['watersheds_uri'])
    args['sub_watersheds'] = ogr.Open(args['sub_watersheds_uri'])
    
    #Open/read in the dbf files into a dictionary and add to
    #dictionary
    biophysical_table_map = {}
    biophysical_table_file = open(args['biophysical_table_uri'])
    reader = csv.DictReader(biophsyical_table_file)
    for row in biophysical_table:
        biophysical_table_map[row['lucode']] = {'etk':row['etk'], \
                                              'root_depth':row['root_depth'], \
                                              'LULC_desc':row['LULC_desc']}
    args['biophysical_dictionary'] = biophysical_table_map
        
    LOGGER.debug('bio_table_map : %s', biophysical_table_map)
    #Call water_yield_core.py