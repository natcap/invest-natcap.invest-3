from numpy import *
import numpy as np

def execute(lulc, pools):
    """iterate through the array and map the pool values to the output array
        lulc is a numpy array
        pools is a numpy array, expecting the index to be the pool index and the value to be the sum of the carbon values for that index.
        output is a numpy array"""

    def mapPool(x, dict):
        if x in dict:
            return dict[x]
        else:
            return None

    if lulc.size > 0:
        mapFun = np.vectorize(mapPool)
        return mapFun(lulc, pools)
    else:
        return []
