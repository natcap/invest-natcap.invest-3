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
    try:
        rasterMin, rasterMax = band.ComputeRasterMinMax(0)
        #make up stddev and mean
        mean = (rasterMax + rasterMin) / 2.0

        #This is an incorrect standard deviation, but saves us from having to 
        #calculate by hand
        stdev = (rasterMax - mean) / 2.0

        band.SetStatistics(rasterMin, rasterMax, mean, stdev)
    except RuntimeError:
        LOGGER.warn("all pixels nodata, so can't set min/max")

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
