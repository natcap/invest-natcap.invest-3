import numpy as np
from osgeo import gdal
import osgeo.gdal
from osgeo.gdalconst import *
import osgeo.osr as osr
from osgeo import ogr
from dbfpy import dbf
import math
import invest_core
import sys
def biophysical(args):
    """
    args['wave_base_data'] - a dictionary
    args['analysis_area'] - 
    args['AOI'] - a shapefile
    args['machine_perf'] - a dictionary
    args['machine_param'] - a dictionary
    args['dem'] - a GIS raster file
        
    """
    filesystemencoding = sys.getfilesystemencoding()
    cutter_uri = '../../test_data/wave_Energy/samp_data/input/WaveData/WCNA_extract.shp'
    cutter = ogr.Open(cutter_uri.encode(filesystemencoding))
    cutterLayer = cutter.GetLayer(0)
    
    global_dem = args['dem']
    format = 'GTiff'
    nodata = -1
    datatype = gdal.GDT_Float32
    layer = args['analysis_area'].GetLayer(0)
    
    #Create a new raster that has the values of the WWW shapefile
    source = cutterLayer.GetSpatialRef()
    projection = source.ExportToWkt()
    
    x_min, x_max, y_min, y_max = cutterLayer.GetExtent()
    geoform = global_dem.GetGeoTransform()
    pixelSizeX = geoform[1]
    pixelSizeY = geoform[5]
    
    x_res = int((x_max-x_min) / pixelSizeX)
    y_res = int((y_max-y_min) / pixelSizeY)
    y_res = math.fabs(y_res)
    cols = x_res
    rows = y_res

    outputpath = '../../test_data/wave_Energy/newRaster4.tif'
    driver = gdal.GetDriverByName(format)
    
    newRaster = driver.Create(outputpath, int(cols), int(rows), 1, gdal.GDT_Float32)
    
    newRaster.SetProjection(projection)
    newRaster.SetGeoTransform((x_min, pixelSizeX, 0, y_max, 0, pixelSizeY))
    newRaster.GetRasterBand(1).SetNoDataValue(nodata)
    newRaster.GetRasterBand(1).Fill(nodata)
    
    raster = gdal.RasterizeLayer(newRaster, [1], layer, options=['ATTRIBUTE=' + 'HSAVG_M'])

    #    performance_dict = getMachinePerf(args['machine_perf'])
    newRaster = None
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