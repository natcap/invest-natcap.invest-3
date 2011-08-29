from numpy import *
import numpy as np

def execute(lulc, pools):
    """iterate through the array and map the pool values to the output array
        """

    def mapPool(x, dict):
        if x in dict:
            return dict[x]
        else:
            return 0

    if lulc.size > 0:
        mapFun = np.vectorize(mapPool)
        return mapFun(lulc, pools)
    else:
        return []
