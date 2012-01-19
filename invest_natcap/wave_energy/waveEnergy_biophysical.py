"""InVEST Wave Energy Model file handler module"""

import sys
import os
import csv
import logging

import simplejson as json
from osgeo import gdal
from osgeo import ogr
import numpy as np

from invest_natcap.wave_energy import waveEnergy_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
logger = logging.getLogger('carbon_biophysical')

def execute(args):
    """This function invokes the biophysical part of the wave energy model 
        given URI inputs. It will do filehandling and open/create appropriate 
        objects to pass to the core wave energy biophysical processing function. 
        It may write log, warning, or error messages to stdout.
        
        args - A python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and ouput folder/files will 
                                be saved.
        args['wave_base_data_uri'] - Directory location of wave base data 
                                     including WW3 data and analyis area shapefile.
        args['analysis_area_uri'] - A string identifying the analysis area of interest.
        args['machine_perf_uri'] - The path of a CSV file that holds the machine 
                                   performace table. 
        args['machine_param_uri'] - The path of a CSV file that holds the machine 
                                    parameter table.
        args['dem_uri'] - The path of the Global Digital Elevation Model (DEM).
        args['aoi_uri'] - A polygon shapefile outlining a more detailed area 
                          within the analyis area. (OPTIONAL)
        returns nothing.        
        """

    #Create the Output and Intermediate directories if they do not exist.
    output_dir = args['workspace_dir'] + os.sep + 'Output' + os.sep
    intermediate_dir = args['workspace_dir'] + os.sep + 'Intermediate' + os.sep
    for dir in [output_dir, intermediate_dir]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    #Dictionary that will hold all the inputs to be passed to waveEnergy_core
    biophysical_args = {}
    biophysical_args['workspace_dir'] = args['workspace_dir']
    biophysical_args['dem'] = gdal.Open(args['dem_uri'])
    #Create a 2D array of the machine performance table and place the row
    #and column headers as the first two arrays in the list of arrays
    try:
        machine_perf_twoDArray = [[], []]
        machine_perf_file = open(args['machine_perf_uri'])
        reader = csv.reader(machine_perf_file)
        get_row = True
        for row in reader:
            if get_row:
                machine_perf_twoDArray[0] = row[1:]
                get_row = False
            else:
                machine_perf_twoDArray[1].append(row.pop(0))
                machine_perf_twoDArray.append(row)
        machine_perf_file.close()
        logger.debug('Machine Performance Rows : %s', machine_perf_twoDArray[0])
        logger.debug('Machine Performance Cols : %s', machine_perf_twoDArray[1])
        biophysical_args['machine_perf'] = machine_perf_twoDArray
    except IOError, e:
        print 'File I/O error' + e
    #Create a dictionary whose keys are the 'NAMES' from the machine parameter table
    #and whose corresponding values are dictionaries whose keys are the column headers of
    #the machine parameter table with corresponding values
    try:
        machine_params = {}
        machine_param_file = open(args['machine_param_uri'])
        reader = csv.DictReader(machine_param_file)
        for row in reader:
            machine_params[row['NAME'].strip()] = row
        machine_param_file.close()
        biophysical_args['machine_param'] = machine_params
    except IOError, e:
        print 'File I/O error' + e
    #Depending on which analysis area is selected:
    #Extrapolate the corresponding WW3 Data and place in the biophysical_args dictionary.
    #Open the point geometry analysis area shapefile containing the corresponding wave farm sites.
    #Open the polygon geometry analysis area extract shapefile contaning the outline of the area of interest.
    if args['analysis_area_uri'] == 'West Coast of North America and Hawaii':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'WCNA_extract.shp'
        biophysical_args['wave_base_data'] = extrapolate_wave_data(args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.txt')
        biophysical_args['analysis_area'] = ogr.Open(analysis_area_path, 1)
        biophysical_args['analysis_area_extract'] = ogr.Open(analysis_area_extract_path, 1)
    elif args['analysis_area_uri'] == 'East Coast of North America and Puerto Rico':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'ECNA_extract.shp'
        biophysical_args['wave_base_data'] = extrapolate_wave_data(args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.txt')
        biophysical_args['analysis_area'] = ogr.Open(analysis_area_path, 1)
        biophysical_args['analysis_area_extract'] = ogr.Open(analysis_area_extract_path)
    elif args['analysis_area_uri'] == 'Global(Eastern Hemisphere)':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'Global_EastHemi_30m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'Global_extract.shp'
        biophysical_args['wave_base_data'] = extrapolate_wave_data(args['wave_base_data_uri'] + os.sep + 'Global_EastHemi_30m.txt')
        biophysical_args['analysis_area'] = ogr.Open(analysis_area_path, 1)
        biophysical_args['analysis_area_extract'] = ogr.Open(analysis_area_extract_path)
    elif args['analysis_area_uri'] == 'Global(Western Hemisphere)':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'Global_WestHemi_30m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'Global_extract.shp'
        biophysical_args['wave_base_data'] = extrapolate_wave_data(args['wave_base_data_uri'] + os.sep + 'Global_WestHemi_30m.txt')
        biophysical_args['analysis_area'] = ogr.Open(analysis_area_path, 1)
        biophysical_args['analysis_area_extract'] = ogr.Open(analysis_area_extract_path)
    else:
        logger.debug('Analysis Area : %s', args['analysis_area_uri'])
        print 'Analysis Area ERROR. The Analysis Area Specified is not handled by this model.'
    #If the area of interest is present add it to the dictionary arguments
    if 'aoi_uri' in args:
        try:
            logger.debug('AOI File : %s', args['aoi'])
            aoi = ogr.Open(args['aoi_uri'], 1)
            biophysical_args['aoi'] = aoi
        except IOError, e:
            print 'File I/O error' + e
    #Fire up the biophysical function in waveEnergy_core with the gathered arguments
    logger.info('Starting Wave Energy Biophysical.')
    waveEnergy_core.biophysical(biophysical_args)
    logger.info('Completed Wave Energy Biophysical.')

def extrapolate_wave_data(wave_file):
    """The extrapolate_wave_data function converts WW3 text data into a dictionary who's
    keys are the corresponding (I,J) values and whose value is a two-dimensional array
    representing a matrix of the number of hours a seastate occurs over a 5 year period.
    The row and column headers are extracted once and stored in the dictionary as well.
    
    wave_file - The path to a text document that holds the WW3 data.
    
    returns - A dictionary of matrices representing hours of specific seastates.  
    """
    try:
        wave_open = open(wave_file)
        wave_dict = {}
        wave_array = []
        wave_row = []
        wave_col = []
        key = ''
        row_indicator = True
        col_indicator = True
        row_col_grab = 0
        for line in wave_open:
            #If it is the start of a new location, get (I,J) values
            if line[0] == 'I':
                key = (int(line.split(',')[1]), int(line.split(',')[3]))
                wave_array = []
                row_col_grab = 1
            #If the lines are corresponding to row and column header, save them
            #as lists.
            elif row_col_grab == 1 or row_col_grab == 2:
                row_col_grab = row_col_grab + 1
                if row_indicator:
                    wave_row = line.split(',')
                    row_indicator = False
                elif col_indicator:
                    wave_col = line.split(',')
                    col_indicator = False
            #If the lines correspond to the seastate bin, save them
            else:
                wave_array.append(line.split(','))
                wave_dict[key] = wave_array

        wave_open.close()
        #Add row/col header to dictionary
        logger.debug('WaveData row %s', wave_row)
        wave_dict[0] = np.array(wave_row, dtype='f')
        logger.debug('WaveData col %s', wave_col)
        wave_dict[1] = np.array(wave_col, dtype='f')
        return wave_dict

    except IOError, e:
        print 'File I/O error'
        print e
