"""InVEST Water Scarcity module at the "uri" level"""

import sys
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
        URI inputs of files. It will do filehandling and open/create
        appropriate objects to pass to the core sediment biophysical 
        processing function.  It may write log, warning, or error messages to 
        stdout.
        
        args - a python dictionary with at the following possible entries:
    
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['water_yield_vol_uri'] - a uri to an input raster, generated from
            the water_yield model, describing the total water yield per
            sub-watershed. The approximate absolute annual water yield across
            the landscape (cubic meters) (required) 
        args['water_yield_mean_uri'] - a uri to an input raster, generated from
            the water_yield model, describing the mean water yield per
            sub-watershed (mm) (required)
        args['lulc_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexs in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape.  (required)
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        args['watershed_yield_table_uri'] - a uri to an input CSV table, 
            generated from the water_yield model, containing values for mean 
            precipitation, potential and actual evapotranspiration and water
            yield per watershed
        args['subwatershed_yield_table_uri'] - a uri to an input CSV table, 
            generated from the water_yield model, containing values for mean 
            precipitation, potential and actual evapotranspiration and water
            yield per sub watershed
        args['sub_watersheds_uri'] - a uri to an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['demand_table_uri'] - a uri to an input dbf table of LULC classes,
            showing consumptive water use for each landuse / land-cover type
            (required)
        args['hydro_calibration_table_uri'] - a  uri to an input dbf table of 
            hydropower stations with associated calibration values (required)
        
        returns nothing"""
    
    workspace_dir = args['workspace']
    #Create the output directories
    for folder_name in ['Output', 'Service', 'Intermediate']:
        folder_path = workspace_dir + os.sep + folder_name
        if not os.path.isdir(folder_path):
            os.path.mkdir(folder_path)
            
    #Open all of the gdal files and place in dictionary
    args['lulc'] = gdal.Open(args['lulc_uri'])
    args['water_yield_vol'] = gdal.Open(args['water_yield_vol_uri'])
    args['water_yield_mn'] = gdal.Open(args['water_yield_mean_uri'])
    
    #Open all the shapefiles and place in dictionary
    args['watersheds'] = ogr.Open(args['watersheds_uri'])
    args['sub_watersheds'] = ogr.Open(args['sub_watersheds_uri'])
    
    #Open/read in the dbf files into a dictionary and add to
    #dictionary
    watershed_yield_table_map = {}
    watershed_yield_table_file = open(args['watershed_yield_table_uri'])
    reader = csv.DictReader(watershed_yield_table_file)
    for row in reader:
        watershed_yield_table_map[row['ws_id']] = {'precip_mn':row['precip_mn'], \
                                              'PET_mn':row['PET_mn'], \
                                              'AET_mn':row['AET_mn'],
                                              'wyield_mn':row['wyield_mn'],
                                              'wyield_sum':row['wyield_sum']}
        
    args['watershed_yield_table'] = watershed_yield_table_map
    watershed_yield_table_file.close()
    
    subwatershed_yield_table_map = {}
    subwatershed_yield_table_file = open(args['subwatershed_yield_table_uri'])
    reader = csv.DictReader(subwatershed_yield_table_file)
    for row in reader:
        subwatershed_yield_table_map[row['subws_id']] = {'ws_id':row['ws_id'],
                                              'precip_mn':row['precip_mn'], \
                                              'PET_mn':row['PET_mn'], \
                                              'AET_mn':row['AET_mn'],
                                              'wyield_mn':row['wyield_mn'],
                                              'wyield_sum':row['wyield_sum']}
        
    args['subwatershed_yield_table'] = subwatershed_yield_table_map
    subwatershed_yield_table_file.close()
    
    demand_table_map = {}
    demand_table_file = open(args['demand_table_uri'])
    reader = csv.DictReader(demand_table_file)
    for row in reader:
        demand_table_map[row['lucode']] = {'demand':row['demand'], \
                                              'LULC_desc':row['LULC_desc']}
        
    args['demand_table'] = demand_table_map
    demand_table_file.close()
    
    
    hydro_cal_table_map = {}
    hydro_cal_table_file = open(args['hydro_calibration_table_uri'])
    reader = csv.DictReader(hydro_cal_table_file)
    for row in reader:
        hydro_cal_table_map[row['id']] = {'ws_id':row['ws_id'], \
                                              'calib':row['calib']}
        
    args['hydro_cal_table'] = hydro_cal_table_map
    hydro_cal_table_file.close()
    
    #Call water_scarcity_core.py
    hydropower_core.water_scarcity(args)