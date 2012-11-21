"""An experiment with graph traversal"""

import scipy.sparse.csgraph
import numpy

n_rows = 4
n_cols = 3
data = numpy.zeros((9, n_rows * n_cols))
data[4,:] = 1

diags = numpy.array([-n_cols-1, -n_cols, -n_cols+1, -1, 0, 
                   1, n_cols-1, n_cols, n_cols+1])

n_elements = n_rows * n_cols

# 0 1 2
# 3 4 5
# 6 7 8
# 91011

outflow_directions = {( 0, 1): 5,
                      (-1, 1): 2,
                      (-1, 0): 1,
                      (-1,-1): 0,
                      ( 0,-1): 3,
                      ( 1,-1): 6,
                      ( 1, 0): 7,
                      ( 1, 1): 8}

#make all nodes flow "down" except for the last row
for node_index in xrange((n_rows-1) * n_cols):
    #One down
    neighbor_index = node_index + n_cols
    data[outflow_directions[(1, 0)], neighbor_index] = 1.0

#Make the left two columns flow into the right
for row_index in xrange(n_rows-1):
    #One down
    for col_index in xrange(n_cols-1):
        node_index = row_index*n_cols+col_index
        #Go diagonal down right
        neighbor_index = node_index + n_cols+1
        data[outflow_directions[(1, 1)], neighbor_index] = 1.0

#Make the last row flow to the right
for col_index in xrange(n_cols-1):
    node_index = (n_rows-1)*n_cols+col_index
    #Go right
    neighbor_index = node_index +1
    data[outflow_directions[(0, 1)], neighbor_index] = 1.0

matrix = scipy.sparse.spdiags(data, diags, n_elements, n_elements, 
                              format="csc")
print matrix.todense()

traversal = scipy.sparse.csgraph.depth_first_order(matrix, 0, directed = True, return_predecessors = True)

print traversal
