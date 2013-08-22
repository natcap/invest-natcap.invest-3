import unittest
import logging
import math

import numpy as np

from invest_natcap.aesthetic_quality import aesthetic_quality_core

class TestAestheticQualityCore(unittest.TestCase):
    def SetUp(self):
        pass

    def test_extreme_cell_angles(self):
        """Ensure the core function list_extreme_cell_angles agrees with 
        a naive implementation of the same functionality"""
        def extreme_cell_angles_naive(cell_coord, viewpoint_coord):
            """Test each of the 4 corners of a cell, compute their angle from
            the viewpoint and return the smallest and largest angles in a tuple"""
            # Convert cell and viewpoint tuples to numpy arrays
            cell = np.array([cell_coord[0], cell_coord[1]])
            viewpoint = np.array([viewpoint_coord[0], viewpoint_coord[1]])
            # Compute the angle to the center of the cell
            viewpoint_to_cell = cell - viewpoint
            angle_to_cell = \
                np.arctan2(viewpoint_to_cell[1], viewpoint_to_cell[0])
            max_angle = angle_to_cell
            min_angle = angle_to_cell
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
                    np.arctan2(viewpoint_to_corner[0], viewpoint_to_corner[1])
                if angle_to_corner > max_angle:
                    max_angle = angle_to_corner
                if angle_to_corner < min_angle:
                    min_angle = angle_to_corner
            # Done, return min and max angles
            return np.array([min_angle, max_angle])

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
