"""InVEST Wave Energy Model file handler module"""

import sys, os
import simplejson as json
import waveEnergy_biophysical_core
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

    dict = {}
    arrayHeader = []
    arrayColumns = []
    machine_perf_twoDArray = []
    
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
                
    for array in dict.itervalues():
        machine_perf_twoDArray.append(array)
        
    machine_params = {}
    count = 0
    with open(args['machine_param_uri'], 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            machine_params[count] = row
            count = count + 1

    
    gdal.AllRegister()
    
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
        
    wave_base_data = 1
    analysis_area = ogr.Open(args['analysis_area_uri'].encode(filesystemencoding), 1)
    AOI = 1
    dem = gdal.Open(args['dem_uri'])
        
    arguments = {'wave_base_data': wave_base_data,
                 'analysis_area': analysis_area,
                 'AOI': AOI,
                 'machine_perf': machine_perf_twoDArray,
                 'machine_param': machine_params,
                 'dem': dem,
    #             'valuation': gp.GetParameterAsText(7),
    #             'landgridpts_uri': gp.GetParameterAsText(8),
    #             'machine_econ_uri': gp.GetParameterAsText(9),
    #             'number_machines': gp.GetParameterAsText(10),
    #             'projection_uri': gp.GetParameterAsText(11)
                }
        
    waveEnergy_biophysical_core.biophysical(arguments)