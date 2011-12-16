import numpy as np
from osgeo import gdal
import osgeo.gdal
from osgeo.gdalconst import *
import osgeo.osr as osr
from osgeo import ogr
import math
import invest_core
import invest_cython_core
import sys, os
import scipy
from scipy.interpolate import LinearNDInterpolator as ip

def biophysical(args):
    """Runs the biophysical part of the Wave Energy Model (WEM).
    
    args['wave_base_data'] - a dictionary of seastate bin data.
    args['analysis_area'] - a point geometry shapefile representing the relevant WW3 points
    args['analysis_area_extract'] - a polygon geometry shapefile encompassing the broader range
                                    of interest.
    args['AOI'] - a polygon geometry shapefile outlining a more specific area of interest.
    args['machine_perf'] - a 2D array representing the machine performance table.
    args['machine_param'] - a dictionary which holds the machine parameter values.
    args['dem'] - a GIS raster file of the global elevation model
    args['workspace_dir'] - the workspace path
    args['wave_data_dir'] - the wave data path, used for retreiving other relevant files.
        
    """
#    transformProjection(args['analysis_area_extract'], args['AOI'])

    #Set variables for common output paths
    #Workspace Directory path
    workspaceDir = args['workspace_dir']
    #Wave Data Directory path
    waveDataDir = args['wave_data_dir']
    #Intermediate Directory path to store information
    interDir = workspaceDir + os.sep + 'Intermediate'
    #Output Directory path to store output rasters
    outputDir = workspaceDir + os.sep + 'Output'
    #Path for clipped wave point shapefile holding values of interest
    waveShapePath = interDir + os.sep + 'WaveData_clipZ.shp'
    #Path for 'new' AOI, see comment below 'if AOI in args'
    waveAOIPath = interDir + os.sep + 'waveAOIShape.shp'
    #Paths for intermediate and output rasters.
    waveHeightPath = interDir + os.sep + 'waveHeight.tif'
    wavePeriodPath = interDir + os.sep + 'wavePeriod.tif'
    waveEnergyPath = interDir + os.sep + 'capwe_mwh.tif'
    wavePowerPath = interDir + os.sep + 'wp_kw.tif'
    
    #Set global_dem and nodata values/datatype for new rasters
    global_dem = args['dem']
    nodata = 0
    datatype = gdal.GDT_Float32
    
    #Determine which shapefile will be used to determine area of interest
    if 'AOI' in args:
        #The AOI shapefile has a different projection than lat/long so by calling
        #the clipShape function with analysis_area_extract (which has lat/long projection
        #which we would expect) and AOI, I am making a new AOI with the proper projection
        cutter = clipShape(args['analysis_area_extract'], args['AOI'], waveAOIPath)        
    else:
        cutter = args['analysis_area_extract']
        
    #Create a new shapefile that is a copy of analysis_area but bounded by AOI
    area_shape = clipShape(args['analysis_area'], cutter, waveShapePath)
    area_layer = area_shape.GetLayer(0)
    #Get the spatial extents of the shapefile.
    #The pixel size for the output rasters will be set to the less of
    #the width or height of the shapefiles extents, divided by 250.
    xmin, xmax, ymin, ymax = area_layer.GetExtent()
    pixelSize = 0
    if (xmax-xmin)<(ymax-ymin):
        pixelSize = (xmax-xmin)/250
    else:
        pixelSize = (ymax-ymin)/250
        
    #Generate an interpolate object for waveEnergyCap, create a dictionary with the sums from each location,
    #and add the sum as a field to the shapefile
    energyInterp = waveEnergyInterp(args['wave_base_data'], args['machine_perf'])
    energyCap = computeWaveEnergyCapacity(args['wave_base_data'], energyInterp, args['machine_param'])
    capturedWaveEnergyToShape(energyCap, area_shape)

    #Create rasters bounded by shape file of analyis area
    for path in (waveHeightPath, wavePeriodPath, waveEnergyPath):
        invest_cython_core.createRasterFromVectorExtents(pixelSize, pixelSize,
                                              datatype, nodata, path, area_shape)

    #Open created rasters
    waveHeightRaster = gdal.Open(waveHeightPath, GA_Update)
    wavePeriodRaster = gdal.Open(wavePeriodPath, GA_Update)
    waveEnergyRaster = gdal.Open(waveEnergyPath, GA_Update)
    #Get the corresponding points and values from the shapefile to be used for interpolation
    heightArray = getPointsValues(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'HSAVG_M'], 'HSAVG_M')
    periodArray = getPointsValues(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'TPAVG_S'], 'TPAVG_S')
    energySumArray = getPointsValues(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'capWE_Sum'], 'capWE_Sum')
    #Interpolate the rasters (give a smooth surface)
    interpPointsOverRaster(heightArray[0], heightArray[1], waveHeightRaster)
    interpPointsOverRaster(periodArray[0], periodArray[1], wavePeriodRaster)
    interpPointsOverRaster(energySumArray[0], energySumArray[1], waveEnergyRaster)
    #Generate the wave power raster
    wavePower(waveHeightRaster, wavePeriodRaster, global_dem, wavePowerPath)    
    wavePowerRaster = gdal.Open(wavePowerPath, GA_Update)
    #Clip the wave energy and wave power rasters so that they are confined to the AOI
    wavePowerRaster = clipRasterFromPolygon(cutter, wavePowerRaster, wavePowerPath)
    waveEnergyRaster = clipRasterFromPolygon(cutter, waveEnergyRaster, waveEnergyPath)
    
    #Clean up Shapefiles and Rasters
    area_shape.Destroy()
    cutter.Destroy()
    waveHeightRaster = None
    wavePeriodRaster = None
    waveEnergyRaster = None
    wavePowerRaster = None
    
def clipRasterFromPolygon(shape, raster, path):
    """Returns a raster where any value outside the bounds of the polygon shape are set
    to nodata values.  This represents clipping the raster to the dimensions of the polygon
    
    shape - A polygon shapefile representing the bounds for the raster
    raster - A raster to be bounded by shape
    path - The path for the clipped output raster
    
    returns - the clipped raster    
    """
    gt = raster.GetGeoTransform()
    pixelX = gt[1]
    pixelY = gt[5]
    
    copyRaster = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    copyBand = copyRaster.GetRasterBand(1)
    nodata = copyBand.GetNoDataValue()
    copyBand.Fill(nodata)
    
    gdal.RasterizeLayer(copyRaster, [1], shape.GetLayer(0))
    
    def op(a,b):
        if b==nodata:
            return b
        else:
            return a
    
    invest_core.vectorize2ArgOp(raster.GetRasterBand(1), copyBand, op, copyBand)
    
    return copyRaster
    
#def transformProjection(targetProj, sourceProj):
#    source_Layer = sourceProj.GetLayer(0)
#    target_Layer = targetProj.GetLayer(0)
#    target_feat  = target_Layer.GetNextFeature()
#    target_geom  = target_feat.GetGeometryRef()
#    targetSR = target_geom.GetSpatialReference()
#    source_feat  = source_Layer.GetNextFeature()
#    source_geom  = source_feat.GetGeometryRef()
#    sourceSR = source_geom.GetSpatialReference()
#    
#    coordTrans = osr.CoordinateTransformation(sourceSR, targetSR)
#    source_geom.Transform(coordTrans)
#    source_Layer.SetSpatialFilter(source_geom)
#
#    print source_geom
#    print source_Layer.GetExtent()

#clipShape takes the shapefile you would like to cut down,
#the polygon shape you want the other shapefile cut to,
#and the path for the new shapefile
#It returns a new shapefile in the same format/projection as shapeToClip
def clipShape(shapeToClip, bindingShape, outputPath):
    """Copies a polygon or point geometry shapefile, only keeping the features
    that intersect or are within a binding polygon shape.
    
    shapeToClip - A point or polygon shapefile to clip
    bindingShape - A polygon shapefile indicating the bounds for the
                    shapeToClip features
    outputPath  - The path for the clipped output shapefile
    
    returns - A shapefile representing the clipped version of shapeToClip
    """
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

#def pointShapeToMatrixRanges(shape, key, valueArray, value):
#    """From a point geometry shape, this function generates a matrix (based
#    on value), an array xrange (based on first element in key), and an array
#    yrange (based on second element in key).  These three arrays can then be
#    be used for interpolation purposes.
#
#    shape - A point geometry shapefile
#    key - A list of Strings referencing fields from the points in shape.
#            This list is used to build xranges/yranges
#    valueArray - A list of STrings referencing fields from the points in shape.
#                    Must include values from list and value to build matrix from
#    value - A String representing the value to be used to build the matrix.
#    
#    returns - A list of 3 arrays, the xrange, yrange, and matrix
#    """
#    shape_layer = shape.GetLayer(0)
#    shape_layer.ResetReading()
#    shape_feat = shape_layer.GetNextFeature()
#
#    fieldDict = {}
#    xrangeLong = []
#    yrangeLat = []
#    xRangeField = 'LONG'
#    yRangeField = 'LATI'
#    while shape_feat is not None:
#
#        valueDict = {}
#        #May want to check to make sure field is in shape layer
#        for field in valueArray:
#            field_index = shape_feat.GetFieldIndex(field)
#            valueDict[field] = shape_feat.GetField(field_index)
#        keyList = []        
#        for k in key:
#            keyList.append(valueDict[k])
#        tupledKey = tuple(keyList)
#        fieldDict[tupledKey] = valueDict
#
#        xrangeLong.append(fieldDict[tupledKey][xRangeField])
#        yrangeLat.append(fieldDict[tupledKey][yRangeField])
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
#    
#    matrix = []
#    for j in yrangeLatNP:
#        tmp = []
#        for i in xrangeLongNP:
#            if (i,j) in fieldDict:
#                tmp.append(fieldDict[(i,j)][value])
#            else:
#                tmp.append(0)
#        matrix.append(tmp)
#        
#    matrixNP = np.array(matrix)
#    results = [xrangeLongNP, yrangeLatNP, matrixNP]
#    return results

def getPointsValues(shape, key, valueArray, value):
    """Generates a list of points and a list of values based on a point
    geometry shapefile and other criteria from the arguments
    
    shape - A point geometry shapefile of which to gather the information from
    key   - A list of fields from shape that will be you points
    valueArray - A list of all the relevant fields from shape requiring fields
                    to be used as key and field for the value
    value - A string representing the field from shape to be used as the value
    
    returns - A list of points and values (points represented as 2D list, values as list)
     """
    shape_layer = shape.GetLayer(0)
    shape_layer.ResetReading()
    shape_feat = shape_layer.GetNextFeature()

    fieldDict = {}
    while shape_feat is not None:

        valueDict = {}
        #May want to check to make sure field is in shape layer
        for field in valueArray:
            field_index = shape_feat.GetFieldIndex(field)
            valueDict[field] = shape_feat.GetField(field_index)
        keyList = []        
        for k in key:
            keyList.append(valueDict[k])
        tupledKey = tuple(keyList)
        fieldDict[tupledKey] = valueDict[value]

        shape_feat.Destroy()
        shape_feat = shape_layer.GetNextFeature()
    
    points = []
    values = []
    for id, val in fieldDict.iteritems():
        points.append(list(id))
        values.append(val)

    results = [points, values]
    return results

def interpPointsOverRaster(points, values, raster):
    """"""
    points = np.array(points)
    values = np.array(values)
    
    gt = raster.GetGeoTransform()
    band = raster.GetRasterBand(1)
    xsize = band.XSize
    ysize = band.YSize
    #newpoints = np.array([[x,y] for x in np.arange(gt[0], xsize*gt[1]+gt[0] , gt[1]) for y in np.arange(gt[3], ysize*gt[5]+gt[3], gt[5])])
    newpoints = np.array([[gt[0]+gt[1]*i,gt[3]+gt[5]*j] for i in np.arange(xsize) for j in np.arange(ysize)])

    spl = ip(points, values, fill_value=0)    
    spl = spl(newpoints)
    spl = spl.reshape(xsize, ysize).transpose()
    
    band.WriteArray(spl, 0, 0)
    
#def interpolateField(x, y, z, raster):
#    """Interpolates a raster (raster that has been rasterized from point
#        geometry shape layer) using arguments x,y,z and dimensions of
#        raster.  Correct interpolated matrix is written out to the raster band.
#    x - An array representing the xrange of the 'original' raster
#    y - An array representing the yrange of the 'original' raster
#    z - A 2D array representing a matrix of the 'original' raster
#    raster - The raster to interpolate
#
#    returns - Nothing
#    xrange = x
#    yrange = y
#    matrix = z
#    
#    gt = raster.GetGeoTransform()
#    band = raster.GetRasterBand(1)
#    newxrange = (np.arange(band.XSize, dtype=float) * gt[1]) + gt[0]
#    newyrange = (np.arange(band.YSize, dtype=float) * gt[5]) + gt[3]
#    
#    #This is probably true if north is up
#    if gt[5] < 0:
#        newyrange = newyrange[::-1]
#        matrix = matrix[::-1]
#
#    spl = invest_cython_core.interpolateMatrix(xrange, yrange, matrix, newxrange, newyrange)
#    
#    band.WriteArray(spl, 0, 0)

def wavePower(waveHeight, wavePeriod, elevation, wavePowerPath):
    """Calculates the wave power from the arguments and writes the
    output raster to hard disk. 
    
    waveHeight - A raster representing the wave heights for AOI
    wavePeriod - A raster representing the wave periods for AOI
    elevation  - A raster representing the elevation for AOI
    wavePowerPath - A String representing the output path
    
    returns - Nothing
    
    """
    heightBand = waveHeight.GetRasterBand(1)
    periodBand = waveHeight.GetRasterBand(1)
    heightNoData = heightBand.GetNoDataValue()
    periodNoData = periodBand.GetNoDataValue()
    noDataOut = -1
    p = 1028
    g = 9.8
    alfa = 0.86
    def op(a, b, c):
        c = np.absolute(c)
        tem = 2.0 * math.pi / (b * alfa)
        k = np.square(tem) / (g * np.sqrt(np.tanh((np.square(tem)) * (c / g))))
        waveGroupVelocity = ((1 + ((2 * k * c) / np.sinh(2 * k * c))) * (np.sqrt((g / k) * np.tanh(k * c)))) / 2
        wp = (((p * g) / 16) * (np.square(a)) * waveGroupVelocity) / 1000
        return wp

    invest_core.vectorizeRasters([waveHeight, wavePeriod, elevation], op,
                                 rasterName=wavePowerPath, datatype=gdal.GDT_Float32)
    
    wpRaster = gdal.Open(wavePowerPath, GA_Update)
    wpNoData = wpRaster.GetRasterBand(1).GetNoDataValue()
    def op2(a):
        if a < 1:
            return wpNoData
        else:
            return a
    invest_core.vectorize1ArgOp(wpRaster.GetRasterBand(1), op2, wpRaster.GetRasterBand(1))

def waveEnergyInterp(waveData, machinePerf):
    """Generates a matrix representing the interpolation of the
    machine performance table using new ranges from wave watch data
    
    waveData - A dictionary holding newxrange,newyrange values
    machinePerf - A 2D array holding the ranges of the machine performance
    
    returns - The interpolated matrix
    """
    x = np.array(machinePerf.pop(0), dtype='f')
    y = np.array(machinePerf.pop(0), dtype='f')
    z = np.array(machinePerf, dtype='f')
    newx = waveData[0]
    newy = waveData[1]
    interpZ = invest_cython_core.interpolateMatrix(x, y, z, newx, newy)
    return interpZ

def computeWaveEnergyCapacity(waveData, interpZ, machineParam):
    """Computes the wave energy capacity for each point and
    generates a dictionary whos keys are the points and whos value
    is the wave energy capacity
    
    waveData - A dictionary containing wave watch data
    interpZ - A 2D array of the interpolated values for the machine
                performance table
    machineParam - A dictionary containing the restrictions for the machines
                    (CapMax, TpMax, HsMax)
                    
    returns - A dictionary
    """
    energyCap = {}
    waveRow = waveData.pop(0)
    waveColumn = waveData.pop(1)
    capMax = float(machineParam['CapMax']['VALUE'])
    periodMax = float(machineParam['TpMax']['VALUE'])
    periodMaxPos = -1
    heightMax = float(machineParam['HsMax']['VALUE'])
    heightMaxPos = -1
    for i, v in enumerate(waveRow):
        if (v > periodMax) and (periodMaxPos == -1):
            periodMaxPos = i
    for i, v in enumerate(waveColumn):
        if (v > heightMax) and (heightMaxPos == -1):
            heightMaxPos = i

    for key, val in waveData.iteritems():
        tempArray = np.array(val, dtype='f')
        multArray = np.multiply(tempArray, interpZ)

        if periodMaxPos != -1:
            multArray[:, periodMaxPos:] = 0
        if heightMaxPos != -1:
            multArray[heightMaxPos:, :] = 0

        validArray = np.divide(multArray, 5.0)
#        validArray = np.where(multArray>capMax, capMax, multArray)
        #Since we are doing a cubic interpolation there is a possibility we
        #will have negative values where they should be zero.  So here
        #we drive any negative values to zero.
        validArray = np.where(validArray < 0, 0, validArray)
#            def deviceConstraints(a, capmax, hmax, tmax):

        sum = (validArray.sum()/1000)
        energyCap[key] = sum

    return energyCap

#This function will hopefully take the dictionary of waveEnergyCapacity sums and
#interpolate them and rasterize them.
def capturedWaveEnergyToShape(energyCap, waveShape):
    """Adds a field, value to a shapefile from a dictionary
    
    energyCap - A dictionary representing the wave energy capacity
    waveShape  - A point geometry shapefile to write the new field/values to
    
    returns - Nothing
    
    """
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

def valuation(args):
    """Executes the valuation calculations for the Wave Energy Model.  The result
    is a smooth output raster of the net present value from the interpolation of
    the specific WW3 wave points npv. Requires the following arguments:
    """
    #For each WW3 wave point:
        #Calculate annualRevenue
        
        #Calculate annualCost
        
        #Calculate installCost
        
        #Calculate mooringCost
        
        #Calculate transCost
        
        #Calculate IC (installCost+mooringCost+transCost)
        
        #Calculate NPVWE :
            
    #        def npv(annualRevenue, annualCost):
    #            for num in range(1, T + 1):
    #                sum = sum + (annualRevenue[num] - annualCost[num]) * ((1 + i) ** (-1 * t))
    #        
    #            return npv
    
        #Need to calculate the distances from each WW3 point to landing points
        
        #Need to calculate distances from underwater cable landing point to power grid connection point
        
    #Generate interpolated raster from points above