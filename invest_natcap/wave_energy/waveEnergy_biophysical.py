"""InVEST Wave Energy Model file handler module"""

import sys
import os
import csv

import simplejson as json
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy as np

from invest_natcap.invest_core import invest_core
from invest_natcap.wave_energy import waveEnergy_core

def execute(args):
    """This function invokes the biophysical part of the wave energy model given URI inputs.
        It will do filehandling and open/create appropriate objects to 
        pass to the core wave energy biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at least the following possible entries:
        args['workspace_dir'] - Where the intermediate and ouput folder/files will be saved.
        args['wave_base_data_uri'] - Directory location of wave base data including WW3 data and analyis area
                                     shapefile.
        args['analysis_area_uri'] - A string identifying the analysis area of interest
        args['AOI_uri'] - A polygon shapefile outlining a more detailed area within the analyis area.
        args['machine_perf_uri'] - The path of a CSV file that holds the machine performace table. 
        args['machine_param_uri'] - The path of a CSV file that holds the machien parameter table.
        args['dem_uri'] - The path of the Global Digital Elevation Model (DEM)
        args['calculate_valuation'] - A boolean value indicating whether to compute the economic evaluation.
        args['landgridpts_uri'] - The path to a CSV file containing the Landing and Power Grid Connection Points table.
        args['machine_econ_uri'] - The path to a CSV file containing the machine economic table.
        args['number_machines'] - An integer representing the number of machines.
        args['projection'] - The path to a projection used for economic evaluation.
        
        returns nothing."""

    filesystemencoding = sys.getfilesystemencoding()

    #Create the Output and Intermediate directories if they do not exist.
    outputDir = args['workspace_dir'] + os.sep + 'Output' + os.sep
    intermediateDir = args['workspace_dir'] + os.sep + 'Intermediate' + os.sep
    for dir in [outputDir, intermediateDir]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    #Dictionary that will hold all the inputs to be passed to waveEnergy_core
    biophysicalargs = {}
    biophysicalargs['workspace_dir'] = args['workspace_dir']
    biophysicalargs['wave_data_dir'] = args['wave_base_data_uri']
    biophysicalargs['dem'] = gdal.Open(args['dem_uri'])
    #Create a 2D array of the machine performance table and place the row
    #and column headers as the first two arrays in the list of arrays
    try:
        machine_perf_twoDArray = [[], []]
        machinePerfFile = open(args['machine_perf_uri'])
        reader = csv.reader(machinePerfFile)
        getRow = True
        for row in reader:
            if getRow:
                machine_perf_twoDArray[0] = row[1:]
                getRow = False
            else:
                machine_perf_twoDArray[1].append(row.pop(0))
                machine_perf_twoDArray.append(row)
        machinePerfFile.close()
        biophysicalargs['machine_perf'] = machine_perf_twoDArray
    except IOError, e:
        print 'File I/O error' + e

    #Create a dictionary whose keys are the 'NAMES' from the machine parameter table
    #and whose corresponding values are dictionaries whose keys are the column headers of
    #the machine parameter table with corresponding values
    try:
        machine_params = {}
        machineParamFile = open(args['machine_param_uri'])
        reader = csv.DictReader(machineParamFile)
        for row in reader:
            machine_params[row['NAME'].strip()] = row
        machineParamFile.close()
        biophysicalargs['machine_param'] = machine_params
    except IOError, e:
        print 'File I/O error' + e

    #Depending on which analyis area is selected:
    #Extrapolate the corresponding WW3 Data and place in the arguments dictionary
    #Open the point geometry analysis area shapefile contaning the corresponding seastate bins
    #Open the polygon geometry analysis area extract shapefile contaning the outline of the area of interest
    if args['analysis_area_uri'] == 'West Coast of North America and Hawaii':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'WCNA_extract.shp'
        biophysicalargs['wave_base_data'] = extrapolateWaveData(args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.txt')
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        biophysicalargs['analysis_area_extract'] = ogr.Open(analysis_area_extract_path.encode(filesystemencoding), 1)
    elif args['analysis_area_uri'] == 'East Coast of North America and Puerto Rico':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'ECNA_extract.shp'
        biophysicalargs['wave_base_data'] = extrapolateWaveData(args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.txt')
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        biophysicalargs['analysis_area_extract'] = ogr.Open(analysis_area_extract_path.encode(filesystemencoding))
    elif args['analysis_area_uri'] == 'Global(Eastern Hemisphere)':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'Global_EastHemi_30m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'Global_extract.shp'
        biophysicalargs['wave_base_data'] = extrapolateWaveData(args['wave_base_data_uri'] + os.sep + 'Global_EastHemi_30m.txt')
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        biophysicalargs['analysis_area_extract'] = ogr.Open(analysis_area_extract_path.encode(filesystemencoding))
    elif args['analysis_area_uri'] == 'Global(Western Hemisphere)':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'Global_WestHemi_30m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'Global_extract.shp'
        biophysicalargs['wave_base_data'] = extrapolateWaveData(args['wave_base_data_uri'] + os.sep + 'Global_WestHemi_30m.txt')
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        biophysicalargs['analysis_area_extract'] = ogr.Open(analysis_area_extract_path.encode(filesystemencoding))
    else:
        print 'Analysis Area ERROR'

    #If the area of interest is present add it to the dictionary arguments
    AOI = None
    if 'AOI_uri' in args:
        try:
            AOI = ogr.Open(args['AOI_uri'].encode(filesystemencoding), 1)
            biophysicalargs['AOI'] = AOI
        except IOError, e:
            print 'File I/O error' + e

    waveEnergy_core.biophysical(biophysicalargs)

def extrapolateWaveData(waveFile):
    """The extrapolateWaveData function converts WW3 text data into a dictionary who's
    keys are the corresponding (I,J) values and whose value is a two-dimensional array
    representing a matrix of the number of hours a seastate occurs over a 5 year period.
    The row and column headers are extracted once and stored in the dictionary as well.
    
    waveFile - The path to a text document that holds the WW3 data.
    
    returns - A dictionary of matrices representing hours of specific seastates.  
    """
    try:
        waveOpen = open(waveFile)
        waveDict = {}
        waveArray = []
        waveRow = []
        waveCol = []
        key = ''
        rowIndicator = True
        colIndicator = True
        rowcolGrab = 0
        for line in waveOpen:
            if line[0] == 'I':
                key = (int(line.split(',')[1]), int(line.split(',')[3]))
                waveArray = []
                rowcolGrab = 1
            elif rowcolGrab == 1 or rowcolGrab == 2:
                rowcolGrab = rowcolGrab + 1
                if rowIndicator:
                    waveRow = line.split(',')
                    rowIndicator = False
                elif colIndicator:
                    waveCol = line.split(',')
                    colIndicator = False
            else:
                waveArray.append(line.split(','))
                waveDict[key] = waveArray

        waveOpen.close()
        waveDict[0] = np.array(waveRow, dtype='f')
        waveDict[1] = np.array(waveCol, dtype='f')
        return waveDict

    except IOError, e:
        print 'File I/O error'
        print e
