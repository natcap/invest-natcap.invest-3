"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import numpy as np
import scipy.interpolate
import scipy.signal
import math
from osgeo import gdal, osr
import logging
from collections import deque
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
    newRaster = driver.Create(str(outputURI), cols, rows, bands, datatype)
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
    #http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RectBivariateSpline.html
    #not using interp2d because this bug: http://projects.scipy.org/scipy/ticket/898
    spl = scipy.interpolate.RectBivariateSpline(x, y, z.transpose(), kx=3, ky=3)
    return spl(newx, newy).transpose()

def vectorizeRasters(rasterList, op, rasterName=None,
                     datatype=gdal.GDT_Float32,):
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
    nodata = 0
    outRaster = newRaster(outCols, outRows, projection, outGt, format,
                          nodata, datatype, 1, outputURI)
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
        band = raster.GetRasterBand(1)
        matrix = band.ReadAsArray(0, 0, band.XSize, band.YSize)
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
        matrixList.append(spl(outYRange[::-1], outXRange)[::-1])
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

#No data out the pixels that used nodata values in calculating slope
def shiftMatrix(M, x, y):
    """Shifts M along the given x and y axis.
    
        M - a 2D numpy array
        x - the number of elements x-wise to shift M
        y - the number of elements y-wise to shift M
    
        returns M rolled x and y elements along the x and y axis"""
    logger.debug('shifting by %s %s' % (x, y))
    return np.roll(np.roll(M, x, axis=1), y, axis=0)

def calculateSlope(dem, uri=''):
    """Calculates the slopeMatrix of the given DEM in terms of percentage rise.
        Here's a good reference for the algorithm:
        http://webhelp.esri.com/arcgiSDEsktop/9.3/index.cfm?TopicName=How%20Slope%20works 
        
        dem - a single band raster of z values.  z units should be identical
            to ground units.
        uri - optional argument if the user wishes to store the raster on disk
            
        returns a raster of the same dimensions as dem whose elements are
            percent slopeMatrix (percent rise)"""

    logger = logging.getLogger('calculateSlope')
    #Read the DEM directly into an array
    demBand = dem.GetRasterBand(1)
    demBandMatrix = demBand.ReadAsArray(0, 0, demBand.XSize, demBand.YSize)
    logger.debug('demBandMatrix size %s' % (demBandMatrix.size))

    #Create an empty slope matrix
    slopeMatrix = np.empty((demBand.YSize, demBand.XSize))
    logger.debug('slopeMatrix size %s' % (slopeMatrix.size))

    gp = dem.GetGeoTransform()
    cellXSize = gp[1]
    cellYSize = gp[5]
    nodata = demBand.GetNoDataValue()
    logger.info('starting pixelwise slope calculation')

    logger.debug('building kernels')
    #Got idea for this from this thread http://stackoverflow.com/q/8174467/42897
    dzdyKernel = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float64)
    dzdxKernel = dzdyKernel.transpose().copy()
    dzdyKernel /= (8 * cellYSize)
    dzdxKernel /= (8 * cellXSize)

    logger.debug('doing convolution')
    dzdx = scipy.signal.convolve2d(demBandMatrix, dzdxKernel, 'same')
    dzdy = scipy.signal.convolve2d(demBandMatrix, dzdyKernel, 'same')
    slopeMatrix = np.sqrt(dzdx ** 2 + dzdy ** 2)

    #Now, "nodata" out the points that used nodata from the demBandMatrix
    noDataIndex = demBandMatrix == nodata
    logger.debug('slopeMatrix and noDataIndex shape %s %s' %
                 (slopeMatrix.shape, noDataIndex.shape))
    slopeMatrix[noDataIndex] = -1

    offsets = [(1, 1), (0, 1), (-1, 1), (1, 0), (-1, 0), (1, -1), (0, -1),
               (-1, -1)]
    for offset in offsets:
        slopeMatrix[shiftMatrix(noDataIndex, *offset)] = -1

    #Create output raster
    format = 'MEM'
    if uri != '': format = 'GTiff'
    logger.debug('create raster for slope')
    slope = newRasterFromBase(dem, uri, format, -1, gdal.GDT_Float32)
    slope.GetRasterBand(1).WriteArray(slopeMatrix, 0, 0)

    rasterMin, rasterMax, mean, stdev = slope.GetRasterBand(1).ComputeStatistics(False)
    slope.GetRasterBand(1).SetStatistics(rasterMin, rasterMax, mean, stdev)
    return slope

def flowDirection(dem, flow):
    """Calculates the D8 pour point algorithm.  The output is a integer
        raster whose values range from 1 to 255.  The values for each direction
        from the center are:

            +---+---+---+
            | 32| 64|128|
            +---+---+---+
            | 16|   | 1 |
            + --+---+---+
            | 8 | 4 | 2 |
            +---+---+---+
            
        Defined by the following algorithm:  
        - If a cell is lower than its eight neighbors, flow is defined toward
          its lowest neighbor this cell. If multiple neighbors have the lowest 
          value, the cell is still given this value, but flow is defined with 
          one of the two methods explained below. This is used to filter out 
          one-cell sinks, which are considered noise.
        - If a cell has the same change in z-value in multiple directions the
          algorithm breadth first searches outward cells until it finds a 
          cell of lower evelvation.  The direction is assigned to be in the 
          closest fitting direction.
        - A cell at the edge of the surface raster will flow toward the inner
          cell with the steepest drop in z-value. If the drop is less than or
          equal to zero, the cell will flow out of the surface raster.
          
       dem - (input) a single band raster with elevation values
       flow - (output) a single band integer raster of same dimensions as
           dem.  After the function call it will have flow direction in it 
       
       returns nothing"""

    logger = logging.getLogger('flowDirection')
    demMatrix = dem.GetRasterBand(1).ReadAsArray(0, 0, dem.RasterXSize,
                                                 dem.RasterYSize)
    #Make the lowest point seen so far the dem, that way we can spot the pits
    #in a later step
    lowest = demMatrix.copy()

    #This matrix holds the flow direction value, initialize to zero
    flowMatrix = np.zeros(lowest.shape, dtype=np.int8)

    #This dictionary indicates how many pixels to shift over in x and y
    #depending on which power of 2 flow direction we're considering
    shiftIndexes = {1:(-1, 0), 2:(-1, -1), 4:(0, -1),
                    8:(1, -1), 16:(1, 0), 32:(1, 1),
                    64:(0, 1), 128:(-1, 1)}

    #Loop through all the flow directions searching for the lowest value
    for dir in shiftIndexes:
        #Define the kernel based on the flow direction
        logger.debug('Calculating flow for direction %s %s' %
                     (dir, shiftIndexes[dir]))
        neighborElevation = shiftMatrix(demMatrix, *shiftIndexes[dir])

        #Search for areas where the neighbor elevations are equal to the current
        #this will indicate a flat region that needs to be cleaned up later
        #In those cases, add the direciton to the flow matrix since there are
        #multiple possible flow directions
        equalElevationIndexes = neighborElevation == lowest
        lowest[equalElevationIndexes] = neighborElevation[equalElevationIndexes]
        flowMatrix[equalElevationIndexes] = flowMatrix[equalElevationIndexes] + dir

        #Next indicate all the pixels where the neighbor pixel is lower than
        #the lowest seen so far
        lowerIndex = neighborElevation < lowest

        #Update the lowest elevation seen so far
        lowest[lowerIndex] = neighborElevation[lowerIndex]
        #and update the flow to point in the direction of that pixel
        flowMatrix[lowerIndex] = dir

    #now flow matrix has flows defined, but some might be ambiguous, like
    #0 flow in a pit, or multiple flows due to flat regions

    flow.GetRasterBand(1).WriteArray(flowMatrix, 0, 0)
    return flow


def flowAccumulation(flowDirection, dem, flowAccumulation):
    """Creates a raster of accumulated flow to each cell.
    
        flowDirection - A raster showing direction of flow out of each cell
            This can be created with invest_core.flowDirection
        dem - the elevation map.  Necessary for fast flow accumulation 
            processing
        flowAccumulation - The output flow accumulation raster set
        
        returns nothing"""

    logger = logging.getLogger('flowAccumulation')
    logger.debug('initalizing temporary buffers')
    #Load the input flow into a numpy array
    flowDirectionMatrix = flowDirection.GetRasterBand(1).ReadAsArray(0, 0,
        flowDirection.RasterXSize, flowDirection.RasterYSize)
    gp = dem.GetGeoTransform()
    cellXSize = gp[1]
    cellYSize = gp[5]
    #Create the output flow, initalize to -1 as undefined
    accumulationMatrix = np.zeros(flowDirectionMatrix.shape)
    accumulationMatrix[:] = -1

    def calculateInflowNeighbors(i, j):
        """Returns a list of the neighboring pixels to i,j that are in bounds
            and also flow into point i,j.  This information is inferred from
            the flowDirectionMatrix"""

        #consider neighbors who flow into j,i
        shiftIndexes = {1:(-1, 0), 2:(-1, -1), 4:(0, -1), 8:(1, -1), 16:(1, 0),
                        32:(1, 1), 64:(0, 1), 128:(-1, 1)}
        neighbors = deque()
        for dir, (io, jo) in shiftIndexes.iteritems():
            pi = i + io
            pj = j + jo
            if pi >= 0 and pj >= 0 and pj < flowDirectionMatrix.shape[0] and \
                pi < flowDirectionMatrix.shape[1]:
                if flowDirectionMatrix[pj, pi] == dir:
                    neighbors.append((pi, pj))
        return neighbors

    def calculateFlow(pixelsToProcess):
        """Takes a list of pixels to calculate flow for, then does a 
            dynamic style programming process of visiting and updating
            each one as it needs processing.  Modified `accumulationMatrix`
            during processing.
            
            pixelsToProcess - a collections.deque of (i,j) tuples"""
        logger = logging.getLogger('calculateFlow')
        while len(pixelsToProcess) > 0:
            i, j = pixelsToProcess.pop()
            logger.debug('i,j=%s %s x,y=%s %s' % (i, j, gp[0] + cellXSize * i,
                                                  gp[3] + cellYSize * j))
            #if p is calculated, skip its calculation
            if accumulationMatrix[j, i] != -1: continue

            #if any neighbors flow into p and are uncalculated, push p and
            #neighbors on the stack
            neighbors = calculateInflowNeighbors(i, j)
            incomplete = False
            for ni, nj in neighbors:
                #Turns out one of the neighbors is uncalculated
                #Stop checking and process all later
                if accumulationMatrix[nj, ni] == -1:
                    incomplete = True
                    break
            #If one of the neighbors was uncalculated, push the pixel and 
            #neighbors back on the processing list
            if incomplete:
                #Put p first, so it's not visited again until neighbors 
                #are processed
                pixelsToProcess.append((i, j))
                pixelsToProcess.extend(neighbors)
            else:
                #Otherwise, all the inflow neighbors are calculated so do the
                #pixelflow calculation 
                accumulationMatrix[j, i] = 0
                for n in neighbors:
                    accumulationMatrix[j, i] += 1 + accumulationMatrix[nj, ni]

    logger.info('calculating flow accumulation')

    for (x, y), value in np.ndenumerate(accumulationMatrix):
        calculateFlow(deque([(x, y)]))

    flowAccumulation.GetRasterBand(1).WriteArray(accumulationMatrix, 0, 0)

