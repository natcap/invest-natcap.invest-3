"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import logging
import math
from collections import deque

import numpy as np
import scipy.interpolate
import scipy.signal
from osgeo import gdal, osr

import invest_natcap.raster_utils as raster_utils

logger = logging.getLogger('invest_core')

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

    logger.warning("`vectorizeRasters` is deprecated, but its being used right now.  That's bad and you should feel bad. Use invest_natcap.raster_utils.vectorize_rasters instead.")

    logger.debug('starting vectorizeRasters')

    #create a new raster with the minimum resolution of rasterList and
    #bounding box that contains aoiBox
    #gt: left, pixelxwidth, pixelywidthforx, top, pixelxwidthfory, pixelywidth
    #generally pixelywidthforx and pixelxwidthfory are zero for maps where 
    #north is up if that's not the case for us, we'll have a few bugs to deal 
    #with aoibox is left, top, right, bottom
    logger.debug('calculating the overlapping rectangles')
    aoiBox = raster_utils.calculateIntersectionRectangle(rasterList)
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
    outRaster = raster_utils.newRaster(outCols, outRows, projection,
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

