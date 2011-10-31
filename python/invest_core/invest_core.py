"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import numpy as np

def rasterDiff(rasterBandA, rasterBandB, outputRasterBand):
    """Iterate through the rows in the two sequestration rasters and calculate 
        the difference in each pixel.  Maps the difference to the output 
        raster.
        
        rasterBandA - a GDAL raster band
        rasterBandB - a GDAL raster band
        outputRasterBand - a GDAL raster band with the elementwise value of 
            rasterBandA-rasterBandB
            
        returns nothing"""

    #Build an operation that does pixel difference unless one of the inputs
    #is a nodata value
    noDataA = rasterBandA.GetNoDataValue()
    noDataB = rasterBandB.GetNoDataValue()

    def noDataDiff(a, b):
        #a is nodata if and only if b is nodata
        if a == noDataA:
            return noDataB
        else:
            return a - b

    vectorizeOp(rasterBandA, rasterBandB, noDataDiff, outputRasterBand)

def vectorizeOp(rasterBandA, rasterBandB, op, outBand):
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
