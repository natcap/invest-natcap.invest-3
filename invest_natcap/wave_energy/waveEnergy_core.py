import math
import sys
import os

import numpy as np
from osgeo import gdal
import osgeo.gdal
from osgeo.gdalconst import *
import osgeo.osr as osr
from osgeo import ogr
import scipy
from scipy.interpolate import LinearNDInterpolator as ip

import invest_cython_core
from invest_natcap.invest_core import invest_core

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

    #Set variables for common output paths
    #Workspace Directory path
    workspace_dir = args['workspace_dir']
    #Wave Data Directory path
    waveDataDir = args['wave_data_dir']
    #Intermediate Directory path to store information
    interDir = workspace_dir + os.sep + 'Intermediate'
    #Output Directory path to store output rasters
    outputDir = workspace_dir + os.sep + 'Output'
    #Path for clipped wave point shapefile holding values of interest
    waveShapePath = interDir + os.sep + 'WaveData_clipZ.shp'
    #Path for 'new' AOI, see comment below 'if AOI in args'
    waveAOIPath = interDir + os.sep + 'waveAOIShape.shp'
    #Paths for intermediate and output rasters.
    waveEnergyPath = interDir + os.sep + 'capwe_mwh.tif'
    wave_power_path = interDir + os.sep + 'wp_shape_version.tif'
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
    
    ### ADD DEPTH FIELD #####  
    demGT = global_dem.GetGeoTransform()
    demBand = global_dem.GetRasterBand(1)
    xsize = demBand.XSize
    ysize = demBand.YSize
    demMatrix = demBand.ReadAsArray()
    
    field_defn = ogr.FieldDefn('Depth_M', ogr.OFTReal)
    area_layer.CreateField(field_defn)
        
    area_layer.ResetReading()
    feature = area_layer.GetNextFeature()
    
    while feature is not None:
        depth_index = feature.GetFieldIndex('Depth_M')    
        geom = feature.GetGeometryRef()
        lat = geom.GetX()
        long = geom.GetY()
        i = int((lat - demGT[0]) / demGT[1])
        j = int((long - demGT[3]) / demGT[5])
        depth = demMatrix[j][i]        
        feature.SetField(depth_index, depth)        
        area_layer.SetFeature(feature)
        feature.Destroy()
        feature = area_layer.GetNextFeature()
    area_shape.Destroy()
    area_shape = ogr.Open(waveShapePath, 1)
    area_layer = area_shape.GetLayer(0)
    
    #Get the spatial extents of the shapefile.
    #The pixel size for the output rasters will be set to the less of
    #the width or height of the shapefiles extents, divided by 250.
    xmin, xmax, ymin, ymax = area_layer.GetExtent()
    pixelSize = 0
    if (xmax - xmin) < (ymax - ymin):
        pixelSize = (xmax - xmin) / 250
    else:
        pixelSize = (ymax - ymin) / 250
        
    #Generate an interpolate object for waveEnergyCap, create a dictionary with the sums from each location,
    #and add the sum as a field to the shapefile
    energyInterp = waveEnergyInterp(args['wave_base_data'], args['machine_perf'])
    energyCap = computeWaveEnergyCapacity(args['wave_base_data'], energyInterp, args['machine_param'])
    capturedWaveEnergyToShape(energyCap, area_shape)
    area_shape = wavePower(area_shape)

    #Create rasters bounded by shape file of analyis area
    invest_cython_core.createRasterFromVectorExtents(pixelSize, pixelSize,
                                              datatype, nodata, waveEnergyPath, area_shape)
    invest_cython_core.createRasterFromVectorExtents(pixelSize, pixelSize,
                                              datatype, nodata, wave_power_path, area_shape)

    #Open created rasters
    wave_power_raster = gdal.Open(wave_power_path, GA_Update)
    waveEnergyRaster = gdal.Open(waveEnergyPath, GA_Update)
    #Get the corresponding points and values from the shapefile to be used for interpolation
    energySumArray = getPointsValues(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'capWE_Sum'], 'capWE_Sum')
    wave_power_array = getPointsValues(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'wp_Kw'], 'wp_Kw')
    #Interpolate the rasters (give a smooth surface)
    interpPointsOverRaster(energySumArray[0], energySumArray[1], waveEnergyRaster)
    interpPointsOverRaster(wave_power_array[0], wave_power_array[1], wave_power_raster)
    #Clip the wave energy and wave power rasters so that they are confined to the AOI
    wave_power_raster = clipRasterFromPolygon(cutter, wave_power_raster, wave_power_path)
    waveEnergyRaster = clipRasterFromPolygon(cutter, waveEnergyRaster, waveEnergyPath)
        
    #Clean up Shapefiles and Rasters
    area_shape.Destroy()
    cutter.Destroy()
    waveEnergyRaster = None
    wave_power_raster = None
    
def wavePower(shape):
    """Calculates the wave power from the arguments and writes the
    output raster to hard disk. 
    
    waveHeight - A raster representing the wave heights for AOI
    wavePeriod - A raster representing the wave periods for AOI
    elevation  - A raster representing the elevation for AOI
    wavePowerPath - A String representing the output path
    
    returns - Nothing
    
    """
    #Sea water density constant (kg/m^3)
    p = 1028
    #Gravitational acceleration (m/s^2)
    g = 9.8
    #Constant determining the shape of a wave spectrum (see users guide pg 23)
    alfa = 0.86
    #Function defining the equations to compute the wave power.
    layer = shape.GetLayer(0)
    field_defn = ogr.FieldDefn('wp_Kw', ogr.OFTReal)
    layer.CreateField(field_defn)
    layer.ResetReading()
    feat = layer.GetNextFeature()
    while feat is not None:
        height_index = feat.GetFieldIndex('HSAVG_M')
        period_index = feat.GetFieldIndex('TPAVG_S')
        depth_index = feat.GetFieldIndex('Depth_M')
        wp_index = feat.GetFieldIndex('wp_Kw')
        height = feat.GetFieldAsDouble(height_index)
        period = feat.GetFieldAsDouble(period_index)
        depth = feat.GetFieldAsInteger(depth_index)

        depth = np.absolute(depth)
        #wave frequency calculation (used to calculate wave number k)
        tem = (2.0 * math.pi) / (period * alfa)
        #wave number calculation (expressed as a function of wave frequency and water depth)
        k = np.square(tem) / (g * np.sqrt(np.tanh((np.square(tem)) * (depth / g))))
        #wave group velocity calculation (expressed as a function of wave energy period and water depth)
        waveGroupVelocity = ((1 + ((2 * k * depth) / np.sinh(2 * k * depth))) * np.sqrt((g / k) * np.tanh(k * depth))) / 2
        #wave power calculation
        wp = (((p * g) / 16) * (np.square(height)) * waveGroupVelocity) / 1000
        
        feat.SetField(wp_index, wp)
        
        layer.SetFeature(feat)
        feat.Destroy()
        feat = layer.GetNextFeature()
    
    return shape
    
def clipRasterFromPolygon(shape, raster, path):
    """Returns a raster where any value outside the bounds of the polygon shape are set
    to nodata values.  This represents clipping the raster to the dimensions of the polygon
    
    shape - A polygon shapefile representing the bounds for the raster
    raster - A raster to be bounded by shape
    path - The path for the clipped output raster
    
    returns - the clipped raster    
    """
    #Get the pixel size from the raster to clip.
    gt = raster.GetGeoTransform()
    pixelX = gt[1]
    pixelY = gt[5]
    #Create a new raster as a copy from 'raster'
    copyRaster = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    copyBand = copyRaster.GetRasterBand(1)
    #Set the copied rasters values to nodata to create a blank raster.
    nodata = copyBand.GetNoDataValue()
    copyBand.Fill(nodata)
    #Rasterize the polygon layer onto the copied raster
    gdal.RasterizeLayer(copyRaster, [1], shape.GetLayer(0))
    #If the copied raster's value is nodata then the pixel is not within
    #the polygon and should write nodata back. If copied raster's value
    #is not nodata, then pixel lies within polygon and the value from 'raster'
    #should be written out.
    def op(a, b):
        if b == nodata:
            return b
        else:
            return a
    
    invest_core.vectorize2ArgOp(raster.GetRasterBand(1), copyBand, op, copyBand)
    
    return copyRaster
    
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
                #Create a new feature from the input feature and set its geometry
                out_feat = ogr.Feature(feature_def=shp_layer.GetLayerDefn())
                out_feat.SetFrom(in_feat)
                out_feat.SetGeometryDirectly(geom)
                #For all the fields in the feature set the field values from the source field
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
    #Retrieve the layer from the shapefile and reset the reader head
    #incase it has been iterated through earlier.
    shape_layer = shape.GetLayer(0)
    shape_layer.ResetReading()
    #Get the first point from the shape layer
    shape_feat = shape_layer.GetNextFeature()

    fieldDict = {}
    #For all the points in the layer add the desired 'key' and 'value' to the dictionary.
    while shape_feat is not None:
        #This dictionary is used to store the needed values of the desired fields from 'valueArray'
        valueDict = {}
        #May want to check to make sure field is in shape layer
        #For the relevant field in the list valueArray, add the fields value to the dictionary
        for field in valueArray:
            field_index = shape_feat.GetFieldIndex(field)
            valueDict[field] = shape_feat.GetField(field_index)
        keyList = []
        #Create a tuple from the elements of the provided key list
        for k in key:
            keyList.append(valueDict[k])
        tupledKey = tuple(keyList)
        #Set the created tuple as the key of this dictionary and set its value to desired element from valueDict
        fieldDict[tupledKey] = valueDict[value]

        shape_feat.Destroy()
        shape_feat = shape_layer.GetNextFeature()
    
    points = []
    values = []
    #Construct two arrays, one a list of all the points from fieldDict, and the other a list
    #of all the values corresponding the points from fieldDict
    for id, val in fieldDict.iteritems():
        points.append(list(id))
        values.append(val)

    results = [points, values]
    return results

def interpPointsOverRaster(points, values, raster):
    """Interpolates the values of a given set of points and values to the points
    of a raster and writes the interpolated matrix to the raster band
    
    points - A 2D array of points, where the points are represented as [x,y]
    values - A list of values corresponding to the points of 'points'
    raster - A raster to write the interpolated values too
    
    returns - Nothing
    """
    #Set the points and values to numpy arrays
    points = np.array(points)
    values = np.array(values)
    #Get the dimensions from the raster as well as the GeoTransform information
    gt = raster.GetGeoTransform()
    band = raster.GetRasterBand(1)
    xsize = band.XSize
    ysize = band.YSize
    #newpoints = np.array([[x,y] for x in np.arange(gt[0], xsize*gt[1]+gt[0] , gt[1]) for y in np.arange(gt[3], ysize*gt[5]+gt[3], gt[5])])
    #Make a numpy array representing the points of the raster (the points are the pixels)
    newpoints = np.array([[gt[0] + gt[1] * i, gt[3] + gt[5] * j] for i in np.arange(xsize) for j in np.arange(ysize)])
    #Interpolate the points and values from the shapefile from earlier
    spl = ip(points, values, fill_value=0)
    #Run the interpolator object over the new set of points from the raster. Will return a list of values.
    spl = spl(newpoints)
    #Reshape the list of values to the dimensions of the raster for writing.
    #Transpose the matrix provided from 'reshape' because gdal thinks of x,y opposite of humans
    spl = spl.reshape(xsize, ysize).transpose()
    #Write interpolated matrix of values to raster
    band.WriteArray(spl, 0, 0)

def waveEnergyInterp(waveData, machinePerf):
    """Generates a matrix representing the interpolation of the
    machine performance table using new ranges from wave watch data
    
    waveData - A dictionary holding newxrange,newyrange values
    machinePerf - A 2D array holding the ranges of the machine performance
    
    returns - The interpolated matrix
    """
    #Get ranges and matrix for machine performance table
    x = np.array(machinePerf.pop(0), dtype='f')
    y = np.array(machinePerf.pop(0), dtype='f')
    z = np.array(machinePerf, dtype='f')
    #Get new ranges to interpolate to, from waveData table
    newx = waveData[0]
    newy = waveData[1]
    #Interpolate machine performance table and return the interpolated matrix
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
    #Get the row,col headers (ranges) for the wave watch data
    waveRow = waveData.pop(0)
    waveColumn = waveData.pop(1)
    #Get the machine parameter restriction values
    capMax = float(machineParam['CapMax']['VALUE'])
    periodMax = float(machineParam['TpMax']['VALUE'])
    heightMax = float(machineParam['HsMax']['VALUE'])
    periodMaxPos = -1
    heightMaxPos = -1
    #Using the restrictions find the max position (index) for period and height
    #in the waveRow/waveColumn ranges
    for i, v in enumerate(waveRow):
        if (v > periodMax) and (periodMaxPos == -1):
            periodMaxPos = i
    for i, v in enumerate(waveColumn):
        if (v > heightMax) and (heightMaxPos == -1):
            heightMaxPos = i
    #For all the wave watch points, multiply the occurence matrix by the interpolated
    #machine performance matrix to get the captured wave energy
    for key, val in waveData.iteritems():
        tempArray = np.array(val, dtype='f')
        multArray = np.multiply(tempArray, interpZ)
        #Set any value that is outside the restricting ranges provided by 
        #machine parameters to zero
        if periodMaxPos != -1:
            multArray[:, periodMaxPos:] = 0
        if heightMaxPos != -1:
            multArray[heightMaxPos:, :] = 0
        #Divide the matrix by 5 to get the yearly values
        validArray = np.divide(multArray, 5.0)
#        validArray = np.where(multArray>capMax, capMax, multArray)
        #Since we are doing a cubic interpolation there is a possibility we
        #will have negative values where they should be zero.  So here
        #we drive any negative values to zero.
        validArray = np.where(validArray < 0, 0, validArray)
#            def deviceConstraints(a, capmax, hmax, tmax):
        #Sum all of the values from the matrix to get the total captured wave energy
        #and convert into mega watts
        sum = (validArray.sum() / 1000)
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
    #Incase the layer has already been read through earlier in the program
    #reset it to start from the beginning
    wave_Layer.ResetReading()
    #Create a new field for the shapefile
    field_def = ogr.FieldDefn('capWE_Sum', ogr.OFTReal)
    wave_Layer.CreateField(field_def)
    #For all of the features (points) in the shapefile, get the 
    #corresponding point/value from the dictionary and set the 'capWE_Sum'
    #field as the value from the dictionary
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
    
    args['workspace_dir'] - 
    args['wave_data_shape'] - 
    args['number_machines'] - 
    args['machine_econ'] - 
    args['land_gridPts'] - 
    args['projection'] - 
    args['global_dem'] - 
    args['capturedWE'] - 
    
    """
    #Set variables for common output paths
    #Workspace Directory path
    workspaceDir = args['workspace_dir']
    #Intermediate Directory path to store information
    interDir = workspaceDir + os.sep + 'Intermediate'
    #Output Directory path to store output rasters
    outputDir = workspaceDir + os.sep + 'Output'
    #Path for clipped wave point shapefile holding values of interest
    projectedShapePath = interDir + os.sep + 'WaveData_clip_Prj.shp'
    landptPath = interDir + os.sep + 'landingPoints.shp'
    gridptPath = interDir + os.sep + 'gridPoint.shp'
    npvPath = interDir + os.sep + 'waveEnergy_NPV.tif'
    
    dem = args['global_dem']
    capWE = args['capturedWE']
    
    if os.path.isfile(landptPath):
        os.remove(landptPath)
    if os.path.isfile(gridptPath):
        os.remove(gridptPath)
    
    
    #Numver of units
    units = args['number_machines']
    #Extract the machine economic parameters
    machine_econ = args['machine_econ']
    capMax = float(machine_econ['CapMax']['VALUE'])
    capitalCost = float(machine_econ['cc']['VALUE'])
    cml = float(machine_econ['cml']['VALUE'])
    cul = float(machine_econ['cul']['VALUE'])
    col = float(machine_econ['col']['VALUE'])
    omc = float(machine_econ['omc']['VALUE'])
    price = float(machine_econ['p']['VALUE'])
    drate = float(machine_econ['r']['VALUE'])
    smlpm = float(machine_econ['smlpm']['VALUE'])
    
    year = 25.0
    T = np.linspace(0.0, year - 1.0, year)
    rho = 1.0 / (1.0 + drate)
    #Extract the landing and grid points data
    land_grid_pts = args['land_gridPts']
    grid_pt = {}
    land_pts = {}
    for key, value in land_grid_pts.iteritems():
        if value['TYPE'] == 'GRID':
            grid_pt = value
        else:
            land_pts[key] = value
            
    #Create a coordinate transformation for lat/long to meters
    prjFile = open(args['projection'])
    prj = prjFile.read()
    srs_prj = osr.SpatialReference()
    srs_prj.ImportFromWkt(prj)
    sourceSR = args['wave_data_shape'].GetLayer(0).GetSpatialRef()
    targetSR = srs_prj
    coordTrans = osr.CoordinateTransformation(sourceSR, targetSR)
    coordTransOp = osr.CoordinateTransformation(targetSR, sourceSR)
    #Create geometry for grid point location:
    grid_lat = grid_pt['LAT']
    grid_long = grid_pt['LONG']
    grid_geom = ogr.Geometry(ogr.wkbPoint)
    grid_geom.AddPoint_2D(float(grid_long), float(grid_lat))
    
    #Make a point shapefile for landing points.
    drv = ogr.GetDriverByName('ESRI Shapefile')
    ds = drv.CreateDataSource(landptPath)
    layer = ds.CreateLayer('landpoints', srs_prj, ogr.wkbPoint)    
    field_defn = ogr.FieldDefn('Id', ogr.OFTInteger)
    layer.CreateField(field_defn)
    
    for key, value in land_pts.iteritems():
        landing_lat = value['LAT']
        landing_long = value['LONG']
        landing_geom = ogr.Geometry(ogr.wkbPoint)
        landing_geom.AddPoint_2D(float(landing_long), float(landing_lat))
        landing_geom.Transform(coordTrans)
        
        feat = ogr.Feature(layer.GetLayerDefn())
        layer.CreateFeature(feat)
        index = feat.GetFieldIndex('Id')
        feat.SetField(index, value['ID'])
        feat.SetGeometryDirectly(landing_geom)
        
        #save the field modifications to the layer.
        layer.SetFeature(feat)
        feat.Destroy()
    
    layer = None
    drv = None
    ds.Destroy()

    #Make a point shapefile for grid points
    drv = ogr.GetDriverByName('ESRI Shapefile')
    ds = drv.CreateDataSource(gridptPath)
    layer = ds.CreateLayer('gridpoint', srs_prj, ogr.wkbPoint)
    field_defn = ogr.FieldDefn('Id', ogr.OFTInteger)
    layer.CreateField(field_defn)

    feat = ogr.Feature(layer.GetLayerDefn())
    layer.CreateFeature(feat)
    index = feat.GetFieldIndex('Id')
    feat.SetField(index, 0)
    
    grid_geom.Transform(coordTrans)
    feat.SetGeometryDirectly(grid_geom)
    #save the field modifications to the layer.
    layer.SetFeature(feat)
    feat.Destroy()
    
    prjFile.close()
    layer = None
    drv = None
    ds.Destroy()
    
    wave_data_shape = args['wave_data_shape']
    wave_data_layer = wave_data_shape.GetLayer(0)
    shape = changeProjection(wave_data_shape, args['projection'], projectedShapePath)
    shape.Destroy()
    shape = ogr.Open(projectedShapePath, 1)
    shape_layer = shape.GetLayer(0)
    
    landingShape = ogr.Open(landptPath)
    gridShape = ogr.Open(gridptPath)
    
    wePoints = getPoints(shape)
    landingPoints = getPoints(landingShape)
    gridPoint = getPoints(gridShape)
    
    W2L_Dist, W2L_ID = calcDist(wePoints, landingPoints)
    L2G_Dist, L2G_ID = calcDist(landingPoints, gridPoint)
    for field in ['W2L_MDIST', 'LAND_ID', 'L2G_MDIST']:
        field_defn = ogr.FieldDefn(field, ogr.OFTReal)
        shape_layer.CreateField(field_defn)
        
    j = 0
    shape_layer.ResetReading()
    feature = shape_layer.GetNextFeature()
    while feature is not None:
        W2L_index = feature.GetFieldIndex('W2L_MDIST')
        L2G_index = feature.GetFieldIndex('L2G_MDIST')
        ID_index = feature.GetFieldIndex('LAND_ID')    
        
        landID = int(W2L_ID[j])
        
        feature.SetField(W2L_index, W2L_Dist[j])
        feature.SetField(L2G_index, L2G_Dist[landID])
        feature.SetField(ID_index, landID)
        
        j = j + 1
        
        shape_layer.SetFeature(feature)
        feature.Destroy()
        feature = shape_layer.GetNextFeature()
    shape.Destroy()
    shape = ogr.Open(projectedShapePath, 1)
    shape_layer = shape.GetLayer(0)
    
    #########Create W2L/L2G Rasters##########
    xmin, xmax, ymin, ymax = wave_data_layer.GetExtent()
    pixelSize = 0
    if (xmax - xmin) < (ymax - ymin):
        pixelSize = (xmax - xmin) / 250
    else:
        pixelSize = (ymax - ymin) / 250
    
    waveLand_path = interDir + os.sep + 'waveLand.tif'
    landGrid_path = interDir + os.sep + 'landGrid.tif'
    datatype = gdal.GDT_Float32
    nodata = 0
    invest_cython_core.createRasterFromVectorExtents(pixelSize, pixelSize,
                                              datatype, nodata, waveLand_path, wave_data_shape)
    invest_cython_core.createRasterFromVectorExtents(pixelSize, pixelSize,
                                              datatype, nodata, landGrid_path, wave_data_shape)
    waveLandRaster = gdal.Open(waveLand_path, GA_Update)
    landGridRaster = gdal.Open(landGrid_path, GA_Update)
    #Get the corresponding points and values from the shapefile to be used for interpolation
    waveLandArray = getPointsValues(shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'W2L_MDIST'], 'W2L_MDIST')
    landGridArray = getPointsValues(shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'L2G_MDIST'], 'L2G_MDIST')

     #Interpolate the rasters (give a smooth surface)
    interpPointsOverRaster(waveLandArray[0], waveLandArray[1], waveLandRaster)
    interpPointsOverRaster(landGridArray[0], landGridArray[1], landGridRaster)
    #########################################
    
    def op(capturedWE, dem, distWL, distLG):
        capWE = capturedWE * 1000.0
        lenml = 3.0 * np.absolute(dem)
        #Calculate annualRevenue
        annualRevenue = price * units * capWE
        #Calculate annualCost
        annualCost = omc * capWE * units
        #Calculate installCost
        installCost = units * capMax * capitalCost
        #Calculate mooringCost
        mooringCost = smlpm * lenml * cml * units
        #Calculate transCost
        transCost = (distWL * cul / 1000.0) + (distLG * col / 1000.0)
        #Calculate IC (installCost+mooringCost+transCost)
        IC = installCost + mooringCost + transCost
            
        NPV = np.zeros(capWE.shape, dtype=float)
        for i in range(len(T)):
            if i == 0:
                NPV = NPV + (-1 * ((rho ** i) * IC))
            else:
                NPV = NPV + (rho ** i * (annualRevenue - annualCost))
       
        return NPV / 1000
    
    invest_core.vectorizeRasters([capWE, dem, waveLandRaster, landGridRaster], op,
                                 rasterName=npvPath, datatype=gdal.GDT_Float32)
    
    def npv_wave(annual_revenue, annual_cost):
        npv = []
        for i in range(len(T)):
            npv.append(rho ** i * (annual_revenue - annual_cost))
        return sum(npv)
    
    field_defn_npv = ogr.FieldDefn('NPV_25Y', ogr.OFTReal)
    shape_layer.CreateField(field_defn_npv)
    
    feat = shape_layer.GetNextFeature()
    while feat is not None:
        depth_index = feat.GetFieldIndex('Depth_M')
        wave_to_land_index = feat.GetFieldIndex('W2L_MDIST')
        land_to_grid_index = feat.GetFieldIndex('L2G_MDIST')
        captured_wave_energy_index = feat.GetFieldIndex('CapWE_MWHY')
        npv_index = feat.GetFieldIndex('NPV_25Y')
        
        depth = feat.GetFieldAsDouble(depth_index)
        wave_to_land = feat.GetFieldAsDouble(wave_to_land_index)
        land_to_grid = feat.GetFieldAsDouble(land_to_grid_index)
        captured_wave_energy = feat.GetFieldAsDouble(captured_wave_energy_index)
        
        captured_we = np.ones(len(T)) * int(captured_wave_energy) * 1000.0
        captured_we[0] = 0
        
        lenml = 3.0 * np.absolute(depth)
        install_cost = units * capMax * capitalCost
        mooring_cost = smlpm * lenml * cml * units
        trans_cost = (wave_to_land * cul / 1000.0) + (land_to_grid * col / 1000.0)
        initial_cost = install_cost + mooring_cost + trans_cost
        annual_revenue = price * units * captured_we
        annual_cost = omc * captured_we * units
        annual_cost[0] = initial_cost
        
        feat.SetField(npv_index, npv_wave(annual_revenue, annual_cost) / 1000.0)
        
        shape_layer.SetFeature(feat)
        feat.Destroy()
        feat = shape_layer.GetNextFeature()
    
def getPoints(shape):
    point = []
    layer = shape.GetLayer(0)
    feat = layer.GetNextFeature()
    while feat is not None:
        x = float(feat.GetGeometryRef().GetX())
        y = float(feat.GetGeometryRef().GetY())
        point.append([x, y])
        feat.Destroy()
        feat = layer.GetNextFeature()
    
    return np.array(point)
    
def calcDist(xy_1, xy_2):
    mindist = np.zeros(len(xy_1))
    minid = np.zeros(len(xy_1))
    for i, xy in enumerate(xy_1):
        dists = np.sqrt(np.sum((xy - xy_2) ** 2, axis=1))
        mindist[i], minid[i] = dists.min(), dists.argmin()
    return mindist, minid

def changeProjection(shapeToReproject, projection, outputPath):
    """Changes the projection of a shapefile by creating a new shapefile based on
    the projection passed in and then copying all the features and fields of
    the shapefile to reproject to the new shapefile.
    """
    shape_source = outputPath

    if os.path.isfile(shape_source):
        os.remove(shape_source)
    #Get the layer of points from the current point geometry shape
    in_layer = shapeToReproject.GetLayer(0)
    #Get the layer definition which holds needed attribute values
    in_defn = in_layer.GetLayerDefn()
    #Create a new shapefile with similar properties of the current point geometry shape
    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = shp_driver.CreateDataSource(shape_source)
    
    prjFile = open(projection)
    prj = prjFile.read()
#    prj = """PROJCS["WGS_1984_UTM_Zone_10N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",
#    SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],
#    UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],
#    PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-123.0],
#    PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0],AUTHORITY["EPSG",32610]]
#    """
#    prj = """GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",
#    SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],
#    UNIT["Degree",0.0174532925199433]]"""
#    print projection
#    print prj
#    print in_layer.GetSpatialRef()
#
#    """
#    PROJCS["WGS_1984_UTM_Zone_10N",
#        GEOGCS["GCS_WGS_1984",
#            DATUM["D_WGS_1984",
#                SPHEROID["WGS_1984",6378137.0,298.257223563]],
#            PRIMEM["Greenwich",0.0],
#            UNIT["Degree",0.0174532925199433]],
#        PROJECTION["Transverse_Mercator"],
#        PARAMETER["False_Easting",500000.0],
#        PARAMETER["False_Northing",0.0],
#        PARAMETER["Central_Meridian",-123.0],
#        PARAMETER["Scale_Factor",0.9996],
#        PARAMETER["Latitude_Of_Origin",0.0],
#        UNIT["Meter",1.0]]
#    """

    srs_prj = osr.SpatialReference()
    srs_prj.ImportFromWkt(prj)
#    srs_prj.StripCTParms()
    shp_layer = shp_ds.CreateLayer(in_defn.GetName(), srs_prj, in_defn.GetGeomType())
    #Get the number of fields in the current point shapefile
    in_field_count = in_defn.GetFieldCount()
    #For every field, create a duplicate field and add it to the new shapefiles layer
    for fld_index in range(in_field_count):
        src_fd = in_defn.GetFieldDefn(fld_index)

        fd = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd.SetWidth(src_fd.GetWidth())
        fd.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd)
    
    in_layer.ResetReading()
    in_feat = in_layer.GetNextFeature()
 
    while in_feat is not None:
        geom = in_feat.GetGeometryRef()
        #Get the spatial reference of the geometry to use in transforming
        sourceSR = geom.GetSpatialReference()
        #Get the spatial reference of the geometry to use in transforming
        targetSR = srs_prj
        #Create a coordinate transformation
        coordTrans = osr.CoordinateTransformation(sourceSR, targetSR)
        #Transform the polygon geometry into the same format as the point shape geometry
        geom.Transform(coordTrans)
        #For all the features in the current point shape (for all the points)
        #Check to see if they Intersect with the binding polygons geometry and
        #if they do, then add all of the fields and values from that point to the new shape
#        print geom
        #Create a new feature from the input feature and set its geometry
        out_feat = ogr.Feature(feature_def=shp_layer.GetLayerDefn())
        out_feat.SetFrom(in_feat)
        out_feat.SetGeometry(geom)
        #For all the fields in the feature set the field values from the source field
        for fld_index2 in range(out_feat.GetFieldCount()):
            src_field = in_feat.GetField(fld_index2)
            out_feat.SetField(fld_index2, src_field)
#
        shp_layer.CreateFeature(out_feat)
        out_feat.Destroy()

        in_feat.Destroy()
        in_feat = in_layer.GetNextFeature()

    return shp_ds
