import unittest
import logging
import math

import numpy as np

from matplotlib import pyplot as plt
from invest_natcap.aesthetic_quality import aesthetic_quality_core

class TestAestheticQualityCore(unittest.TestCase):
    def SetUp(self):
        pass

    def test_extreme_cell_angles_naive(self):
        """Testing extreme_cell_angles_naive on 3x3 array.
            Sanity check to make sure the naive function does what we expect.
        
            Inputs: None
            
            Returns nothing"""
        array_shape = (3, 3)
        viewpoint = (array_shape[0]/2, array_shape[1]/2)
        # Shorthand constants
        pi = math.pi
        rad_to_deg = 180.0 / pi
        deg_to_rad = 1.0 / rad_to_deg
        # The angle we're expecting
        a = {}
        a[18] = (np.arctan2(0.5, 1.5) * rad_to_deg + 360.) % 360.
        a[45] = 45.0
        a[71] = (np.arctan2(1.5, 0.5) * rad_to_deg + 360.) % 360.
        a[90] = 90.
        a[108] = (np.arctan2(1.5, -0.5) * rad_to_deg + 360.) % 360.
        a[135] = 135.0
        a[161] = (np.arctan2(0.5, -1.5) * rad_to_deg + 360.) % 360.
        a[180] = 180.
        a[198] = (np.arctan2(-0.5, -1.5) * rad_to_deg + 360.) % 360.
        a[225] = 225.0
        a[251] = (np.arctan2(-1.5, -0.5) * rad_to_deg + 360.) % 360.
        a[270] = 270.
        a[288] = (np.arctan2(-1.5, 0.5) * rad_to_deg + 360.) % 360.
        a[315] = 315.0
        a[341] = (np.arctan2(-0.5, 1.5) * rad_to_deg + 360.) % 360.
        # Convert to rad so it's compatible with extreme_cell_angles_naive
        for key in a.keys():
            a[key] *= deg_to_rad
        # Use the angles above to create the expected min/max angles
        expected_extreme_angles = [ \
            (a[108], (a[135], a[161])), \
            (a[45], (a[90], a[135])), \
            (a[18], (a[45], a[71])), \
            (a[135], (a[180], a[225])), \
            (a[18], (0., a[341])), \
            (a[198], (a[225], a[251])), \
            (a[225], (a[270], a[315])), \
            (a[288], (a[315], a[341]))]
        # Compute extreme angles for each cell
        computed_extreme_angles = []
        for row in range(array_shape[0]):
            for col in range(array_shape[1]):
                if row == 1 and col == 1:
                    continue
                cell = (row, col)
                computed_extreme_angles.append( \
                    self.extreme_cell_angles_naive(cell, viewpoint))
        # convert tuple to np.array
        a, b = zip(*computed_extreme_angles)
        b, c = zip(*b)
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        computed_extreme_angles = np.array([a, b, c])
        a, b = zip(*expected_extreme_angles)
        b, c = zip(*b)
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        expected_extreme_angles = np.array([a, b, c])
        # Compare both results
        error = np.sum(np.absolute(computed_extreme_angles - \
            expected_extreme_angles))
        # Assert if necessary
        assert abs(error) < 1e-14

    def extreme_cell_angles_naive(self, cell_coord, viewpoint_coord):
        """Test each of the 4 corners of a cell, compute their angle from
        the viewpoint and return the smallest and largest angles in a tuple.
        
            Inputs:
                -cell_coord: (row, col) tuple of the cell we want to compute
                    the extreme angles from.
                -viewpoint_coord: (row, col) tuple of the observer that is
                looking at the point cell_coord.
                
            Returns a numpy array with the extreme angles 
                [min_cell_angle, center_cell_angle, max_cell_angle]"""
        # Convert cell and viewpoint tuples to numpy arrays
        cell = np.array([cell_coord[0], cell_coord[1]])
        viewpoint = np.array([viewpoint_coord[0], viewpoint_coord[1]])
        # Compute the angle to the center of the cell
        viewpoint_to_cell = cell - viewpoint
        center_angle = np.arctan2(-viewpoint_to_cell[0], viewpoint_to_cell[1])
        center_angle = (2.0 * math.pi + center_angle) % (2.0 * math.pi)
        # Compute the minimum and maximum angles by goignt hrough each corner
        max_angle = 0.
        min_angle = 2.0 * math.pi
        # Define the 4 cell corners
        corners = np.array([ \
            [cell_coord[0] + .5, cell_coord[1] + .5], \
            [cell_coord[0] - .5, cell_coord[1] + .5], \
            [cell_coord[0] + .5, cell_coord[1] - .5], \
            [cell_coord[0] - .5, cell_coord[1] - .5]])
        # Compute angle to all 4 cell corners and update min and max angles
        for corner in corners:
            viewpoint_to_corner = corner - viewpoint
            angle_to_corner = \
                np.arctan2(-viewpoint_to_corner[0], viewpoint_to_corner[1])
            angle_to_corner = \
                (2.0 * math.pi + angle_to_corner) % (2.0 * math.pi)
            if angle_to_corner > max_angle:
                max_angle = angle_to_corner
            if angle_to_corner < min_angle:
                min_angle = angle_to_corner
        # Done, return min and max angles
        return (min_angle, (center_angle, max_angle))

    def test_extreme_cell_angles(self):
        """Testing naive vs optimized version of the same functionality"""
        array_shape = (3, 3)
        viewpoint = (array_shape[0]/2, array_shape[1]/2)

        # Gather extreme angles from naive algorithm 
        extreme_angles_naive = []
        for row in range(array_shape[0]):
            for col in range(array_shape[1]):
                if (row == viewpoint[0]) and (col == viewpoint[1]):
                    continue
                cell = (row, col)
                extreme_angles_naive.append( \
                    self.extreme_cell_angles_naive(cell, viewpoint))
        # Convert to numpy
        min_angles, nested_list = zip(*extreme_angles_naive)
        min_angles = np.array(min_angles)
        center_angles, max_angles = zip(*nested_list)
        center_angles = np.array(center_angles)
        max_angles = np.array(max_angles)
        extreme_angles_naive = (min_angles, center_angles, max_angles)
        # Gather extreme angles from efficient algorithm
        extreme_angles_fast = \
            aesthetic_quality_core.list_extreme_cell_angles(array_shape, viewpoint)
        # Compare the two
        error = np.sum(np.abs(extreme_angles_naive[0]-extreme_angles_fast[0])+\
            np.abs(extreme_angles_naive[1]-extreme_angles_fast[1]) + \
            np.abs(extreme_angles_naive[2]-extreme_angles_fast[2]))
        # assert if necessary
        if error > 5e-15:
            print('naive', extreme_angles_naive)
            print('fast', extreme_angles_fast)
            print('difference')
            print(extreme_angles_fast[0] - extreme_angles_naive[0])
            print(extreme_angles_fast[1] - extreme_angles_naive[1])
            print(extreme_angles_fast[2] - extreme_angles_naive[2])
        message = 'error on expected and computed angles is too large:' + \
        str(error)
        assert error < 5e-15, message


    def get_perimeter_cells(self, array_shape, viewpoint):
        """Compute cells along the perimeter of an array.

            Inputs:
                -array_shape: tuple (row, col) as ndarray.shape containing the
                size of the array from which to compute the perimeter
                -viewpoint: tuple (row, col) indicating the position of the
                observer
                
            Returns a tuple (rows, cols) of the cell rows and columns following
            the convention of numpy.where() where the first cell is immediately
            right to the viewpoint, and the others are enumerated clockwise."""
        # list all perimeter cell center angles
        row_count, col_count = array_shape
        # Create top row, except cell (0,0)
        rows = np.zeros(col_count - 1)
        cols = np.array(range(col_count-1, 0, -1))
        # Create left side, avoiding repeat from top row
        rows = np.concatenate((rows, np.array(range(row_count -1))))
        cols = np.concatenate((cols, np.zeros(row_count - 1)))
        # Create bottom row, avoiding repat from left side
        rows = np.concatenate((rows, np.ones(col_count - 1) * (row_count -1)))
        cols = np.concatenate((cols, np.array(range(col_count - 1))))
        # Create last part of the right side, avoiding repeat from bottom row
        rows = np.concatenate((rows, np.array(range(row_count - 1, 0, -1))))
        cols = np.concatenate((cols, np.ones(row_count - 1) * (col_count - 1)))
        # Roll the arrays so the first point's angle at (rows[0], cols[0]) is 0
        rows = np.roll(rows, viewpoint[0])
        cols = np.roll(cols, viewpoint[0])
        return (rows, cols)

    def test_get_perimeter_cells(self):
        """Test get_perimeter_cells on 2 hand-designed examples"""
        # First hand-designed example: 3x4 raster
        # Given the shape of the array below and the viewpoint coordinates
        array_shape = (3, 4)
        viewpoint = (2, 3)
        # The coordinates of perimeter cells should be as follows:
        expected_rows = np.array([2.,1.,0.,0.,0.,0.,1.,2.,2.,2.])
        expected_cols = np.array([3.,3.,3.,2.,1.,0.,0.,0.,1.,2.])
        # Test if the computed rows and columns agree with the expected ones
        computed_rows, computed_cols = \
            self.get_perimeter_cells(array_shape, viewpoint)
        message = 'number of rows disagree: expected' + str(expected_rows.shape) + \
            ', computed' + str(computed_rows.shape)
        assert expected_rows.shape == computed_rows.shape, message
        message = 'number of cols disagree: expected' + str(expected_rows.shape) + \
            ', computed' + str(computed_rows.shape)
        assert expected_cols.shape == computed_cols.shape, message
        row_diff = np.sum(np.absolute(expected_rows - computed_rows))
        message = 'difference in rows: ' + str(row_diff)
        assert row_diff == 0, message
        col_diff = np.sum(np.absolute(expected_cols - computed_cols))
        message = 'difference in columns: ' + str(col_diff)
        assert col_diff == 0, message

        # Second hand-designed example: 5x3 raster
        # Given the shape of the array below and the viewpoint coordinates
        array_shape = (5, 3)
        viewpoint = (0, 1)
        # The coordinates of perimeter cells should be as follows:
        expected_rows = np.array([0.,0.,0.,1.,2.,3.,4.,4.,4.,3.,2.,1.])
        expected_cols = np.array([2.,1.,0.,0.,0.,0.,0.,1.,2.,2.,2.,2.])
        # Test if the computed rows and columns agree with the expected ones
        computed_rows, computed_cols = \
            self.get_perimeter_cells(array_shape, viewpoint)
        message = 'number of rows disagree: expected' + str(expected_rows.shape) + \
            ', computed' + str(computed_rows.shape)
        assert expected_rows.shape == computed_rows.shape, message
        message = 'number of cols disagree: expected' + str(expected_rows.shape) + \
            ', computed' + str(computed_rows.shape)
        assert expected_cols.shape == computed_cols.shape, message
        row_diff = np.sum(np.absolute(expected_rows - computed_rows))
        message = 'difference in rows: ' + str(row_diff)
        assert row_diff == 0, message
        col_diff = np.sum(np.absolute(expected_cols - computed_cols))
        message = 'difference in columns: ' + str(col_diff)
        assert col_diff == 0, message

    def cell_angles(self, cell_coords, viewpoint):
        """Compute angles between cells and viewpoint where 0 angle is right of
        viewpoint.
            Inputs:
                -cell_coords: coordinate tuple (rows, cols) as numpy.where()
                from which to compute the angles
                -viewpoint: tuple (row, col) indicating the position of the
                observer. Each of row and col is an integer.
                
            Returns a sorted list of angles"""
        rows, cols = cell_coords
        # List the angles between each perimeter cell
        two_pi = 2.0 * math.pi
        r = np.array(range(rows.size))
        p = (rows[r] - viewpoint[0], cols[r] - viewpoint[1])
        angles = (np.arctan2(-p[0], p[1]) + two_pi) % two_pi
        return angles

    def test_cell_angles(self):
        """Test the angles computed by angles_from_perimeter_cells agains the
        function cell_angles"""
        array_shape = (400, 400)
        viewpoint = (350, 200)
        # Get the perimeter cells
        perimeter_cells = self.get_perimeter_cells(array_shape, viewpoint)
        # Compute angles associated to the perimeter cells
        angles_fast = self.cell_angles(perimeter_cells, viewpoint)
        # Compute the same angles individually
        angles_naive = []
        for cell in zip(perimeter_cells[0], perimeter_cells[1]):
            angles_naive.append(self.cell_angle(cell, viewpoint))
        angles_naive = np.array(angles_naive)
        # Compute the error between both algorithms
        error = np.sum(np.absolute(angles_fast - angles_naive))
        message = 'error between cell angle algorithms: ' + str(error)
        assert error < 1e-15, message

    def cell_angle(self, cell_pos, viewpoint_pos):
        """Compute the angle from a single cell to the viewpoint where 0 is 
        the positive J axis:
        
            Inputs:
                -cell_pos: coordinate tuple (row, col) of the cell position
                -viewer_pos: coordinate tuple (row, col) of the viewer's 
                position
                
            Returns the cell's angle in radians"""
        two_pi = 2. * math.pi
        return (np.arctan2(-(cell_pos[0]-viewpoint_pos[0]),
            cell_pos[1]-viewpoint_pos[1]) + two_pi) % two_pi

    def test_cell_angle(self):
        """Simple test that ensures cell_angle is doing what it is supposed to"""
        viewpoint_pos = (3, 3)
        cell_pos = [(0,0),(0,3),(2,2),(2,4),(3,0),(3,4),(4,2),(4,3),(4,4)]
        # Pre-computed angles
        pi = math.pi
        precomputed_angles = np.array([3.*pi/4.,pi/2.,3.*pi/4.,pi/4.,pi,0., \
        5.*pi/4., 3.*pi/2., 7.*pi/4.])
        # compute the angles using cell_angles
        computed_angles = []
        for cell in cell_pos:
            computed_angles.append(self.cell_angle(cell, viewpoint_pos))
        # Convert computed result and compute error 
        computed_angles = np.array(computed_angles)
        error = np.sum(np.absolute(computed_angles - precomputed_angles))
        message = 'error on cell angles is ' + str(error)
        assert error < 1e-14, message

    def test_viewshed(self):
        array_shape = (4,4) 
        viewpoint = np.array([array_shape[0]/2, array_shape[1]/2])

        # 1- get perimeter cells
        perimeter_cells = self.get_perimeter_cells(array_shape, viewpoint)
        # 1.1- remove perimeter cell if same coord as viewpoint
        # 2- compute cell angles
        angles = self.cell_angles(perimeter_cells, viewpoint)
        # 3- build event lists
        print('angles', angles.size, angles)
        add_cell_events = np.array(angles.shape)
        cell_center_events = np.array(angles.shape)
        remove_cell_events = np.array(angles.shape)
        # 5- compute angles on raster cells
        events = \
        aesthetic_quality_core.list_extreme_cell_angles(array_shape, viewpoint)
        print('min', events[0])
        print('center', events[1])
        print('max', events[2])
        # Add the events to the 3 event lists

        

    def tare_down(self):
        pass
