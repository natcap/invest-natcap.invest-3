import unittest
import logging
import math

import numpy as np

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
        a[108] = (np.arctan2(1.5, -0.5) * rad_to_deg + 360.) % 360.
        a[135] = 135.0
        a[161] = (np.arctan2(0.5, -1.5) * rad_to_deg + 360.) % 360.
        a[198] = (np.arctan2(-0.5, -1.5) * rad_to_deg + 360.) % 360.
        a[225] = 225.0
        a[251] = (np.arctan2(-1.5, -0.5) * rad_to_deg + 360.) % 360.
        a[288] = (np.arctan2(-1.5, 0.5) * rad_to_deg + 360.) % 360.
        a[315] = 315.0
        a[341] = (np.arctan2(-0.5, 1.5) * rad_to_deg + 360.) % 360.
        # Use the angles above to create the expected min/max angles
        expected_extreme_angles = np.array([ \
            [a[108], 135., a[161]], \
            [a[45], 90., a[135]], \
            [a[18], 45., a[71]], \
            [a[135], 180., a[225]], \
            [a[18], 0., a[341]], \
            [a[198], 225., a[251]], \
            [a[225], 270., a[315]], \
            [a[288], 315., a[341]]])
        # Convert to rad so it's compatible with extreme_cell_angles_naive
        expected_extreme_angles *= deg_to_rad
        # Compute extreme angles for each cell
        computed_extreme_angles = []
        for row in range(array_shape[0]):
            for col in range(array_shape[1]):
                if row == 1 and col == 1:
                    continue
                cell = (row, col)
                computed_extreme_angles.append( \
                    self.extreme_cell_angles_naive(cell, viewpoint))
        computed_extreme_angles = np.array(computed_extreme_angles)
        # Compare both results
        error = np.sum(computed_extreme_angles - expected_extreme_angles)
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
        return np.array([min_angle, center_angle, max_angle])

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
        extreme_angles_naive = np.array(extreme_angles_naive)
        # Gather extreme angles from efficient algorithm
        extreme_angles_fast = \
            aesthetic_quality_core.list_extreme_cell_angles(array_shape, viewpoint)
        # Colmpare the two
        error = np.sum(np.abs(extreme_angles_naive - extreme_angles_fast))
        # assert if necessary
        if error > 5e-15:
            print('naive', extreme_angles_naive)
            print('fast', extreme_angles_fast)
            print('difference', extreme_angles_fast - extreme_angles_naive)
        message = 'error on expected and computed angles is too large:' + \
        str(error)
        assert error < 5e-15, message

    def test_viewshed(self):
        array_shape = (4, 2)
        viewpoint = (array_shape[0]/2, array_shape[1]/2)
        # list all perimeter cell center angles
        row_count, col_count = array_shape
        print(col_count, col_count)
        # Create the rows on the right side from viewpoint to top right corner
        perimeter_rows = np.array(range(viewpoint[0], -1, -1))
        perimeter_cols = np.ones(perimeter_rows.size) * (col_count - 1)
        # Create top row, avoiding repeat from what's already created
        perimeter_rows = np.concatenate((perimeter_rows, \
            np.zeros(col_count - 1)))
        perimeter_cols = np.concatenate((perimeter_cols, \
            np.array(range(row_count-2, -1, -1))))
        # Create left side, avoiding repeat from top row
        perimeter_rows = np.concatenate((perimeter_rows, \
            np.array(range(1, row_count))))
        perimeter_cols = np.concatenate((perimeter_cols, \
            np.zeros(row_count - 1)))
        # Create bottom row, avoiding repat from left side
        perimeter_rows = np.concatenate((perimeter_rows, \
            np.ones(col_count - 1) * (row_count -1)))
        perimeter_cols = np.concatenate((perimeter_cols, \
            np.array(range(1, col_count))))
        # Create last part of the right side, avoiding repeat from bottom row
        perimeter_rows = np.concatenate((perimeter_rows, \
            np.array(range(row_count - 2, viewpoint[0], -1))))
        perimeter_cols = np.concatenate((perimeter_cols, \
            np.ones(row_count - viewpoint[0] - 2) * (col_count - 1)))
        
        
        print('perimeter_rows', perimeter_rows)
        print('perimeter_cols', perimeter_cols)

    def tare_down(self):
        pass
