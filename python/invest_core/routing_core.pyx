"""This module contains general purpose geoprocessing functions useful for
    the InVEST toolset"""

import numpy as np
import math
from osgeo import gdal, osr
import logging
from collections import deque
logger = logging.getLogger('invest_core')

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
        #neighborElevation = shiftMatrix(demMatrix, *shiftIndexes[dir])

        #Search for areas where the neighbor elevations are equal to the current
        #this will indicate a flat region that needs to be cleaned up later
        #In those cases, add the direciton to the flow matrix since there are
        #multiple possible flow directions
        #equalElevationIndexes = neighborElevation == lowest
        #lowest[equalElevationIndexes] = neighborElevation[equalElevationIndexes]
        #flowMatrix[equalElevationIndexes] = flowMatrix[equalElevationIndexes] + dir

        #Next indicate all the pixels where the neighbor pixel is lower than
        #the lowest seen so far
        #lowerIndex = neighborElevation < lowest

        #Update the lowest elevation seen so far
        #lowest[lowerIndex] = neighborElevation[lowerIndex]
        #and update the flow to point in the direction of that pixel
        #flowMatrix[lowerIndex] = dir

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
            #logger.debug('i,j=%s %s x,y=%s %s' % (i, j, gp[0] + cellXSize * i,
            #                                      gp[3] + cellYSize * j))
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

