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
    #Shapefile of polygon that has the dimensions for providing the area of interest
    cutter_uri = '../../test_data/wave_Energy/samp_data/input/WaveData/WCNA_extract.shp'
    cutter = ogr.Open(cutter_uri.encode(filesystemencoding))
    cutterLayer = cutter.GetLayer(0)
    
    global_dem = args['dem']
    format = 'GTiff'
    nodata = -1
    datatype = gdal.GDT_Float32
    layer = args['analysis_area'].GetLayer(0)
    
    #Create a new raster that has the values of the WWW shapefile
    #Get the resolution from the global dem
    geoform = global_dem.GetGeoTransform()
    pixelSizeX = abs(geoform[1])
    pixelSizeY = abs(geoform[5])

    #Rasters which will be past (along with global_dem) to vectorize with wave power op.
    waveHeightPath = '../../test_data/wave_Energy/waveHeight.tif'
    wavePeriodPath = '../../test_data/wave_Energy/wavePeriod.tif'
    #Create rasters bounded by shape file of analyis area
    for path in (waveHeightPath, wavePeriodPath):
        invest_core.createRasterFromVectorExtents(pixelSizeX, pixelSizeY, 
                                              datatype, nodata, path, cutter)
    #Open created rasters
    waveHeightRaster = gdal.Open(waveHeightPath, GA_Update)
    wavePeriodRaster = gdal.Open(wavePeriodPath, GA_Update)
    #Rasterize the height and period values into respected rasters from shapefile
    for prop, raster in (('HSAVG_M', waveHeightRaster), ('TPAVG_S', wavePeriodRaster)):
        raster.GetRasterBand(1).SetNoDataValue(nodata)
        gdal.RasterizeLayer(raster, [1], layer, options=['ATTRIBUTE=' + prop])
    
    
    #Make a duplicate copy of the global_dem to try and crop
#    drv = gdal.GetDriverByName(format)
#    newGlobal = drv.CreateCopy('../../test_data/wave_Energy/newGlobal.tif', newRaster, 1)
#    newGlobal.GetRasterBand(1).SetNoDataValue(0)
#    newGlobal.GetRasterBand(1).Fill(0)
#    #Burn Height values from shapefile onto new raster
#    newRaster = None

    interpolateWaveData(args['machine_perf'], args['wave_base_data'])
    clipShape()
    
def clipShape(shapeToClip, bindingShape):
    shape_source = '../../test_data/wave_Energy/samp_data/Intermediate'
    #Copy the input shapefile into the designated output folder
    copiedShape = ogr.GetDriverByName('ESRI Shapefile').\
        CopyDataSource(shapeToClip, shape_source)
    clip_feat = bindingShape.GetLayer(0).GetNextFeature()
    clip_geom = clip_feat.GetGeometryRef().Clone()
    
    copied_feat = copiedShape.GetLayer(0).GetNextFeature()
    while copied_feat is not None:
        geom = copied_feat.GetGeometryRef().Clone()
        geom = copied_feat.GetGeometryRef().Clone().Intersection(clip_geom)
        
        if(geom.GetGeometryCount() + geom.GetPointCount()) != 0:
            out_feat = ogr.Feature(feature_def = copiedShape.GetLayer(0).GetLayerDefn())
            out_feat.SetFrom(copied_feat)
            out_feat.SetGeometryDirectly(geom)
            
            out_feat.Destroy()
        copied_feat.Destroy()
        copied_feat = copiedShape.GetLayer(0).GetNextFeature()
    
    clip_feat.Destroy()
    bindingShape.Destroy()
    copiedShape.Destroy()
    
def interpolateWaveData(machinePerf, waveBaseData):
    #Trim down the waveBaseData based on the machinePerf rows/columns
    #and then interpolate if need be.
    #Once interpolated and trimmed vectorize over two matrices returning
    #and saving the output to a dictionary with key being I,J value
    
    #A 2D array that will be vectorized with machinePerf
    interpWaveData = []
#    machineCol = machinePerf[0]
#    machineRow = machinePerf[1]
##    print machineCol
##    print machineRow
#    for key, pointData in waveBaseData.iteritems():
#        waveCol = pointData[0]
#        waveRow = pointData[1]
#        newCol = []
#        newRow = []
#        lowBound = -1
#        highBound = -1
#        for index, num in enumerate(waveCol):
#            if float(num) < machineCol
#       
#        
    
    return interpWaveData
    
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
