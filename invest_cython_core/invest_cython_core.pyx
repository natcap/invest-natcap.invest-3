"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import math
import logging
import bisect

import numpy as np
cimport numpy as np
cimport cython
import scipy
from osgeo import gdal, osr

from invest_natcap.invest_core import invest_core

LOGGER = logging.getLogger('invest_cython_core')

cdef extern from "stdlib.h":
    ctypedef void const_void "const void"
    void qsort(void *base, int nmemb, int size,
            int(*compar)(const_void *, const_void *)) 
    void free(void* ptr)
    void* malloc(size_t size)
    
cdef extern from "math.h":
    double atan(double x)
    double sqrt(double x)
    double sin(double x)
    double cos(double x)

cdef extern from "simplequeue.h":
    ctypedef struct Queue:
        pass
    ctypedef int QueueValue

    Queue *queue_new()
    void queue_free(Queue *queue)
    Queue* queue_push_tail(Queue *queue, QueueValue data)
    Queue* queue_push_head(Queue *queue, QueueValue data)
    QueueValue queue_pop_head(Queue *queue)
    int queue_size(Queue *queue)

cdef class CQueue:
    cdef Queue *_c_queue
    def __cinit__(self,items=None):
        self._c_queue = queue_new()
        if items != None:
            for i in items:
                queue_push_tail(self._c_queue,i)

    def __dealloc__(self):
        queue_free(self._c_queue)
        
    def __len__(self): 
        return queue_size(self._c_queue)

    cdef extend(self, items):
        for i in items:
            queue_push_tail(self._c_queue,i)

    cdef int pop(self):
        return queue_pop_head(self._c_queue)
    
    cdef push(self, int x):
        queue_push_head(self._c_queue, x)
    
    cdef append(self, int x):
        queue_push_tail(self._c_queue, x)
        
    cdef int size(self):
        return queue_size(self._c_queue)


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
    raster.GetRasterBand(1).SetNoDataValue(nodata)

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

def interpolateMatrix(x, y, z, newx, newy, degree=1):
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

#No data out the pixels that used nodata values in calculating slope
def shiftMatrix(M, x, y):
    """Shifts M along the given x and y axis.
    
        M - a 2D numpy array
        x - the number of elements x-wise to shift M
        y - the number of elements y-wise to shift M
    
        returns M rolled x and y elements along the x and y axis"""
    LOGGER.debug('shifting by %s %s' % (x, y))
    return np.roll(np.roll(M, x, axis=1), y, axis=0)

"""This is a structure that's used in flow direction"""
cdef struct Pair:
    int i,j
    float h

cdef struct NeighborFlow:
    int i,j
    float prop

"""This is a compare function that can be passed to stdlib's qsort such
    that pairs are sorted in increasing height order"""
cdef int pairCompare(const_void *a, const_void *b):
    cdef float v = ((<Pair*>a)).h-((<Pair*>b)).h
    if v < 0: return -1
    if v > 0: return 1
    return 0

def flowDirectionD8(dem, flow):
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

    cdef np.int_t x, y, dcur, xdim, ydim, xmax, ymax, i, j, d, nodataFlow, \
        validPixelCount
    cdef np.float_t lowest, h, nodataDem, drainageDistance, currentHeight, \
        neighborHeight, neighborDistance, currentDistance, stepDistance
    cdef Pair *demPixels = \
        <Pair *>malloc(dem.RasterXSize*dem.RasterYSize * sizeof(Pair))
    cdef CQueue q = CQueue()
    
    #This is an array that makes checking neighbor indexes easier
    cdef int *neighborOffsets = \
        [-1, 0, 
         -1, -1, 
         0, -1, 
         1, -1, 
         1, 0, 
         1, 1, 
         0, 1, 
         -1, 1]
    nodataDem = dem.GetRasterBand(1).GetNoDataValue()
    nodataFlow = flow.GetRasterBand(1).GetNoDataValue()

    #GDal inverts x and y, so it's easier to transpose in and back out later
    #on gdal arrays, so we invert the x and y offsets here
    demMatrixTmp = dem.GetRasterBand(1).ReadAsArray(0, 0, dem.RasterXSize,\
        dem.RasterYSize).transpose()

    #Incoming matrix type could be anything numerical.  Cast to a floating
    #point for cython speed and because it's the most general form.
    cdef np.ndarray[np.float_t,ndim=2] demMatrix = demMatrixTmp.astype(np.float)
    demMatrix[:] = demMatrixTmp
    
    xmax, ymax = demMatrix.shape[0], demMatrix.shape[1]
    
    #Construct a lookup table that sorts DEM pixels by height so we can process
    #the lowest pixels to the highest in propagating shortest path distances.
    validPixelCount = 0
    for x in range(1,xmax-1):
        for y in range(1,ymax-1):
            h = demMatrix[x,y]
            if h == nodataDem: continue
            demPixels[validPixelCount].i = x
            demPixels[validPixelCount].j = y
            demPixels[validPixelCount].h = h
            validPixelCount += 1
    
    #Sort pixels by increasing height so that we visit drainage points in order
    qsort(demPixels,validPixelCount,sizeof(Pair),pairCompare)
    
    #This matrix holds the minimum path distance from the current pixel to the
    #most downhill connected pixel on the grid.
    cdef np.ndarray[np.float_t,ndim=2] distanceToDrain = \
        np.zeros([xmax,ymax], dtype=np.float)
    distanceToDrain[:] = -1.0 #Initialize all heights to -1
    

    
    #Do a breadth first walk from each pixel uphill updating the minimum
    #distance from the current pixel to the starting pixel
    for p in range(validPixelCount):
        i = demPixels[p].i
        j = demPixels[p].j
        
        #if this point has been processed, it's not a drainage point, so skip
        if distanceToDrain[i,j] != -1: continue
        
        #initialize the drainage point to 0 height above drainage point
        distanceToDrain[i,j] = 0
        q.append(i)
        q.append(j)
        
        while q.size() > 0:
            i = q.pop()
            j = q.pop()
            drainageDistance = distanceToDrain[i,j]
            currentHeight = demMatrix[i,j]
            #visit neighbors of i,j
            for k in range(8):
                io = i + neighborOffsets[k*2]
                jo = j + neighborOffsets[k*2+1]
                #make sure io and jo are in bounds
                if io < 0 or jo < 0 or io >= xmax or jo >= ymax: continue
                #make sure io,jo is upstream or equal
                neighborHeight = demMatrix[io,jo]
                if neighborHeight < currentHeight: continue
                
                #stepDistance refers to the distance we travel across the
                #pixel, whether it's 1 across or sqrt(2) diagonally. We're
                #diagonal if both the io and jo offsets are turned on
                if abs(neighborOffsets[k*2])+abs(neighborOffsets[k*2+1]) < 2:
                    stepDistance = 1.0
                else:
                    stepDistance = math.sqrt(2)
                #update distance if the current distance
                #neighbor pixel is greater than what we could calculate
                #now.  If it is, update the height and enqueue the neighbor
                #for further propogation of processing distances
                
                if distanceToDrain[io,jo] == -1 or \
                    drainageDistance+stepDistance < distanceToDrain[io,jo]:
                    distanceToDrain[io,jo] = drainageDistance+stepDistance
                    q.append(io)
                    q.append(jo)
                    
    
    #This matrix holds the flow direction value, initialize to zero
    cdef np.ndarray[np.int_t,ndim=2] flowMatrix = \
        np.zeros([xmax,ymax], dtype=np.int)
    
    #This array indicates the integer flow direction based on which pixel
    # to shift to.  The order is d,xo,yo eight times for 8 directions
    cdef np.ndarray[np.int_t,ndim=1] shiftIndexes = np.array([1, 1, 0,
                                                              2, 1, 1,
                                                              4, 0, 1,
                                                              8, -1, 1,
                                                              16, -1, 0,
                                                              32, -1, -1,
                                                              64, 0, -1,
                                                              128, 1, -1],
                                                             dtype=np.int)
    #loop through each cell and skip any edge pixels
    for x in range(1,xmax-1):
        for y in range(1,ymax-1):
            #The lowest height seen so far, initialize to current pixel height
            currentHeight = demMatrix[x,y]
            lowest = currentHeight
            #check for nodata values
            if lowest == nodataDem:
                flowMatrix[x,y] = nodataFlow
                continue
            currentDistance = distanceToDrain[x,y]
            
            #The current flow direction, initialize to 0 for no direction
            dcur = 0
            #search the neighbors for the lowest pixel(s)
            for i in range(8):
                d = shiftIndexes[i*3]
                #the height of the neighboring cell
                neighborHeight = demMatrix[x+shiftIndexes[i*3+1],
                                           y+shiftIndexes[i*3+2]]
                #ensure that the neighbor is downhill
                if neighborHeight > currentHeight: continue 
                neighborDistance = distanceToDrain[x+shiftIndexes[i*3+1],
                                           y+shiftIndexes[i*3+2]]
                if neighborDistance < currentDistance:
                    currentDistance = neighborDistance
                    dcur = d
            flowMatrix[x,y] = dcur

    flow.GetRasterBand(1).WriteArray(flowMatrix.transpose(), 0, 0)
    free(demPixels)
    
    distanceRaster = newRasterFromBase(flow,'distance.tiff', 'GTiff', -5.0,
        gdal.GDT_Float32)
    distanceRaster.GetRasterBand(1).WriteArray(distanceToDrain.transpose(),0,0)
    
    return flow

cdef void calculate_inflow_neighbors_dinf(int i, int j, 
                    np.ndarray[np.float_t,ndim=2] flow_direction_matrix, 
                    int nodata_flow_direction,
                    NeighborFlow *neighbors):
    
    """Returns a list of the neighboring pixels to i,j that are in bounds
        and also flow into point i,j.  This information is inferred from
        the flow_direction_matrix
        
        i - column of pixel to calculate neighbors for
        j - row of pixel to calculate neighbors for
        flow_direction_matrix - a 2D numpy float array whose values indicate
            outward flow directions in terms of radians
        nodata_flow_direction - the value that corresponds to a nodata entry
            in flow_direction_matrix
        neighbors - an output as an array of NeighborFlow structs (i, j, prop).
            Valid entries start at index 0 and end when the NeighborFlow.prop
            value == -1
            
        returns nothing
        """

    #consider neighbors who flow into i,j, third argument is the inflow
    #radian direction
    cdef float PI = 3.14159265, alpha, beta, prop
    cdef int *shift_indexes = [-1, 0,
                               -1, -1,
                               0, -1,
                               1, -1,
                               1, 0,
                               1, 1,
                               0, 1,
                               -1, 1]
    cdef float *inflow_angles = [0.0,
                                 7.0*PI/4.0,
                                 3.0*PI/2.0,
                                 5.0*PI/4.0,
                                 PI,
                                 3.0*PI/4.0,
                                 PI/2.0,
                                 PI/4.0]
    
    cdef int pi, pj, k, n, neighbor_index = 0
    for k in range(8):
        #alpha is the angle that flows from pixel pi, pj, to i, j
        alpha = inflow_angles[k]
        pi = i + shift_indexes[k*2+0]
        pj = j + shift_indexes[k*2+1]
        #LOGGER.debug('visiting pi pj %s %s' % (pi,pj))
        #ensure that the offsets are within bounds of the matrix
        if pi >= 0 and pj >= 0 and pi < flow_direction_matrix.shape[0] and \
            pj < flow_direction_matrix.shape[1]:
            #beta is the current outflow direction from pi,pj 
            beta = flow_direction_matrix[pi, pj]
            if beta == nodata_flow_direction:
                continue
            prop = -1 #initialize
            if abs(alpha-beta) < PI/4.0 or \
                (alpha == 0 and abs(2*PI-beta) < PI/4.0):
                neighbors[neighbor_index].i = pi
                neighbors[neighbor_index].j = pj

                #The proporation is 1-the proportion of beta pointing to alpha
                #if alpha == beta then prop == 1, otherwise it's less than 1
                #but greater than 0 because of the if statement guard above
                if alpha == 0 and beta > PI: alpha = 2*PI
                prop = 1-abs(alpha-beta)/(PI/4.0)
                neighbors[neighbor_index].prop = prop
                neighbor_index += 1
    #Placing a -1 in prop marks the end of the neighbor array
    neighbors[neighbor_index].prop = -1

cdef void d_p_area(CQueue pixels_to_process,
                   np.ndarray[np.float_t,ndim=2] accumulation_matrix,
                   np.ndarray[np.float_t,ndim=2] flow_direction_matrix,
                   int nodata_flow_direction, float nodata_flow_accumulation,
                   np.ndarray[np.float_t,ndim=2] dem_pixels):
    """Takes a list of pixels to calculate flow for the dinf algorithm, then
        does a dynamic style programming process of visiting and updating
        each one as it needs processing.  Modified `accumulation_matrix`
        during processing.
        
        pixels_to_process - a collections CQueue of i,j indexes to process.
            Popping i then j will give you the next pixel to process.  This
            queue will be modified and eventually returned empty as part of
            the calculation process.
            
        flow_direction_matrix - a numpy array input indicating the flow 
            direction at each pixel in radians.
            
        accumulation_matrix - a numpy array output of the flow accumulation
            along each pixel.  Must be the same dimensions as 
            flow_direction_matrix

        nodata_flow_direction - the value that can be used to determine if
            a pixel in flow_direction_matrix is a nodata value
            
        nodata_flow_accumulation - the value to assign to a pixel in 
            accumulation_matrix if a nodata value should go there.  Should
            correspond to a nodata value pixel in flow_direction_matrix

        dem_pixels - a matrix of DEM pixel heights, used to march the 
            algorithm from uphill to downhill"""
        
    cdef int i,j, ni, nj, runningSum, pi, pj, neighbor_index, \
        uncalculated_neighbors
    cdef float PI = 3.14159265, prop
    #cdef CQueue neighbors
    #This is an array of pairs that keeps track of i,j indexes and proportion
    #of flow to the inner cell.
    cdef NeighborFlow *neighbors = <NeighborFlow *>malloc(9 * sizeof(Pair))
    LOGGER = logging.getLogger('d_p_area')
    while pixels_to_process.size() > 0:
        i = pixels_to_process.pop()
        j = pixels_to_process.pop()
        #LOGGER.debug("working on pixel %s, %s, direction %s height %s" % (i,j, flow_direction_matrix[i, j]*180/PI, dem_pixels[i,j]))
        #LOGGER.debug("%s, %s, %s\n%s, %s, %s\n%s, %s, %s" % (dem_pixels[i-1,j+1],dem_pixels[i,j+1],dem_pixels[i+1,j+1],dem_pixels[i-1,j],dem_pixels[i,j],dem_pixels[i+1,j],dem_pixels[i-1,j-1],dem_pixels[i,j-1],dem_pixels[i+1,j-1]))
        #LOGGER.debug("rows col %s %s" % (dem_pixels.shape[0],dem_pixels.shape[1]))
        #LOGGER.debug("nodata flow direction %s\n " % (nodata_flow_direction))
        if flow_direction_matrix[i, j] == nodata_flow_direction:
            accumulation_matrix[i, j] = nodata_flow_accumulation
            continue

        #if pixel set, continue
        if accumulation_matrix[i, j] > 0: continue

        #build list of uncalculated neighbors
        calculate_inflow_neighbors_dinf(i,j, flow_direction_matrix, 
                                        nodata_flow_direction, neighbors)
        
        #mark visited
        accumulation_matrix[i, j] = 0
        
        #check to see if any of the neighbors were uncalculated, if so, 
        #calculate them
        neighbors_uncalculated = False
        #Visit each uncalculated neighbor and push on the work queue
        for neighbor_index in range(8):
            #-1 prop marks the end of the neighbor list
            if neighbors[neighbor_index].prop == -1: break 
            
            pi = neighbors[neighbor_index].i
            pj = neighbors[neighbor_index].j
            
            #see if neighbor is uncalculated
            if accumulation_matrix[pi, pj] == -1:
                #push the current pixel back on, note the indexes are in reverse
                #order so they can be popped off in order
                pixels_to_process.push(j)
                pixels_to_process.push(i)
                    
                pixels_to_process.push(pj)
                pixels_to_process.push(pi)
                neighbors_uncalculated = True
                break
        #this skips over the calculation of pixel i,j until neighbors 
        #are calculated
        if neighbors_uncalculated:
            continue 

        #If we get here then this pixel and its neighbors have been processed
        accumulation_matrix[i, j] = 1
        #Add contribution from each neighbor to current pixel 
        for neighbor_index in range(8):
            prop = neighbors[neighbor_index].prop
            if prop == -1: break 
            
            pi = neighbors[neighbor_index].i
            pj = neighbors[neighbor_index].j

            #calculate the contribution of pi,pj to i,j
            accumulation_matrix[i, j] += prop * accumulation_matrix[pi, pj]
            #LOGGER.debug("prop %s accumulation_matrix[i, j] = %s" % (prop, accumulation_matrix[i, j]))

def flow_accumulation_dinf(flow_direction, flow_accumulation, dem):
    """Creates a raster of accumulated flow to each cell.
    
        flow_direction - A raster showing direction of flow out of each cell
            with direcitonal values given in radians.
        flow_accumulation - The output flow accumulation raster set
        dem - heightmap raster for the area of interest
        
        returns nothing"""

    cdef int nodata_flow_direction, i, j
    cdef float nodata_flow_accumulation
    cdef CQueue q
    LOGGER = logging.getLogger('flow_accumulation_dinf')
    LOGGER.debug('initializing temporary buffers')
    #Load the input flow into a numpy array
    #GDal inverts x and y, so it's easier to transpose in and back out later
    #on gdal arrays, so we invert the x and y offsets here
    cdef np.ndarray[np.float_t,ndim=2] flow_direction_matrix = \
        flow_direction.GetRasterBand(1).ReadAsArray(0, 0,
        flow_direction.RasterXSize, flow_direction.RasterYSize).transpose().astype(np.float)
    cdef np.ndarray[np.float_t,ndim=2] dem_pixels  = \
        dem.GetRasterBand(1).ReadAsArray(0, 0,
        dem.RasterXSize, dem.RasterYSize).transpose().astype(np.float)
    nodata_flow_direction = flow_direction.GetRasterBand(1).GetNoDataValue()
    nodata_flow_accumulation = flow_accumulation.GetRasterBand(1).GetNoDataValue()
    nodata_dem = dem.GetRasterBand(1).GetNoDataValue()
    gp = flow_direction.GetGeoTransform()
    cellXSize = gp[1]
    cellYSize = gp[5]
    #Create the output flow, initialize to -1 as undefined
    idim, jdim = flow_direction_matrix.shape[0], flow_direction_matrix.shape[1]
    cdef np.ndarray[np.float_t,ndim=2] accumulation_matrix = \
        np.zeros([idim, jdim],dtype=np.float)
    cdef Pair *dem_pixel_pairs = \
        <Pair *>malloc(flow_direction.RasterXSize*flow_direction.RasterYSize * sizeof(Pair))
        
    #initalize to -2 to indicate no processing has occured.  This will change
    #to -1 to indicate it's been enqueued, and something else when value is
    #calculated
    accumulation_matrix[:] = -1

    LOGGER.info('calculating flow accumulation')

    #Construct a lookup table that sorts DEM pixels by height so we can process
    #the lowest pixels to the highest in propagating shortest path distances.
    valid_pixel_count = 0
    for i in range(idim):
        for j in range(jdim):
            h = dem_pixels[i,j]
            if h == nodata_dem:
                accumulation_matrix[i,j] = nodata_flow_accumulation 
                continue
            dem_pixel_pairs[valid_pixel_count].i = i
            dem_pixel_pairs[valid_pixel_count].j = j
            dem_pixel_pairs[valid_pixel_count].h = h
            valid_pixel_count += 1
    
    #Sort pixels by increasing height so that we visit drainage points in order
    qsort(dem_pixel_pairs,valid_pixel_count,sizeof(Pair),pairCompare)
    
    q = CQueue()
    for i in range(valid_pixel_count):
            if valid_pixel_count/100 != 0 and i % (valid_pixel_count/100) == 0:
                LOGGER.debug('percent complete %2.2f %%' % 
                             (100*(i+1.0)/valid_pixel_count))
            q.append(dem_pixel_pairs[i].i)
            q.append(dem_pixel_pairs[i].j)
            #LOGGER.debug('q size %s' %(q.size()))
            d_p_area(q,accumulation_matrix,flow_direction_matrix,
                          nodata_flow_direction, nodata_flow_accumulation,
                          dem_pixels)

    flow_accumulation.GetRasterBand(1).WriteArray(\
        accumulation_matrix.transpose(), 0, 0)
    invest_core.calculateRasterStats(flow_accumulation.GetRasterBand(1))
    
    free(dem_pixel_pairs)

def flow_direction_inf(dem, flow):
    """Calculates the D-infinity flow algorithm.  The output is a float
        raster whose values range from 0 to 2pi.
        Algorithm from: Tarboton, "A new method for the determination of flow
        directions and upslope areas in grid digital elevation models," Water
        Resources Research, vol. 33, no. 2, pages 309 - 319, February 1997.

       dem - (input) a single band raster with elevation values
       flow - (output) a single band float raster of same dimensions as
           dem.  After the function call it will have flow direction in it 
       
       returns nothing"""

    cdef int col_index, row_index, col_max, row_max, max_index, facet_index
    cdef double e_0, e_1, e_2, s_1, s_2, d_1, d_2, flow_direction, slope, \
        flow_direction_max_slope, slope_max, nodata_dem, nodata_flow

    nodata_dem = dem.GetRasterBand(1).GetNoDataValue()
    nodata_flow = flow.GetRasterBand(1).GetNoDataValue()

    #GDal inverts col_index and row_index, so it'slope easier to transpose in and 
    #back out later on gdal arrays, so we invert the col_index and row_index 
    #offsets here
    LOGGER.info("loading DEM")
    dem_matrix_tmp = dem.GetRasterBand(1).ReadAsArray(0, 0, dem.RasterXSize, 
                                         dem.RasterYSize).transpose()

    #Incoming matrix type could be anything numerical.  Cast to a floating
    #point for cython speed and because it'slope the most general form.
    cdef np.ndarray [np.float_t,ndim=2] dem_matrix = dem_matrix_tmp.astype(np.float)
    dem_matrix[:] = dem_matrix_tmp

    col_max, row_max = dem_matrix.shape[0], dem_matrix.shape[1]

    #This matrix holds the flow direction value, initialize to nodata_flow
    cdef np.ndarray [np.float_t,ndim=2] flow_matrix = np.empty([col_max, row_max], 
                                                               dtype=np.float)
    flow_matrix[:] = nodata_flow

    #facet elevation and factors for slope and flow_direction calculations 
    #from Table 1 in Tarboton 1997.  
    #THIS IS IMPORTANT:  The order is row (j), column (i), transposed to GDAL
    #convention.
    cdef int *e_0_offsets = [+0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0,
                             +0, +0]
    cdef int *e_1_offsets = [+0, +1,
                             -1, +0,
                             -1, +0,
                             +0, -1,
                             +0, -1,
                             +1, +0,
                             +1, +0,
                             +0, +1]
    cdef int *e_2_offsets = [-1, +1,
                             -1, +1,
                             -1, -1,
                             -1, -1,
                             +1, -1,
                             +1, -1,
                             +1, +1,
                             +1, +1]
    cdef int *a_c = [0, 1, 1, 2, 2, 3, 3, 4]
    cdef int *a_f = [1, -1, 1, -1, 1, -1, 1, -1]

    #Get pixel sizes
    d_1 = abs(dem.GetGeoTransform()[1])
    d_2 = abs(dem.GetGeoTransform()[5])

    LOGGER.info("calculating d-inf per pixel flows")
    #loop through each cell and skip any edge pixels
    for col_index in range(1, col_max - 1):
        for row_index in range(1, row_max - 1):

            #If we're on a nodata pixel, set the flow to nodata and skip
            if dem_matrix[col_index, row_index] == nodata_dem:
                flow_matrix[col_index, row_index] = nodata_flow
                continue

            #Calculate the flow flow_direction for each facet
            slope_max = 0 #use this to keep track of the maximum down-slope
            flow_direction_max_slope = 0 #flow direction on max downward slope
            max_index = 0 #index to keep track of max slope facet
            
            #Initialize flow matrix to nod_data flow so the default is to 
            #calculate with D8.
            flow_matrix[col_index, row_index] = nodata_flow
            
            for facet_index in range(8):
                #This defines the three height points
                e_0 = dem_matrix[e_0_offsets[facet_index*2+1] + col_index,
                                 e_0_offsets[facet_index*2+0] + row_index]
                e_1 = dem_matrix[e_1_offsets[facet_index*2+1] + col_index,
                                 e_1_offsets[facet_index*2+0] + row_index]
                e_2 = dem_matrix[e_2_offsets[facet_index*2+1] + col_index,
                                 e_2_offsets[facet_index*2+0] + row_index]
                
                #LOGGER.debug('facet %s' % (facet_index+1))
                #LOGGER.debug('e_1_offsets %s %s' %(e_1_offsets[facet_index*2+1],
                #                                   e_1_offsets[facet_index*2+0]))
                #LOGGER.debug('e_0 %s e_1 %s e_2 %s' % (e_0, e_1, e_2))
                
                #avoid calculating a slope on nodata values
                if e_1 == nodata_dem or e_2 == nodata_dem: 
                    break #fallthrough to D8
                 
                #s_1 is slope along straight edge
                s_1 = (e_0 - e_1) / d_1 #Eqn 1
                
                #slope along diagonal edge
                s_2 = (e_1 - e_2) / d_2 #Eqn 2
                
                if s_1 <= 0 and s_2 <= 0:
                    #uphill slope or flat, so skip, D8 resolve 
                    continue 
                
                #Default to pi/2 in case s_1 = 0 to avoid divide by zero cases
                flow_direction = 3.14159262/2.0
                if s_1 != 0:
                    flow_direction = atan(s_2 / s_1) #Eqn 3

                if flow_direction < 0: #Eqn 4
                    #LOGGER.debug("flow direciton negative")
                    #If the flow direction goes off one side, set flow
                    #direction to that side and the slope to the straight line
                    #distance slope
                    flow_direction = 0
                    slope = s_1
                    #LOGGER.debug("flow direction < 0 slope=%s"%slope)
                elif flow_direction > atan(d_2 / d_1): #Eqn 5
                    #LOGGER.debug("flow direciton greater than 45 degrees")
                    #If the flow direciton goes off the diagonal side, figure
                    #out what its value is and
                    flow_direction = atan(d_2 / d_1)
                    slope = (e_0 - e_2) / sqrt(d_1 ** 2 + d_2 ** 2)
                    #LOGGER.debug("flow direction > 45 slope=%s"%slope)
                else:
                    #LOGGER.debug("flow direciton in bounds")
                    slope = sqrt(s_1 ** 2 + s_2 ** 2) #Eqn 3
                    #LOGGER.debug("flow direction in middle slope=%s"%slope)

                #LOGGER.debug("slope %s" % slope)
                if slope > slope_max:
                    flow_direction_max_slope = flow_direction
                    slope_max = slope
                    max_index = facet_index
            else: 
                # This is the fallthrough condition for the for loop, we reach
                # it only if we haven't encountered an invalid slope or pixel
                # that caused the above algorithm to break out
                 
                #Calculate the global angle depending on the max slope facet
                #LOGGER.debug("slope_max %s" % slope_max)
                #LOGGER.debug("max_index %s" % (max_index+1))
                if slope_max > 0:
                    flow_matrix[col_index, row_index] = \
                        a_f[max_index] * flow_direction_max_slope + \
                        a_c[max_index] * 3.14159265 / 2.0

    #Calculate D8 flow to resolve undefined flows in D-inf
    d8_flow_dataset = newRasterFromBase(flow, '', 'MEM', -5.0, gdal.GDT_Float32)
    LOGGER.info("calculating D8 flow")
    flowDirectionD8(dem, d8_flow_dataset)
    d8_flow_matrix = d8_flow_dataset.ReadAsArray(0, 0, dem.RasterXSize, 
                                    dem.RasterYSize).transpose()
    
    nodata_d8 = d8_flow_dataset.GetRasterBand(1).GetNoDataValue()

    d8_to_radians = {0: -1.0,
                     1: 0.0,
                     2: 5.497787144,
                     4: 4.71238898,
                     8: 3.926990817,
                     16: 3.141592654,
                     32: 2.35619449,
                     64: 1.570796327,
                     128: 0.785398163,
                     nodata_d8: nodata_flow
                     }
    
    for col_index in range(1, col_max - 1):
        for row_index in range(1, row_max - 1):
            if flow_matrix[col_index, row_index] == nodata_flow:
                flow_matrix[col_index, row_index] = \
                    d8_to_radians[d8_flow_matrix[col_index, row_index]]

    LOGGER.info("writing flow data to raster")
    flow.GetRasterBand(1).WriteArray(flow_matrix.transpose(), 0, 0)
    invest_core.calculateRasterStats(flow.GetRasterBand(1))

def calculate_slope(dem, slope):
    """Generates raster maps of slope.  Follows the algorithm described here:
        http://webhelp.esri.com/arcgiSDEsktop/9.3/index.cfm?TopicName=How%20Slope%20works 
        
        dem - (input) a single band raster of z values.  z units should be identical
            to ground units.
        slope - (modified output) a single band raster of the same dimensions 
            as dem whose elements are percent rise
            
        returns nothing"""

    LOGGER = logging.getLogger('calculateSlope')
    #Read the DEM directly into an array
    demBand = dem.GetRasterBand(1)
    demBandMatrix = demBand.ReadAsArray(0, 0, demBand.XSize, demBand.YSize)
    LOGGER.debug('demBandMatrix size %s' % (demBandMatrix.size))

    #Create an empty slope matrix
    slopeMatrix = np.empty((demBand.YSize, demBand.XSize))
    LOGGER.debug('slopeMatrix size %s' % (slopeMatrix.size))

    gp = dem.GetGeoTransform()
    cellXSize = gp[1]
    cellYSize = gp[5]
    nodata = demBand.GetNoDataValue()
    LOGGER.info('starting pixelwise slope calculation')

    LOGGER.debug('building kernels')
    #Got idea for this from this thread http://stackoverflow.com/q/8174467/42897
    dzdyKernel = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float64)
    dzdxKernel = dzdyKernel.transpose().copy()
    dzdyKernel /= (8 * cellYSize)
    dzdxKernel /= (8 * cellXSize)

    LOGGER.debug('doing convolution')
    dzdx = scipy.signal.convolve2d(demBandMatrix, dzdxKernel, 'same')
    dzdy = scipy.signal.convolve2d(demBandMatrix, dzdyKernel, 'same')
    slopeMatrix = np.sqrt(dzdx ** 2 + dzdy ** 2)

    #Now, "nodata" out the points that used nodata from the demBandMatrix
    noDataIndex = demBandMatrix == nodata
    LOGGER.debug('slopeMatrix and noDataIndex shape %s %s' %
                 (slopeMatrix.shape, noDataIndex.shape))
    slopeMatrix[noDataIndex] = -1

    offsets = [(1, 1), (0, 1), (-1, 1), (1, 0), (-1, 0), (1, -1), (0, -1),
               (-1, -1)]
    for offset in offsets:
        slopeMatrix[shiftMatrix(noDataIndex, *offset)] = slope.GetRasterBand(1).GetNoDataValue()

    slope.GetRasterBand(1).WriteArray(slopeMatrix,0,0)
    invest_core.calculateRasterStats(slope.GetRasterBand(1))

def calculate_ls_factor(upslope_area, slope_raster, aspect, ls_factor,
    slope_threshold = 0.075):
    """Calculates the LS factor as Equation 3 from "Extension and validation 
        of a geographic information system-based method for calculating the
        Revised Universal Soil Loss Equation length-slope factor for erosion
        risk assessments in large watersheds"   
        
        (Required that all raster inputs are same dimensions and projections
        and have square cells)
        upslope_area - a single band raster of type float that indicates
            the contributing area at the inlet of a grid cell
        slope_raster - a single band raster of type float that indicates
            the slope at a pixel given as a proportion (e.g. a value of 0.05
            is a slope of 5%)
        aspect - a single band raster of type float that indicates the 
            direction that slopes are facing in terms of radians east and
            increase clockwise: pi/2 is north, pi is west, 3pi/2, south and 
            0 or 2pi is east.
        ls_factor - (modified output) a single band raster dataset that will
            have the per-pixel ls factor written to it
        slope_threshold - the cutoff for areas that the LS factor should be
            calcualted with the Huan and Lu formula from the InVEST 2.2.0 user's
            guide 
            
        returns a raster of the same dimensions as inputs whose elements """
    
    cdef int nrows = upslope_area.RasterXSize, \
             ncols = upslope_area.RasterYSize, \
             row_index, col_index
    
    #Assumes that cells are square
    cdef float cell_size = abs(upslope_area.GetGeoTransform()[1])
    cdef float cell_area = cell_size ** 2
    cdef float m, alpha, beta, xij, contributing_area
    cdef float PI = 3.14159265 
    
    #Tease out all the nodata values for reading and setting
    cdef float upslope_nodata = upslope_area.GetRasterBand(1).GetNoDataValue()
    cdef float slope_nodata = slope_raster.GetRasterBand(1).GetNoDataValue()
    cdef float aspect_nodata = aspect.GetRasterBand(1).GetNoDataValue()
    cdef float ls_nodata = ls_factor.GetRasterBand(1).GetNoDataValue()
    
    cdef np.ndarray [np.float_t,ndim=2] upslope_area_matrix = \
        upslope_area.GetRasterBand(1).ReadAsArray(0, 0, \
        nrows,ncols).transpose().astype(np.float)
        
    cdef np.ndarray [np.float_t,ndim=2] slope_matrix = \
        slope_raster.GetRasterBand(1).ReadAsArray(0, 0, \
        nrows,ncols).transpose().astype(np.float)
        
    cdef np.ndarray [np.float_t,ndim=2] aspect_matrix = \
        aspect.GetRasterBand(1).ReadAsArray(0, 0, \
        nrows, ncols).transpose().astype(np.float)
        
    cdef np.ndarray [np.float_t,ndim=2] ls_factor_matrix = \
        np.zeros((nrows,ncols))
        
    for row_index in range(1,nrows-1):
        LOGGER.debug('row_index %s' % row_index)
        for col_index in range(1,ncols-1):
            #Set the nodata bounds first
            if aspect_matrix[row_index, col_index] == aspect_nodata or \
                slope_matrix[row_index, col_index] == slope_nodata or \
                upslope_area_matrix[row_index, col_index] == upslope_nodata:
                ls_factor_matrix[row_index,col_index] = ls_nodata
                continue
                
            alpha = aspect_matrix[row_index, col_index]
            xij = abs(sin(alpha)+ cos(alpha))
            
            contributing_area = \
                (upslope_area_matrix[row_index,col_index]-1) * cell_area

            #A placeholder for simplified slope stuff
            slope = slope_matrix[row_index, col_index]
            slope_in_radians = atan(slope)
            
            #From Equation 4 in "Extension and validataion of a geographic 
            #information system ..."
            if slope < 0.09:
                slope_factor =  10.8*sin(slope_in_radians)+0.03
            else:
                slope_factor =  16.8*sin(slope_in_radians)-0.5
            
            #Set the m value to the lookup table that's from Yonas's handwritten
            #notes.  On the margin it says "Equation 15".  Don't know from
            #where.
            beta = (sin(slope_in_radians) / 0.0896) / \
                   (3*pow(sin(slope_in_radians),0.8)+0.56)
            slope_table = [0.01, 0.035, 0.05, 0.09]
            exponent_table = [0.2, 0.3, 0.4, 0.5, beta/(1+beta)]
            
            #Use the bisect function to do a nifty range 
            #lookup. http://docs.python.org/library/bisect.html#other-examples
            m = exponent_table[bisect.bisect(slope_table,slope)]
            
            #The length part of the ls_factor:
            ls_factor_matrix[row_index,col_index] = \
                ((contributing_area+cell_area)**(m+1)-
                 contributing_area**(m+1)) / \
                ((cell_size**(m+2))*(xij**m)*(22.13**m))

            #From the paper "as a final check against exessively long slope
            #length calculations ... cap of 333m"
            if ls_factor_matrix[row_index,col_index] > 333:
                ls_factor_matrix[row_index,col_index] = 333
                
            ls_factor_matrix[row_index,col_index] *= slope_factor

    ls_factor.GetRasterBand(1).WriteArray(ls_factor_matrix.transpose(),0,0)
    invest_core.calculateRasterStats(ls_factor.GetRasterBand(1))
