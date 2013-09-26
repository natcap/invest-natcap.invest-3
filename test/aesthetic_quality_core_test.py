import unittest
import logging
import math
import collections

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
        # Compute the minimum and maximum angles by goignt hrough each corner
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

    def find_angle_index(self, angle_list, angle):
        breadth = angle_list.size / 2
        
        index = breadth
        print('index', index, 'breadth', breadth)
        while (angle_list[index] > angle) or (angle_list[index + 1] < angle):
            breadth /= 2
            if angle_list[index] > angle:
                index -= breadth
            if angle_list[index + 1] < angle:
                index += breadth
            print('index', index, 'breadth', breadth)
            if breadth == 0:
                return index

    def test_skip_list(self):
        """Test the data structure that holds active pixels in the sweep line
        What is tested:
            1- At the leaves:
                1.1- insertions:
                    1.1.1- check for list length
                    1.1.2- check elements are sorted
                1.2- deletions:
                    1.2.1- check for list length
                    1.2.2- check elements are sorted
                1.3- access for data retreival
                    1.3.1- check the right element is retreived
                    1.3.2- check return value is None if element is not there
                    1.3.3- O(log n) performance is maintained
            2- In the intermediate levels:
                2.1- creation of skip links after leaf insertions:
                    2.1.1- insert new leaf in the right place
                    2.1.2- create intermediate links when and where expected
                    2.1.3- O(log n) performance is maintained
                2.2- deletion of skip links after leaf deletions:
                    2.2.1- delete the correct leaf
                    2.2.2- trim intermediate links: the skip list reduces to 1
                    2.2.3- O(log n) performance is maintained
                2.3- fast access:
                    2.3.1- Finds the appropriate value
                    2.3.2- O(log n) performance is maintained"""
        # 1- Leaf operations:
        # 1.1- leaf insertions
        # Add random elements to the list
        test_list = {}
        additions = 50
        forward_range = np.array(range(additions)) * 2
        inverted_range = forward_range[::-1]
        shuffled_range = np.copy(forward_range)
        np.random.shuffle(shuffled_range)
        half_shuffled_range = np.copy(shuffled_range[:shuffled_range.size/2])
        np.random.shuffle(half_shuffled_range)
        for i in shuffled_range:
            distance = i
            visibility = 0
            aesthetic_quality_core.add_active_pixel(test_list, distance, \
                visibility)
        expected_length = additions + 1
        actual_length = len(test_list)
        # 1.1.1- Check for list length 
        message = 'Unexpected dictionary size after additions (' + \
            str(expected_length) + ' expected ' + str(actual_length)
        assert expected_length == actual_length, message
        # 1.1.2- Check elements are sorted
        distances = []
        current = test_list['closest']
        distances.append(current['distance'])
        while current['next'] is not None:
            current = current['next']
            distances.append(current['distance'])
        distances = np.array(distances)
        differences = distances[1:] - distances[:-1]
        all_differences_negative = (differences > 0).all()
        message = 'Array elements are not sorted in increasing order: '  + \
            str(distances)
        assert all_differences_negative, message
        # 1.2- leaf removal
        # Removing element that is not in the list
        length_before = len(test_list)
        aesthetic_quality_core.remove_active_pixel(test_list, 1)
        actual_length_decrease = length_before - len(test_list)
        message = 'Unexpected length decrease ' + str(actual_length_decrease)+\
        ', expected 0'
        # Removing random elements from the list
        for i in shuffled_range:
            distance = i
            aesthetic_quality_core.remove_active_pixel(test_list, distance)
        expected_length = 0
        actual_length = len(test_list)
        # 1.2.1- Check for list length 
        message = 'Unexpected dictionary size after removal ' + \
            str(actual_length) + ' expected ' + str(expected_length) + \
            " dictionary: " + str(test_list)
        assert expected_length == actual_length, message
        # 1.3- access for data retreival
        distance = 1
        aesthetic_quality_core.add_active_pixel(test_list, distance, 0.5)
        pixel = aesthetic_quality_core.find_active_pixel(test_list, distance)
        # 1.3.1- check the right element is retreived
        message = 'Error, returned None for a pixel that should be in the list'
        assert pixel is not None, message
        message = "Failed to retreive the right pixel. Expected 1, found " + \
            str(pixel['distance'])
        assert pixel['distance'] == distance, message
        # 1.3.2- check return value is None if element is not there
        pixel = aesthetic_quality_core.find_active_pixel(test_list, distance+1)
        message = "Wrong return value for searching a non-existent item: " + \
            str(pixel)
        assert pixel is None, message
        # 1.3.3- O(log n) performance is maintained
        # 2- Intermediate nodes insertion 
        # 2.3- fast access:
        # Create a hierarchy that can be searched:
        # The basal sweep line:
        sweep_line = {}
        sweep_line[0] = {'next':None, 'up':None, 'down':None, 'distance':0}
        sweep_line['closest'] = sweep_line[0]
        sweep_line[2] = {'next':None, 'up':None, 'down':None, 'distance':2}
        sweep_line[0]['next'] = sweep_line[2]
        sweep_line[4] = {'next':None, 'up':None, 'down':None, 'distance':4}
        sweep_line[2]['next'] = sweep_line[4]
        sweep_line[6] = {'next':None, 'up':None, 'down':None, 'distance':6}
        sweep_line[4]['next'] = sweep_line[6]
        # Creating the skip node hierarchy:
        skip_nodes = []
        # skip_nodes[0]
        skip_nodes.append([])
        # skip_nodes[0][0]
        skip_nodes[0].append({'next':None, 'up':None, 'down':sweep_line[0], \
            'span':2, 'distance':sweep_line[0]['distance']})
        # skip_nodes[0][1
        skip_nodes[0].append({'next':None, 'up':None, 'down':sweep_line[4], \
            'span':2, 'distance':sweep_line[4]['distance']})
        skip_nodes[0][0]['next'] = skip_nodes[0][1]
        # skip_nodes[1]
        skip_nodes.append([])
        # skip_nodes[1][0]
        skip_nodes[1].append({'next':None, 'up':None, \
        'down':skip_nodes[0][0], 'span':2, \
        'distance':skip_nodes[0][0]['distance']})
        skip_nodes[0][0]['up'] = skip_nodes[1][0]
        # Adjusting the 'up' fields in sweep_line elements:
        sweep_line[0]['up'] = skip_nodes[0][0]
        sweep_line[4]['up'] = skip_nodes[0][1]
        # Check all the skip levels are accessible:
        current_node = skip_nodes[0][-1]
        # -- Debug info for sanity check:
        print('Skip pointers hierarchy:')
        print('active pixels:')
        current = sweep_line['closest']
        right = current['next']
        print('distance ' + str(current['distance']) + ', next ' + \
            str(right if right is None else right['distance']))
        while(right is not None):
            current = current['next']
            right = current['next']
            print('distance ' + str(current['distance']) + ', next ' + \
                str(right if right is None else right['distance']))
        for level in range(len(skip_nodes)):
            print('skip nodes level ' + str(level) + ':')
            current = skip_nodes[level][0]
            right = current['next']
            span = current['span']
            print('distance ' + str(current['distance']) + ', next ' + \
                str(right if right is None else right['distance']), \
                'down ' + str(current['down']['distance']), \
                'span', span)
            while(right is not None):
                current = current['next']
                right = current['next']
                print('distance ' + str(current['distance']) + ', next ' + \
                    str(right if right is None else right['distance']), \
                    'down ' + str(current['down']['distance']), \
                    'span', span)
        # Test the data structure is valid
        print('skip list is consistent', \
            self.skip_list_is_consistent(sweep_line, skip_nodes))
        # 2.3.1- Find the appropriate value
        for distance in [0, 2, 4, 6, -1, 3, 7]:
            found = aesthetic_quality_core.find_active_pixel_fast(sweep_line, \
                skip_nodes, distance)
            expected = aesthetic_quality_core.find_active_pixel(sweep_line, distance)
            message = 'Error: return value is ' + str(found) + \
            ', expected is ' + str(expected)
            assert found == expected, message
        # 2.3.2- O(log n) performance is maintained


    def skip_list_is_consistent(self, linked_list, skip_nodes):
        """Function that checks for skip list inconsistencies.
        
            Inputs: 
                -sweep_line: the container proper which is a dictionary
                    implementing a linked list that contains the items 
                    ordered in increasing distance
                -skip_nodes: python dict that is the hierarchical structure 
                    that sitting on top of the sweep_line to allow O(log n) 
                    operations.
            
            Returns True if list is consistent, False otherwise"""
        # 1-Testing the linked_list:
        #   1.1-If len(linked_list) > 0 then len(linked_list) >= 2
        #   1.2-If len(linked_list) > 0 then 'closest' exists
        #   1.3-down is None
        #   1.4-No negative distances
        #   1.5-distances increase
        #   1.6-Check the gaps between the up pointers
        #   1.7-Check the number of up pointers is valid
        #   1.8-chain length is 1 less than len(linked_list)
        #   1.9-The non-linked element is the same as linked_list['closest']
        #   1.10-linked_list['closest'] is the smallest distance
        #   1.11-Last element has 'next' set to None
        if len(linked_list) == 0:
            return True
        
        # 1.1-If len(linked_list) > 0 then len(linked_list) >= 2
        if len(linked_list) < 2:
            return False
        # 1.2-If len(linked_list) > 0 then 'closest' exists
        if not linked_list.has_key('closest'):
            return False

        pixel = linked_list['closest']
        chain_length = 1
        # 1.3-down is None
        if pixel['down'] is not None:
            return False

        last_distance = pixel['distance']
        # 1.4-No negative distances
        if last_distance < 0:
            return False

        # Minimum and maximum number of allowed up pointers
        min_up_count = math.ceil(float((len(linked_list) -1) / 3))
        max_up_count = math.ceil(float((len(linked_list) -1) / 2))

        up_count = 0    # actual number of up pointers
        up_gap = -1     # gap since last up pointer
        
        # Traverse the linked list
        while pixel['next'] is not None:
            pixel = pixel['next']
            chain_length += 1
            # 1.3-down is None
            if pixel['down'] is not None:
                return False
            # 1.5-distances increase
            if (pixel['distance'] - last_distance) <= 0.:
                return False
            last_distance = pixel['distance']
            # Updating the number of 'up' pointers and the gap between them
            if pixel['up'] is not None:
                # It's not the first 'up' pointer, so check the gap is ok
                # 1.6-Check the gaps between the up pointers
                if up_count > 0:
                    if up_gap < 1:
                        return False
                    if up_gap > 2:
                        return False
                up_count += 1
                up_gap = -1
            # If there are up pointers, updating the gap
            if up_count:
                up_gap += 1

        # 1.7-Check the number of up pointers is valid
        if up_count > max_up_count:
            return False
        if up_count < min_up_count:
            return False

        # 1.8-chain length is 1 less than len(linked_list)
        if (chain_length != len(linked_list) -1):
            return False
        # 1.9-linked_list['closest'] is the smallest distance
        # True if 1.5 and 1.8 are true
        # 1.10-The non-linked element is the same as linked_list['closest']
        if not linked_list.has_key(linked_list['closest']['distance']):
            return False
        # 1.11-Last element has 'next' set to None
        # True if 1.8 and 1.10 are true

        # 2-Testing the skip pointers
        #   2.1-The entry 'down' is never None
        #   2.2-The 'up' entries at a lower level match the # of higher entries
        #   2.3-The number of pointers at each level has to be valid
        #   2.4-The gaps between each pointer at each level has to be valid
        #   2.5-Each skip node references the right element in the linked list
        #   2.6-Each skip node at the end of its level has 'next' == None
        #   2.7-All the skip nodes can be reached from the first one on top
        #   2.8-All the distances at a given level increase
        #   2.9-The span at each skip node is either 2 or 3
        #   2.10-The last node spanned by a higher skip node is right before the
        #       first node spanned by the next higher skip node
        #   2.11-The first top level node always points to 'closest'

        total_skip_nodes = 0
        for l in range(len(skip_nodes)):
            total_skip_nodes += len(skip_nodes[l])
            # 2.6-Each skip node at the end of its level has 'next' == None
            if skip_nodes[l][-1]['next'] is not None:
                return False
            previous_distance = skip_nodes[l][0]['distance'] -1
            for n in range(len(skip_nodes[l])):
                node = skip_nodes[l][n]
                # 2.1-The entry 'down' is never None
                if node['down'] is None:
                    return False
                # 2.8-All the distances at a given level increase
                distance = node['distance']
                if distance <= previous_distance:
                    return False
                # 2.9-The span at each skip node is either 2 or 3
                if (node['span'] != 2) and (node['span'] != 3):
                    return False
                # 2.10-The last node spanned by a higher skip node is right
                # before the first node spanned by the next higher skip node
                # How to test:
                #
                # level |     nodes
                #   2   |   0------->5----->
                #   1   |   0->2->3->5->6->8 
                #
                # Node 0 at level 2 has a span of 3:
                #  1-From level 2, go down from node 0 until node 3
                #  2-From level 2, go down from node 5
                # See if node 3's next (from step 1) is the same as the node 
                # from step 2.
                if n < (len(skip_nodes[l])-1):
                    # Step 1, get 
                    last_node = node['down']
                    for i in range(node['span'] -1):
                        last_node = last_node['next']
                    next_node = node['next']['down']
                    # Last spanned node is connected to the next one. See if
                    # the node after the last is 
                    if last_node['next']['distance'] != next_node['distance']:
                        return False
                # 2.5-Each skip node references the right element in the 
                # linked list, i.e. each node's distance values are identical
                while node['down'] is not None:
                    node = node['down']
                    if node['distance'] != distance:
                        return False
                previous_distance = distance
        # 2.11-The first top level node always points to 'closest'
        if (skip_nodes[-1][0]['distance'] !=linked_list['closest']['distance']):
            return False
        # 2.2-The 'up' entries at a lower level match the # of higher entries
        # Find the number of 'up' entries in linked_list
        node = linked_list['closest']
        lower_level_size = 1
        up_count = 0
        if node['up'] is not None:
            up_count += 1
        while node['next'] is not None:
            node = node['next']
            lower_level_size += 1
            if node['up'] is not None:
                up_count += 1
        print('up_count', up_count)

        skip_nodes_size = 0
        for level in range(len(skip_nodes)):
            # Count the number of 'up' that are not None at this level
            level_up_count = 0
            up_gap = -1
            node = skip_nodes[level][0]
            if node['up'] is not None:
                level_up_count += 1
            while node['next'] is not None:
                node = node['next']
                if node['up'] is not None:
                    # It's not the first 'up' pointer, so check the gap is ok
                    # 2.4-Check the gaps between the up pointers
                    if level_up_count > 0:
                        if up_gap < 1:
                            return False
                        if up_gap > 2:
                            return False
                    level_up_count += 1
                    up_gap = -1
                # If there are up pointers, updating the gap
                if level_up_count:
                    up_gap += 1
            # 2.2-The 'up' entries at a lower level match the # higher entries
            if up_count != len(skip_nodes[level]):
                return False
            # Minimum and maximum number of allowed up pointers
            min_up_count = math.ceil(float(len(skip_nodes[level])-1) / 3)
            max_up_count = math.ceil(float(len(skip_nodes[level])-1) / 2)
            # 2.3-The number of pointers at each level has to be valid
            if level_up_count > max_up_count:
                print('len(skip_nodes[level])',len(skip_nodes[level]) )
                print(level, 'Error: level_up_count', level_up_count, \
                    '> max_up_count', max_up_count)
                return False
            if level_up_count < min_up_count:
                print('len(skip_nodes[level])', len(skip_nodes[level]))
                print(level, 'Error: level_up_count', level_up_count, \
                    '< min_up_count', min_up_count)
                return False
            lower_level_size = len(skip_nodes[level]) # update for next iter
            up_count = level_up_count
            print('up_count', up_count)

        # 2.7-All the skip nodes can be reached from the first one on top
        first_nodes = []
        # Create a list of first nodes for each level
        first_nodes.append(linked_list['closest']['up'])
        while first_nodes[-1]['up'] is not None:
            first_nodes.append(first_nodes[-1]['up'])
        # Traverse a level from the first node of a given level and count the
        # nodes encontered
        nodes_reached = 0
        for node in first_nodes:
            nodes_reached += 1
            while node['next'] is not None:
                node = node['next']
                nodes_reached += 1
        if nodes_reached != total_skip_nodes:
            return False

        return True

    def test_viewshed(self):
        array_shape = (6,6)
        DEM = np.random.random([array_shape[0], array_shape[1]]) * 10.
        viewpoint = (3, 1) #np.array([array_shape[0]/2, array_shape[1]/2])
        viewpoint_elevation = 1.75

        # 1- get perimeter cells
        perimeter_cells = self.get_perimeter_cells(array_shape, viewpoint)
        # 1.1- remove perimeter cell if same coord as viewpoint
        # 2- compute cell angles
        angles = self.cell_angles(perimeter_cells, viewpoint)
        angles = np.append(angles, 2.0 * math.pi)
        print('angles', angles.size, angles)
        # 3- compute information on raster cells
        events = \
        aesthetic_quality_core.list_extreme_cell_angles(array_shape, viewpoint)
        I = events[3]
        J = events[4]
        distances = (viewpoint[0] - I)**2 + (viewpoint[1] - J)**2
        visibility = \
        (DEM[(I, J)] - DEM[viewpoint[0], viewpoint[1]] - viewpoint_elevation) \
        / distances
        # 4- build event lists
        add_cell_events = []
        add_event_id = 0
        add_events = events[0]
        add_event_count = add_events.size
        cell_center_events = []
        center_event_id = 0
        center_events = events[1]
        center_event_count = center_events.size
        remove_cell_events = []
        remove_event_id = 0
        remove_events = events[2]
        remove_event_count = remove_events.size
        # 5- Sort event lists
        arg_min = np.argsort(events[0])
        #print('min', events[0][arg_min])
        arg_center = np.argsort(events[1])
        #print('center', events[1][arg_center])
        arg_max = np.argsort(events[2])
        #print('max', events[2][arg_max])
        
        # Add the events to the 3 event lists
        #print('index', self.find_angle_index(angles, 1.6))
        #print('center', events[1][arg_center])
        #print('center', arg_center)
        # Add center angles to center_events_array
        for a in range(1, len(angles)): 
            #print('current angle', angles[a])
            # Collect cell_center events
            current_events = []
            while (center_event_id < center_event_count) and \
                (center_events[arg_center[center_event_id]] < angles[a]):
                #print(events[1][arg_center[event_id]], '< current angle')
                #print('center', arg_center[center_event_id], center_events[arg_center[center_event_id]])
                current_events.append(arg_center[center_event_id])
                arg_center[center_event_id] = 0
                center_event_id += 1
            cell_center_events.append(np.array(current_events))
            # Collect add_cell events:
            current_events = []
            while (add_event_id < add_event_count) and \
                (add_events[arg_min[add_event_id]] < angles[a]):
                #print(events[0][arg_min[add_event_id]], '< current angle')
                if center_events[arg_min[add_event_id]] > 0.:
                    #print('add', arg_min[add_event_id],add_events[arg_min[add_event_id]])
                    current_events.append(arg_min[add_event_id])
                #else:
                #    print('    found 0:', arg_min[add_event_id])
                arg_min[add_event_id] = 0
                add_event_id += 1
            add_cell_events.append(np.array(current_events))
            # Collect remove_cell events:
            current_events = []
            while (remove_event_id < remove_event_count) and \
                (remove_events[arg_max[remove_event_id]] <= angles[a]):
                #print(events[2][arg_max[remove_event_id]], '< current angle')
                #print('remove', arg_max[remove_event_id], remove_events[arg_max[remove_event_id]])
                current_events.append(arg_max[remove_event_id])
                arg_max[remove_event_id] = 0
                remove_event_id += 1
            remove_cell_events.append(np.array(current_events))
        #print('add_cell_events', add_cell_events)

        # Create the binary search tree as depicted in Kreveld et al.
        # "Variations on Sweep Algorithms"
        # Updating active cells
        active_cells = set()
        active_line = {}
        # 1- add cells at angle 0
        for c in cell_center_events[0]:
            active_cells.add(c)
            d = distances[c]
            v = visibility[c]
            active_line = \
                aesthetic_quality_core.add_active_pixel(active_line, d, v)
        # 2- loop through line sweep angles:
        for a in range(len(angles) - 1):
            #print('sweep angle', a)
        #   2.1- add cells
            #print('  add cell events', add_cell_events[a])
            if add_cell_events[a].size > 0:
                for c in add_cell_events[a]:
                    #print('  adding', c)
                    active_cells.add(c)
        #   2.2- remove cells
            #print('  remove cell events', remove_cell_events[a])
            for c in remove_cell_events[a]:
                #print('  removing', c)
                active_cells.remove(c)
        #    print('  active cells', len(active_cells), active_cells)
        #print('active cells', active_cells, len(active_cells) == 0)

        # Sanity checks
        print('---------------------------------')
        print('add_cell events:')
        for i in range(len(add_cell_events)):
            add_cell_ids = add_cell_events[i]
            if add_cell_ids.size > 0:
                add_cell = add_events[add_cell_ids]
                print('within bounds:', (add_cell >= angles[i]).all() and \
                    (add_cell < angles[i+1]).all())
        print('unprocessed add_cell ids', np.where(arg_min > 0)[0])
        print('remove_cell events:')
        for i in range(len(remove_cell_events)):
            remove_cell_ids = remove_cell_events[i]
            if remove_cell_ids.size > 0:
                remove_cell = remove_events[remove_cell_ids]
                print('within bounds:', (remove_cell >= angles[i]).all() and \
                    (remove_cell <= angles[i+1]).all())
        print('unprocessed remove_cell ids', np.where(arg_max > 0)[0])
        print('cell_center events:')
        for i in range(len(cell_center_events)):
            cell_center_ids = cell_center_events[i]
            if cell_center_ids.size > 0:
                cell_centers = center_events[cell_center_ids]
                print('within bounds:', (cell_centers >= angles[i]).all() and \
                    (cell_centers < angles[i+1]).all())
        print('unprocessed cell_center ids', np.where(arg_center > 0)[0])
            
    def tare_down(self):
        pass
