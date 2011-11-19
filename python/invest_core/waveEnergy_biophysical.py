"""InVEST Wave Energy Model file handler module"""

import sys, os
import simplejson as json
import waveEnergy_core
import invest_core
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy as np
from dbfpy import dbf

import csv

def execute(args):
    """This function invokes the wave energy model given URI inputs of files.
        It will do filehandling and open/create appropriate objects to 
        pass to the core wave energy biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at the following possible entries:
        args['workspace_dir'] - 
        args['wave_base_data_uri'] - 
        args['analysis_area_uri'] - 
        args['AOI_uri'] - 
        args['machine_perf_uri'] - 
        args['machine_param_uri'] - 
        args['dem_uri'] - 
        args['calculate_valuation'] - 
        args['landgridpts_uri'] - 
        args['machine_econ_uri'] - 
        args['number_machines'] - 
        args['projection'] - 
        
        returns nothing."""

    #This ensures we are not in Arc's python directory so that when
    #we import gdal stuff we don't get the wrong GDAL version.
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    filesystemencoding = sys.getfilesystemencoding()
    
    #Create the Output and Intermediate directories if they do not exist.
    outputDir = args['workspace_dir'] + os.sep + 'Output' + os.sep
    intermediateDir = args['workspace_dir'] + os.sep + 'Intermediate' + os.sep
    for dir in [outputDir, intermediateDir]:
        if not os.path.exists(dir):
            os.makedirs(dir)
        
    biophysicalargs = {}
    
    dict = {}
    arrayHeader = []
    arrayColumns = []
    machine_perf_twoDArray = []
    
    #Create a dictionary of arrays which represent the rows
    #Keep separate arrays for the row header and column header
    try:
        f = open(args['machine_perf_uri'])
        reader = csv.reader(f)
        i = -1
        for row in reader:
            if i==-1:
                arrayHeader = row
                arrayHeader.pop(0)
                i = 0
            else:
                arrayColumns.append(row.pop(0))                
                dict[i] = row
                i = i + 1
        f.close()
    except IOError, e:
        print 'File I/O error' + e
        
    #Create 2D array by compiling rows of arrays from dict
    #Add on the row/col fields in same order as WW 3 text file
    machine_perf_twoDArray.append(arrayHeader)
    machine_perf_twoDArray.append(arrayColumns)
    for array in dict.itervalues():
        for index, val in enumerate(array):
            array[index] = float(val)
        machine_perf_twoDArray.append(array)
    
    for index, val in enumerate(arrayHeader):
        arrayHeader[index] = float(val)
    for index, val in enumerate(arrayColumns):
        arrayColumns[index] = float(val)
    
    biophysicalargs['machine_perf'] = machine_perf_twoDArray
    #Create a dictionary of dictionaries where the inner dictionaries keys are the column fields.
    machine_params = {}
    count = 0
    try:
        machineParamFile = open(args['machine_param_uri'])
        reader = csv.DictReader(machineParamFile)
        for row in reader:
            machine_params[count] = row
            count = count + 1
        machineParamFile.close()
        biophysicalargs['machine_param'] = machine_params
    except IOError, e:
        print 'File I/O error' + e
    #WaveDate information depends on analysis area
    if args['analysis_area_uri'] == 'West Coast of North America and Hawaii':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.shp'
        waveFile = open(args['wave_base_data_uri']+os.sep+'NAmerica_WestCoast_4m.txt')
        biophysicalargs['wave_base_data'] = extrapolateWaveData(analysis_area_path, waveFile)
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        
    elif args['analysis_area_uri'] == 'East Coast of North America and Puerto Rico':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.shp'
        waveFile = open(args['wave_base_data_uri']+os.sep+'NAmerica_EastCoast_4m.txt')
        biophysicalargs['wave_base_data'] = extrapolateWaveData(analysis_area_path, waveFile)
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        
    elif args['analysis_area_uri'] == 'Global(Eastern Hemisphere)':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'Global_EastHemi_30m.shp'
        waveFile = open(args['wave_base_data_uri']+os.sep+'Global_EastHemi_30m.txt')
        biophysicalargs['wave_base_data'] = extrapolateWaveData(analysis_area_path, waveFile)
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        
    elif args['analysis_area_uri'] == 'Global(Western Hemisphere)':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'Global_WestHemi_30m.shp'
        waveFile = open(args['wave_base_data_uri']+os.sep+'Global_WestHemi_30m.txt')      
        biophysicalargs['wave_base_data'] = extrapolateWaveData(analysis_area_path, waveFile)
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        
    else:
        print 'Analysis Area ERROR'
    
    gdal.AllRegister()
    
    AOI = None
    if 'AOI_uri' in args:
        try:
            AOI = ogr.Open(args['AOI_uri'].encode(filesystemencoding))
            biophysicalargs['AOI'] = AOI
            
        except IOError, e:
            print 'File I/O error' + e

    if 'calculate_valuation' in args:
        for file, id in (('machine_econ', 'NAME'), ('landgridpts', 'ID')):
            try:
                f = open(args[file+'_uri'])
                dict = {}
                reader = csv.DictReader(f)
                for row in reader:
                    dict[row[id]] = row
                biophysicalargs[file] = dict
                f.close()
            except IOError, e:
                print 'File I/O error' + e
    
    biophysicalargs['dem'] = gdal.Open(args['dem_uri'])
        
    waveEnergy_core.biophysical(biophysicalargs)

def extrapolateWaveData(analysis_path, waveOpen):
    analysis_area_path = analysis_path
    waveFile = waveOpen
    waveDict = {}
    waveArray = []
    waveRow = []
    waveCol = []
    key = ''
    lineCount = 0
    check = 0
    rowcolGrab = False
    for line in waveFile:
        if line[0] == 'I':
            iVal = int(line.split(',')[1])
            jVal = int(line.split(',')[3])
            key = (iVal, jVal)
            waveArray = []
            rowcolGrab = True
        elif rowcolGrab:
            if lineCount == 0:
                if check != -1:
                    waveRow.append(line.split(','))
                    waveRow = waveRow[0]
                lineCount = lineCount + 1
            elif lineCount == 1:
                if check != -1:
                    waveCol.append(line.split(','))
                    waveCol = waveCol[0]
                    check = -1
                lineCount = 0
                rowcolGrab = False
        else:
            waveArray.append(line.split(','))
            waveDict[key] = waveArray
    for i, val in enumerate(waveRow):
        waveRow[i] = float(val)
    for i, val in enumerate(waveCol):
        waveCol[i] = float(val)
        
    waveDict[0] = waveRow
    waveDict[1] = waveCol
    return waveDict
    