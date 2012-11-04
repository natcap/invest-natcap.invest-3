"""Compare the wall-clock running times of mean on numpy + gdal."""
# This demonstrates that the gdal approach runs 1.737 times faster than
# the numpy approach (5.007s vs. 8.7002s) if we only calculate the mean in
# numpy.
#
# Note that if we calculate ALL 4 statistics (min, max, mean, stddev), gdal is
# about 15.618 times faster, clocking in at ~5 seconds, while Numpy takes ~77
# seconds.
#
# Clearly, GDAL's statistics are the superior option here.
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
    mean = masked_array.mean()
    a_min = masked_array.min()
    a_max = masked_array.max()
    a_stddev = masked_array.std()

array = ds.GetRasterBand(1).ReadAsArray()
def do_numpy_no_array():
    masked_array = np.ma.masked_array(array, array == nodata)
    mean = masked_array.mean()
    a_min = masked_array.min()
    a_max = masked_array.max()
    a_stddev = masked_array.std()

def do_gdal():
    ds.GetRasterBand(1).ComputeStatistics(0)
    min, max, mean, stdev = ds.GetRasterBand(1).GetStatistics(0,1)

# This approach takes about 77.568s to complete 1000 times.
numpy_time = 'numpy ' + str(timeit.timeit(do_numpy, number=1000))

# This approach takes about 77.188s to complete 1000 times.
numpy_no_array_time = 'numpy (no array loading) ' + str(timeit.timeit(do_numpy, number=1000))

# This approach takes about 4.94s to complete 1000 times.
gdal_time = 'gdal ' + str(timeit.timeit(do_gdal, number=1000))

print numpy_time
print numpy_no_array_time
print gdal_time

