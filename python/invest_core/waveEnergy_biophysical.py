"""InVEST Wave Energy Model file handler module"""

import sys, os
import simplejson as json
import waveEnergy_core
import invest_core
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy as np
from dbfpy import dbf

from xlrd import open_workbook
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
    biophysicalargs = {}
    
    dict = {}
    arrayHeader = []
    arrayColumns = []
    machine_perf_twoDArray = []
    
    #Create a dictionary of arrays which represent the rows
    #Keep separate arrays for the row header and column header
    with open(args['machine_perf_uri'], 'rb') as f:
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
    #Create 2D array by compiling rows of arrays from dict    
    for array in dict.itervalues():
        machine_perf_twoDArray.append(array)
        
    biophysicalargs['machine_perf'] = machine_perf_twoDArray
    #Create a dictionary of dictionaries where the inner dictionaries keys are the column fields.
    machine_params = {}
    count = 0
    with open(args['machine_param_uri'], 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            machine_params[count] = row
            count = count + 1
        biophysicalargs['machine_param'] = machine_params
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
        AOI = ogr.Open(args['AOI_uri'].encode(filesystemencoding))
        biophysicalargs['AOI'] = AOI

    if (AOI != None) and (args['calculate_valuation']):
        with open(args['machine_econ_uri'], 'rb') as f:
            machine_econ = {}
            count = 0
            reader = csv.DictReader(f)
            for row in reader:
                machine_econ[count] = row
                count = count + 1
            biophysicalargs['machine_econ'] = machine_econ
    
        with open(args['landgridpts_uri'], 'rb') as f:
            landgridpts = {}
            count = 0
            reader = csv.DictReader(f)
            for row in reader:
                landgridpts[count] = row
                count = count + 1
            biophysicalargs['machine_econ'] = landgridpts
            
        
    
    
    biophysicalargs['dem'] = gdal.Open(args['dem_uri'])
        
    waveEnergy_core.biophysical(biophysicalargs)
    
def extrapolateWaveData(analysis_path, waveOpen):
    analysis_area_path = analysis_path
    waveFile = waveOpen
    waveDict = {}
    waveArray = []
    key = ''
    lineCount = 0
    for line in waveFile:
        lineCount = lineCount + 1
        if line[0] == 'I':
            key = line
            waveArray = []
        else:
            waveArray.append(line)
            waveDict[key] = waveArray
    print lineCount
    return waveDict
    
#    perfPathList = args['machine_perf_uri'].rsplit(os.sep, 1)
#    perfPathWkbook = perfPathList[0]
#    perfWkshtList = perfPathList[1].split('$')
#    perfWksht = perfWkshtList[0]
#    
#    paramPathList = args['machine_param_uri'].rsplit(os.sep, 1)
#    paramPathWkbook = paramPathList[0]
#    paramWkshtList = paramPathList[1].split('$')
#    paramWksht = paramWkshtList[0]
#    
#    machine_perfSheet = open_workbook(perfPathWkbook).sheet_by_name(perfWksht)
#    machine_paramSheet= open_workbook(paramPathWkbook).sheet_by_name(paramWksht)
        
#    arguments = {'wave_base_data': wave_base_data,
#                 'analysis_area': analysis_area,
#                 'AOI': AOI,
#                 'machine_perf': machine_perf_twoDArray,
#                 'machine_param': machine_params,
#                 'dem': dem,
    #             'valuation': gp.GetParameterAsText(7),
    #             'landgridpts_uri': gp.GetParameterAsText(8),
    #             'machine_econ_uri': gp.GetParameterAsText(9),
    #             'number_machines': gp.GetParameterAsText(10),
    #             'projection_uri': gp.GetParameterAsText(11)
#                }
        