from numpy import *

#lulc is a numpy array
#pools is a numpy array, expecting the index to be the pool index and the value to be the sum of the carbon values for that index.
#output is a numpy array

def carbon_seq(lulc, pools, output):
    lulc_dimensions = list(lulc.shape) #convert to a list to access dimensions by index
 
    #iterate through the array and map the pool values to the output array 
    for x in range(0, lulc_dimensions[1]):
        for y in range(0, lulc_dimensions[1]):
            output[x][y] = pools[lulc[x][y]]


