from __future__ import print_function

import unittest
import logging
import os
import sys
import subprocess
import math
import numpy as np
import random
import time
import csv
import glob
import shutil
import json

from osgeo import gdal
from osgeo import ogr
from nose.plugins.skip import SkipTest

import invest_test_core
from invest_natcap import raster_utils
from invest_natcap.scenic_quality \
    import scenic_quality as sq
from invest_natcap.scenic_quality \
    import scenic_quality_core as sqc
import scenic_quality_cython_core

LOGGER = logging.getLogger('scenic_quality_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestScenicQuality(unittest.TestCase):
    """Main testing class for the scenic quality tests"""
    
    def setUp(self):
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
        # The angles we're expecting
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
        # 1st line is for pixel at row 0, col 0
        # Subsequent lines are: 
        #    row 0, col 1, 
        #    row 0, col 2, 
        #    row 1, col 0,
        #    row 1, col 2, (skip center point at row 1, col 1)
        #    row 2, col 0,
        #    row 2, col 1,
        #    row 2, col 2,
        expected_extreme_angles = [ \
            (a[108], (a[135], a[161])), \
            (a[45], (a[90], a[135])), \
            (a[18], (a[45], a[71])), \
            (a[135], (a[180], a[225])), \
            (a[315], (0., a[45])), \
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
        message = 'error is ' + str(error)
        assert abs(error) < 1e-14, message

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
        # Compute the minimum and maximum angles by goign through each corner
        max_angle = 0.
        min_angle = 2.0 * math.pi
        # Define the 4 cell corners
        corners = np.array([ \
            [cell_coord[0] + .5, cell_coord[1] + .5], \
            [cell_coord[0] - .5, cell_coord[1] + .5], \
            [cell_coord[0] + .5, cell_coord[1] - .5], \
            [cell_coord[0] - .5, cell_coord[1] - .5]])
        # If cell angle is 0, use pre-computed corners for min and max:
        if center_angle == 0.:
            viewpoint_to_corner = corners[2] - viewpoint
            min_angle = \
                np.arctan2(-viewpoint_to_corner[0], viewpoint_to_corner[1])
            min_angle = (2.0 * math.pi + min_angle) % (2.0 * math.pi)
            viewpoint_to_corner = corners[3] - viewpoint
            max_angle = \
                np.arctan2(-viewpoint_to_corner[0], viewpoint_to_corner[1])
            max_angle = (2.0 * math.pi + max_angle) % (2.0 * math.pi)
        else:
            # Compute angle to all 4 cell corners and update min and max angles
            for corner in corners:
                viewpoint_to_corner = corner - viewpoint
                angle_to_corner = \
                    np.arctan2(-viewpoint_to_corner[0], viewpoint_to_corner[1])
                angle_to_corner = \
                    (2.0 * math.pi + angle_to_corner) % (2.0 * math.pi)
                # Sort the angles
                if angle_to_corner > max_angle:
                    max_angle = angle_to_corner
                if angle_to_corner < min_angle:
                    min_angle = angle_to_corner
        # Done, return min and max angles
        return (min_angle, (center_angle, max_angle))

    def test_maximum_distance(self):
        """Test that the maximum distance is properly computed in
        Python's list_extreme_angles"""
        def disk(radius):
            """Create a disk of radius 'radius' around a center pixel"""
            diameter = radius * 2 + 1
            A = np.zeros((diameter, diameter))
            center_r = radius
            center_c = center_r
            for r in range(diameter):
                for c in range(diameter):
                    if (r == center_r) and (c == center_c):
                        pass
                    d = (r-center_r)**2+(c-center_c)**2
                    if d <= center_r**2:
                        A[r, c] = 1
            return A

        # Test for discs of radius 1 to 5
        for max_dist in range(1, 6):
            array_shape = (max_dist * 2 + 1, max_dist * 2 + 1)
            viewpoint = (max_dist, max_dist)
            # Generate disc from nested function
            D = disk(max_dist)
            # Double check that what we have is within the radius
            I, J = np.where(D > 0)
            I = I - viewpoint[0]
            J = J - viewpoint[1]
            L = I**2 + J**2
            assert (L <= max_dist**2).all()
            I, J = np.where(D <= 0)
            I = I - viewpoint[0]
            J = J - viewpoint[1]
            L = I**2 + J**2
            assert (L > max_dist**2).all()
            # Adjusting the center to conform with list_extreme_angles
            D[viewpoint] = 0
            # Gather extreme angles from efficient algorithm
            extreme_angles = \
            sqc.list_extreme_cell_angles(array_shape, \
            viewpoint, max_dist)
            A = np.zeros(array_shape)
            A[extreme_angles[3], extreme_angles[4]] = 1
            # compare both
            if np.sum(np.abs(A-D)) > 0:
                print('expected:')
                print(D)
                print('computed:')
                print(A)
            message = "Area of extreme angles doesn't form a valid disc."
            assert np.sum(np.abs(A-D)) == 0, message


    def test_extreme_cell_angles(self):
        """Testing naive vs optimized version of extreme cell angles"""
        max_dist = 4
        array_shape = (max_dist*2+1, max_dist*2+1)
        viewpoint = (array_shape[0]/2, array_shape[1]/2)
        max_dist_sq = max_dist **2 # Used to skip cells that are too far

        # Gather extreme angles from naive algorithm 
        extreme_angles_naive = []
        for row in range(array_shape[0]):
            for col in range(array_shape[1]):
                cell = np.array([row, col])
                viewpoint_to_cell = cell - viewpoint
                if np.sum(viewpoint_to_cell**2) > max_dist_sq:
                    continue
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
            sqc.list_extreme_cell_angles(array_shape, \
            viewpoint, max_dist)
        _min = extreme_angles_fast[0]
        _ctr = extreme_angles_fast[1]
        _max = extreme_angles_fast[2]
        I = extreme_angles_fast[3]
        J = extreme_angles_fast[4]
        matrix = np.zeros([np.max(I)+1, np.max(J)+1])
        np.set_printoptions(precision = 4)
        matrix[(I, J)] = _max
        #print('max')
        #print(matrix)
        #matrix[(I, J)] = _ctr
        #print('center')
        #print(matrix)
        #matrix[(I, J)] = _min
        #print('min')
        #print(matrix)
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


    def test_list_extreme_cell_angles_cython(self):
        """Comparing cython vs python list_extreme_cell_angles"""
        array_size = 6
        array_shape = (array_size, array_size)
        viewpoint = (array_shape[0]/4, array_shape[1]/3)

        # Test with infinite distance
        max_dist = -1
        # Gather extreme angles from cython algorithm
        extreme_angles_cython = \
        scenic_quality_cython_core.list_extreme_cell_angles(array_shape, \
        viewpoint, max_dist)
        # Gather extreme angles from python algorithm
        extreme_angles_python = \
        sqc.list_extreme_cell_angles(array_shape, \
        viewpoint, max_dist)
        # Compare the two
        error = np.sum(np.abs(extreme_angles_python[0]-extreme_angles_cython[0])+\
            np.abs(extreme_angles_python[1]-extreme_angles_cython[1]) + \
            np.abs(extreme_angles_python[2]-extreme_angles_cython[2]))
        # assert if necessary
        if error > 5e-15:
            print('python', extreme_angles_python)
            print('cython', extreme_angles_cython)
            print('difference')
            print(extreme_angles_cython[0] - extreme_angles_python[0])
            print(extreme_angles_cython[1] - extreme_angles_python[1])
            print(extreme_angles_cython[2] - extreme_angles_python[2])
        message = 'error on expected and computed angles is too large:' + \
        str(error)
        assert error < 5e-15, message

        # Test with finite distance
        max_dist = 2
        # Gather extreme angles from cython algorithm
        extreme_angles_cython = \
        scenic_quality_cython_core.list_extreme_cell_angles(array_shape, \
        viewpoint, max_dist)
        # Gather extreme angles from python algorithm
        extreme_angles_python = \
        sqc.list_extreme_cell_angles(array_shape, \
        viewpoint, max_dist)
        # Compare the two
        error = np.sum(np.abs(extreme_angles_python[0]-extreme_angles_cython[0])+\
            np.abs(extreme_angles_python[1]-extreme_angles_cython[1]) + \
            np.abs(extreme_angles_python[2]-extreme_angles_cython[2]))
        # assert if necessary
        if error > 5e-15:
            print('python', extreme_angles_python)
            print('cython', extreme_angles_cython)
            print('difference')
            print(extreme_angles_cython[0] - extreme_angles_python[0])
            print(extreme_angles_cython[1] - extreme_angles_python[1])
            print(extreme_angles_cython[2] - extreme_angles_python[2])
        message = 'error on expected and computed angles is too large:' + \
        str(error)
        assert error < 5e-15, message

    def test_get_perimeter_cells(self):
        """Test get_perimeter_cells on 2 hand-designed examples"""
        return
        # First hand-designed example: 3x4 raster, infinite max_dist
        # Given the shape of the array below and the viewpoint coordinates
        array_shape = (3, 4)
        viewpoint = (2, 3)
        # The coordinates of perimeter cells should be as follows:
        expected_rows = np.array([2.,1.,0.,0.,0.,0.,1.,2.,2.,2.])
        expected_cols = np.array([3.,3.,3.,2.,1.,0.,0.,0.,1.,2.])
        # Test if the computed rows and columns agree with the expected ones
        computed_rows, computed_cols = \
        sqc.get_perimeter_cells(array_shape, viewpoint)
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

        # Second hand-designed example: 5x3 raster, infinite max_dist
        # Given the shape of the array below and the viewpoint coordinates
        array_shape = (5, 3)
        viewpoint = (0, 1)
        # The coordinates of perimeter cells should be as follows:
        expected_rows = np.array([0.,0.,0.,1.,2.,3.,4.,4.,4.,3.,2.,1.])
        expected_cols = np.array([2.,1.,0.,0.,0.,0.,0.,1.,2.,2.,2.,2.])
        # Test if the computed rows and columns agree with the expected ones
        computed_rows, computed_cols = \
            sqc.get_perimeter_cells(array_shape, viewpoint)
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

        # Third hand-designed example: 100x100 raster, max_dist = 100
        array_shape = (100, 100)
        viewpoint = (25, 75)
        max_dist = 100
        row_count, col_count = array_shape
        # Create top row, except cell (0,0)
        expected_rows = np.zeros(col_count - 1)
        expected_cols = np.array(range(col_count-1, 0, -1))
        # Create left side, avoiding repeat from top row
        expected_rows = \
        np.concatenate((expected_rows, np.array(range(row_count -1))))
        expected_cols = \
        np.concatenate((expected_cols, np.zeros(row_count - 1)))
        # Create bottom row, avoiding repat from left side
        expected_rows = \
        np.concatenate((expected_rows, np.ones(col_count -1) * (row_count -1)))
        expected_cols = \
        np.concatenate((expected_cols, np.array(range(col_count - 1))))
        # Create last part of the right side, avoiding repeat from bottom row
        expected_rows = \
        np.concatenate((expected_rows, np.array(range(row_count - 1, 0, -1))))
        expected_cols = \
        np.concatenate((expected_cols, np.ones(row_count -1) * (col_count -1)))
        # Roll the arrays so the first point's angle at (rows[0], cols[0]) is 0
        expected_rows = np.roll(expected_rows, viewpoint[0])
        expected_cols = np.roll(expected_cols, viewpoint[0])
        # Test if the computed rows and columns agree with the expected ones
        computed_rows, computed_cols = \
            sqc.get_perimeter_cells(array_shape, viewpoint,\
            max_dist)
        message = \
            'number of rows disagree: expected' + str(expected_rows.shape) + \
            ', computed' + str(computed_rows.shape)
        assert expected_rows.shape == computed_rows.shape, message
        message = \
            'number of cols disagree: expected' + str(expected_rows.shape) + \
            ', computed' + str(computed_rows.shape)
        assert expected_cols.shape == computed_cols.shape, message
        row_diff = np.sum(np.absolute(expected_rows - computed_rows))
        message = 'difference in rows: ' + str(row_diff)
        assert row_diff == 0, message
        col_diff = np.sum(np.absolute(expected_cols - computed_cols))
        message = 'difference in columns: ' + str(col_diff)
        assert col_diff == 0, message

        # Fourth hand-designed example: 100x100 raster, max_dist = 50
        max_dist = 50
        # Create top row, except cell (0,0)
        expected_rows = np.zeros(74)
        expected_cols = np.array(range(99, 25, -1))
        # Create left side, avoiding repeat from top row
        expected_rows = \
        np.concatenate((expected_rows, np.array(range(74))))
        expected_cols = \
        np.concatenate((expected_cols, np.ones(74) * 25))
        # Create bottom row, avoiding repat from left side
        expected_rows = \
        np.concatenate((expected_rows, np.ones(74) * 74))
        expected_cols = \
        np.concatenate((expected_cols, np.array(range(25, 99))))
        # Create last part of the right side, avoiding repeat from bottom row
        expected_rows = \
        np.concatenate((expected_rows, np.array(range(74, 0, -1))))
        expected_cols = \
        np.concatenate((expected_cols, np.ones(74) * 99))
        # Roll the arrays so the first point's angle at (rows[0], cols[0]) is 0
        expected_rows = np.roll(expected_rows, viewpoint[0])
        expected_cols = np.roll(expected_cols, viewpoint[0])
        # Test if the computed rows and columns agree with the expected ones
        computed_rows, computed_cols = \
            sqc.get_perimeter_cells(array_shape, viewpoint,\
            max_dist)
        message = \
            'number of rows disagree: expected' + str(expected_rows.shape) + \
            ', computed' + str(computed_rows.shape)
        assert expected_rows.shape == computed_rows.shape, message
        message = \
            'number of cols disagree: expected' + str(expected_cols.shape) + \
            ', computed' + str(computed_cols.shape)
        assert expected_cols.shape == computed_cols.shape, message
        row_diff = np.sum(np.absolute(expected_rows - computed_rows))
        if row_diff > 0:
            print('expected_rows')
            print(expected_rows)
            print('computed_rows')
            print(computed_rows)
        message = 'difference in rows: ' + str(row_diff)
        assert row_diff == 0, message
        col_diff = np.sum(np.absolute(expected_cols - computed_cols))
        message = 'difference in columns: ' + str(col_diff)
        assert col_diff == 0, message

        # Fifth hand-designed example: 100x100 raster, max_dist = 25
        max_dist = 20
        # Create top row, except cell (0,0)
        expected_rows = np.ones(39) * 5
        expected_cols = np.array(range(94, 55, -1))
        # Create left side, avoiding repeat from top row
        expected_rows = \
        np.concatenate((expected_rows, np.array(range(5, 44))))
        expected_cols = \
        np.concatenate((expected_cols, np.ones(39) * 55))
        # Create bottom row, avoiding repat from left side
        expected_rows = \
        np.concatenate((expected_rows, np.ones(39) * 44))
        expected_cols = \
        np.concatenate((expected_cols, np.array(range(55, 94))))
        # Create last part of the right side, avoiding repeat from bottom row
        expected_rows = \
        np.concatenate((expected_rows, np.array(range(44, 5, -1))))
        expected_cols = \
        np.concatenate((expected_cols, np.ones(39) * 94))
        # Roll the arrays so the first point's angle at (rows[0], cols[0]) is 0
        expected_rows = np.roll(expected_rows, viewpoint[0] - 5)
        expected_cols = np.roll(expected_cols, viewpoint[0] - 5)
        # Test if the computed rows and columns agree with the expected ones
        computed_rows, computed_cols = \
            aesthetic_quality_core.get_perimeter_cells(array_shape, viewpoint,\
            max_dist)
        message = \
            'number of rows disagree: expected' + str(expected_rows.shape) + \
            ', computed' + str(computed_rows.shape)
        assert expected_rows.shape == computed_rows.shape, message
        message = \
            'number of cols disagree: expected' + str(expected_cols.shape) + \
            ', computed' + str(computed_cols.shape)
        assert expected_cols.shape == computed_cols.shape, message
        row_diff = np.sum(np.absolute(expected_rows - computed_rows))
        message = 'difference in rows: ' + str(row_diff)
        assert row_diff == 0, message
        col_diff = np.sum(np.absolute(expected_cols - computed_cols))
        message = 'difference in columns: ' + str(col_diff)
        assert col_diff == 0, message

    def test_cell_angles(self):
        """Test the angles computed by angles_from_perimeter_cells agains the
        function cell_angles"""
        array_shape = (400, 400)
        viewpoint = (350, 200)
        # Get the perimeter cells
        perimeter_cells = \
        sqc.get_perimeter_cells(array_shape, viewpoint)
        # Compute angles associated to the perimeter cells
        angles_fast = sqc.cell_angles(perimeter_cells, viewpoint)
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

    def test_get_perimeter_cells(self):
        DEM_size = 9
        elevation = np.zeros((DEM_size, DEM_size))
        viewpoint = (DEM_size/2+2, DEM_size/2-2)
        radius = 3
	perimeter = sqc.get_perimeter_cells(elevation.shape, viewpoint, radius)
        #print('perimeter', perimeter)
        elevation[perimeter] = 1
        elevation[viewpoint[0], viewpoint[1]] = 2
        #print(elevation)

    def cell_row(self, cell_id, col_count):
        """Compute the row index from a cell ID"""
        return float(cell_id / col_count)

    def cell_col(self, cell_id, row_count):
        """Compute the col index from a cell ID"""
        return float(cell_id % row_count)

    def test_indexing_algorithm(self):
        """This test checks each possible direction for a small example.
        This test is valuable because the coordinates are more manageable
        and the algorithm tests every pixel on the quadrants."""
        row_count = 5
        col_count = 5
        test_parameters = [ \
            ([0., 0.], [0., 4.], [0, 1, 2, 3, 4]), \
            ([0., 0.], [1., 4.], [0, 1, 2, 7, 8, 9]), \
            ([0., 0.], [2., 4.], [0, 1, 6, 7, 8, 13, 14]), \
            ([0., 0.], [3., 4.], [0, 1, 6, 7, 12, 17, 18, 23]), \
            ([0., 0.], [4., 4.], [0, 6, 12, 18, 24]), \
            ([0., 0.], [4., 3.], [0, 5, 6, 11, 12, 17, 18, 23]), \
            ([0., 0.], [4., 2.], [0, 5, 6, 11, 16, 17, 22]), \
            ([0., 0.], [4., 1.], [0, 5, 10, 11, 16, 21]), \
            ([0., 0.], [4., 0.], [0, 5, 10, 15, 20]), \

            ([4., 4.], [0., 4.], [24, 19, 14, 9, 4]), \
            ([4., 4.], [0., 3.], [24, 19, 14, 13, 8, 3]), \
            ([4., 4.], [0., 2.], [24, 19, 18, 13, 8, 7, 2]), \
            ([4., 4.], [0., 1.], [24, 19, 18, 13, 12, 7, 6, 1]), \
            ([4., 4.], [0., 0.], [24, 18, 12, 6, 0]), \
            ([4., 4.], [1., 0.], [24, 23, 18, 17, 12, 11, 6, 5]), \
            ([4., 4.], [2., 0.], [24, 23, 18, 17, 16, 11, 10]), \
            ([4., 4.], [3., 0.], [24, 23, 22, 17, 16, 15]), \
            ([4., 4.], [4., 0.], [24, 23, 22, 21, 20]), \

            ([0., 4.], [0., 0.], [4, 3, 2, 1, 0]), \
            ([0., 4.], [1., 0.], [4, 3, 2, 7, 6, 5]), \
            ([0., 4.], [2., 0.], [4, 3, 8, 7, 6, 11, 10]), \
            ([0., 4.], [3., 0.], [4, 3, 8, 7, 12, 11, 16, 15]), \
            ([0., 4.], [4., 0.], [4, 8, 12, 16, 20]), \
            ([0., 4.], [4., 1.], [4, 9, 8, 13, 12, 17, 16, 21]), \
            ([0., 4.], [4., 2.], [4, 9, 8, 13, 18, 17, 22]), \
            ([0., 4.], [4., 3.], [4, 9, 14, 13, 18, 23]), \
            ([0., 4.], [4., 4.], [4, 9, 14, 19, 24]), \

            ([4., 0.], [0., 0.], [20, 15, 10, 5, 0]), \
            ([4., 0.], [0., 1.], [20, 15, 10, 11, 6, 1]), \
            ([4., 0.], [0., 2.], [20, 15, 16, 11, 6, 7, 2]), \
            ([4., 0.], [0., 3.], [20, 15, 16, 11, 12, 7, 8, 3]), \
            ([4., 0.], [0., 4.], [20, 16, 12, 8, 4]), \
            ([4., 0.], [1., 4.], [20, 21, 16, 17, 12, 13, 8, 9]), \
            ([4., 0.], [2., 4.], [20, 21, 16, 17, 18, 13, 14]), \
            ([4., 0.], [3., 4.], [20, 21, 22, 17, 18, 19]), \
            ([4., 0.], [4., 4.], [20, 21, 22, 23, 24]), \
            ]
        expected_results = [ \
            [0, 2, 4, 6, 8], \
            [0, 2, 4, 5, 6, 8], \
            [0, 2, 3, 4, 6, 7, 8], \
            [0, 2, 3, 4, 5, 6, 7, 8], \
            [0, 2, 4, 6, 8], \
            [0, 2, 3, 4, 5, 6, 7, 8], \
            [0, 2, 3, 4, 6, 7, 8], \
            [0, 2, 4, 5, 6, 8], \
            [0, 2, 4, 6, 8], \

            [0, 2, 4, 6, 8], \
            [0, 2, 4, 5, 6, 8], \
            [0, 2, 3, 4, 6, 7, 8], \
            [0, 2, 3, 4, 5, 6, 7, 8], \
            [0, 2, 4, 6, 8], \
            [0, 2, 3, 4, 5, 6, 7, 8], \
            [0, 2, 3, 4, 6, 7, 8], \
            [0, 2, 4, 5, 6, 8], \
            [0, 2, 4, 6, 8], \

            [0, 2, 4, 6, 8], \
            [0, 2, 4, 5, 6, 8], \
            [0, 2, 3, 4, 6, 7, 8], \
            [0, 2, 3, 4, 5, 6, 7, 8], \
            [0, 2, 4, 6, 8], \
            [0, 2, 3, 4, 5, 6, 7, 8], \
            [0, 2, 3, 4, 6, 7, 8], \
            [0, 2, 4, 5, 6, 8], \
            [0, 2, 4, 6, 8], \

            [0, 2, 4, 6, 8], \
            [0, 2, 4, 5, 6, 8], \
            [0, 2, 3, 4, 6, 7, 8], \
            [0, 2, 3, 4, 5, 6, 7, 8], \
            [0, 2, 4, 6, 8], \
            [0, 2, 3, 4, 5, 6, 7, 8], \
            [0, 2, 3, 4, 6, 7, 8], \
            [0, 2, 4, 5, 6, 8], \
            [0, 2, 4, 6, 8]
            ]


        for t in range(len(test_parameters)):
            test = test_parameters[t]
            
            for i in range(len(test[2])):
                p = test[2][i]
                P0 = self.cell_row(p, row_count)
                P1 = self.cell_col(p, col_count)
                computed = sqc.active_pixel_index(test[0], [P0, P1], test[1])
                expected = expected_results[t][i]
                if computed != expected_results[t][i]:
                    print('')
                    print('difference: test', t, 'pixel', i, \
                        'expected', expected_results[t][i], \
                        'computed', computed)
                assert computed == expected_results[t][i]

    def test_line_state(self):
        """Test the state of the sweep line on a 9x9 hand-made grid by testing
        every pixel reached by the sweep line. Nice thing about this test:
        the coordinates come from the same grid, with O at (0, 0)"""
        origin_and_end = [ \
            [[0, 0], [0, 4]], \
            [[0, 0], [1, 4]], \
            [[0, 0], [2, 4]], \
            [[0, 0], [3, 4]], \
            [[0, 0], [4, 4]], \
            [[0, 0], [4, 3]], \
            [[0, 0], [4, 2]], \
            [[0, 0], [4, 1]], \
            [[0, 0], [4, 0]], \
            [[0, 0], [4,-1]], \
            [[0, 0], [4,-2]], \
            [[0, 0], [4,-3]], \
            [[0, 0], [4,-4]], \
            [[0, 0], [3,-4]], \
            [[0, 0], [2,-4]], \
            [[0, 0], [1,-4]], \
            [[0, 0], [0,-4]], \
            [[0, 0], [-1,-4]], \
            [[0, 0], [-2,-4]], \
            [[0, 0], [-3,-4]], \
            [[0, 0], [-4,-4]], \
            [[0, 0], [-4,-3]], \
            [[0, 0], [-4,-2]], \
            [[0, 0], [-4,-1]], \
            [[0, 0], [-4,-0]], \
            [[0, 0], [-4, 1]], \
            [[0, 0], [-4, 2]], \
            [[0, 0], [-4, 3]], \
            [[0, 0], [-4, 4]], \
            [[0, 0], [-3, 4]], \
            [[0, 0], [-2, 4]], \
            [[0, 0], [-1, 4]], \
            ]
        cell_indices = [ \
            [0, 2, 4, 6, 8], \
            [0, 2, 4, 5, 6], \
            [0, 2, 3, 4, 6, 7], \
            [0, 2, 3, 4, 5, 6], \
            [0, 2, 4], \
            [0, 2, 3, 4, 5, 6], \
            [0, 2, 3, 4, 6, 7], \
            [0, 2, 4, 5, 6], \
            [0, 2, 4, 6, 8], \
            [0, 2, 4, 5, 6], \
            [0, 2, 3, 4, 6, 7], \
            [0, 2, 3, 4, 5, 6], \
            [0, 2, 4], \
            [0, 2, 3, 4, 5, 6], \
            [0, 2, 3, 4, 6, 7], \
            [0, 2, 4, 5, 6], \
            [0, 2, 4, 6, 8], \
            [0, 2, 4, 5, 6], \
            [0, 2, 3, 4, 6, 7], \
            [0, 2, 3, 4, 5, 6], \
            [0, 2, 4], \
            [0, 2, 3, 4, 5, 6], \
            [0, 2, 3, 4, 6, 7], \
            [0, 2, 4, 5, 6], \
            [0, 2, 4, 6, 8], \
            [0, 2, 4, 5, 6], \
            [0, 2, 3, 4, 6, 7], \
            [0, 2, 3, 4, 5, 6], \
            [0, 2, 4], \
            [0, 2, 3, 4, 5, 6], \
            [0, 2, 3, 4, 6, 7], \
            [0, 2, 4, 5, 6], \
        ]
        cell_points = [ \
            [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]], \
            [[0, 0], [0, 1], [0, 2], [1, 2], [1, 3]], \
            [[0, 0], [0, 1], [1, 1], [1, 2], [1, 3], [2, 3]], \
            [[0, 0], [0, 1], [1, 1], [1, 2], [2, 2], [2, 3]], \
            [[0, 0], [1, 1], [2, 2]], \
            [[0, 0], [1, 0], [1, 1], [2, 1], [2, 2], [3, 2]], \
            [[0, 0], [1, 0], [1, 1], [2, 1], [3, 1], [3, 2]], \
            [[0, 0], [1, 0], [2, 0], [2, 1], [3, 1]], \
            [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]], \
            [[0, 0], [1, 0], [2, 0], [2,-1], [3,-1]], \
            [[0, 0], [1, 0], [1,-1], [2,-1], [3,-1], [3,-2]], \
            [[0, 0], [1, 0], [1,-1], [2,-1], [3,-1], [3,-2]], \
            [[0, 0], [1,-1], [2,-2]], \
            [[0, 0], [0,-1], [1,-1], [1,-2], [2,-2], [2,-3]], \
            [[0, 0], [0,-1], [1,-1], [1,-2], [1,-3], [2,-3]], \
            [[0, 0], [0,-1], [0,-2], [1,-2], [1,-3]], \
            [[0, 0], [0,-1], [0,-2], [0,-3], [0,-4]], \
            [[0, 0], [0,-1], [0,-2], [-1,-2], [-1,-3]], \
            [[0, 0], [0,-1], [-1,-1], [-1,-2], [-1,-3], [-2, -3]], \
            [[0, 0], [0,-1], [-1,-1], [-1,-2], [-2,-2], [-2, -3]], \
            [[0, 0], [-1,-1], [-2,-2]], \
            [[0, 0], [-1, 0], [-1,-1], [-2,-1], [-2,-2], [-3,-2]], \
            [[0, 0], [-1, 0], [-1,-1], [-2,-1], [-3,-1], [-3,-2]], \
            [[0, 0], [-1, 0], [-2, 0], [-2,-1], [-3,-1]], \
            [[0, 0], [-1, 0], [-2, 0], [-3, 0], [-4, 0]], \
            [[0, 0], [-1, 0], [-2, 0], [-2, 1], [-3, 1]], \
            [[0, 0], [-1, 0], [-1, 1], [-2, 1], [-3, 1], [-3, 2]], \
            [[0, 0], [-1, 0], [-1, 1], [-2, 1], [-2, 2], [-3, 2]], \
            [[0, 0], [-1, 1], [-2, 2]], \
            [[0, 0], [0, 1], [-1, 1], [-1, 2], [-2, 2], [-2, 3]], \
            [[0, 0], [0, 1], [-1, 1], [-1, 2], [-1, 3], [-2, 3]], \
            [[0, 0], [0, 1], [ 0, 2], [-1, 2], [-1, 3]], \
        ]


        for (O,E), ID, P in zip(origin_and_end, cell_indices, cell_points):
            for i, p in zip(ID, P):
                computed = sqc.active_pixel_index(O, p, E)
                message = 'Point ' + str(p) + ' in ' + str((O, E)) + \
                    ' expected at ' + str(i) + ' but computed at ' + \
                    str(computed) + ': ' + str(zip(P, ID))
            assert i == computed, message


    def test_visibility_basic_array(self):
        DEM_size = 31
        elevation = np.zeros((DEM_size, DEM_size))
        nodata = -1
        viewpoint = (DEM_size/2, DEM_size/2)
        elevation[viewpoint[0]+1, viewpoint[1]+1] = 2.
        obs_elev = 1.0
        tgt_elev = 0.0
        max_dist = 4 
        cell_size = 5.0
        refraction_coeff = 0.13
        alg_version = 'cython' #'python'
        visibility = sqc.compute_viewshed(elevation, nodata, viewpoint, \
            obs_elev, tgt_elev, max_dist, cell_size, refraction_coeff, \
            alg_version)
        visibility[visibility > 0] = 1
        visibility[visibility < 0] = 0
        visibility[DEM_size/2, DEM_size/2] = 2
        #print(visibility.astype(int))

    def test_cython_vs_python_on_default_1_pt_data(self):
	return
        args_uri = "../../ScenicQuality/tests/default-1-pt/run_parameters_default-1-pt.json"
        with open(args_uri) as args_file:
            args = json.load(args_file)
        sq.execute(args)
        reference_uri = "../../ScenicQuality/tests/default-1-pt/python/output/vshed.tif"
        reference_raster = gdal.Open(reference_uri)
        message = "Cannot open " + reference_uri
        assert reference_raster is not None, message
        reference_band = reference_raster.GetRasterBand(1)
        reference_array = reference_band.ReadAsArray()
        computed_uri = "../../ScenicQuality/tests/default-1-pt/cython/output/vshed.tif"
        computed_raster = gdal.Open(computed_uri)
        message = "Cannot open " + computed_uri
        assert computed_raster is not None, message
        computed_band = computed_raster.GetRasterBand(1)
        computed_array = computed_band.ReadAsArray()
        difference = np.sum(np.absolute(reference_array - computed_array))
        message = "Computed viewshed " + computed_uri + \
            " doesn't correspond to " + reference_uri + '. diff = ' + \
            str(difference)
        assert difference == 0.0, message
	return

    def test_cython_vs_python_on_default_data_data(self):
	return
        args_uri = "../../ScenicQuality/tests/default-data/run_parameters_default-data.json"
        with open(args_uri) as args_file:
            args = json.load(args_file)
        sq.execute(args)
        reference_uri = "../../ScenicQuality/tests/default-data/python/output/vshed.tif"
        reference_raster = gdal.Open(reference_uri)
        message = "Cannot open " + reference_uri
        assert reference_raster is not None, message
        reference_band = reference_raster.GetRasterBand(1)
        reference_array = reference_band.ReadAsArray()
        computed_uri = "../../ScenicQuality/tests/default-data/cython/output/vshed.tif"
        computed_raster = gdal.Open(computed_uri)
        message = "Cannot open " + computed_uri
        assert computed_raster is not None, message
        computed_band = computed_raster.GetRasterBand(1)
        computed_array = computed_band.ReadAsArray()
        difference = np.sum(np.absolute(reference_array - computed_array))
        message = "Computed viewshed " + computed_uri + \
            " doesn't correspond to " + reference_uri + '. diff = ' + \
            str(difference)
        assert difference == 0.0, message
	return

    def test_cython_vs_python_on_block_island(self):
        return
        args_uri = "../../ScenicQuality/tests/block-island/run_parameters_block-island.json"
        with open(args_uri) as args_file:
            args = json.load(args_file)
            for entry in args:
                print('entry', entry, args[entry], type(args[entry]))
        sq.execute(args)
        reference_uri = "../../ScenicQuality/tests/block-island/python/output/vshed.tif"
        reference_raster = gdal.Open(reference_uri)
        message = "Cannot open " + reference_uri
        assert reference_raster is not None, message
        reference_band = reference_raster.GetRasterBand(1)
        reference_array = reference_band.ReadAsArray()
        computed_uri = "../../ScenicQuality/tests/block-island/cython/output/vshed.tif"
        computed_raster = gdal.Open(computed_uri)
        message = "Cannot open " + computed_uri
        assert computed_raster is not None, message
        computed_band = computed_raster.GetRasterBand(1)
        computed_array = computed_band.ReadAsArray()
        difference = np.sum(np.absolute(reference_array - computed_array))
        message = "Computed viewshed " + computed_uri + \
            " doesn't correspond to " + reference_uri + '. diff = ' + \
            str(difference)
        assert difference == 0.0, message
	return

    def test_visibility_simple_obstacles(self):
        return
        obs_elev = 1.0
        tgt_elev = 0.0
        max_dist = -1.0
        coefficient = 1.0
        height = 0.0
        refraction_coeff = 0.13
        base_dem_uri = "../../AQ_Rob/Block_Island_fast_alg/SQ/bi_100meters/hdr.adf"
        base_dem_nodata = raster_utils.get_nodata_from_uri(base_dem_uri)
	raster = gdal.Open(base_dem_uri)
        band = raster.GetRasterBand(1)
        base_array = band.ReadAsArray()
        (rows, cols) = base_array.shape
        band = None
        raster = None
        cell_size = raster_utils.get_cell_size_from_uri(base_dem_uri)
        GT = raster_utils.get_geotransform_uri(base_dem_uri)
        iGT = gdal.InvGeoTransform(GT)[1]
        flat_dem_uri = "flat_dem.tif"

        structure_uri = "../../AQ_Rob/Block_Island_fast_alg/SQ/1_pt/e911_132.shp"
        shapefile = ogr.Open(structure_uri)
        assert shapefile is not None
        layer = shapefile.GetLayer(0)
        assert layer is not None
        feature = layer.GetFeature(0)
        field_count = feature.GetFieldCount()
        # Check for feature information (radius, coeff, height)
        for field in range(field_count):
            field_def = feature.GetFieldDefnRef(field)
            field_name = field_def.GetNameRef()
            if (field_name.upper() == 'RADIUS2') or \
                (field_name.upper() == 'RADIUS'):
                max_dist = abs(int(feature.GetField(field)))
                assert max_dist is not None, "max distance can't be None"
                max_dist = int(max_dist/cell_size)
            if field_name.lower() == 'coeff':
                coefficient = float(feature.GetField(field))
                assert coefficient is not None, "feature coeff can't be None"
            if field_name.lower() == 'offseta':
                obs_elev = float(feature.GetField(field))
                assert obs_elev is not None, "OFFSETA can't be None"
            if field_name.lower() == 'offsetb':
                tgt_elev = float(feature.GetField(field))
                assert tgt_elev is not None, "OFFSETB can't be None"
                
        geometry = feature.GetGeometryRef()
        assert geometry is not None
        message = 'geometry type is ' + str(geometry.GetGeometryName()) + \
        ' point is "POINT"'
        assert geometry.GetGeometryName() == 'POINT', message
        x = geometry.GetX()
        y = geometry.GetY()
        j = int((iGT[0] + x*iGT[1] + y*iGT[2]))
        i = int((iGT[3] + x*iGT[4] + y*iGT[5]))

        viewpoint = (i, j)

        print('x', x, 'y', y, 'i', i, 'j', j)
        print('RADIUS', max_dist, 'coefficient', coefficient, \
            'obs_elev', obs_elev, 'tgt_elev', tgt_elev)

        raster_utils.new_raster_from_base_uri( \
            base_dem_uri, flat_dem_uri, 'GTiff', 2., gdal.GDT_Float32, \
            fill_value = base_dem_nodata, n_rows = rows, n_cols = cols)

	raster = gdal.Open(flat_dem_uri, gdal.GA_Update)
        band = raster.GetRasterBand(1)
        array = band.ReadAsArray()

        alg_version = 'python'
        print('array_shape', base_array.shape)
        print('viewpoint', viewpoint)
        visibility = sqc.compute_viewshed(base_array, base_dem_nodata, \
            viewpoint, obs_elev, tgt_elev, max_dist, cell_size, \
            refraction_coeff, alg_version)
        visibility[viewpoint[0], viewpoint[1]] = 2
        #sqc.viewshed(
        #    input_array, cell_size, array_shape, nodata, tmp_visibility_uri,
        #    (i,j), obs_elev, tgt_elev, max_dist, refr_coeff)
        band.WriteArray(visibility)
	print('file saved in', os.path.join(os.getcwd(), flat_dem_uri))

    def test_visibility_multiple_points(self):
        pass

    def tare_down(self):
        """ Clean up code."""
        # Do nothing for now 
        pass
