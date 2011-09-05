from numpy import *
import numpy as np

def execute(nodata, lulc_cur, lulc_fut):
    """iterate through the array and map the difference of the two input arrays to the output array
        """
    
    def mapDiff(a, b):
        if a == nodata['cur']:
            return nodata['fut']
        else:
            return a-b
    
    if lulc_cur.size > 0:
        mapFun = np.vectorize(mapDiff)
        return mapFun(lulc_cur, lulc_fut)