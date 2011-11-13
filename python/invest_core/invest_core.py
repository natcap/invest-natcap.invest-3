"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import numpy as np
import math
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
    tiff_width = int(math.ceil(abs(shpExtent[1] - shpExtent[0])) / xRes)
    tiff_height = int(math.ceil(abs(shpExtent[3] - shpExtent[2])) / yRes)

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

def vectorizeRasters(bandList, op):
    """Apply the numpy vectorized operation `op` on the rasters contained in
        bandList where the arguments to `op` are brodcasted pixels from
        each raster in bandList in the order they exist in the list
        
        bandList - list of bands
        op - numpy vectorized operation, takes brodcasted pixels from bandList
            in order and returns a new pixel
        
        returns a single band raster"""

    matrixList = []
    for band in bandList:
        matrixList.append(band.ReadAsArray(0, 0, band.XSize, band.YSize))
        outArray = op(*matrixList)
        #write the array somewhere
    #return the new raster
    return None
