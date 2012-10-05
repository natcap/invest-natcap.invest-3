"""InVEST Wave Energy Model file handler module"""

import os
import csv
import logging
import struct

from osgeo import gdal
from osgeo import ogr
import numpy as np

from invest_natcap.wave_energy import wave_energy_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('wave_energy_biophysical')

def execute(args):
    """This function invokes the biophysical part of the wave energy model 
        given URI inputs. It will do filehandling and open/create appropriate 
        objects to pass to the core wave energy biophysical processing function. 
        It may write log, warning, or error messages to stdout.
        
        args - A python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and output folder/files  
                                will be saved.
        args['wave_base_data_uri'] - Directory location of wave base data 
                                     including WW3 data and analysis area 
                                     shapefile.
        args['analysis_area_uri'] - A string identifying the analysis area of 
                                    interest. Used to determine wave data 
                                    shapefile, wave data text file, and 
                                    analysis area boundary shape.
        args['machine_perf_uri'] - The path of a CSV file that holds the 
                                   machine performance table. 
        args['machine_param_uri'] - The path of a CSV file that holds the 
                                    machine parameter table.
        args['dem_uri'] - The path of the Global Digital Elevation Model (DEM).
        args['aoi_uri'] - A polygon shapefile outlining a more detailed area 
                          within the analysis area. (OPTIONAL, but required to
                          run Valuation model)
        returns nothing.        
        """

    #Create the Output and Intermediate directories if they do not exist.
    output_dir = args['workspace_dir'] + os.sep + 'Output' + os.sep
    intermediate_dir = args['workspace_dir'] + os.sep + 'Intermediate' + os.sep
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    #Dictionary that will hold all the input arguments to be 
    #passed to wave_energy_core.biophysical
    biophysical_args = {}
    biophysical_args['workspace_dir'] = args['workspace_dir']
    biophysical_args['dem'] = gdal.Open(args['dem_uri'])
    
    #Create a dictionary that stores the wave periods and wave heights as
    #arrays. Also store the amount of energy the machine produces 
    #in a certain wave period/height state as a 2D array
    machine_perf_dict = {}
    machine_perf_file = open(args['machine_perf_uri'])
    reader = csv.reader(machine_perf_file)
    #Get the column header which is the first row in the file
    #and specifies the range of wave periods
    periods = reader.next()
    machine_perf_dict['periods'] = periods[1:]
    #Set the keys for storing wave height range and the machine performance
    #at each state
    machine_perf_dict['heights'] = []
    machine_perf_dict['bin_matrix'] = []
    for row in reader:
        #Build up the row header by taking the first element in each row
        #This is the range of heights
        machine_perf_dict['heights'].append(row.pop(0))
        machine_perf_dict['bin_matrix'].append(row)
    machine_perf_file.close()
    LOGGER.debug('Machine Performance Rows : %s', machine_perf_dict['periods'])
    LOGGER.debug('Machine Performance Cols : %s', machine_perf_dict['heights'])
    biophysical_args['machine_perf'] = machine_perf_dict
    
    #Create a dictionary whose keys are the 'NAMES' from the machine parameter
    #table and whose values are from the corresponding 'VALUES' field.
    machine_params = {}
    machine_param_file = open(args['machine_param_uri'])
    reader = csv.DictReader(machine_param_file)
    for row in reader:
        machine_params[row['NAME'].strip().lower()] = row['VALUE']
    machine_param_file.close()
    biophysical_args['machine_param'] = machine_params
   
    #Build up a dictionary of possible analysis areas where the key
    #is the analysis area selected and the value is a dictionary
    #that stores the related uri paths to the needed inputs 
    analysis_dict = \
        {'West Coast of North America and Hawaii': \
            {'point_shape': args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.shp',
             'extract_shape': args['wave_base_data_uri'] + os.sep + 'WCNA_extract.shp',
             'ww3_uri': args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.txt.bin'
            },
         'East Coast of North America and Puerto Rico': \
            {'point_shape': args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.shp',
             'extract_shape': args['wave_base_data_uri'] + os.sep + 'ECNA_extract.shp',
             'ww3_uri': args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.txt.bin'
            },
         'Global': \
            {'point_shape': args['wave_base_data_uri'] + os.sep + 'Global.shp',
             'extract_shape': args['wave_base_data_uri'] + os.sep + 'Global_extract.shp',
             'ww3_uri': args['wave_base_data_uri'] + os.sep + 'Global_WW3.txt.bin'
            }
       }
    #Add the ww3 dictionary, point shapefile, and polygon extract shapefile
    #to the biophysical_args based on the analysis area selected
    biophysical_args['wave_base_data'] = \
        load_binary_wave_data(analysis_dict[args['analysis_area_uri']]['ww3_uri'])
    
    biophysical_args['analysis_area'] = \
        ogr.Open(analysis_dict[args['analysis_area_uri']]['point_shape'])
    
    biophysical_args['analysis_area_extract'] = \
        ogr.Open(analysis_dict[args['analysis_area_uri']]['extract_shape'])
        
    #If the area of interest is present add it to the dictionary arguments
    if 'aoi_uri' in args and len(args['aoi_uri']) > 0:
        LOGGER.debug('AOI File : %s', args['aoi_uri'])
        LOGGER.debug(args['aoi_uri'].__class__)
        aoi = ogr.Open(args['aoi_uri'])
        biophysical_args['aoi'] = aoi
        
    #Fire up the biophysical function in wave_energy_core with the 
    #gathered arguments
    LOGGER.info('Starting Wave Energy Biophysical.')
    wave_energy_core.biophysical(biophysical_args)
    LOGGER.info('Completed Wave Energy Biophysical.')

def load_binary_wave_data(wave_file_uri):
    """The load_binary_wave_data function converts a pickled WW3 text file into a 
    dictionary who's keys are the corresponding (I,J) values and whose value 
    is a two-dimensional array representing a matrix of the number of hours 
    a seastate occurs over a 5 year period. The row and column headers are 
    extracted once and stored in the dictionary as well.
    
    wave_file_uri - The path to a pickled binary WW3 file.
    
    returns - A dictionary of matrices representing hours of specific seastates,
              as well as the period and height ranges.  It has the following
              structure:
               {'periods': [1,2,3,4,...],
                'heights': [.5,1.0,1.5,...],
                'bin_matrix': { (i0,j0): [[2,5,3,2,...], [6,3,4,1,...],...],
                                (i1,j1): [[2,5,3,2,...], [6,3,4,1,...],...],
                                 ...
                                (in, jn): [[2,5,3,2,...], [6,3,4,1,...],...]
                              }
               }  
    """
    LOGGER.debug('Extrapolating wave data from text to a dictionary')
    wave_file = open(wave_file_uri,'rb')
    wave_dict = {}
    #Create a key that hosts another dictionary where the matrix representation
    #of the seastate bins will be saved
    wave_dict['bin_matrix'] = {}
    wave_array = None
    wave_periods = []
    wave_heights = []
    key = None

    #get rows,cols
    row_col_bin = wave_file.read(8)
    col,row = struct.unpack('ii',row_col_bin)

    #get the periods and heights
    line = wave_file.read(col*4)

    wave_periods = list(struct.unpack('f'*col,line))
    line = wave_file.read(row*4)
    wave_heights = list(struct.unpack('f'*row,line))

    key = None
    while True:
        line = wave_file.read(8)
        if len(line) == 0:
            #end of file
            wave_dict['bin_matrix'][key] = np.array(wave_array)
            break

        if key != None:
            wave_dict['bin_matrix'][key] = np.array(wave_array)

        #Clear out array
        wave_array = []

        key = struct.unpack('ii',line)

        for row_id in range(row):
            line = wave_file.read(col*4)
            array = list(struct.unpack('f'*col,line))
            wave_array.append(array)

    wave_file.close()
    #Add row/col header to dictionary
    LOGGER.debug('WaveData col %s', wave_periods)
    wave_dict['periods'] = np.array(wave_periods, dtype='f')
    LOGGER.debug('WaveData row %s', wave_heights)
    wave_dict['heights'] = np.array(wave_heights, dtype='f')
    LOGGER.debug('Finished extrapolating wave data to dictionary')
    return wave_dict
