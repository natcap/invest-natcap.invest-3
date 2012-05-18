"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import logging
import math
from collections import deque

import numpy as np
import scipy.interpolate
import scipy.signal
from osgeo import gdal, osr

import invest_cython_core

logger = logging.getLogger('invest_core')

def new_raster_from_base(base, outputURI, format, nodata, datatype):
    """Create a new, empty GDAL raster dataset with the spatial references,
        dimensions and geotranforms of the base GDAL raster dataset.
        
        base - a the GDAL raster dataset to base output size, and transforms on
        outputURI - a string URI to the new output raster dataset.
        format - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata - a value that will be set as the nodata value for the 
            output raster.  Should be the same type as 'datatype'
        datatype - the pixel datatype of the output raster, for example 
            gdal.GDT_Float32.  See the following header file for supported 
            pixel types:
            http://www.gdal.org/gdal_8h.html#22e22ce0a55036a96f652765793fb7a4
                
        returns a new GDAL raster dataset."""

    cols = base.RasterXSize
    rows = base.RasterYSize
    projection = base.GetProjection()
    geotransform = base.GetGeoTransform()
    return new_raster(cols, rows, projection, geotransform, format, nodata,
                     datatype, base.RasterCount, outputURI)

def new_raster(cols, rows, projection, geotransform, format, nodata, datatype,
              bands, outputURI):
    """Create a new raster with the given properties.
    
        cols - number of pixel columns
        rows - number of pixel rows
        projection - the datum
        geotransform - the coordinate system
        format - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata - a value that will be set as the nodata value for the 
            output raster.  Should be the same type as 'datatype'
        datatype - the pixel datatype of the output raster, for example 
            gdal.GDT_Float32.  See the following header file for supported 
            pixel types:
            http://www.gdal.org/gdal_8h.html#22e22ce0a55036a96f652765793fb7a4
        bands - the number of bands in the raster
        outputURI - the file location for the outputed raster.  If format
            is 'MEM' this can be an empty string
            
        returns a new GDAL raster with the parameters as described above"""

    driver = gdal.GetDriverByName(format)
    newRaster = driver.Create(str(outputURI), cols, rows, bands, datatype)
    newRaster.SetProjection(projection)
    newRaster.SetGeoTransform(geotransform)
    for i in range(bands):
        newRaster.GetRasterBand(i + 1).SetNoDataValue(nodata)
        newRaster.GetRasterBand(i + 1).Fill(nodata)

    return newRaster

def pixel_area(dataset):
    """Calculates the pixel area of the given dataset in Ha.
    
        dataset - GDAL dataset
    
        returns area in Ha of each pixel in dataset"""

    srs = osr.SpatialReference()
    srs.SetProjection(dataset.GetProjection())
    linearUnits = srs.GetLinearUnits()
    geotransform = dataset.GetGeoTransform()
    #take absolute value since sometimes negative widths/heights
    areaMeters = abs(geotransform[1] * geotransform[5] * (linearUnits ** 2))
    return areaMeters / (10 ** 4) #convert m^2 to Ha

def pixel_size_in_meters(dataset, coord_trans, point):
    """Calculates the pixel width and height in meters given a coordinate 
        transform and reference point on the dataset that's close to the 
        transform's projected coordinate sytem.  This is only necessary
        if dataset is not already in a meter coordinate system, for example
        dataset may be in lat/long (WGS84).  
     
       dataset - A projected GDAL dataset in the form of lat/long decimal degrees
       coord_trans - An OSR coordinate transformation from dataset coordinate
           system to meters
       point - a reference point close to the coordinate transform coordinate
           system.  must be in the same coordinate system as dataset.
       
       returns a tuple containing (pixel width in meters, pixel height in 
           meters)"""
    #Get the first points (x,y) from geoTransform
    geo_tran = dataset.GetGeoTransform()    
    pixel_size_x = geo_tran[1]
    pixel_size_y = geo_tran[5]
    top_left_x = point[0]
    top_left_y = point[1]
    LOGGER.debug('pixel_size_x: %s', pixel_size_x)
    LOGGER.debug('pixel_size_x: %s', pixel_size_y)
    LOGGER.debug('top_left_x : %s', top_left_x)
    LOGGER.debug('top_left_y : %s', top_left_y)
    #Create the second point by adding the pixel width/height
    new_x = top_left_x + pixel_size_x
    new_y = top_left_y + pixel_size_y
    LOGGER.debug('top_left_x : %s', new_x)
    LOGGER.debug('top_left_y : %s', new_y)
    #Transform two points into meters
    point_1 = coord_trans.TransformPoint(top_left_x, top_left_y)
    point_2 = coord_trans.TransformPoint(new_x, new_y)
    #Calculate the x/y difference between two points
    #taking the absolue value because the direction doesn't matter for pixel
    #size in the case of most coordinate systems where y increases up and x
    #increases to the right (right handed coordinate system).
    pixel_diff_x = abs(point_2[0] - point_1[0])
    pixel_diff_y = abs(point_2[1] - point_1[1])
    LOGGER.debug('point1 : %s', point_1)
    LOGGER.debug('point2 : %s', point_2)
    LOGGER.debug('pixel_diff_x : %s', pixel_diff_x)
    LOGGER.debug('pixel_diff_y : %s', pixel_diff_y)
    return (pixel_diff_x, pixel_diff_y)

def create_raster_from_vector_extents(xRes, yRes, format, nodata, rasterFile, shp):
    """Create a blank raster based on a vector file extent.  This code is
        adapted from http://trac.osgeo.org/gdal/wiki/FAQRaster#HowcanIcreateablankrasterbasedonavectorfilesextentsforusewithgdal_rasterizeGDAL1.8.0
    
        xRes - the x size of a pixel in the output dataset must be a positive 
            value
        yRes - the y size of a pixel in the output dataset must be a positive 
            value
        format - gdal GDT pixel type
        nodata - the output nodata value
        rasterFile - URI to file location for raster
        shp - vector shapefile to base extent of output raster on
        
        returns a blank raster whose bounds fit within `shp`s bounding box
            and features are equivalent to the passed in data"""

    #Determine the width and height of the tiff in pixels based on desired
    #x and y resolution
    shpExtent = shp.GetLayer(0).GetExtent()
    tiff_width = int(math.ceil(abs(shpExtent[1] - shpExtent[0]) / xRes))
    tiff_height = int(math.ceil(abs(shpExtent[3] - shpExtent[2]) / yRes))

    driver = gdal.GetDriverByName('GTiff')
    raster = driver.Create(rasterFile, tiff_width, tiff_height, 1, format)
    raster.GetRasterBand(1).SetNoDataValue(nodata)

    #Set the transform based on the upper left corner and given pixel
    #dimensions
    raster_transform = [shpExtent[0], xRes, 0.0, shpExtent[3], 0.0, -yRes]
    raster.SetGeoTransform(raster_transform)

    #Use the same projection on the raster as the shapefile
    srs = osr.SpatialReference()
    srs.ImportFromWkt(shp.GetLayer(0).GetSpatialRef().__str__())
    raster.SetProjection(srs.ExportToWkt())

    #Initialize everything to nodata
    raster.GetRasterBand(1).Fill(nodata)
    raster.GetRasterBand(1).FlushCache()

def calculate_intersection_rectangle(rasterList):
    """Return a bounding box of the intersections of all the rasters in the
        list.
        
        rasterList - a list of GDAL rasters in the same projection and 
            coordinate system
            
        returns a 4 element list that bounds the intersection of all the 
            rasters in rasterList.  [left, top, right, bottom]"""

    #Define the initial bounding box
    gt = rasterList[0].GetGeoTransform()
    #order is left, top, right, bottom of rasterbounds
    boundingBox = [gt[0], gt[3], gt[0] + gt[1] * rasterList[0].RasterXSize,
                   gt[3] + gt[5] * rasterList[0].RasterYSize]

    for band in rasterList:
        #intersect the current bounding box with the one just read
        gt = band.GetGeoTransform()
        LOGGER.debug('geotransform on raster band %s %s' % (gt, band))
        LOGGER.debug('pixel x and y %s %s' % (band.RasterXSize,
                                              band.RasterYSize))
        rec = [gt[0], gt[3], gt[0] + gt[1] * band.RasterXSize,
               gt[3] + gt[5] * band.RasterYSize]
        #This intersects rec with the current bounding box
        boundingBox = [max(rec[0], boundingBox[0]),
                       min(rec[1], boundingBox[1]),
                       min(rec[2], boundingBox[2]),
                       max(rec[3], boundingBox[3])]
    return boundingBox

def interpolate_matrix(x, y, z, newx, newy, degree=1):
    """Takes a matrix of values from a rectangular grid along with new 
        coordinates and returns a matrix with those values interpolated along
        the new axis points.
        
        x - an array of x points on the grid
        y - an array of y points on the grid
        z - the values on the grid
        newx- the new x points for the interpolated grid
        newy - the new y points for the interpolated grid
        
        returns a matrix of size len(newx)*len(newy) whose values are 
            interpolated from z"""

    #Create an interpolator for the 2D data.  Here's a reference
    #http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RectBivariateSpline.html
    #not using interp2d because this bug: http://projects.scipy.org/scipy/ticket/898
    spl = scipy.interpolate.RectBivariateSpline(x, y, z.transpose(), kx=degree, ky=degree)
    return spl(newx, newy).transpose()

def calculateRasterStats(band):
    """Calculates and sets the min, max, stdev, and mean for the given band.
    
        band - a GDAL rasterband that will be modified by having its band
            statistics set
    
        returns nothing
    """

    #calculating raster statistics
    rasterMin, rasterMax = band.ComputeRasterMinMax(0)
    #make up stddev and mean
    mean = (rasterMax + rasterMin) / 2.0

    #This is an incorrect standard deviation, but saves us from having to 
    #calculate by hand
    stdev = (rasterMax - mean) / 2.0

    band.SetStatistics(rasterMin, rasterMax, mean, stdev)

def rasterDiff(rasterBandA, rasterBandB, outputRasterBand):
    """Iterate through the rows in the two sequestration rasters and calculate 
        the difference in each pixel.  Maps the difference to the output 
        raster.
        
        rasterBandA - a GDAL raster band
        rasterBandB - a GDAL raster band
        outputRasterBand - a GDAL raster band with the elementwise value of 
            rasterBandA-rasterBandB.  If either rasterBandA and rasterBandB
            have nodata values, a nodata out is written, otherwise if just 
            one or the other rasters has a nodata value, it is treated as a 0
            and the difference is calculated
            
        returns nothing"""

    #Build an operation that does pixel difference unless one of the inputs
    #is a nodata value
    noDataA = rasterBandA.GetNoDataValue()
    noDataB = rasterBandB.GetNoDataValue()
    noDataOut = outputRasterBand.GetNoDataValue()

    def noDataDiff(a, b):
        if a == noDataA:
            if b == noDataB:
                return noDataOut
            else:
                return -b
        elif b == noDataB:
            return a
        else:
            return a - b

    vectorize2ArgOp(rasterBandA, rasterBandB, noDataDiff, outputRasterBand)

def rasterAdd(rasterBandA, rasterBandB, outputRasterBand):
    """Iterate through the rows in the two rasters and calculate 
        the sum in each pixel.  Maps the sum to the output 
        raster. 
        
        rasterBandA - a GDAL raster band
        rasterBandB - a GDAL raster band
        outputRasterBand - a GDAL raster band with the elementwise value of 
            rasterBandA+rasterBandB. If either rasterBandA and rasterBandB
            have nodata values, a nodata out is written, otherwise if just 
            one or the other rasters has a nodata value, it is treated as a 0
            and the difference is calculated
            
        returns nothing"""

    #Build an operation that does pixel difference unless one of the inputs
    #is a nodata value
    #Build an operation that does pixel difference unless one of the inputs
    #is a nodata value
    noDataA = rasterBandA.GetNoDataValue()
    noDataB = rasterBandB.GetNoDataValue()
    noDataOut = outputRasterBand.GetNoDataValue()

    def noDataAdd(a, b):
        if a == noDataA:
            if b == noDataB:
                return noDataOut
            else:
                return b
        elif b == noDataB:
            return a
        else:
            return a + b

    vectorize2ArgOp(rasterBandA, rasterBandB, noDataAdd, outputRasterBand)

def vectorize2ArgOp(rasterBandA, rasterBandB, op, outBand):
    """Applies the function 'op' over rasterBandA and rasterBandB
    
        rasterBandA - a GDAL raster
        rasterBandB - a GDAL raster of the same dimensions as rasterBandA
        op- a function that that takes 2 arguments and returns 1 value
        outBand - the result of vectorizing op over rasterbandA and 
            rasterBandB
            
        returns nothing"""

    vOp = np.vectorize(op)
    for i in range(0, rasterBandA.YSize):
        dataA = rasterBandA.ReadAsArray(0, i, rasterBandA.XSize, 1)
        dataB = rasterBandB.ReadAsArray(0, i, rasterBandB.XSize, 1)
        out_array = vOp(dataA, dataB)
        outBand.WriteArray(out_array, 0, i)

def vectorize1ArgOp(rasterBand, op, outBand, bounding_box=None):
    """Applies the function 'op' over rasterBand and outputs to outBand
    
        rasterBand - (input) a GDAL raster
        op - (input) a function that that takes 2 arguments and returns 1 value
        outBand - (output) the result of vectorizing op over rasterBand
        bounding_box - (input, optional) a 4 element list that corresponds
            to the bounds in GDAL's ReadAsArray to limit the vectorization
            over that region in rasterBand and writing to the corresponding
            outBand.  If left None, defaults to the size of the band
            
        returns nothing"""

    vOp = np.vectorize(op, otypes=[np.float])
    if bounding_box == None:
        bounding_box = [0, 0, rasterBand.XSize, rasterBand.YSize]

    data = rasterBand.ReadAsArray(*bounding_box)
    out_array = vOp(data)
    outBand.WriteArray(out_array, *bounding_box[0:2])

def vectorizeRasters(rasterList, op, rasterName=None,
                     datatype=gdal.GDT_Float32, nodata=0.0):
    """Apply the numpy vectorized operation `op` on the rasters contained in
        rasterList where the arguments to `op` are brodcasted pixels from
        each raster in rasterList in the order they exist in the list
        
        rasterList - list of rasters
        op - numpy vectorized operation, takes broadcasted pixels from 
            the first bands in rasterList in order and returns a new pixel
        rasterName - the desired URI to the output raster.  If None then
            resulting raster is only mapped to MEM
        datatype - the GDAL datatype of the output raster.  By default this
            is a 32 bit float.
        nodata - the nodata value for the output raster
        
        returns a single band raster"""

    logger.debug('starting vectorizeRasters')

    #create a new raster with the minimum resolution of rasterList and
    #bounding box that contains aoiBox
    #gt: left, pixelxwidth, pixelywidthforx, top, pixelxwidthfory, pixelywidth
    #generally pixelywidthforx and pixelxwidthfory are zero for maps where 
    #north is up if that's not the case for us, we'll have a few bugs to deal 
    #with aoibox is left, top, right, bottom
    logger.debug('calculating the overlapping rectangles')
    aoiBox = invest_cython_core.calculateIntersectionRectangle(rasterList)
    logger.debug('the aoi box: %s' % aoiBox)
    #determine the minimum pixel size
    gt = rasterList[0].GetGeoTransform()
    pixelWidth, pixelHeight = gt[1], gt[5]
    for raster in rasterList:
        gt = raster.GetGeoTransform()
        pixelWidth = min(pixelWidth, gt[1], key=abs)
        pixelHeight = min(pixelHeight, gt[5], key=abs)

    logger.debug('min pixel width and height: %s %s' % (pixelWidth,
                                                        pixelHeight))

    #These define the output raster's columns and outRows
    outCols = int(math.ceil((aoiBox[2] - aoiBox[0]) / pixelWidth))
    outRows = int(math.ceil((aoiBox[3] - aoiBox[1]) / pixelHeight))
    logger.debug('number of pixel outCols and outRows %s %s' % (outCols, outRows))
    #outGt order: 
    #1) left coordinate of top left corner
    #2) pixel width in x direction
    #3) pixel width in y direciton (usually zero)
    #4) top coordinate of top left corner
    #5) pixel height in x direction (usually zero)
    #6) pixel height in y direction 
    outGt = [aoiBox[0], pixelWidth, 0.0, aoiBox[1], 0.0, pixelHeight]

    projection = rasterList[0].GetProjection()
    outputURI = ''
    format = 'MEM'
    if rasterName != None:
        outputURI = rasterName
        format = 'GTiff'
    outRaster = invest_cython_core.newRaster(outCols, outRows, projection,
        outGt, format, nodata, datatype, 1, outputURI)
    outBand = outRaster.GetRasterBand(1)
    outBand.Fill(0)

    #Determine the output raster's x and y range
    outXRange = (np.arange(outCols, dtype=float) * outGt[1]) + outGt[0]
    outYRange = (np.arange(outRows, dtype=float) * outGt[5]) + outGt[3]

    logger.debug('outXRange shape %s ' % (outXRange.shape))
    logger.debug('outYRange shape %s ' % (outYRange.shape))
    #create an interpolator for each raster band
    matrixList = []
    nodataList = []
    for raster in rasterList:
        logging.debug('building interpolator for %s' % raster)
        gt = raster.GetGeoTransform()
        logging.debug('gt = %s' % (str(gt)))
        band = raster.GetRasterBand(1)
        matrix = band.ReadAsArray(0, 0, band.XSize, band.YSize)

        #Need to set nodata values to something reasonable to avoid weird
        #interpolation issues if nodata is a large value like -3e38.
        nodataMask = matrix == band.GetNoDataValue()
        matrix[nodataMask] = nodata

        logger.debug('bandXSize bandYSize %s %s' % (band.XSize, band.YSize))
        xrange = (np.arange(band.XSize, dtype=float) * gt[1]) + gt[0]
        logger.debug('gt[0] + band.XSize * gt[1] = %s' % (gt[0] + band.XSize * gt[1]))
        logger.debug('xrange[-1] = %s' % xrange[-1])
        yrange = (np.arange(band.YSize, dtype=float) * gt[5]) + gt[3]
        #This is probably true if north is up
        if gt[5] < 0:
            yrange = yrange[::-1]
            matrix = matrix[::-1]
        logger.debug('xrange shape %s' % xrange.shape)
        logger.debug('yrange shape %s' % yrange.shape)
        logger.debug('matrix shape %s %s' % matrix.shape)
        #transposing matrix here since numpy 2d array order is matrix[y][x]
        logger.debug('creating RectBivariateSpline interpolator')
        spl = scipy.interpolate.RectBivariateSpline(yrange, xrange,
                                                    matrix,
                                                    kx=1, ky=1)
        logger.debug('interpolating')

        #This handles the case where Y is increasing downwards in the output.
        #We encountered this when writing a testcase for a 50x50 box wih no
        #geotransform.
        if outGt[5] < 0:
            matrixList.append(spl(outYRange[::-1], outXRange)[::-1])
        else:
            matrixList.append(spl(outYRange, outXRange))

        nodataList.append(band.GetNoDataValue())


    #invoke op with interpolated values that overlap the output raster
    logger.debug('applying operation on matrix stack')
    outMatrix = op(*matrixList)
    logger.debug('result of operation on matrix stack shape %s %s' %
                 (outMatrix.shape))
    logger.debug('outmatrix size %s raster size %s %s'
                 % (outMatrix.shape, outBand.XSize, outBand.YSize))

    #Nodata out any values in outBand that have corresponding nodata values
    #in the matrixList
    for band, nodata in zip(matrixList, nodataList):
        noDataIndex = band == nodata
        outMatrix[noDataIndex] = outBand.GetNoDataValue()

    outBand.WriteArray(outMatrix, 0, 0)

    #return the new raster
    return outRaster

def bounding_box_index(ogr_feature, gdal_dataset):
    """Calculates the bounding box in GDAL raster index coordinates given the
        geotransform object corresponding to a raster in the same projection as
        ogr_geometry.
        
        ogr_feature - an OGR Feature object
        gdal_dataset - the GDAL dataset object to calculate ogr_geometry 
            coordinates for

        raises an exception if the dataset index bounding box is outside the
            range of gdal_dataset

        returns [xoff, yoff, win_xsize, win_ysize]"""

    feature_geometry = ogr_feature.GetGeometryRef()
    geometry_bounding_box = feature_geometry.GetEnvelope()
    dataset_geotransform = gdal_dataset.GetGeoTransform()


    min_col = int((geometry_bounding_box[0] - dataset_geotransform[0]) / \
                  dataset_geotransform[1]) - 1
    max_col = int((geometry_bounding_box[1] - dataset_geotransform[0]) / \
                  dataset_geotransform[1]) + 1

    #Recall that rows increase going DOWN, so the "max" row is really the
    #bottom row. that's the index of geometry_bounding_box[2].
    #This is really confusing, so check out the class structure here:
    #http://www.gdal.org/ogr/ogr__core_8h-source.html
    max_row = int(math.ceil((geometry_bounding_box[2] - dataset_geotransform[3]) / \
                  dataset_geotransform[5])) + 1
    min_row = int(math.ceil((geometry_bounding_box[3] - dataset_geotransform[3]) / \
                  dataset_geotransform[5])) - 1

    if min_row < 0: min_row = 0
    if min_col < 0: min_col = 0
    if max_col >= gdal_dataset.RasterXSize: gdal_dataset.RasterXSize - 1
    if max_row >= gdal_dataset.RasterYSize: gdal_dataset.RasterYSize - 1

    return [min_col, min_row, max_col - min_col, max_row - min_row]

