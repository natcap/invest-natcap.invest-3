"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import numpy as np
from osgeo import gdal, osr

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

    driver = gdal.GetDriverByName(format)
    newRaster = driver.Create(outputURI, cols, rows, 1, datatype)
    newRaster.SetProjection(projection)
    newRaster.SetGeoTransform(geotransform)
    newRaster.GetRasterBand(1).SetNoDataValue(nodata)

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
