"""File for core operations of the InVEST Nutrient Retention model."""

import numpy as np

def biophysical(args):
    """This function executes the biophysical Nutrient Retention model.

        args - a python dictionary with the following entries:"""
    print args
    pass

def get_mean_pixel_value(array, nodata):
    """Get the mean pixel value of an array, given a nodata value.

        array - a numpy matrix
        nodata - a python number.  All values of array with this value will be
            ignored when calculating the mean of array.

        returns a python number that is the mean value of the matrix."""
    masked_array = np.ma.masked_array(array, array == nodata)
    return np.mean(masked_array)
