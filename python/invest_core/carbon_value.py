from numpy import *
import numpy as np

def execute(data, numYears, carbonValue, multiplier):
    """iterate through the array and calculate the economic value of sequestered carbon.
        Map the values to the output array"""
        
    def mapValue(x):
        return carbonValue*(x/numYears)*multiplier
    
    if data.size > 0:
        mapFun = np.vectorize(mapValue)
        return mapFun(data)
    else:
        return []