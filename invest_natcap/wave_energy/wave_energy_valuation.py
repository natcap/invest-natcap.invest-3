"""InVEST Wave Energy Model file handler module"""

import os
import csv
import logging 

from osgeo import ogr
from osgeo import gdal

import invest_cython_core
from invest_natcap.invest_core import invest_core
from invest_natcap.wave_energy import wave_energy_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
logger = logging.getLogger('wave_energy_valuation')

def execute(args):
    """This function invokes the valuation part of the wave energy model given URI inputs.
        It will do filehandling and open/create appropriate objects to 
        pass to the core wave energy valuation processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - A python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and ouput folder/files will be saved.
        args['land_gridPts_uri'] - A CSV file path containing the Landing and Power 
                                   Grid Connection Points table.
        args['machine_econ_uri'] - A CSV file path for the machine economic parameters table.
        args['number_of_machines'] - An integer specifying the number of machines for a 
                                     wave farm site.
        args['global_dem'] - The file path to the global dem.
        args['wave_data_shape_path'] - The path to the point shapefile output created during 
                                       biophysical run.
        
        returns - Nothing
        """
    #Dictionary of the arguments to be passed to valuation
    valuation_args = {}
    valuation_args['workspace_dir'] = args['workspace_dir']
    valuation_args['global_dem'] = gdal.Open(args['global_dem'])
    valuation_args['wave_data_shape'] = ogr.Open(args['wave_data_shape_path'], 1)
    valuation_args['number_machines'] = int(args['number_of_machines'])
    #Open/create the output directory
    output_dir = args['workspace_dir'] + os.sep + 'Output' + os.sep
    intermediate_dir = args['workspace_dir'] + os.sep + 'Intermediate' + os.sep
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    #Read machine economic parameters into a dictionary
    try:
        machine_econ = {}
        machine_econ_file = open(args['machine_econ_uri'])
        reader = csv.DictReader(machine_econ_file)
        logger.debug('reader fieldnames : %s ', reader.fieldnames)
        #Read in the field names from the column headers
        name_key = reader.fieldnames[0]
        value_key = reader.fieldnames[1]
        for row in reader:
            #Convert name to lowercase
            name = row[name_key].strip().lower()
            logger.debug('Name : %s and Value : % s', name, row[value_key])
            machine_econ[name] = row[value_key]
        machine_econ_file.close()
        valuation_args['machine_econ'] = machine_econ
    except IOError, error:
        print 'File I/O error' + error
    #Read landing and power grid connection points into a dictionary
    try:
        land_grid_pts = {}
        land_grid_pts_file = open(args['land_gridPts_uri'])
        reader = csv.DictReader(land_grid_pts_file)
        for row in reader:
            logger.debug('Land Grid Row: %s', row)
            if row['ID'] in land_grid_pts:
                land_grid_pts[row['ID'].strip()][row['TYPE']] = [row['LAT'],
                                                                 row['LONG']]
            else:
                land_grid_pts[row['ID'].strip()] = {row['TYPE']:[row['LAT'],
                                                                 row['LONG']]}
        logger.debug('New Land_Grid Dict : %s', land_grid_pts)
        land_grid_pts_file.close()
        valuation_args['land_gridPts'] = land_grid_pts
    except IOError, error:
        print 'File I/O error' + error
    #Call the valuation core module with attached arguments to run the economic valuation
    logger.info('Beginning Wave Energy Valuation.')
    wave_energy_core.valuation(valuation_args)
    logger.info('Wave Energy Valuation Completed.')
