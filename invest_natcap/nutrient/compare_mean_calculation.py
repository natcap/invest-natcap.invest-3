"""Compare the wall-clock running times of mean on numpy + gdal."""
# This demonstrates that the gdal approach runs 1.737 times faster than
# the numpy approach (5.007s vs. 8.7002s)
import os
import timeit

import numpy as np
from osgeo import gdal

NUTR_INPUT = 'test/data/nutrient/input'

ds = gdal.Open(os.path.join(NUTR_INPUT, 'dem'))
nodata = ds.GetRasterBand(1).GetNoDataValue()

def do_numpy():
    array = ds.GetRasterBand(1).ReadAsArray()
    masked_array = np.ma.masked_array(array, array == nodata)
    mean = np.mean(masked_array)

array = ds.GetRasterBand(1).ReadAsArray()
def do_numpy_no_array():
    masked_array = np.ma.masked_array(array, array == nodata)
    mean = np.mean(masked_array)

def do_gdal():
    ds.GetRasterBand(1).ComputeStatistics(0)
    min, max, mean, stdev = ds.GetRasterBand(1).GetStatistics(0,1)

numpy_time = 'numpy ' + str(timeit.timeit(do_numpy, number=1000))
numpy_no_array_time = 'numpy (no array loading) ' + str(timeit.timeit(do_numpy, number=1000))

gdal_time = 'gdal ' + str(timeit.timeit(do_gdal, number=1000))

print numpy_time
print numpy_no_array_time
print gdal_time

