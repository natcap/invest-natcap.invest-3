"""File for core operations of the InVEST Nutrient Retention model."""

import numpy as np

def biophysical(args):
    """This function executes the biophysical Nutrient Retention model.

        args - a python dictionary with the following entries:"""
    print args
    pass

def get_mean_pixel_value(array, nodata):
    masked_array = np.ma.masked_array(array, array == nodata)
    return np.mean(masked_array)
