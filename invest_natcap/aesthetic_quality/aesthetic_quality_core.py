import math

import numpy as np
import collections
import logging

#LOGGER = logging.get('aesthetic_quality_core')
#logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
#    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def list_extreme_cell_angles(array_shape, viewpoint_coords):
    """List the minimum and maximum angles spanned by each cell of a
        rectangular raster if scanned by a sweep line centered on
        viewpoint_coords.
    
        Inputs:
            -array_shape: a shape tuple (rows, cols) as is created from
                calling numpy.ndarray.shape()
            -viewpoint_coords: a 2-tuple of coordinates similar to array_shape
            where the sweep line originates
            
        returns a tuple (min, center, max, I, J) with min, center and max 
        Nx1 numpy arrays of each raster cell's minimum, center, and maximum 
        angles and coords as two Nx1 numpy arrays of row and column of the 
        coordinate of each point.
    """
    viewpoint = np.array(viewpoint_coords)

    pi = math.pi
    two_pi = 2. * pi
    rad_to_deg = 180.0 / pi
    deg_to_rad = 1.0 / rad_to_deg

    extreme_cell_points = [ \
    {'min_angle':[0.5, -0.5], 'max_angle':[-0.5, -0.5]}, \
    {'min_angle':[0.5, 0.5], 'max_angle':[-0.5, -0.5]}, \
    {'min_angle':[0.5, 0.5], 'max_angle':[0.5, -0.5]}, \
    {'min_angle':[-0.5, 0.5], 'max_angle':[0.5, -0.5]}, \
    {'min_angle':[-0.5, 0.5], 'max_angle':[0.5, 0.5]}, \
    {'min_angle':[-0.5, -0.5], 'max_angle':[0.5, 0.5]}, \
    {'min_angle':[-0.5, -0.5], 'max_angle':[-0.5, 0.5]}, \
    {'min_angle':[0.5, -0.5], 'max_angle':[-0.5, 0.5]}]

    min_angles = []
    angles = []
    max_angles = []
    I = []
    J = []
    for row in range(array_shape[0]):
        for col in range(array_shape[1]):
            # Skip if cell falls on the viewpoint
            if (row == viewpoint[0]) and (col == viewpoint[1]):
                continue
            cell = np.array([row, col])
            I.append(row)
            J.append(col)
            viewpoint_to_cell = cell - viewpoint
            # Compute the angle of the cell center
            angle = np.arctan2(-viewpoint_to_cell[0], viewpoint_to_cell[1])
            angles.append((angle + two_pi) % two_pi)
            # find index in extreme_cell_points that corresponds to the current
            # angle to compute the offset from cell center
            sector = int(4. * angles[-1] / two_pi) * 2
            if np.amin(np.absolute(viewpoint_to_cell)) > 0:
                sector += 1
            min_corner_offset = \
                np.array(extreme_cell_points[sector]['min_angle'])
            max_corner_offset = \
                np.array(extreme_cell_points[sector]['max_angle'])
            # Use the offset to compute extreme angles
            min_corner = viewpoint_to_cell + min_corner_offset
            min_angle = np.arctan2(-min_corner[0], min_corner[1])
            min_angles.append((min_angle + two_pi) % two_pi) 
            
            max_corner = viewpoint_to_cell + max_corner_offset
            max_angle = np.arctan2(-max_corner[0], max_corner[1])
            max_angles.append((max_angle + two_pi) % two_pi)
    # Create a tuple of ndarray angles before returning
    min_angles = np.array(min_angles)
    angles = np.array(angles)
    max_angles = np.array(max_angles)
    I = np.array(I)
    J = np.array(J)

    return (min_angles, angles, max_angles, I, J)

# Linked cells used for the active pixels
linked_cell_factory = collections.namedtuple('linked_cell', \
    ['previous', 'next', 'distance', 'visibility'])

# Links to the cells
cell_link_factory = collections.namedtuple('cell_link', \
    ['top', 'right', 'bottom', 'level', 'distance'])

def add_active_pixel_fast(sweep_line, skip_nodes, distance):
    """Insert an active pixel in the sweep_line and update the skip_nodes.
    
            -sweep_line: a linked list of linked_cell as created by the
                linked_cell_factory.
            -skip_nodes: an array of linked lists that constitutes the hierarchy
                of skip pointers in the skip list. Each cell is defined as ???
            -distance: the value to be added to the sweep_line

            Return a tuple (sweep_line, skip_nodes) with the updated sweep_line
            and skip_nodes"""

    def insert_new_skip_node(node, upper_node, skip_nodes):
        """Add a new skip node after 'node[up]'. Assumes node[up]'s span is 4
        
            Inputs: 
                -node: the overstretched node (span is too large) that needs
                    to be offloaded by a new intermediate node.
                -upper_node: the upper skip node which span should be updated.
                The variable is None if no upper node exists.
                -skip_nodes: dictionary of skip nodes to which the new skip
                node should be added.
            
            Returns the span at the node above, otherwise 'None'"""
        message = 'Span for node ' + str(node['distance']) + \
        ' expected to be 4, instead is ' + \
        str(node['up']['span'])
        assert node['up']['span'] == 4, message
        before = node['up']
        after = before['next']
        below = node['next']['next']
        current_distance = below['distance']
        skip_nodes[current_distance] = {'next':after, 'up':None, \
        'down':below, 'distance':current_distance, 'span':2}
        below['up'] = skip_nodes[current_distance]
        before['next'] = skip_nodes[current_distance]
        before['span'] = 2
        span = None
        if upper_node is not None:
            print('Updating upper node ' + str(upper_node['distance']) + '-' + \
            str(None) if upper_node['next'] is None else \
            str(upper_node['next']['distance']) + ' span from ' + \
            str(upper_node['span']) + ' to ' + str(upper_node['span'] + 1))
            upper_node['span'] += 1
            span = upper_node['span']
        else:
            print('Upper node is None')
            
        return span

    def update_skip_node_span(pixel, level, hierarchy, skip_nodes):
        """Update span for pixel and insert as many skip nodes as necessary. 
        Create additional hierarchical levels as necessary.
        
            Inputs:
                -node: the node right before the place of insertion
                -level: the level in skip_list where the new node will be
                -skip_nodes: the skip pointers hierarchy, which is a list of
                dictionaries containing skip_nodes indexed by the node's
                'distance' entry.
                
            Returns nothing."""
        while pixel['up'] is not None:
            print('adding span to node ' +str(pixel['up']['distance']) +' '+\
            str(level) + ' which currently is ' + str(pixel['up']['span']))
            pixel['up']['span'] += 1
            # Adjusting span if too large
            if pixel['up']['span'] > 3:
                # Insert the missing skip_node
                print('hierarchy depth is ' + str(len(hierarchy)))
                for node in hierarchy:
                    print('  node ', node['distance'], None if node['next'] is \
                    None else node['next']['distance'])
                upper_node = \
                hierarchy[level+1] if (len(hierarchy)>level+1) else None
                span = \
                insert_new_skip_node(pixel, upper_node, skip_nodes[level])
                # Create a new level if needed
                if (len(skip_nodes[level]) == 4) and \
                    (len(skip_nodes) == level + 1):
                    print('new level needed after ' + str(level))
                    skip_nodes.append({})
                    pixel = pixel['up']
                    distance = pixel['distance']
                    # First skip node points to the first element in sweep_line
                    skip_node = {'next':None, 'up':None, \
                    'down':skip_nodes[level][distance],\
                    'distance':pixel['distance'], 'span':2}
                    skip_nodes[level+1][distance] = skip_node
                    pixel['up'] = skip_nodes[+1][distance]
                    # Second skip node points to the second last element in sweep_line
                    second_last = pixel['next']['next']
                    second_distance = second_last['distance']
                    skip_node = {'next':None, 'up':None, \
                    'down':skip_nodes[level][second_distance], \
                    'distance':second_distance, 'span':2}
                    skip_nodes[level+1][second_distance] = skip_node
                    second_last['up'] = skip_nodes[level+1][second_distance]
                    skip_nodes[level+1][distance]['next'] = skip_nodes[level+1][second_distance]
                    # Check whether we should keep updating the skip_nodes
                    list_is_consistent, message = \
                        skip_list_is_consistent(sweep_line, skip_nodes)
                    # List is consistent, we're done: break out of the while
                    if not list_is_consistent:
                        print('Error after creating new level: ' + message)
                # Check whether we should keep updating the skip_nodes
                list_is_consistent, message = \
                    skip_list_is_consistent(sweep_line, skip_nodes)
                # List is consistent, we're done: break out of the while
                if (span == 2) or (span == 3):
                    break
                # We assume the only problem is potential intermediate skip
                # nodes that might be missing in the upper levels
                else:
                    #error_message = 'unexpected error ' + str(message)
                    #assert ('Level ' + str(level) + ':' in message) and \
                    #('< min_up_count' in message), error_message
                    pixel = pixel['up']
                    level += 1
            # Nothing to adjust, break outpof the while
            else:
                break

    # Add the field 'closest' to the empty sweep line
    if not sweep_line:
        sweep_line[distance] = {'next':None, 'up':None, 'down':None, \
            'distance':distance}
        sweep_line['closest'] = sweep_line[distance]
        return (sweep_line, skip_nodes)

    # If distance already exist in sweep_line, no need to re-organize
    if distance in sweep_line:
        # Code to update visibility here
        return (sweep_line, skip_nodes)

    # Need to re-organize the sweep line:
    pixel, hierarchy = find_pixel_before_fast( \
        sweep_line, skip_nodes, distance)
    #print('---pixel before addition', pixel if pixel is None else pixel['distance'])
    # Add to the beginning of the list
    if pixel is None:
        # New pixel points to previously first pixel
        second = sweep_line['closest']['distance']
        sweep_line[distance] = {'next':sweep_line[second], \
            'up':sweep_line[second]['up'], \
            'down':None, 'distance':distance}
        # Move skip pointers to the pixel
        sweep_line[second]['up'] = None
        # Update the skip pointer's distances:
        skip_node = sweep_line[distance]['up']
        if skip_node is not None:
            level = 0
            skip_node['distance'] = distance
            skip_node['down'] = sweep_line[distance]
            skip_nodes[level][distance] = skip_node
            del skip_nodes[level][second]
            sweep_line[distance]['up'] = skip_nodes[level][distance]
            while skip_node['up'] is not None:
                level += 1
                skip_node = skip_node['up']
                skip_node['distance'] = distance
                skip_node['down'] = skip_nodes[level-1][distance]
                #print('level', level, 'levels available', len(skip_nodes))
                skip_nodes[level][distance] = skip_node
                del skip_nodes[level][second]
                if level < len(skip_nodes) -1:
                    skip_nodes[level][distance]['up'] = \
                        skip_nodes[level][distance]
                else:
                    skip_nodes[level][distance]['up'] = None
        # Updating span
        if sweep_line[distance]['up'] is not None:
            print('Increasing span ' + str(sweep_line[distance]['up']['span']) + \
            ' of new front pixel ' + str(distance))
        update_skip_node_span(sweep_line[distance], 0, hierarchy, skip_nodes)
        # The old first is not first anymore: shouldn't point up
        sweep_line[second]['up'] = None
        # pixel 'closest' points to first
        #print('making closest point to ' + str(sweep_line[distance]['distance']))
        sweep_line['closest'] = sweep_line[distance]
    # Add after the beginning
    else:
        # Connecting new pixel to next one
        sweep_line[distance] = {'next':pixel['next'], 'up':None, \
            'down':None, 'distance':distance}
        # Connecting previous pixel to new one
        pixel['next'] = sweep_line[distance]
        # Update the span if necessary
        if hierarchy:
            #for p in range(len(hierarchy)):
            #    print('hierarchy', p, hierarchy[p]['distance'])
            update_skip_node_span(hierarchy[-1]['down'], 0, hierarchy, skip_nodes)

    if len(sweep_line) == 5:
        # Preparing the skip_list to receive the new skip pointers
        skip_nodes = []
        skip_nodes.append({})
        pixel = sweep_line['closest']
        distance = pixel['distance']
        # First skip node points to the first element in sweep_line
        skip_node = {'next':None, 'up':None, \
        'down':sweep_line[distance], 'distance':distance, 'span':2}
        skip_nodes[0][distance] = skip_node
        sweep_line[distance]['up'] = skip_nodes[0][distance]
        # Second skip node points to the second last element in sweep_line
        second_last = sweep_line['closest']
        while second_last['next']['next'] is not None:
            second_last = second_last['next']
        second_distance = second_last['distance']
        skip_node = {'next':None, 'up':None, 'down':second_last, \
        'distance':second_distance, 'span':2}
        skip_nodes[0][second_distance] = skip_node
        sweep_line[second_distance]['up'] = skip_nodes[0][second_distance]
        skip_nodes[0][distance]['next'] = skip_nodes[0][second_distance]

    print('--after change:')
    sorted_keys = sorted(sweep_line.keys())
    for key in sorted_keys:
        print(key, 'next', sweep_line[key]['next'] if sweep_line[key]['next'] is None
            else sweep_line[key]['next']['distance'], \
            'up', None if sweep_line[key]['up'] is None else \
            sweep_line[key]['up']['distance'])
    print('--skip_nodes:')
    for level in range(len(skip_nodes)):
        print('level', level)
        sorted_keys = sorted(skip_nodes[level])
        for key in sorted_keys:
            skip_node = skip_nodes[level][key]
            print(skip_node['distance'], 'span', skip_node['span'], \
            'next', None if skip_node['next'] is None else \
            skip_node['next']['distance'], 'up', None if skip_node['up'] \
            is None else skip_node['up']['distance'])

    return (sweep_line, skip_nodes)

def find_pixel_before_fast(sweep_line, skip_nodes, distance):
    """Find the active pixel before the one with distance. 
        
        Inputs:
            -sweep_line: a linked list of linked_cell as created by the
                linked_cell_factory.
            -skip_list: an array of linked lists that constitutes the hierarchy
                of skip pointers in the skip list. Each cell is defined as ???
            -distance: the key used to search the sweep_line

            Return a tuple (pixel, hierarchy) where: 
                -pixel is the linked_cell right before 'distance', or None if 
                it doesn't exist (either 'distance' is the first cell, or the 
                sweep_line is empty).
                -hierarchy is the list of intermediate skip nodes starting from
                the bottom node right above the active pixel up to the top node.
            """
    hierarchy = []
    if 'closest' in sweep_line:
        # Find the starting point
        if len(skip_nodes) > 0:
            level = len(skip_nodes) -1
            # Get information about first pixel in the list
            first = sorted(skip_nodes[level].keys())[0]
            pixel = skip_nodes[level][first]
            span = len(skip_nodes[level])
            hierarchy.append(pixel)
        else:
            pixel = sweep_line['closest']
            span = len(sweep_line)
        previous = pixel
        # No smaller distance available
        if pixel['distance'] >= distance:
            # Add all the nodes all the way to the active pixel
            while hierarchy and hierarchy[-1]['down'] is not None:
                hierarchy.append(hierarchy[-1]['down'])
            # Return the hierarchy list without the active pixel
            return (None, hierarchy[-2::-1])
        # Didn't find distance, continue
        while (pixel['distance'] <= distance):
            # go right before distance is passed
            iteration = 0
            while (iteration < span -1) and (pixel['distance'] < distance):
                previous = pixel
                pixel = pixel['next']
                iteration += 1
            # Went too far, backtrack 
            if (pixel is None) or (pixel['distance'] >= distance):
                pixel = previous
            # Try to go down 1 level
            # If not possible, return the pixel itself.
            if pixel['down'] is None:
                return (pixel, hierarchy[::-1])
            hierarchy.append(pixel)
            span = pixel['span']
            pixel = pixel['down']
    # Empty sweep_line, there's no cell to return
    else:
        return (None, hierarchy[::-1])

def find_active_pixel_fast(sweep_line, skip_nodes, distance):
    """Find an active pixel based on distance. 
        
        Inputs:
            -sweep_line: a linked list of linked_cell as created by the
                linked_cell_factory.
            -skip_list: an array of linked lists that constitutes the hierarchy
                of skip pointers in the skip list. Each cell is defined as ???
            -distance: the key used to search the sweep_line

            Return the linked_cell associated to 'distance', or None if such
            cell doesn't exist"""
    # Empty sweep_line, nothing to return
    if not sweep_line:
        return None
        
    pixel, _ = find_pixel_before_fast(sweep_line, skip_nodes, distance)

    # Sweep-line is non-empty:
    # Pixel is None: could be first element
    if pixel is None:
        return sweep_line['closest'] if \
            sweep_line['closest']['distance'] == distance else None
    # Could be an existing pixel in the sweep_line
    elif pixel['next'] is not None:
        return pixel['next'] if \
            pixel['next']['distance'] == distance else None
    # Can't be a pixel in sweep_line, since it should be after last
    else:
        return None
    

def find_active_pixel(sweep_line, distance):
    """Find an active pixel based on distance. Return None if can't be found"""
    if 'closest' in sweep_line:
        # Get information about first pixel in the list
        pixel = sweep_line[sweep_line['closest']['distance']] # won't change
        # Move on to next pixel if we're not done
        while (pixel is not None) and \
            (pixel['distance'] < distance):
            pixel = pixel['next']
        # We reached the end and didn't find anything
        if pixel is None:
            return None
        # We didn't reach the end: either pixel doesn't exist...
        if pixel['distance'] != distance:
            return None
        # ...or we found it
        else:
            return pixel
    else:
        return None


def remove_active_pixel(sweep_line, distance):
    """Remove a pixel based on distance. Do nothing if can't be found."""
    if 'closest' in sweep_line:
        # Get information about first pixel in the list
        previous = None
        pixel = sweep_line[sweep_line['closest']['distance']] # won't change
        # Move on to next pixel if we're not done
        while (pixel is not None) and \
            (pixel['distance'] < distance):
            previous = pixel
            pixel = pixel['next']
        # We reached the end and didn't find anything
        if pixel is None:
            return sweep_line
        # We didn't reach the end: either pixel doesn't exist:
        if pixel['distance'] != distance:
            return sweep_line
        # Or we found the value we want to delete
        # Make the previous element point to the next
        # We're at the beginning of the list: update the list's first element
        if previous is None:
            # No next pixel: we have to delete 'closest'
            if pixel['next'] is None:
                del sweep_line['closest']
            # Otherwise, update it
            else:
                sweep_line['closest'] = pixel['next']
        # We're not at the beginning of the list: only update previous
        else:
            previous['next'] = sweep_line[distance]['next']
        # Remove the value from the list
        del sweep_line[distance]
    return sweep_line


def add_active_pixel(sweep_line, distance, visibility):
    """Add a pixel to the sweep line in O(n) using a linked_list of
    linked_cells."""
    # Make sure we're not creating any duplicate
    message = 'Duplicate entry: the value ' + str(distance) + ' already exist'
    assert distance not in sweep_line, message
    new_pixel = {'next':None, 'distance':distance, 'visibility':visibility}
    if 'closest' in sweep_line:
        # Get information about first pixel in the list
        previous = None
        pixel = sweep_line[sweep_line['closest']['distance']] # won't change
        # Move on to next pixel if we're not done
        while (pixel is not None) and \
            (pixel['distance'] < distance):
            previous = pixel
            pixel = pixel['next']
        # 1- Make the current pixel points to the next one
        new_pixel['next'] = pixel
        # 2- Insert the current pixel in the sweep line:
        sweep_line[distance] = new_pixel
        # 3- Make the preceding pixel point to the current one
        if previous is None:
            sweep_line['closest'] = new_pixel
        else:
            sweep_line[previous['distance']]['next'] = sweep_line[distance]
    else:
        sweep_line[distance] = new_pixel
        sweep_line['closest'] = new_pixel
    return sweep_line

def skip_list_is_consistent(linked_list, skip_nodes):
    """Function that checks for skip list inconsistencies.
    
        Inputs: 
            -sweep_line: the container proper which is a dictionary
                implementing a linked list that contains the items 
                ordered in increasing distance
            -skip_nodes: python dict that is the hierarchical structure 
                that sitting on top of the sweep_line to allow O(log n) 
                operations.
        
        Returns a tuple (is_consistent, message) where is_consistent is 
            True if list is consistent, False otherwise. If is_consistent
            is False, the string 'message' explains the cause"""
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
        return (True, 'Empty list is fine')
    
    # 1.1-If len(linked_list) > 0 then len(linked_list) >= 2
    if len(linked_list) < 2:
        return (False, 'Linked list size is not valid: ' + \
            str(len(linked_list)))
    # 1.2-If len(linked_list) > 0 then 'closest' exists
    if not linked_list.has_key('closest'):
        message = "Missing key linked_list['closest']"
        return (False, message)

    pixel = linked_list['closest']
    chain_length = 1
    # 1.3-down is None
    if pixel['down'] is not None:
        message = "linked_list['closest']['down'] is not None"
        return (False, message)

    last_distance = pixel['distance']
    # 1.4-No negative distances
    if last_distance < 0:
        message = "linked_list['closest'] has a negative distance"
        return (False, message)

    # Minimum and maximum number of allowed up pointers
    min_up_count = 0 if len(linked_list) < 5 else \
        math.ceil(float(len(linked_list) -1) / 3)
    max_up_count = math.ceil(float(len(linked_list) -1) / 2)

    up_count = 0    # actual number of up pointers
    up_gap = -1     # gap since last up pointer
    
    # Counting the first 'up' pointer
    if pixel['up'] is not None:
        up_count += 1
        up_gap = 0

    # Traverse the linked list
    while pixel['next'] is not None:
        pixel = pixel['next']
        chain_length += 1
        # 1.3-down is None
        if pixel['down'] is not None:
            message = "pixel['down'] is None"
            return (False, message)
        # 1.5-distances increase
        if (pixel['distance'] - last_distance) <= 0.:
            message = "Distance in the linked list decreased!" + \
                str(last_distance) + ' > ' + str(pixel['distance'])
            return (False, message)
        last_distance = pixel['distance']
        # Updating the number of 'up' pointers and the gap between them
        if pixel['up'] is not None:
            # It's not the first 'up' pointer, so check the gap is ok
            # 1.6-Check the gaps between the up pointers
            if up_count > 0:
                if up_gap < 1:
                    message = "gap in the linked_list (" + str(up_gap) + \
                        ") is < 1"
                    return (False, message)
                if up_gap > 2:
                    message = "gap in the linked_list (" + str(up_gap) + \
                    ") is > 2"
                    return (False, message)
            up_count += 1
            up_gap = -1
        # If there are up pointers, updating the gap
        if up_count:
            up_gap += 1

    # 1.7-Check the number of up pointers is valid
    if up_count > max_up_count:
        message = "Too many up pointers in linked_list (" + str(up_count)+\
            ') max is ' + str(max_up_count)
        return (False, message)
    if up_count < min_up_count:
        message = "Too few up pointers in linked_list (" + str(up_count) +\
            ') min is ' + str(min_up_count)
        return (False, message)

    # 1.8-chain length is 1 less than len(linked_list)
    if (chain_length != len(linked_list) -1):
        message = 'Discrepancy between the nodes in the linked list (' + \
        str(len(linked_list)-1) + ') and the number of nodes chained together ' + \
        str(chain_length) + ". Does 'closest' point to the second node?"
        sorted_keys = sorted(linked_list.keys())
        for key in sorted_keys:
            node = linked_list[key]
            next_node = None if node['next'] is None else node['next']['distance']
            #print('distance', key, 'next', next_node)
        return (False, message)
    # 1.9-linked_list['closest'] is the smallest distance
    # True if 1.5 and 1.8 are true
    # 1.10-The non-linked element is the same as linked_list['closest']
    if not linked_list.has_key(linked_list['closest']['distance']):
        message = 'The element not linked to the list is not the same' + \
        'as closest (' + str(linked_list['closest']['distance']) + ')'
        return (False, message)
    # 1.11-Last element has 'next' set to None
    # True if 1.8 and 1.10 are true

    # 2-Testing the skip pointers
    #   2.0-Check skip_nodes are properly indexed by their distance
    #   2.1-The spans at a level is the size of the level below
    #   2.2-The entry 'down' is never None
    #   2.3-Each skip node before last has 'next' != None
    #   2.4-Each skip node at the end of its level has 'next' == None
    #   2.5-Equality ['distances'] == ['down']['distance'] should be True
    #   2.6-All the distances at a given level increase
    #   2.7-The span at each skip node is either 2 or 3
    #   2.8-The last node spanned by a higher skip node is right before the
    #       first node spanned by the next higher skip node
    #   2.9-Each skip node references the right element in the linked list
    #   2.10-The first top level node always points to 'closest'
    #   2.11-The 'up' entries at a lower level match the # of higher entries
    #   2.12-The gaps between each pointer at each level has to be valid
    #   2.13-The number of pointers at each level has to be valid
    #   2.14-All the skip nodes can be reached from the first one on top

    # Empty skip node
    if not skip_nodes:
        # Small enough: good, we can return
        if len(linked_list) < 5:
            return (True, 'All is well')
        # Linked list is big enough and should have skip pointers
        else:
            return (False, 'Linked list needs skip pointers.')

    total_skip_nodes = 0
    for l in range(len(skip_nodes)):
        ascending_distances = sorted(skip_nodes[l].keys())
        # 2.0-Check skip_nodes are properly indexed by their distance
        for n in skip_nodes[l]:
            message = 'skip_nodes[' + str(n) + '] is not ' + str(n) + '.' + \
            ' Instead, it is ' + str(skip_nodes[l][n]['distance'])
            assert n == skip_nodes[l][n]['distance'], message
        total_skip_nodes += len(skip_nodes[l])
        # 2.1-The spans at a level is the size of the level below
        total_span = 0
        for n in skip_nodes[l]:
            total_span += skip_nodes[l][n]['span']
        if l > 0:
            # Comparing two levels in skip_nodes
            if total_span != len(skip_nodes[l-1]):
                message = 'Level '+ str(l) + ': span of ' + \
                str(total_span) + ' disagrees with size of level below '+\
                str(len(skip_nodes[l-1]))
                return (False, message)
        else:
            # 2.1- Comparing first level in skip_nodes with linked_list
            if total_span != len(linked_list) -1:
                message = 'Level ' + str(l) + ': span of ' + str(total_span) + \
                ' disagrees with entries in linked_list ' + \
                    str(len(linked_list) -1)
                return (False, message)
        previous_distance = ascending_distances[0] -1 # smallest distance
        for n in ascending_distances:
            node = skip_nodes[l][n]
            # 2.2-The entry 'down' is never None
            if node['down'] is None:
                message = 'Entry ' + str(l) + str(n) + \
                'has a "down" entry that is not None (' + \
                str(node['down']['distance']) + ')'
                return (False, message)
            # Looking at the skip node 'next' values:
            if n != ascending_distances[-1]:
                # 2.3-Each skip node before the last one has 'next' != None
                if skip_nodes[l][n]['next'] is None:
                    message = 'Skip node ' + str(len(skip_nodes[l]) -1) + \
                    ' before last at level ' + str(l) + ' is None.'
                    return (False, message)
            else:
                # 2.4-Last skip node at the end of its level has 'next' == None
                if skip_nodes[l][n]['next'] is not None:
                    message = 'Last skip node '+str(len(skip_nodes[l])-1)+\
                    ' at level ' + str(l) + ' is not None (' + \
                    str(skip_nodes[l][n]['next']['distance']) + ')'
                    return (False, message)
            # 2.5-Equality ['distances'] == ['down']['distance'] should be True
            if node['distance'] != node['down']['distance']:
                message = 'Node [' + str(l) + '][' + str(n) + '] has ' + \
                'inconsistent values between ' + \
                "node['distance'] = " + str(node['distance']) + ' and ' + \
                "node['down']['distance'] = " + str(node['down']['distance'])
                return (False, message)
            # 2.6-All the distances at a given level increase
            distance = node['distance']
            if distance <= previous_distance:
                message = 'Node [' + str(l) + '][' + str(n) + \
                "]'s distance " + str(distance) + ' <= ' + \
                str(previous_distance) + ' instead of increasing.'
                return (False, message)
            # 2.7-The span at each skip node is either 2 or 3
            if (node['span'] != 2) and (node['span'] != 3):
                message = 'Wrong span: should be either 2 or 3, but is ' + \
                    str(node['span'])
                return (False, message)
            # 2.8-The last node spanned by a higher skip node is right
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
            if n != ascending_distances[-1]:
                # Step 1, get the last node of the current higher node
                last_node = node['down']
                #print('level', l, 'n', n)
                #print('first node spanned by [' + str(l) + ']['+str(n) + \
                #']' , last_node['distance'])
                for i in range(node['span'] -1):
                    last_node = last_node['next']
                    #print('next is', last_node['distance'])
                #print('after last is', last_node['next']['distance'])
                next_node = node['next']['down']
                #print('first node spanned by [' + str(l) + \
                #']['+str(next_node['distance']) + ']' , next_node['distance'])
                # Last spanned node should be connected to the first one \
                # from the next higher node.
                if last_node['next']['distance'] != next_node['distance']:
                    message = 'Last node spanned by [' +str(l) +'][' +str(n) +\
                    "] = " + str(last_node['next']['distance']) + \
                    " is not before first node spanned by [" + str(l) + '][' + \
                    str(node['next']['distance']) + '] = ' + \
                    str(next_node['distance'])
                    return (False, message)
            # 2.9-Each skip node references the correct element below it,
            # i.e. each node's distance values are identical
            while node['down'] is not None:
                node = node['down']
                if node['distance'] != distance:
                    message = "Node['down'] refers a node with another " +\
                    'value (' + str(distance) + ' expected ' + \
                    str(node['distance'])
                    return (False, message)
            previous_distance = distance
    # 2.10-The first top level node always points to 'closest'
    first = sorted(skip_nodes[-1].keys())[0]
    if (skip_nodes[-1][first]['distance'] !=linked_list['closest']['distance']):
        message="First top level node "+str(skip_nodes[-1][first]['distance'])\
        + " doesn't point to linked_list['closest'] (" + \
        str(linked_list['closest']['distance']) + ')'
        return (False, message)
    # 2.11-The 'up' entries at a lower level match the # of higher entries
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

    skip_nodes_size = 0
    for level in range(len(skip_nodes)):
        # Count the number of 'up' that are not None at this level
        level_up_count = 0
        up_gap = -1
        first = sorted(skip_nodes[level].keys())[0]
        node = skip_nodes[level][first]
        if node['up'] is not None:
            level_up_count += 1
        while node['next'] is not None:
            node = node['next']
            # If there are up pointers, updating the gap
            if level_up_count:
                up_gap += 1
            if node['up'] is not None:
                # It's not the first 'up' pointer, so check the gap is ok
                # 2.12-Check the gaps between the up pointers
                if level_up_count > 0:
                    if up_gap < 1:
                        message = 'Skip node ' + str(node['distance']) + \
                        ' at level ' +str(level) +' has a gap too small:'+\
                        str(up_gap) + ' < 1'
                        return (False, message)
                    if up_gap > 2:
                        message = 'Skip node ' + str(node['distance']) + \
                        ' at level ' +str(level) +' has a gap too large:'+\
                        str(up_gap) + ' > 2'
                        return (False. message)
                level_up_count += 1
                up_gap = -1
        # 2.11-The 'up' entries at a lower level match the # higher entries
        if up_count != len(skip_nodes[level]):
            message = 'Level ' + str(level) + \
            ": the number of 'up' entries " + str(up_count) + \
            ' disagrees with the number of skip nodes above ' + \
                str(len(skip_nodes[level]))
            return (False, message)
        # Minimum and maximum number of allowed up pointers
        min_up_count = 0 if len(skip_nodes[level]) < 4 else \
            math.ceil(float(len(skip_nodes[level])) / 3)
        max_up_count = math.ceil(float(len(skip_nodes[level])-1) / 2)
        # 2.13-The number of pointers at each level has to be valid
        if level_up_count > max_up_count:
            message = 'Level ' + str(level) + ': level_up_count = ' + \
            str(level_up_count) + ' > max_up_count = ' + \
            str(max_up_count)
            return (False, message)
        if level_up_count < min_up_count:
            message = 'Level ' + str(level) + ': level_up_count = ' + \
            str(level_up_count) + ' < min_up_count = ' + \
            str(min_up_count)
            return (False, message)
        lower_level_size = len(skip_nodes[level]) # update for next iter
        up_count = level_up_count

    # 2.14-All the skip nodes can be reached from the first one on top
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
        message = 'Number of nodes reached in the skip_list ' + \
        str(nodes_reached) + \
        "doesn't agree with the total number of nodes" + \
        str(total_skip_nodes)
        return (False, message)

    return (True, 'All good')

def viewshed(input_uri, output_uri, coordinates, obs_elev=1.75, tgt_elev=0.0, \
max_dist=-1., refraction_coeff=None):
    """Viewshed computation function
        
        Inputs: 
            -input_uri: uri of the input elevation raster map
            -output_uri: uri of the output raster map
            -coordinates: tuple (east, north) of coordinates of viewing
                position
            -obs_elev: observer elevation above the raster map.
            -tgt_elev: offset for target elevation above the ground. Applied to
                every point on the raster
            -max_dist: maximum visibility radius. By default infinity (-1), 
                not used yet
            -refraction_coeff: refraction coefficient (0.0-1.0), not used yet"""
    add_cell_events = []
    delete_cell_events = []
    cell_center_events = []

    in_raster = gdal.Open(input_uri)
    in_array = in_raster.GetRasterBand(1).ReadAsArray()

    extreme_angles

def execute(args):
    """Entry point for aesthetic quality core computation.
    
        Inputs:
        
        Returns
    """
    pass
