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
    args['wave_base_data'] -
    arcs['analysis_area'] -
    arcs['AOI'] -
    arcs['machine_perf'] -
    arcs['machine_param'] -
    arcs['dem'] -
        
    """
    performance_dict = getMachinePerf(args['machine_perf'])
    
def getMachinePerf(machine_perf):
    performance_dict = {}
    return performance_dict