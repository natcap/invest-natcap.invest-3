import logging
import time

import scipy.sparse
from scipy.sparse.linalg import spsolve
import numpy as np

def diffusion_advection_solver(source_point_data, in_water_array, 
                               tide_e_array, adv_u_array, 
                               adv_v_array, nodata, cell_size):
    """2D Water quality model to track a pollutant in the ocean.  Three input
       arrays must be of the same shape.  Returns the solution in an array of
       the same shape.
    
    source_point_data - dictionary of the form:
        { source_point_id_0: {'point': [row_point, col_point] (in gridspace),
                            'KPS': float (decay?),
                            'WPS': float (loading?),
                            'point': ...},
          source_point_id_1: ...}
    in_water_array - 2D numpy array of booleans where False is a land pixel and
        True is a water pixel.
    tide_e_array - 2D numpy array with tidal E values or nodata values, must
        be same shape as in_water_array (m^2/sec)
    adv_u_array, adv_v_array - the u and v components of advection, must be
       same shape as in_water_array (units?)
    nodata - the value in the input arrays that indicate a nodata value.
    cell_size - the length of the side of a cell in meters
    """

    n_rows = in_water_array.shape[0]
    n_cols = in_water_array.shape[1]

    #Flatten arrays for use in the matrix building step
    in_water = in_water_array.flatten()
    e_array_flat = tide_e_array.flatten()
    adv_u_flat = adv_u_array.flatten()
    adv_v_flat = adv_v_array.flatten()

    LOGGER = logging.getLogger('marine_water_quality')
    LOGGER.info('Calculating advection diffusion')
    t0 = time.clock()

    def calc_index(i, j):
        """used to abstract the 2D to 1D index calculation below"""
        if i >= 0 and i < n_rows and j >= 0 and j < n_cols:
            return i * n_cols + j
        else:
            return -1

    #set up variables to hold the sparse system of equations
    #upper bound  n*m*5 elements
    b_vector = np.zeros(n_rows * n_cols)

    #holds the rows for diagonal sparse matrix creation later, row 4 is 
    #the diagonal
    a_matrix = np.zeros((9, n_rows * n_cols))
    diags = np.array([-2 * n_cols, -n_cols, -2, -1, 0, 1, 2, n_cols, 2 * n_cols])

    #Set up a data structure so we can index point source data based on 1D 
    #indexes
    source_points = {}
    for source_id, source_data in source_point_data.iteritems():
        source_index = calc_index(*source_data['point'])
        source_points[source_index] = source_data

    #iterate over the non-zero elments in grid to build the linear system
    LOGGER.info('Building diagonals for linear advection diffusion system.')
    #Right now, just run for one source so we extract out the "first" source 
    #point
    source_point_index, source_point_data = source_points.items()[0]
    for i in range(n_rows):
        for j in range(n_cols):
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

            if  a_diagonal_index == source_point_index:
                a_matrix[4, a_diagonal_index] = 1
                b_vector[a_diagonal_index] = source_point_data['WPS']
                continue

            E = e_array_flat[a_diagonal_index]
            adv_u = adv_u_flat[a_diagonal_index]
            adv_v = adv_v_flat[a_diagonal_index]
            #check for nodata values
            if nodata in [E, adv_u, adv_v]:
                a_matrix[4, a_diagonal_index] = 1
                continue

            #Build up terms
            #Ey
            if a_up_index > 0 and a_down_index > 0 and \
                in_water[a_up_index] and in_water[a_down_index]:
                #Ey
                a_matrix[4, a_diagonal_index] += -2.0 * E / cell_size ** 2
                a_matrix[7, a_down_index] += E / cell_size ** 2
                a_matrix[1, a_up_index] += E / cell_size ** 2

                #Uy
                a_matrix[7, a_down_index] += adv_v / (2.0 * cell_size)
                a_matrix[1, a_up_index] += -adv_v / (2.0 * cell_size)
            if a_up_index < 0 and in_water[a_down_index]:
                #we're at the top boundary, forward expansion down
                #Ey
                a_matrix[4, a_diagonal_index] += -E / cell_size ** 2
                a_matrix[7, a_down_index] += E / cell_size ** 2

                #Uy
                a_matrix[7, a_down_index] += adv_v / (2.0 * cell_size)
                a_matrix[4, a_diagonal_index] += -adv_v / (2.0 * cell_size)
            if a_down_index < 0 and in_water[a_up_index]:
                #we're at the bottom boundary, forward expansion up
                #Ey
                a_matrix[4, a_diagonal_index] += -E / cell_size ** 2
                a_matrix[1, a_up_index] += E / cell_size ** 2

                #Uy
                a_matrix[1, a_up_index] += adv_v / (2.0 * cell_size)
                a_matrix[4, a_diagonal_index] += -adv_v / (2.0 * cell_size)
            if not in_water[a_up_index]:
                #Ey
                a_matrix[4, a_diagonal_index] += -2.0 * E / cell_size ** 2
                a_matrix[7, a_down_index] += E / cell_size ** 2

                #Uy
                a_matrix[7, a_down_index] += adv_v / (2.0 * cell_size)
            if not in_water[a_down_index]:
                #Ey
                a_matrix[4, a_diagonal_index] += -2.0 * E / cell_size ** 2
                a_matrix[1, a_up_index] += E / cell_size ** 2

                #Uy
                a_matrix[1, a_up_index] += -adv_v / (2.0 * cell_size)

            if a_left_index > 0 and a_right_index > 0 and \
                in_water[a_left_index] and in_water[a_right_index]:
                #Ex
                a_matrix[4, a_diagonal_index] += -2.0 * E / cell_size ** 2
                a_matrix[5, a_right_index] += E / cell_size ** 2
                a_matrix[3, a_left_index] += E / cell_size ** 2

                #Ux
                a_matrix[5, a_right_index] += adv_u / (2.0 * cell_size)
                a_matrix[3, a_left_index] += -adv_u / (2.0 * cell_size)
            if a_left_index < 0 and in_water[a_right_index]:
                #we're on left boundary, expand right
                #Ex
                a_matrix[4, a_diagonal_index] += -E / cell_size ** 2
                a_matrix[5, a_right_index] += E / cell_size ** 2

                a_matrix[5, a_right_index] += adv_u / (2.0 * cell_size)
                a_matrix[4, a_diagonal_index] += -adv_u / (2.0 * cell_size)
                #Ux
            if a_right_index < 0 and in_water[a_left_index]:
                #we're on right boundary, expand left
                #Ex
                a_matrix[4, a_diagonal_index] += -E / cell_size ** 2
                a_matrix[3, a_left_index] += E / cell_size ** 2

                #Ux
                a_matrix[3, a_left_index] += adv_u / (2.0 * cell_size)
                a_matrix[4, a_diagonal_index] += -adv_u / (2.0 * cell_size)

            if not in_water[a_right_index]:
                #Ex
                a_matrix[4, a_diagonal_index] += -2.0 * E / cell_size ** 2
                a_matrix[3, a_left_index] += E / cell_size ** 2

                #Ux
                a_matrix[3, a_left_index] += -adv_u / (2.0 * cell_size)

            if not in_water[a_left_index]:
                #Ex
                a_matrix[4, a_diagonal_index] += -2.0 * E / cell_size ** 2
                a_matrix[5, a_right_index] += E / cell_size ** 2

                #Ux
                a_matrix[5, a_right_index] += adv_u / (2.0 * cell_size)

            #K
            a_matrix[4, a_diagonal_index] += -source_point_data['KPS']

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
        [-2 * n_cols, -n_cols, -2, -1, 0, 1, 2, n_cols, 2 * n_cols], 
         n_rows * n_cols, n_rows * n_cols, "csc")
    LOGGER.info('generating preconditioner via sparse incomplete lu decomposition')
    #normally factor will use m*(n*m) extra space, we restrict to 
    #\sqrt{m}*(n*m) extra space
    P = scipy.sparse.linalg.spilu(matrix, fill_factor=int(np.sqrt(n_cols)))
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
