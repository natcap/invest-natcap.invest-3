import unittest
import logging
import math

import numpy as np

from invest_natcap.aesthetic_quality import aesthetic_quality_core

class TestAestheticQualityCore(unittest.TestCase):
    def SetUp(self):
        pass

    def test_extreme_cell_angles_naive(self):
        """Testing extreme_cell_angles_naive with minimal data.
            Sanity check to make sure the naive function does what we expect.
        
            Inputs: None
            
            Returns nothing"""
        array_shape = (3, 3)
        viewpoint = (1, 1)

        pi = math.pi
        two_pi = 2.0 * pi
        rad_to_deg = 180.0 / pi
        deg_to_rad = 1.0 / rad_to_deg

        a = {}
        a[18] = (np.arctan2(0.5, 1.5) * rad_to_deg + two_pi) % two_pi
        a[45] = 45.0
        a[71] = (np.arctan2(1.5, 0.5) * rad_to_deg + two_pi) % two_pi
        a[135] = 135.0
        a[161] = (np.arctan2(0.5, -1.5) * rad_to_deg + two_pi) % two_pi
        a[198] = (np.arctan2(-0.5, -1.5) * rad_to_deg + two_pi) % two_pi
        a[225] = 225.0
        a[251] = (np.arctan2(1.5, -0.5) * rad_to_deg + two_pi) % two_pi
        a[288] = (np.arctan2(-1.5, -0.5) * rad_to_deg + two_pi) % two_pi
        a[315] = 315.0
        a[345] = 345.0
        for key in a.keys():
            print(key, a[key])
        #expected_extreme_angles = np.array([[],[],[],[],[],[],[],[]])
        computed_extreme_angles = []
        for row in range(array_shape[0]):
            for col in range(array_shape[1]):
                if row == 1 and col == 1:
                    continue
                cell = (row, col)
                computed_extreme_angles.append( \
                    extreme_cell_angles_naive(cell, viewpoint))
                print('cell', cell, 'viewpoint', viewpoint, \
                    'angles', extreme_angles * 180.0 / math.pi)




    def extreme_cell_angles_naive(cell_coord, viewpoint_coord):
        """Test each of the 4 corners of a cell, compute their angle from
        the viewpoint and return the smallest and largest angles in a tuple"""
        # Convert cell and viewpoint tuples to numpy arrays
        cell = np.array([cell_coord[0], cell_coord[1]])
        viewpoint = np.array([viewpoint_coord[0], viewpoint_coord[1]])
        # Compute the angle to the center of the cell
        max_angle = 0.
        min_angle = 2.0 * math.pi
        # Compute the angle to the 4 cell corners
        corners = np.array([ \
            [cell_coord[0] + .5, cell_coord[1] + .5], \
            [cell_coord[0] - .5, cell_coord[1] + .5], \
            [cell_coord[0] + .5, cell_coord[1] - .5], \
            [cell_coord[0] - .5, cell_coord[1] - .5]])
        # Compute angle to cell corner and update extreme angles as needed
        for corner in corners:
            viewpoint_to_corner = corner - viewpoint
            angle_to_corner = \
                np.arctan2(-viewpoint_to_corner[0], viewpoint_to_corner[1])
            angle_to_corner = \
                (2.0 * math.pi + angle_to_corner) % (2.0 * math.pi)
            print(corner, viewpoint_to_corner, angle_to_corner * \
            180.0 / math.pi)
            if angle_to_corner > max_angle:
                max_angle = angle_to_corner
            if angle_to_corner < min_angle:
                min_angle = angle_to_corner
        # Done, return min and max angles
        return np.array([min_angle, max_angle])

    def test_extreme_cell_angles(self):
        """Ensure the core function list_extreme_cell_angles agrees with 
        a naive implementation of the same functionality"""
        array_shape = (3, 3)
        viewpoint = (1, 1)

        for row in range(array_shape[0]):
            for col in range(array_shape[1]):
                if row == 1 and col == 1:
                    continue
                cell = (row, col)
                extreme_angles = \
                    extreme_cell_angles_naive(cell, viewpoint)
                print('cell', cell, 'viewpoint', viewpoint, \
                    'angles', extreme_angles * 180.0 / math.pi)

        aesthetic_quality_core.list_extreme_cell_angles(array_shape, viewpoint)

    def test_viewshed(self):
        pass

    def tare_down(self):
        pass
