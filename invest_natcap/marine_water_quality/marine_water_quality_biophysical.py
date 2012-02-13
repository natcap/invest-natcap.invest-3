"""InVEST Marine Water Quality Biophysical module at the "uri" level"""

import sys
import os
import logging

from osgeo import gdal
from osgeo import ogr
import simplejson as json
import scipy.sparse.linalg
from scipy.sparse.linalg import spsolve
import numpy as np
import time
import matplotlib
import scipy.linalg
import math


logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

logger = logging.getLogger('marine_water_quality')

def water_quality(n, m, in_water, E, ux, uy, k_matrix, s0, h, directSolve=False):
    """2D Water quality model to track a pollutant in the ocean
    
    Keyword arguments:
    n,m -- the number of rows, columns in the 2D grid.  Used to determine 
        indices into list parameters 'water', 'E', 'ux', 'uy', and 'k_matrix' i*m+j in
        a list
    water -- 1D list n*m elements long of booleans indicating land/water.  True
            is water, False is land.  
    E -- 1D list n*m elements long of dispersion coefficients
    ux -- 1D list n*m elements long of x component velocity vectors
    uy -- 1D list n*m elements long y component velocity vectors
    k_matrix -- 1D list n*m elements long of decay coefficients
    s0 -- map of sourceIndex to pollutant density
    h -- scalar describing grid cell size
    directSolve -- if True uses a direct solver that may be faster, but use
        more memory.  May crash in cases where memory is fragmented or low
        Default False.
    
    returns a 2D grid of pollutant densities in the same dimension as  'grid'
    
    """

    print 'initialize ...',
    t0 = time.clock()

    #used to abstract the 2D to 1D index calculation below
    def calc_index(i, j):
        if i >= 0 and i < n and j >= 0 and j < m:
            return i * m + j
        else:
            return -1

    #set up variables to hold the sparse system of equations
    #upper bound  n*m*5 elements
    b_vector = np.zeros(n * m)
    #holds the columns for diagonal sparse matrix creation later
    a_matrix = np.zeros((5, n * m))

    print '(' + str(time.clock() - t0) + 's elapsed)'
    t0 = time.clock()

    #iterate over the non-zero elments in grid to build the linear system
    print 'building system a_matrix...',
    t0 = time.clock()
    for i in range(n):
        for j in range(m):
            #diagonal element i,j always in bounds, calculate directly
            row_index = calc_index(i, j)

            #if land then s = 0 and quit
            if not in_water[row_index]:
                a_matrix[2, row_index] = 1
                continue

            #formulate elements as a single array
            term_a = 2 * E[row_index]
            ux_tmp = ux[row_index] * h
            uy_tmp = uy[row_index] * h

            elements = [
             (2, 0, row_index, -4.0 * (term_a + h * h * k_matrix[row_index])),
             (4, m, calc_index(i + 1, j), term_a - uy_tmp),
             (0, -m, calc_index(i - 1, j), term_a + uy_tmp),
             (3, 1, calc_index(i, j + 1), term_a - ux_tmp),
             (1, -1, calc_index(i, j - 1), term_a + ux_tmp)]

            for k, offset, colIndex, term in elements:
                if colIndex >= 0: #make sure we're in the grid
                    if in_water[colIndex]: #if water
                        a_matrix[k, row_index + offset] += term
                    else:
                        #handle the land boundary case s_ij' = s_ij
                        a_matrix[2, row_index] += term

    #define sources by erasing the rows in the matrix that have already been set
    for row_index in s0:
        #the magic numbers are the diagonals and their offsets due to gridsize
        for i, offset in [(4, m), (0, -m), (3, 1), (1, -1)]:
            #zero out that row
            a_matrix[i, row_index + offset] = 0
        a_matrix[2, row_index] = 1
        b_vector[row_index] = s0[row_index]
    print '(' + str(time.clock() - t0) + 's elapsed)'

    print 'building sparse matrix ...',
    t0 = time.clock()
    matrix = spdiags(a_matrix, [-m, -1, 0, 1, m], n * m, n * m, "csc")
    print '(' + str(time.clock() - t0) + 's elapsed)'

    if directSolve:
        t0 = time.clock()
        print 'direct solving ...',
        result = spsolve(matrix, b_vector)
    else:
        print 'generating preconditioner via sparse ilu ',
        #normally factor will use m*(n*m) extra space, we restrict to 
        #\sqrt{m}*(n*m) extra space
        P = scipy.sparse.linalg.spilu(matrix, fill_factor=int(math.sqrt(m)))
        print '(' + str(time.clock() - t0) + 's elapsed)'
        t0 = time.clock()
        print 'gmres iteration starting ',
        #create linear operator for precondioner
        M_x = lambda x: P.solve(x)
        M = scipy.sparse.linalg.LinearOperator((n * m, n * m), M_x)
        result = scipy.sparse.linalg.lgmres(matrix, b_vector, tol=1e-5, M=M)[0]
    print '(' + str(time.clock() - t0) + 's elapsed)'
    return result

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':
    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
