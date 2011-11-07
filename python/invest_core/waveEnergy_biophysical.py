"""InVEST Wave Energy Model file handler module"""

import sys, os
import simplejson as json
import waveEnergy_biophysical_core
import invest_core
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf

from xlrd import open_workbook

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
    gdal.AllRegister()
    
    perfPathList = args['machine_perf_uri'].rsplit(os.sep, 1)
    perfPathWkbook = perfPathList[0]
    perfWkshtList = perfPathList[1].split('$')
    perfWksht = perfWkshtList[0]
    
    paramPathList = args['machine_param_uri'].rsplit(os.sep, 1)
    paramPathWkbook = paramPathList[0]
    paramWkshtList = paramPathList[1].split('$')
    paramWksht = paramWkshtList[0]
    
    machine_perfSheet = open_workbook(perfPathWkbook).sheet_by_name(perfWksht)
    machine_paramSheet= open_workbook(paramPathWkbook).sheet_by_name(paramWksht)
        
    wave_base_data = 1
    analysis_area = 1
    AOI = 1
    dem = 1
    
    arguments = {'wave_base_data': wave_base_data,
             'analysis_area': analysis_area,
             'AOI': AOI,
             'machine_perf': machine_perfSheet,
             'machine_param': machine_paramSheet,
             'dem': dem,
#             'valuation': gp.GetParameterAsText(7),
#             'landgridpts_uri': gp.GetParameterAsText(8),
#             'machine_econ_uri': gp.GetParameterAsText(9),
#             'number_machines': gp.GetParameterAsText(10),
#             'projection_uri': gp.GetParameterAsText(11)
            }
    
    waveEnergy_biophysical_core.biophysical(arguments)