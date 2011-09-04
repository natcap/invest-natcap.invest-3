from numpy import *
import numpy as np

def execute(data, numYears, carbonValue, multiplier):
    """iterate through the array and calculate the economic value of sequestered carbon.
        Map the values to the output array.
        
        data - a numpy array with shape (1,n), where n is a positive integer
        numYears - an int: the number of years the simulation covers
        carbonValue - a float: the dollar value of carbon
        multiplier - a float"""
        
    def mapValue(x):
        #caluclate the pixel-specific value of carbon for this simulation
        return carbonValue*(x/numYears)*multiplier 
    
    if data.size > 0:
        mapFun = np.vectorize(mapValue)
        return mapFun(data)
    else:
        return []