import numpy as np
from osgeo import gdal
import osgeo.gdal
from osgeo.gdalconst import *
import osgeo.osr as osr
from osgeo import ogr
from dbfpy import dbf
import math
import invest_core
import sys, os

def biophysical(args):
    """
    args['wave_base_data'] - a dictionary
    args['analysis_area'] - 
    args['AOI'] - a shapefile
    args['machine_perf'] - a dictionary
    args['machine_param'] - a dictionary
    args['dem'] - a GIS raster file
        
    """
    captureWaveEnergy(args['wave_base_data'], args['machine_perf'], args['machine_param'])
    
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

    outputPath = '../../test_data/wave_Energy/samp_data/Intermediate/WaveData_clipZ.shp'
    clipShape(args['analysis_area'], args['AOI'], outputPath)
    
def clipShape(shapeToClip, bindingShape, outputPath):
    shape_source = outputPath
    
    if os.path.isfile(shape_source):
        os.remove(shape_source)
    #Get the layer of points from the current point geometry shape
    in_layer = shapeToClip.GetLayer(0)
    #Get the layer definition which holds needed attribute values
    in_defn = in_layer.GetLayerDefn()
    #Get the layer of the polygon (binding) geometry shape
    clip_layer = bindingShape.GetLayer(0)
    #Create a new shapefile with similar properties of the current point geometry shape
    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = shp_driver.CreateDataSource(shape_source)
    shp_layer = shp_ds.CreateLayer(in_defn.GetName(), in_layer.GetSpatialRef(), in_defn.GetGeomType())
    #Get the number of fields in the current point shapefile
    in_field_count = in_defn.GetFieldCount()
    #For every field, create a duplicate field and add it to the new shapefiles layer
    for fld_index in range(in_field_count):
        src_fd = in_defn.GetFieldDefn(fld_index)
        
        fd = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd.SetWidth(src_fd.GetWidth())
        fd.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd)
    #Retrieve the binding polygon feature and get it's geometry reference
    clip_feat = clip_layer.GetNextFeature()
    clip_geom = clip_feat.GetGeometryRef()
    #Get the spatial reference of the geometry to use in transforming
    sourceSR = clip_geom.GetSpatialReference()
    #Retrieve the current point shapes feature and get it's geometry reference
    in_feat = in_layer.GetNextFeature()
    geom = in_feat.GetGeometryRef()
    #Get the spatial reference of the geometry to use in transforming
    targetSR = geom.GetSpatialReference()
    #Create a coordinate transformation
    coordTrans = osr.CoordinateTransformation(sourceSR, targetSR)
    #Transform the polygon geometry into the same format as the point shape geometry
    clip_geom.Transform(coordTrans)
    #For all the features in the current point shape (for all the points)
    #Check to see if they Intersect with the binding polygons geometry and
    #if they do, then add all of the fields and values from that point to the new shape
    while in_feat is not None:
        geom = in_feat.GetGeometryRef()
        #Intersection returns a new geometry if they intersect
        geom = geom.Intersection(clip_geom)
        if(geom.GetGeometryCount() + geom.GetPointCount()) != 0:
            out_feat = ogr.Feature(feature_def = shp_layer.GetLayerDefn())
            out_feat.SetFrom(in_feat)
            out_feat.SetGeometryDirectly(geom)
            
            for fld_index2 in range(out_feat.GetFieldCount()):
                src_field = in_feat.GetField(fld_index2)
                out_feat.SetField(fld_index2, src_field)
                
            shp_layer.CreateFeature(out_feat)
            out_feat.Destroy()
            
        in_feat.Destroy()
        in_feat = in_layer.GetNextFeature()
    
    #Close shapefiles
    clip_feat.Destroy()
    bindingShape.Destroy()
    shapeToClip.Destroy()
    shp_ds.Destroy()
    
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

def captureWaveEnergy(waveData, machinePerf, machineParam):
    x = np.array(machinePerf.pop(0))
    y = np.array(machinePerf.pop(0))
    z = np.array(machinePerf)
    newx = np.array(waveData[0])
    newy = np.array(waveData[1])
    interpZ = invest_core.interpolateMatrix(x, y, z, newx, newy)
    computeWaveEnergyCapacity(waveData, interpZ)

def computeWaveEnergyCapacity(waveData, interpZ):
    energyCap = {}
    waveRow = waveData.pop(0)
    waveColumn = waveData.pop(1)
    periodMax = 17 #Get value from machine_param
    periodMaxPos = -1
    heightMax = 5.5 #Get value from machine_param
    heightMaxPos = -1
    for i, v in enumerate(waveRow):
        if v > periodMax and periodMaxPos == -1:
            periodMaxPos = i
            print periodMaxPos
    for i, v in enumerate(waveColumn):
        if v > heightMax and heightMaxPos == -1:
            heightMaxPos = i
    
    
    for key, val in waveData.iteritems():
        for index, array in enumerate(val):
            for i, num in enumerate(array):
                array[i] = float(num)
        tempArray = np.array(val)
        multArray = np.multiply(tempArray, interpZ)
        
        if periodMaxPos != -1:
            multArray[:,periodMaxPos:] = 0
        if heightMaxPos != -1:
            multArray[heightMaxPos:, :] = 0
        validArray = np.divide(multArray, 5.0)
#        validArray = np.where(multArray>750, 750, multArray)
        #Since we are doing a cubic interpolation there is a possibility we
        #will have negative values where they should be zero.  So here
        #we drive any negative values to zero.
        validArray = np.where(validArray<0, 0, validArray)
#            def deviceConstraints(a, capmax, hmax, tmax):
                
        sum = np.sum(validArray)
        energyCap[key] = sum
        if key == (556, 496):
#            print interpZ
#            print multArray
            print validArray
            print sum
    print energyCap[(556,496)]
    return energyCap 


