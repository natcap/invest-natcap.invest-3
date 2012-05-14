"""InVEST Wave Energy Model file handler module"""

import os
import csv
import logging

from osgeo import gdal
from osgeo import ogr
import numpy as np

from invest_natcap.ck_wave_energy import wave_energy_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('wave_energy_biophysical')

def execute(args):
    """This function invokes the biophysical part of the wave energy model 
        given URI inputs. It will do filehandling and open/create appropriate 
        objects to pass to the core wave energy biophysical processing function. 
        It may write log, warning, or error messages to stdout.
        
        args - A python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and ouput folder/files  
                                will be saved.
        args['wave_base_data_uri'] - Directory location of wave base data 
                                     including WW3 data and analyis area 
                                     shapefile.
        args['analysis_area_uri'] - A string identifying the analysis area of 
                                    interest. Used to determine wave data 
                                    shapefile, wave data text file, and 
                                    analysis area boundary shape.
        args['machine_perf_uri'] - The path of a CSV file that holds the 
                                   machine performace table. 
        args['machine_param_uri'] - The path of a CSV file that holds the 
                                    machine parameter table.
        args['dem_uri'] - The path of the Global Digital Elevation Model (DEM).
        args['aoi_uri'] - A polygon shapefile outlining a more detailed area 
                          within the analyis area. (OPTIONAL, but required to
                          run Valuation model)
        args['bin_attributes'] - Path to a text file that has information
                                 to wave bin site, including: I,J,LONG,LATI,HSAVG,TPAVG
                                 values
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
    
    #Depending on which analysis area is selected:
    #Extrapolate the corresponding WW3 Data and place in the 
    #biophysical_args dictionary.
    #Open the point geometry analysis area shapefile containing the 
    #corresponding wave farm sites.
    #Open the polygon geometry analysis area extract shapefile contaning the 
    #outline of the area of interest.
    if args['analysis_area_uri'] == 'West Coast of North America and Hawaii':
        analysis_area_path = \
            args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.shp'
        analysis_area_extract_path = \
            args['wave_base_data_uri'] + os.sep + 'WCNA_extract.shp'
        biophysical_args['wave_base_data'] = \
            extrapolate_wave_data(args['wave_base_data_uri']
                                  + os.sep + 'NAmerica_WestCoast_4m.txt')
        biophysical_args['analysis_area'] = ogr.Open(analysis_area_path)
        biophysical_args['analysis_area_extract'] = \
            ogr.Open(analysis_area_extract_path)
    elif args['analysis_area_uri'] == \
             'East Coast of North America and Puerto Rico':
        analysis_area_path = \
            args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.shp'
        analysis_area_extract_path = \
            args['wave_base_data_uri'] + os.sep + 'ECNA_extract.shp'
        biophysical_args['wave_base_data'] = \
            extrapolate_wave_data(args['wave_base_data_uri']
                                  + os.sep + 'NAmerica_EastCoast_4m.txt')
        biophysical_args['analysis_area'] = ogr.Open(analysis_area_path)
        biophysical_args['analysis_area_extract'] = \
            ogr.Open(analysis_area_extract_path)
    elif args['analysis_area_uri'] == 'Global(Eastern Hemisphere)':
        analysis_area_path = \
            args['wave_base_data_uri'] + os.sep + 'union/merged/merged.shp'
        analysis_area_extract_path = \
            args['wave_base_data_uri'] + os.sep + 'Global_extract.shp'
        biophysical_args['wave_base_data'] = \
            extrapolate_wave_data(args['wave_base_data_uri']
                                  + os.sep + 'ck_clean2.txt')
#        biophysical_args['analysis_area'] = ogr.Open(analysis_area_path)
        
        
        #new_dict = extrapolate_bin_info(args['bin_attributes'])
#        path = args['workspace_dir'] + os.sep + 'new_global_shape.shp'
        #create_new_shape(path, biophysical_args['analysis_area'], new_dict)
        biophysical_args['analysis_area'] = ogr.Open(args['global_shape'])
        
        biophysical_args['analysis_area_extract'] = \
            ogr.Open(analysis_area_extract_path)
    elif args['analysis_area_uri'] == 'Global(Western Hemisphere)':
        analysis_area_path = \
            args['wave_base_data_uri'] + os.sep + 'Global_WestHemi_30m.shp'
        analysis_area_extract_path = \
            args['wave_base_data_uri'] + os.sep + 'Global_extract.shp'
        biophysical_args['wave_base_data'] = \
            extrapolate_wave_data(args['wave_base_data_uri']
                                  + os.sep + 'Global_WestHemi_30m.txt')
        biophysical_args['analysis_area'] = ogr.Open(analysis_area_path)
        biophysical_args['analysis_area_extract'] = \
            ogr.Open(analysis_area_extract_path)
    else:
        LOGGER.debug('Analysis Area : %s', args['analysis_area_uri'])
        LOGGER.error('Analysis Area ERROR.')
        
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


def extrapolate_bin_info(path):
    LOGGER.debug('extrapolating_bin_info')
    #Open/read in the csv files into a dictionary and add to arguments
    table_map = {}
    table_file = open(path)
    reader = csv.DictReader(table_file)
    for row in reader:
#        LOGGER.debug('row : %s', row)
        table_map[(int(row['I']),int(row['J']))] = \
            {'long':float(row['LONG']), 
             'lati':float(row['LATI']),
             'hsavg':float(row['HSAVG']),
             'tpavg':float(row['TPAVG']),
             }
            
    table_file.close()

    return table_map


def create_new_shape(path, shape, table):
    LOGGER.debug('CREATING NEW SHAPE FILE')
    fields_list = ['HSAVG_M','I','J','LATI','LONG','TPAVG_S']
    
    dr = ogr.GetDriverByName('ESRI Shapefile')
    ds = dr.CreateDataSource(path)
    ds.CreateLayer('new_global_shape', shape.GetLayer().GetSpatialRef(), 
                   ogr.wkbPoint)
    layer = ds.GetLayer()
    for field in fields_list:
        fld_def = ogr.FieldDefn(field, ogr.OFTReal)
        layer.CreateField(fld_def)
        
    for key, val in table.iteritems():
        i_val = key[0]
        j_val = key[1]
        long = val['long']
        lati = val['lati']
        height = val['hsavg']
        period = val['tpavg']
        
        out_feat = ogr.Feature(feature_def=layer.GetLayerDefn())
        out_feat.SetField('I', i_val)
        out_feat.SetField('J', j_val)
        out_feat.SetField('LATI', lati)
        out_feat.SetField('LONG', long)
        out_feat.SetField('HSAVG_M', height)
        out_feat.SetField('TPAVG_S', period)
                
        pt = ogr.Geometry(ogr.wkbPoint)
        pt.SetPoint_2D(0, long, lati)
        out_feat.SetGeometry(pt)
        
        layer.CreateFeature(out_feat)
        out_feat.Destroy()
    
    ds = None
    LOGGER.debug('DONE CREATING NEW SHAPE FILE')
        

def extrapolate_wave_data(wave_file_uri):
    """The extrapolate_wave_data function converts WW3 text data into a 
    dictionary who's keys are the corresponding (I,J) values and whose value 
    is a two-dimensional array representing a matrix of the number of hours 
    a seastate occurs over a 5 year period. The row and column headers are 
    extracted once and stored in the dictionary as well.
    
    wave_file_uri - The path to a text document that holds the WW3 data.
    
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
    wave_file = open(wave_file_uri)
    wave_dict = {}
    #Create a key that hosts another dictionary where the matrix representation
    #of the seastate bins will be saved
    wave_dict['bin_matrix'] = {}
    wave_array = None
    wave_periods = []
    wave_heights = []
    key = None

    #get the periods and heights 
    #wave_file.readline() #skipping first I,J line
    wave_periods = wave_file.readline().split(',')
    wave_heights = wave_file.readline().split(',')
    LOGGER.debug('wave_periods: %s', wave_periods)
    #wave_file.seek(0) #reset to the first line in the file

    while True:
        line = wave_file.readline()
        if len(line) == 0:
            #end of file
            wave_dict['bin_matrix'][key] = wave_array
            break

        #If it is the start of a new location, get (I,J) values
        if line[0] == 'I':
            #If key is not None that means there is a full array waiting
            #to be written to the dictionary, so write it
            if key != None:
                wave_dict['bin_matrix'][key] = wave_array

            #Clear out array
            wave_array = []

            key = (int(line.split(',')[1]), int(line.split(',')[3]))

            #Skip the next two lines that are period and height
#            wave_file.readline()
#            wave_file.readline()
        else:
            wave_array.append(line.split(','))

    wave_file.close()
    #Add row/col header to dictionary
    LOGGER.debug('WaveData row %s', wave_periods)
    wave_dict['periods'] = np.array(wave_periods, dtype='f')
    LOGGER.debug('WaveData col %s', wave_heights)
    wave_dict['heights'] = np.array(wave_heights, dtype='f')
    LOGGER.debug('Finished extrapolating wave data to dictionary')
    return wave_dict
