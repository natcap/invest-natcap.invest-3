"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import numpy as np
import scipy.interpolate
import math
from osgeo import gdal, osr
import logging
logger = logging.getLogger('invest_core')

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

def vectorize1ArgOp(rasterBand, op, outBand):
    """Applies the function 'op' over rasterBand and outputs to outBand
    
        rasterBand - a GDAL raster
        op- a function that that takes 2 arguments and returns 1 value
        outBand - the result of vectorizing op over rasterBand
            
        returns nothing"""

    vOp = np.vectorize(op)
    for i in range(0, rasterBand.YSize):
        data = rasterBand.ReadAsArray(0, i, rasterBand.XSize, 1)
        out_array = vOp(data)
        outBand.WriteArray(out_array, 0, i)


def newRasterFromBase(base, outputURI, format, nodata, datatype):
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
    return newRaster(cols, rows, projection, geotransform, format, nodata,
                     datatype, base.RasterCount, outputURI)

def newRaster(cols, rows, projection, geotransform, format, nodata, datatype,
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
    newRaster = driver.Create(outputURI, cols, rows, bands, datatype)
    newRaster.SetProjection(projection)
    newRaster.SetGeoTransform(geotransform)
    for i in range(bands):
        newRaster.GetRasterBand(i + 1).SetNoDataValue(nodata)

    return newRaster

def pixelArea(dataset):
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

def createRasterFromVectorExtents(xRes, yRes, format, nodata, rasterFile, shp):
    """Create a blank raster based on a vector file extent.  This code is
        adapted from http://trac.osgeo.org/gdal/wiki/FAQRaster#HowcanIcreateablankrasterbasedonavectorfilesextentsforusewithgdal_rasterizeGDAL1.8.0
    
        xRes - the x resolution of the output dataset
        yRes - the y resolution of the output dataset
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
    raster.GetRasterBand(1).SetNoDataValue(1.0)

    #Set the transform based on the hupper left corner and given pixel
    #dimensions
    raster_transform = [shpExtent[0], xRes, 0.0, shpExtent[3], 0.0, -yRes]
    raster.SetGeoTransform(raster_transform)

    #Use the same projection on the raster as the shapefile
    srs = osr.SpatialReference()
    srs.ImportFromWkt(shp.GetLayer(0).GetSpatialRef().__str__())
    raster.SetProjection(srs.ExportToWkt())

    #Initalize everything to nodata
    raster.GetRasterBand(1).Fill(nodata)

def calculateIntersectionRectangle(rasterList):
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
        logger.debug('geotransform on raster band %s %s' % (gt, band))
        logger.debug('pixel x and y %s %s' % (band.RasterXSize,
                                              band.RasterYSize))
        rec = [gt[0], gt[3], gt[0] + gt[1] * band.RasterXSize,
               gt[3] + gt[5] * band.RasterYSize]
        #This intersects rec with the current bounding box
        boundingBox = [max(rec[0], boundingBox[0]),
                       min(rec[1], boundingBox[1]),
                       min(rec[2], boundingBox[2]),
                       max(rec[3], boundingBox[3])]
    return boundingBox

def interpolateMatrix(x, y, z, newx, newy):
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
    #http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp2d.html
    spl = scipy.interpolate.interp2d(x, y, z, kind='linear', fill_value=0.0)
    return spl(newx, newy)

def vectorizeRasters(rasterList, op, rasterName=None,
                     datatype=gdal.GDT_Float32):
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
        
        returns a single band raster"""

    logger.debug('starting vectorizeRasters')

    #create a new raster with the minimum resolution of rasterList and
    #bounding box that contains aoiBox
    #gt: left, pixelxwidth, pixelywidthforx, top, pixelxwidthfory, pixelywidth
    #generally pixelywidthforx and pixelxwidthfory are zero for maps where 
    #north is up if that's not the case for us, we'll have a few bugs to deal 
    #with aoibox is left, top, right, bottom
    logger.debug('calculating the overlapping rectangles')
    aoiBox = calculateIntersectionRectangle(rasterList)
    logger.debug('the aoi box: %s' % aoiBox)
    #determine the minimum pixel size
    gt = rasterList[0].GetGeoTransform()
    pixelWidth, pixelHeight = gt[1], gt[5]
    for raster in rasterList:
        gt = raster.GetGeoTransform()
        pixelWidth = min(pixelWidth, gt[1])
        pixelHeight = min(pixelWidth, gt[5])

    logger.debug('min pixel width and height: %s %s' % (pixelWidth,
                                                        pixelHeight))

    #DEFINE THESE BASED ON MINIMUM PIXEL WIDTH/HEIGHT
    cols = int(math.ceil((aoiBox[2] - aoiBox[0]) / pixelWidth))
    rows = int(math.ceil((aoiBox[3] - aoiBox[1]) / pixelHeight))
    logger.debug('number of pixel cols and rows %s %s' % (cols, rows))
    #geotransform order: 
    #1) left coordinate of top left corner
    #2) pixel width in x direction
    #3) pixel width in y direciton (usually zero)
    #4) top coordinate of top left corner
    #5) pixel height in x direction (usually zero)
    #6) pixel height in y direction 
    geotransform = [aoiBox[0], pixelWidth, 0.0, aoiBox[1], 0.0, pixelHeight]

    projection = rasterList[0].GetProjection()

    outputURI = ''
    format = 'MEM'
    if rasterName != None:
        outputURI = rasterName
        format = 'GTiff'
    nodata = 0
    outRaster = newRaster(cols, rows, projection, geotransform, format,
                          nodata, datatype, 1, outputURI)
    outRaster.GetRasterBand(1).Fill(1)

    #extract a matrix from each raster that's contained in the bounding box
    #create a scipy.interpolate RectBivariateSpline for each one below is some
    #biovariate spline tracer code

    matrixList = []

#        matrixList.append(band.ReadAsArray(0, 0, band.XSize, band.YSize))
#        outArray = op(*matrixList)
        #write the array somewhere
    #return the new raster
    return None
