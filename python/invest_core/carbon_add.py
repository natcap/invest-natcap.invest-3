from numpy import *
import numpy as np

def execute(nodata, storage_raster, hwp_raster):
    """iterate through the array and map the difference of the two input arrays to the output array
        """
    
    def mapSum(a, b):
        if a == nodata['cur']:
            return nodata['fut']
        else:
            return a + b
    
    if storage_raster.size > 0:
        mapFun = np.vectorize(mapSum)
        return mapFun(storage_raster, hwp_raster)