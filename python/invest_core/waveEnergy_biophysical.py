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
    
    #Dictionary that will hold all the inputs to be passed to waveEnergy_core
    biophysicalargs = {}
    biophysicalargs['workspace_dir'] = args['workspace_dir']
    biophysicalargs['wave_data_dir'] = args['wave_base_data_uri']
#    biophysicalargs['workspace_dir'] = args['workspace_dir']
    
    machine_perf_twoDArray = [[],[]]
    
    #Create a 2D array of the machine performance table and place the x fields
    #and y fields as first two arrays in the list of arrays
    try:
        f = open(args['machine_perf_uri'])
        reader = csv.reader(f)
        getRow = True
        for row in reader:
            if getRow:
                machine_perf_twoDArray[0] = row[1:]
                getRow = False
            else:
                machine_perf_twoDArray[1].append(row.pop(0))
                machine_perf_twoDArray.append(row)
        f.close()
    except IOError, e:
        print 'File I/O error' + e
    
    biophysicalargs['machine_perf'] = machine_perf_twoDArray
    
    #Create a dictionary of dictionaries where the inner dictionaries keys are the column fields.
    #This is for the machine parameter values.
    machine_params = {}
    try:
        machineParamFile = open(args['machine_param_uri'])
        reader = csv.DictReader(machineParamFile)
        for row in reader:
            machine_params[row['NAME'].strip()] = row
        machineParamFile.close()
        biophysicalargs['machine_param'] = machine_params
    except IOError, e:
        print 'File I/O error' + e
        
    #WaveDate information depends on analysis area
    if args['analysis_area_uri'] == 'West Coast of North America and Hawaii':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'NAmerica_WestCoast_4m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'WCNA_extract.shp'
        biophysicalargs['wave_base_data'] = extrapolateWaveData(args['wave_base_data_uri']+os.sep+'NAmerica_WestCoast_4m.txt')
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        biophysicalargs['analysis_area_extract'] = ogr.Open(analysis_area_extract_path.encode(filesystemencoding), 1)
    elif args['analysis_area_uri'] == 'East Coast of North America and Puerto Rico':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'NAmerica_EastCoast_4m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'ECNA_extract.shp'
        biophysicalargs['wave_base_data'] = extrapolateWaveData(args['wave_base_data_uri']+os.sep+'NAmerica_EastCoast_4m.txt')
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        biophysicalargs['analysis_area_extract'] = ogr.Open(analysis_area_extract_path.encode(filesystemencoding))
    elif args['analysis_area_uri'] == 'Global(Eastern Hemisphere)':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'Global_EastHemi_30m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'Global_extract.shp'
        biophysicalargs['wave_base_data'] = extrapolateWaveData(args['wave_base_data_uri']+os.sep+'Global_EastHemi_30m.txt')
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        biophysicalargs['analysis_area_extract'] = ogr.Open(analysis_area_extract_path.encode(filesystemencoding))
    elif args['analysis_area_uri'] == 'Global(Western Hemisphere)':
        analysis_area_path = args['wave_base_data_uri'] + os.sep + 'Global_WestHemi_30m.shp'
        analysis_area_extract_path = args['wave_base_data_uri'] + os.sep + 'Global_extract.shp' 
        biophysicalargs['wave_base_data'] = extrapolateWaveData(args['wave_base_data_uri']+os.sep+'Global_WestHemi_30m.txt')
        biophysicalargs['analysis_area'] = ogr.Open(analysis_area_path.encode(filesystemencoding), 1)
        biophysicalargs['analysis_area_extract'] = ogr.Open(analysis_area_extract_path.encode(filesystemencoding))
    else:
        print 'Analysis Area ERROR'
    
    gdal.AllRegister()
    
    #If the area of interest is present add it to the output arguments
    AOI = None
    if 'AOI_uri' in args:
        try:
            AOI = ogr.Open(args['AOI_uri'].encode(filesystemencoding), 1)
            biophysicalargs['AOI'] = AOI
            
        except IOError, e:
            print 'File I/O error' + e
    #If the valuation is true, then create dictionaries for the following files
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

def extrapolateWaveData(waveFile):
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
                iVal = int(line.split(',')[1])
                jVal = int(line.split(',')[3])
                key = (iVal, jVal)
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