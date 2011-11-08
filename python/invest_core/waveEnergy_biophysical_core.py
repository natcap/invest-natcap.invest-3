import numpy as np
from osgeo import gdal
import osgeo.gdal
import osgeo.osr as osr
from osgeo import ogr
from dbfpy import dbf
import math
import invest_core

def biophysical(args):
    """
    args['wave_base_data'] - a dictionary
    arcs['analysis_area'] - 
    arcs['AOI'] - a shapefile
    arcs['machine_perf'] - a dictionary
    arcs['machine_param'] - a dictionary
    arcs['dem'] - a GIS raster file
        
    """
    performance_dict = getMachinePerf(args['machine_perf'])
    
    
    
    
def getMachinePerf(machine_perf):
    performance_dict = {}
    return performance_dict

def wavePower():
    P = ((p*g)/16)*(H**2)*waveGroupVelocity()
    return P

def waveGroupVelocity():
    return (1+((2*k*h)/math.sinh(2*k*h)) * (math.sqrt((g/k)*math.tanh(k*h))))/2

def waveNumber():
    return (w**2)/(g*math.tanh((w**2)*(h/g)))

def npv():
    for num in range(1, T+1):
        sum = sum + (B[num]-C[num])*((1+i)**(-1 * t))
        
    return npv