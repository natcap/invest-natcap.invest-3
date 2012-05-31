"""InVEST Marine Water Quality Biophysical module at the "uri" level"""

import sys
import logging
import re
import os
import time
import math
import csv

from osgeo import ogr
from osgeo import gdal
import scipy.sparse.linalg
from scipy.sparse.linalg import spsolve
import numpy as np
from numpy.ma import masked_array
import scipy.linalg
import pylab

from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('marine_water_quality_biophysical')

def execute(args):
    """Main entry point for the InVEST 3.0 marine water quality 
        biophysical model.

        args - dictionary of string value pairs for input to this model.
        args['workspace'] - output directory.
        args['aoi_poly_uri'] - OGR polygon Datasource indicating region
            of interest to run the model.  Will define the grid.
        args['pixel_size'] - float indicating pixel size in meters
            of output grid.
        args['land_poly_uri'] - OGR polygon DataSource indicating areas where land
            is.
        args['source_points_uri'] - OGR point Datasource indicating point sources
            of pollution.
        args['source_point_data_uri'] - csv file indicating the biophysical
            properties of the point sources.
        args['tide_e_points_uri'] - OGR point Datasource with spatial information 
            about the E parameter
        args['adv_uv_points_uri'] - OGR point Datasource with spatial advection
            u and v vectors."""

    LOGGER.info("Starting MWQ execute")
    aoi_poly = ogr.Open(args['aoi_poly_uri'])
    land_poly = ogr.Open(args['land_poly_uri'])
    land_layer = land_poly.GetLayer()
    source_points = ogr.Open(args['source_points_uri'])
    tide_e_points = ogr.Open(args['tide_e_points_uri'])
    adv_uv_points = ogr.Open(args['adv_uv_points_uri'])

    #Create a grid based on the AOI
    LOGGER.info("Creating grid based on the AOI polygon")
    pixel_size = args['pixel_size']
    #the nodata value will be a min float
    nodata_out = float(np.finfo(np.float32).min)
    raster_out_uri = os.path.join(args['workspace'],'concentration.tif')
    raster_out = raster_utils.create_raster_from_vector_extents(pixel_size, 
        pixel_size, gdal.GDT_Float32, nodata_out, raster_out_uri, aoi_poly)
    
    #create a temporary grid of interpolated points for tide_e and adv_uv
    LOGGER.info("Creating grids for the interpolated tide E and ADV uv points")
    tide_e_raster = raster_utils.new_raster_from_base(raster_out, 'tide_e.tif', 
        'GTiff', nodata_out, gdal.GDT_Float32)
    adv_u_raster = raster_utils.new_raster_from_base(raster_out, 'adv_u.tif',
        'GTiff', nodata_out, gdal.GDT_Float32)
    adv_v_raster = raster_utils.new_raster_from_base(raster_out, 'adv_v.tif',
        'GTiff', nodata_out, gdal.GDT_Float32)

    #Interpolate the ogr datasource points onto a raster the same size as raster_out
    raster_utils.vectorize_points(tide_e_points, 'kh_km2_day', tide_e_raster)
    raster_utils.vectorize_points(adv_uv_points, 'U_m_sec_', adv_u_raster)
    raster_utils.vectorize_points(adv_uv_points, 'V_m_sec_', adv_v_raster)

    #Mask the interpolated points to the land polygon
    LOGGER.info("Masking Tide E and ADV UV to the land polygon")
    for dataset in [tide_e_raster, adv_u_raster, adv_v_raster]:
        band = dataset.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        gdal.RasterizeLayer(dataset,[1], land_layer, burn_values=[nodata])

    #Now we have 3 input rasters for tidal dispersion and uv advection
    LOGGER.info("Load the point sources")
    source_layer = source_points.GetLayer()
    aoi_layer = aoi_poly.GetLayer()
    aoi_polygon = aoi_layer.GetFeature(0)
    aoi_geometry = aoi_polygon.GetGeometryRef()
    source_point_list = []
    for point_feature in source_layer:
        point_geometry = point_feature.GetGeometryRef()
        if aoi_geometry.Contains(point_geometry):
            point = point_geometry.GetPoint()
            point_id = point_feature.GetField('id')
            LOGGER.debug("point and id %s %s" % (point,point_id))
            #Appending point geometry with y first so it can be converted
            #to the numpy (row,col) 2D notation easily.
            source_point_list.append([point[1],point[0]])

    #Project source point y,x to row, col notation for the output array.

    #Load the point source data CSV file.
    point_source_values = {}
    csv_file = open(args['source_point_data_uri'])
    reader = csv.DictReader(csv_file)
    for row in reader:
        point_source_values[int(row['ID'])] = {
            'KPS': float(row['KPS']),
            'WPS': float(row['WPS'])}

    LOGGER.debug(point_source_values)
    LOGGER.info("Solving advection/diffusion equation")

    LOGGER.info("Done with MWQ execute")


def marine_water_quality(n, m, in_water, E, ux, uy, point_source, h,
                         direct_solve=False):
    """2D Water quality model to track a pollutant in the ocean
    
    Keyword arguments:
    n, m - the number of rows, columns in the 2D grid.  Used to determine
        indices into list parameters 'water', 'E', 'ux', 'uy', and i * m + j in
        a list
    water - 1D list n * m elements long of booleans indicating land / water.
        True is water, False is land.
    E - constant indicating tidal dispersion coefficient: km ^ 2 / day
    ux - constant indicating x component of advective velocity: m / s
    uy - constant indicating y component of advective velocity: m / s
    point_source - dictionary of (xps, yps, wps, kps, id) for the point source,
        xps, yps: cartesian coordinates of point wps: kg / day, k: 1 / day.
    h - scalar describing grid cell size: m
    direct_solve - if True uses a direct solver that may be faster, but use
        more memory.  May crash in cases where memory is fragmented or low
        Default False.
    
    returns a 2D grid of pollutant densities in the same dimension as  'grid'
    """
    LOGGER = logging.getLogger('marine_water_quality')
    LOGGER.info('Calculating advection diffusion for %s' % \
                (point_source['id']))
    t0 = time.clock()

    #convert E from km^2/day to m^2/sec
    E *= 10 ** 6 / 86400.0

    def calc_index(i, j):
        """used to abstract the 2D to 1D index calculation below"""
        if i >= 0 and i < n and j >= 0 and j < m:
            return i * m + j
        else:
            return -1

    #convert point x,y to an index that coodinates with input arrays
    point_index = calc_index(int(point_source['yps'] / h),
                             int(point_source['xps'] / h))

    #Absorption parameter
    k = point_source['kps']

    #Convert h to km for calculation since other parameters are in KM
    h /= 1000.0

    #set up variables to hold the sparse system of equations
    #upper bound  n*m*5 elements
    b_vector = np.zeros(n * m)

    #holds the rows for diagonal sparse matrix creation later, row 4 is 
    #the diagonal
    a_matrix = np.zeros((9, n * m))
    diags = np.array([-2 * m, -m, -2, -1, 0, 1, 2, m, 2 * m])


    #iterate over the non-zero elments in grid to build the linear system
    LOGGER.info('Building diagonals for linear advection diffusion system.')
    for i in range(n):
        for j in range(m):
            #diagonal element i,j always in bounds, calculate directly
            a_diagonal_index = calc_index(i, j)
            a_up_index = calc_index(i - 1, j)
            a_down_index = calc_index(i + 1, j)
            a_left_index = calc_index(i, j - 1)
            a_right_index = calc_index(i, j + 1)


            #if land then s = 0 and quit
            if not in_water[a_diagonal_index]:
                a_matrix[4, a_diagonal_index] = 1
                continue

            if point_index == a_diagonal_index:
                a_matrix[4, point_index] = 1
                b_vector[point_index] = point_source['wps']
                continue

            #Build up terms
            #Ey
            if a_up_index > 0 and a_down_index > 0 and \
                in_water[a_up_index] and in_water[a_down_index]:
                #Ey
                a_matrix[4, a_diagonal_index] += -2.0 * E / h ** 2
                a_matrix[7, a_down_index] += E / h ** 2
                a_matrix[1, a_up_index] += E / h ** 2

                #Uy
                a_matrix[7, a_down_index] += uy / (2.0 * h)
                a_matrix[1, a_up_index] += -uy / (2.0 * h)
            if a_up_index < 0 and in_water[a_down_index]:
                #we're at the top boundary, forward expansion down
                #Ey
                a_matrix[4, a_diagonal_index] += -E / h ** 2
                a_matrix[7, a_down_index] += E / h ** 2

                #Uy
                a_matrix[7, a_down_index] += uy / (2.0 * h)
                a_matrix[4, a_diagonal_index] += -uy / (2.0 * h)
            if a_down_index < 0 and in_water[a_up_index]:
                #we're at the bottom boundary, forward expansion up
                #Ey
                a_matrix[4, a_diagonal_index] += -E / h ** 2
                a_matrix[1, a_up_index] += E / h ** 2

                #Uy
                a_matrix[1, a_up_index] += uy / (2.0 * h)
                a_matrix[4, a_diagonal_index] += -uy / (2.0 * h)
            if not in_water[a_up_index]:
                #Ey
                a_matrix[4, a_diagonal_index] += -2.0 * E / h ** 2
                a_matrix[7, a_down_index] += E / h ** 2

                #Uy
                a_matrix[7, a_down_index] += uy / (2.0 * h)
            if not in_water[a_down_index]:
                #Ey
                a_matrix[4, a_diagonal_index] += -2.0 * E / h ** 2
                a_matrix[1, a_up_index] += E / h ** 2

                #Uy
                a_matrix[1, a_up_index] += -uy / (2.0 * h)



            if a_left_index > 0 and a_right_index > 0 and \
                in_water[a_left_index] and in_water[a_right_index]:
                #Ex
                a_matrix[4, a_diagonal_index] += -2.0 * E / h ** 2
                a_matrix[5, a_right_index] += E / h ** 2
                a_matrix[3, a_left_index] += E / h ** 2

                #Ux
                a_matrix[5, a_right_index] += ux / (2.0 * h)
                a_matrix[3, a_left_index] += -ux / (2.0 * h)
            if a_left_index < 0 and in_water[a_right_index]:
                #we're on left boundary, expand right
                #Ex
                a_matrix[4, a_diagonal_index] += -E / h ** 2
                a_matrix[5, a_right_index] += E / h ** 2

                a_matrix[5, a_right_index] += ux / (2.0 * h)
                a_matrix[4, a_diagonal_index] += -ux / (2.0 * h)
                #Ux
            if a_right_index < 0 and in_water[a_left_index]:
                #we're on right boundary, expand left
                #Ex
                a_matrix[4, a_diagonal_index] += -E / h ** 2
                a_matrix[3, a_left_index] += E / h ** 2

                #Ux
                a_matrix[3, a_left_index] += ux / (2.0 * h)
                a_matrix[4, a_diagonal_index] += -ux / (2.0 * h)

            if not in_water[a_right_index]:
                #Ex
                a_matrix[4, a_diagonal_index] += -2.0 * E / h ** 2
                a_matrix[3, a_left_index] += E / h ** 2

                #Ux
                a_matrix[3, a_left_index] += -ux / (2.0 * h)

            if not in_water[a_left_index]:
                #Ex
                a_matrix[4, a_diagonal_index] += -2.0 * E / h ** 2
                a_matrix[5, a_right_index] += E / h ** 2

                #Ux
                a_matrix[5, a_right_index] += ux / (2.0 * h)

            #K
            a_matrix[4, a_diagonal_index] += -k

            if not in_water[a_up_index]:
                a_matrix[1, a_up_index] = 0
            if not in_water[a_down_index]:
                a_matrix[7, a_down_index] = 0
            if not in_water[a_left_index]:
                a_matrix[3, a_left_index] = 0
            if not in_water[a_right_index]:
                a_matrix[5, a_right_index] = 0

    LOGGER.info('Building sparse matrix from diagonals.')

    matrix = scipy.sparse.spdiags(a_matrix,
        [-2 * m, -m, -2, -1, 0, 1, 2, m, 2 * m], n * m, n * m, "csc")
    LOGGER.info('generating preconditioner via sparse incomplete lu decomposition')
    #normally factor will use m*(n*m) extra space, we restrict to 
    #\sqrt{m}*(n*m) extra space
    P = scipy.sparse.linalg.spilu(matrix, fill_factor=int(math.sqrt(m)))
    LOGGER.info('Solving via gmres iteration')
    #create linear operator for precondioner
    M_x = lambda x: P.solve(x)
    M = scipy.sparse.linalg.LinearOperator((n * m, n * m), M_x)
    result = scipy.sparse.linalg.lgmres(matrix, b_vector, tol=1e-5, M=M)[0]
    LOGGER.info('(' + str(time.clock() - t0) + 's elapsed and done for %s)' % \
                (point_source['id']))
    return result

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError("Wrong amount of command line arguments.\nUsage: \
python % s landarray_filename parameter_filename" % (sys.argv[0]))
    MODULENAME, LANDARRAY_FILENAME, PARAMETER_FILENAME = sys.argv

    #parse land array into a 1D array of booleans
    #input file is of the form '1\t0\r\n...' 1's are True, 0's are False and
    #separator characters are removed.  The \r comes from a DOS newline, will
    #be ignored if a Unix based file.
    LAND_FILE = open(LANDARRAY_FILENAME)
    LAND_STRING = LAND_FILE.read()
    N_ROWS = LAND_STRING.count('\n')

    #Remove any instances of spacing characters
    IN_WATER = map(lambda x: x == '1', re.sub('[\n\t\r, ]', '', LAND_STRING))
    N_COLS = len(IN_WATER) / N_ROWS
    #parse WQM file
    #Initialize variables that need to get set.  Putting None here so if they
    #don't get parsed correctly something will crash.
    U0 = None
    V0 = None
    E = None
    H = None
    VMIN = None
    VMAX = None
    #List of tubples of (index, WPS, KPS, CPS)
    POINT_SOURCES = []

    HYDRODYNAMIC_HEADER = re.compile('C1 +U0 +V0 +E +H')
    POINT_SOURCE_HEADER = re.compile('C2-1 +NPS')
    DISPLAY_HEADER = re.compile('C3 +VMIN +VMAX')
    OUTFILE_HEADER = re.compile('C4 OUTPUT FILE NAME')

    PARAMETER_FILE = open(PARAMETER_FILENAME)
    while True:
        line = PARAMETER_FILE.readline()
        if line == '': break #end of file
        if HYDRODYNAMIC_HEADER.match(line):
            #Next line will be hydrodynamic characteristics
            line = PARAMETER_FILE.readline()
            U0, V0, E, H = map(float, line.split())
        if POINT_SOURCE_HEADER.match(line):
            steps = int(PARAMETER_FILE.readline())
            PARAMETER_FILE.readline() #read C2-2 header garbage
            for step_number in range(steps):
                point_parameters = PARAMETER_FILE.readline().split()
                POINT_SOURCES.append((int(point_parameters[0]),
                                     int(point_parameters[1]),
                                     int(point_parameters[2]),
                                     float(point_parameters[3]),
                                     point_parameters[4]))
        if DISPLAY_HEADER.match(line):
            #Next line will be hydrodynamic characteristics
            line = PARAMETER_FILE.readline()
            VMIN, VMAX = map(float, line.split())
        if OUTFILE_HEADER.match(line):
            line = PARAMETER_FILE.readline()
            OUTFILE_NAME = line.split('"')[1]

    density = np.zeros(N_ROWS * N_COLS)
    POINT_COUNT = 1
    for xps, yps, wps, kps, id in POINT_SOURCES:
        LOGGER.info('Processing point %s of %s' % (POINT_COUNT,
                                                   len(POINT_SOURCES)))
        POINT_COUNT += 1
        point_source = {'xps': xps,
                        'yps': yps,
                        'wps': wps,
                        'kps': kps,
                        'id': id}
        density += marine_water_quality(N_ROWS, N_COLS, IN_WATER, E, U0, V0,
                                       point_source, H)

    LOGGER.info("Done with point source diffusion.  Now plotting.")
    density = np.resize(density, (N_ROWS, N_COLS))
    np.savetxt(OUTFILE_NAME, density, delimiter=',')
    IN_WATER = np.resize(IN_WATER, (N_ROWS, N_COLS))

    axes = pylab.subplot(111)
    #Plot the pollutant density
    COLORMAP = pylab.cm.gist_earth
    COLORMAP.set_over(color='#330000')
    COLORMAP.set_under(color='#330000')
    axis_extent = [0, H * N_COLS, 0, H * N_ROWS]
    pylab.imshow(density,
                 interpolation='nearest',
                 cmap=COLORMAP,
                 vmin=VMIN,
                 vmax=VMAX,
                 origin='lower',
                 extent=axis_extent)

    pylab.colorbar()

    #Plot the land by masking out water regions.  In non-water
    #regions the data values will be 0, so okay to use PuOr to have
    #an orangy land.  pylab doesn't behave well if the mask is all 
    #True, so we check to see if its false first.
    if False in IN_WATER:
        pylab.hold(True)
        pylab.imshow(masked_array(data=density, mask=(IN_WATER)),
                     interpolation = 'nearest',
                     cmap=pylab.cm.PuOr,
                     origin='lower',
                     extent=axis_extent)

    #This is for a handy overlap graph mouse explorer on the plot.
    class Cursor:
        def __init__(self, ax):
            self.ax = ax
            self.lx = ax.axhline(color='w')  # the horiz line
            self.ly = ax.axvline(color='w')  # the vert line

            # text location in axes coords
            self.txt = ax.text(0.7, 0.9, '', transform=ax.transAxes, color='w')

        def mouse_move(self, event):
            if not event.inaxes: return

            x, y = event.xdata, event.ydata
            # update the line positions
            self.lx.set_ydata(y)
            self.ly.set_xdata(x)

            #This section does a translation from axis coordinates to the 
            #index values in the density array.
            index_x = int((x - axis_extent[0]) / (axis_extent[1] -
                                                  axis_extent[0]) * N_COLS)
            index_y = int((y - axis_extent[2]) / (axis_extent[3] -
                                                  axis_extent[2]) * N_ROWS)
            try:
                self.txt.set_text('s=%1.2f' % \
                                  (density[int(index_y), int(index_x)]))
            except IndexError:
                #Sometimes they very slightly overlap and throw an exception.  
                #This is okay which is why we silently pass here
                pass
            pylab.draw()
    cursor = Cursor(axes)
    pylab.connect('motion_notify_event', cursor.mouse_move)

    pylab.show()
