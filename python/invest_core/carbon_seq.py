from numpy import *

#lulc is a numpy array
#pools is a numpy array, expecting the index to be the pool index and the value to be the sum of the carbon values for that index.
#output is a numpy array

def execute(lulc, pools, output):
    lulc_dimensions = list(lulc.shape) #convert to a list to access dimensions by index
    #iterate through the array and map the pool values to the output array 
    for x in range(0, lulc_dimensions[0]):
        for y in range(0, lulc_dimensions[1]):
            index = lulc[x][y]
            if index != 255:
                output[x][y] = pools[index]

    return output

