import numpy as np
from osgeo import gdal
import osgeo.gdal
from osgeo.gdalconst import *
import osgeo.osr as osr
from osgeo import ogr
from dbfpy import dbf
import math
import invest_core
import invest_cython_core
import sys, os
import scipy


def biophysical(args):
    """
    args['wave_base_data'] - a dictionary
    args['analysis_area'] - 
    args['analysis_area_extract']
    args['AOI'] - a shapefile
    args['machine_perf'] - a dictionary
    args['machine_param'] - a dictionary
    args['dem'] - a GIS raster file
    args['workspace_dir'] - the workspace path
        
    """
    filesystemencoding = sys.getfilesystemencoding()
#    transformProjection(args['analysis_area_extract'], args['AOI'])

    #Set variables for common output paths
    workspaceDir = args['workspace_dir']
    interDir = workspaceDir + os.sep + 'Intermediate'
    outputDir = workspaceDir + os.sep + 'Output'
    waveDataDir = args['wave_data_dir']
    waveShapePath = interDir + os.sep + 'WaveData_clipZ.shp'
    #Path for 'new' AOI, see comment below 'if AOI in args'
    waveAOIPath = interDir + os.sep + 'waveAOIShape.shp'
    
    #Set global_dem and nodata values/datatype for new rasters
    global_dem = args['dem']
    nodata = -1
    datatype = gdal.GDT_Float32
    #Get the resolution from the global dem to be used for creating new blank rasters
    geoform = global_dem.GetGeoTransform()
    pixelSizeX = abs(geoform[1])
    pixelSizeY = abs(geoform[5])
    
    #Determine which shapefile will be used to determine area of interest
    if 'AOI' in args:
        #The AOI shapefile has a different projection than lat/long so by calling
        #the clipShape function with analysis_area_extract (which has lat/long projection
        #which we would expect) and AOI I am making a new AOI with the proper projection
        cutter = clipShape(args['analysis_area_extract'], args['AOI'], waveAOIPath)        
    else:
        cutter = args['analysis_area_extract']

    #Blank raster to be used in clipping output rasters to areas of interest
    blankRaster = aoiBlankRaster(cutter, interDir, pixelSizeX, pixelSizeY, datatype)
    
    #Create a new shapefile that is a copy of analysis_area but bounded by AOI
    area_shape = clipShape(args['analysis_area'], cutter, waveShapePath)
    area_layer = area_shape.GetLayer(0)
    #Generate an interpolate object for waveEnergyCap, create a dictionary with the sums from each location,
    #and add the sum as a field to the shapefile
    energyInterp = waveEnergyInterp(args['wave_base_data'], args['machine_perf'], args['machine_param'])
    energyCap = computeWaveEnergyCapacity(args['wave_base_data'], energyInterp)
    capturedWaveEnergyToShape(energyCap, area_shape)

    #Rasters which will be past (along with global_dem) to vectorize with wave power op.
    waveHeightPath = interDir + os.sep + 'waveHeight.tif'
    wavePeriodPath = interDir + os.sep + 'wavePeriod.tif'
    waveEnergyPath = interDir + os.sep + 'waveEnergyCap.tif'
    #Create rasters bounded by shape file of analyis area
    for path in (waveHeightPath, wavePeriodPath, waveEnergyPath):
        invest_cython_core.createRasterFromVectorExtents(pixelSizeX, pixelSizeY,
                                              datatype, nodata, path, cutter)

    #Open created rasters
    waveHeightRaster = gdal.Open(waveHeightPath, GA_Update)
    wavePeriodRaster = gdal.Open(wavePeriodPath, GA_Update)
    waveEnergyRaster = gdal.Open(waveEnergyPath, GA_Update)
    #Rasterize the height and period values into respected rasters from shapefile
    for prop, raster in (('HSAVG_M', waveHeightRaster), ('TPAVG_S', wavePeriodRaster),  ('capWE_Sum', waveEnergyRaster)):
        raster.GetRasterBand(1).SetNoDataValue(nodata)
        gdal.RasterizeLayer(raster, [1], area_layer, options=['ATTRIBUTE=' + prop])

    heightArray = pointShapeToDict(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'HSAVG_M'], 'HSAVG_M')
    periodArray = pointShapeToDict(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'TPAVG_S'], 'TPAVG_S')
    interpolateHeight(heightArray, waveHeightRaster)
    interpolatePeriod(periodArray, wavePeriodRaster)
    
    energySumArray = pointShapeToDict(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'capWE_Sum'], 'capWE_Sum')
    interpolateSum(energySumArray, waveEnergyRaster)

    wavePowerPath = interDir + os.sep + 'wp_kw.tif'
    wavePower(waveHeightRaster, wavePeriodRaster, global_dem, wavePowerPath, blankRaster)

    area_shape.Destroy()
    cutter.Destroy()
    waveHeightRaster = None
    wavePeriodRaster = None

def aoiBlankRaster(aoiShape, interDir, xRes, yRes, datatype):
    rasterPath = interDir + os.sep + 'aoiBlankRaster.tif'
    invest_cython_core.createRasterFromVectorExtents(xRes, yRes, datatype, 0, rasterPath, aoiShape)
    blankRaster = gdal.Open(rasterPath, GA_Update)
    blankRaster.GetRasterBand(1).SetNoDataValue(0)
    gdal.RasterizeLayer(blankRaster, [1], aoiShape.GetLayer(0))
    
    return blankRaster

def transformProjection(targetProj, sourceProj):
    source_Layer = sourceProj.GetLayer(0)
    target_Layer = targetProj.GetLayer(0)
    target_feat  = target_Layer.GetNextFeature()
    target_geom  = target_feat.GetGeometryRef()
    targetSR = target_geom.GetSpatialReference()
    source_feat  = source_Layer.GetNextFeature()
    source_geom  = source_feat.GetGeometryRef()
    sourceSR = source_geom.GetSpatialReference()
    
    coordTrans = osr.CoordinateTransformation(sourceSR, targetSR)
    source_geom.Transform(coordTrans)
    source_Layer.SetSpatialFilter(source_geom)
#
#    print source_geom
#    print source_Layer.GetExtent()

#clipShape takes the shapefile you would like to cut down,
#the polygon shape you want the other shapefile cut to,
#and the path for the new shapefile
#It returns a new shapefile in the same format/projection as shapeToClip
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
    while clip_feat is not None:
        clip_geom = clip_feat.GetGeometryRef()
        #Get the spatial reference of the geometry to use in transforming
        sourceSR = clip_geom.GetSpatialReference()
        #Retrieve the current point shapes feature and get it's geometry reference
        in_layer.ResetReading()
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
                out_feat = ogr.Feature(feature_def=shp_layer.GetLayerDefn())
                out_feat.SetFrom(in_feat)
                out_feat.SetGeometryDirectly(geom)

                for fld_index2 in range(out_feat.GetFieldCount()):
                    src_field = in_feat.GetField(fld_index2)
                    out_feat.SetField(fld_index2, src_field)

                shp_layer.CreateFeature(out_feat)
                out_feat.Destroy()

            in_feat.Destroy()
            in_feat = in_layer.GetNextFeature()
        clip_feat.Destroy()
        clip_feat = clip_layer.GetNextFeature()

    return shp_ds

def pointShapeToDict(shape, key, valueArray, value):

    shape_layer = shape.GetLayer(0)
    shape_layer.ResetReading()
    shape_feat = shape_layer.GetNextFeature()

#    aoiDictionary = {}
#    latlongDict = {}
#    xrangeLong = []
#    yrangeLat = []

    fieldDict = {}
    xrangeLong = []
    yrangeLat = []
    xRangeField = 'LONG'
    yRangeField = 'LATI'
    while shape_feat is not None:
#
#        itemArray = [0, 0, 0, 0, 0, 0]
#        
#        for field, var in (('I', 0), ('J', 1), ('LONG', 2), ('LATI', 3), ('HSAVG_M', 4), ('TPAVG_S', 5)):
#            field_index = shape_feat.GetFieldIndex(field)
#            itemArray[var] = shape_feat.GetField(field_index)
#            
#            fieldDict[field] = 
#        
#        fieldDict[key] = 

        valueDict = {}
        #May want to check to make sure field is in shape layer
        for field in valueArray:
            field_index = shape_feat.GetFieldIndex(field)
            valueDict[field] = shape_feat.GetField(field_index)
        keyList = []        
        for k in key:
            keyList.append(valueDict[k])
        tupledKey = tuple(keyList)
        fieldDict[tupledKey] = valueDict

        xrangeLong.append(fieldDict[tupledKey][xRangeField])
        yrangeLat.append(fieldDict[tupledKey][yRangeField])
        
        shape_feat.Destroy()
        shape_feat = shape_layer.GetNextFeature()
    
    xrangeLongNoDup = list(set(xrangeLong))
    yrangeLatNoDup = list(set(yrangeLat))
    
    xrangeLongNoDup.sort()
    yrangeLatNoDup.sort()
    
    xrangeLongNP = np.array(xrangeLongNoDup)
    yrangeLatNP = np.array(yrangeLatNoDup)
    
    matrix = []
    for j in yrangeLatNP:
        tmp = []
        for i in xrangeLongNP:
            if (i,j) in fieldDict:
                tmp.append(fieldDict[(i,j)][value])
            else:
                tmp.append(0)
        matrix.append(tmp)
        
    matrixNP = np.array(matrix)
    results = [xrangeLongNP, yrangeLatNP, matrixNP]
    return results
    

#        xrangeLong.append(itemArray[2])
#        yrangeLat.append(itemArray[3])
#        
#        aoiDictionary[(itemArray[0], itemArray[1])] = [itemArray[2], itemArray[3], itemArray[4], itemArray[5]]
#        latlongDict[(itemArray[2], itemArray[3])] = [itemArray[4], itemArray[5]]
#        
#        shape_feat.Destroy()
#        shape_feat = shape_layer.GetNextFeature()
#
#    xrangeLongNoDup = list(set(xrangeLong))
#    yrangeLatNoDup = list(set(yrangeLat))
#    
#    xrangeLongNoDup.sort()
#    yrangeLatNoDup.sort()
#    
#    xrangeLongNP = np.array(xrangeLongNoDup)
#    yrangeLatNP = np.array(yrangeLatNoDup)
#    matrixHeight = []
#    matrixPeriod = []
#    for j in yrangeLatNP:
#        tmpHeight = []
#        tmpPeriod = []
#        for i in xrangeLongNP:
#            if (i,j) in latlongDict:
#                tmpHeight.append(latlongDict[(i,j)][0])
#                tmpPeriod.append(latlongDict[(i,j)][1])
#            else:
#                tmpHeight.append(0)
#                tmpPeriod.append(0)
#        matrixHeight.append(tmpHeight)
#        matrixPeriod.append(tmpPeriod)
#        
#    matrixHeightNP = np.array(matrixHeight)
#    matrixPeriodNP = np.array(matrixPeriod)
#    
#    results = [xrangeLongNP, yrangeLatNP, matrixHeightNP, matrixPeriodNP]
#    return results

def interpolateHeight(results, raster):
    xrange = results[0]
    yrange = results[1]
    matrixHeight = results[2]
    
    gt = raster.GetGeoTransform()
    band = raster.GetRasterBand(1)
    matrix = band.ReadAsArray(0, 0, band.XSize, band.YSize)
    newxrange = (np.arange(band.XSize, dtype=float) * gt[1]) + gt[0]
    newyrange = (np.arange(band.YSize, dtype=float) * gt[5]) + gt[3]
    
    #This is probably true if north is up
    if gt[5] < 0:
        print 'North is up'
#        yrange = yrange[::-1]
#        matrixHeight = matrixHeight[::-1]

    spl = scipy.interpolate.RectBivariateSpline(yrange, xrange, matrixHeight, kx=1, ky=1)
    spl = spl(newyrange[::-1], newxrange)[::-1]

#    spl = scipy.interpolate.RectBivariateSpline(xrange, yrange, matrixHeight.transpose(), kx=3, ky=3)
#    spl = spl(newxrange, newyrange).transpose()

    band.WriteArray(spl, 0, 0)
    
def interpolatePeriod(results, raster):
    xrange = results[0]
    yrange = results[1]
    matrixHeight = results[2]
    
    gt = raster.GetGeoTransform()
    band = raster.GetRasterBand(1)
    matrix = band.ReadAsArray(0, 0, band.XSize, band.YSize)
    newxrange = (np.arange(band.XSize, dtype=float) * gt[1]) + gt[0]
    newyrange = (np.arange(band.YSize, dtype=float) * gt[5]) + gt[3]
    
    #This is probably true if north is up
    if gt[5] < 0:
        print 'North is up'
#        yrange = yrange[::-1]
#        matrixHeight = matrixHeight[::-1]

    spl = scipy.interpolate.RectBivariateSpline(yrange, xrange, matrixHeight, kx=1, ky=1)
    spl = spl(newyrange[::-1], newxrange)[::-1]

#    spl = scipy.interpolate.RectBivariateSpline(xrange, yrange, matrixHeight.transpose(), kx=3, ky=3)
#    spl = spl(newxrange, newyrange).transpose()

    band.WriteArray(spl, 0, 0)

def wavePower(waveHeight, wavePeriod, elevation, wavePowerPath, blankRaster):
    heightBand = waveHeight.GetRasterBand(1)
    periodBand = waveHeight.GetRasterBand(1)
    heightNoData = heightBand.GetNoDataValue()
    periodNoData = periodBand.GetNoDataValue()
    noDataOut = -1
    p = 1028
    g = 9.8

    def op(a, b, c, d):
        c = np.absolute(c)
        tem = 2.0 * math.pi / (b * .86)
        k = np.square(tem) / (g * np.sqrt(np.tanh((np.square(tem)) * (c / g))))
        waveGroupVelocity = ((1 + ((2 * k * c) / np.sinh(2 * k * c))) * (np.sqrt((g / k) * np.tanh(k * c)))) / 2
        wp = (((p * g) / 16) * (np.square(a)) * waveGroupVelocity) / 1000
        return wp

    invest_core.vectorizeRasters([waveHeight, wavePeriod, elevation, blankRaster], op,
                                 rasterName=wavePowerPath, datatype=gdal.GDT_Float32)

def npv():
    for num in range(1, T + 1):
        sum = sum + (B[num] - C[num]) * ((1 + i) ** (-1 * t))

    return npv

def waveEnergyInterp(waveData, machinePerf, machineParam):
    x = np.array(machinePerf.pop(0))
    y = np.array(machinePerf.pop(0))
    z = np.array(machinePerf)
    newx = np.array(waveData[0])
    newy = np.array(waveData[1])
    interpZ = invest_cython_core.interpolateMatrix(x, y, z, newx, newy)
    return interpZ

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
            multArray[:, periodMaxPos:] = 0
        if heightMaxPos != -1:
            multArray[heightMaxPos:, :] = 0
        validArray = np.divide(multArray, 5.0)
#        validArray = np.where(multArray>750, 750, multArray)
        #Since we are doing a cubic interpolation there is a possibility we
        #will have negative values where they should be zero.  So here
        #we drive any negative values to zero.
        validArray = np.where(validArray < 0, 0, validArray)
#            def deviceConstraints(a, capmax, hmax, tmax):

        sum = np.sum(validArray)
        energyCap[key] = sum
#        if key == (556, 496):
#            print interpZ

#            print sum
    print energyCap[(556, 496)]
    return energyCap

#This function will hopefully take the dictionary of waveEnergyCapacity sums and
#interpolate them and rasterize them.
def capturedWaveEnergyToShape(energyCap, waveShape):
    
    wave_Layer = waveShape.GetLayer(0)
    wave_Layer.ResetReading()
    field_def = ogr.FieldDefn('capWE_Sum', ogr.OFTReal)
    wave_Layer.CreateField(field_def)
    
    for feat in wave_Layer:
        iIndex = feat.GetFieldIndex('I')
        jIndex = feat.GetFieldIndex('J')
        iVal = feat.GetField(iIndex)
        jVal = feat.GetField(jIndex)
        value = energyCap[(iVal, jVal)]
        
        index = feat.GetFieldIndex('capWE_Sum')
        feat.SetField(index, value)

        #save the field modifications to the layer.
        wave_Layer.SetFeature(feat)
        feat.Destroy()

    
def pointShapeToDictWE(shape):

    shape_layer = shape.GetLayer(0)
    shape_layer.ResetReading()
    shape_feat = shape_layer.GetNextFeature()
    aoiDictionary = {}
    latlongDict = {}
    xrangeLong = []
    yrangeLat = []
    while shape_feat is not None:

        itemArray = [0, 0, 0, 0, 0]
        
        for field, var in (('I', 0), ('J', 1), ('LONG', 2), ('LATI', 3), ('capWE_Sum', 4)):
            field_index = shape_feat.GetFieldIndex(field)
            itemArray[var] = shape_feat.GetField(field_index)

        xrangeLong.append(itemArray[2])
        yrangeLat.append(itemArray[3])
        
        aoiDictionary[(itemArray[0], itemArray[1])] = [itemArray[2], itemArray[3], itemArray[4]]
        latlongDict[(itemArray[2], itemArray[3])] = [itemArray[4]]
        
        shape_feat.Destroy()
        shape_feat = shape_layer.GetNextFeature()
        
    xrangeLongNoDup = list(set(xrangeLong))
    yrangeLatNoDup = list(set(yrangeLat))
    
    xrangeLongNoDup.sort()
    yrangeLatNoDup.sort()
    
    xrangeLongNP = np.array(xrangeLongNoDup)
    yrangeLatNP = np.array(yrangeLatNoDup)
    matrixSum = []
    for j in yrangeLatNP:
        tmpSum = []
        for i in xrangeLongNP:
            if (i,j) in latlongDict:
                tmpSum.append(latlongDict[(i,j)][0])
            else:
                tmpSum.append(0)
        matrixSum.append(tmpSum)
        
    matrixSumNP = np.array(matrixSum)
    
    results = [xrangeLongNP, yrangeLatNP, matrixSumNP]
    return results

def interpolateSum(results, raster):
    xrange = results[0]
    yrange = results[1]
    matrixSum = results[2]
    
    gt = raster.GetGeoTransform()
    band = raster.GetRasterBand(1)
    matrix = band.ReadAsArray(0, 0, band.XSize, band.YSize)
    newxrange = (np.arange(band.XSize, dtype=float) * gt[1]) + gt[0]
    newyrange = (np.arange(band.YSize, dtype=float) * gt[5]) + gt[3]
    
    #This is probably true if north is up
    if gt[5] < 0:
        print 'North is up'
#        yrange = yrange[::-1]
#        matrixHeight = matrixHeight[::-1]

    spl = scipy.interpolate.RectBivariateSpline(yrange, xrange, matrixSum, kx=1, ky=1)
    spl = spl(newyrange[::-1], newxrange)[::-1]

#    spl = scipy.interpolate.RectBivariateSpline(xrange, yrange, matrixHeight.transpose(), kx=3, ky=3)
#    spl = spl(newxrange, newyrange).transpose()

    band.WriteArray(spl, 0, 0)


