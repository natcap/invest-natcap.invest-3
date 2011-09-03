from numpy import *
import numpy as np

def execute(lulc_cur, lulc_fut):
    """iterate through the array and map the difference of the two input arrays to the output array
        """
          
    if lulc_cur.size > 0:
        return np.subtract(lulc_cur, lulc_fut)
    else:
        return []