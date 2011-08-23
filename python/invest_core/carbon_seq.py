from numpy import *
import numpy as np
#lulc is a numpy array
#pools is a numpy array, expecting the index to be the pool index and the value to be the sum of the carbon values for that index.
#output is a numpy array

def execute(lulc, pools, output):
    #iterate through the array and map the pool values to the output array 
    for x in range(0, lulc.shape[1]):
        index = lulc[0][x]
        if (index != 255):
            output[0][x] = pools[index]

    return output

