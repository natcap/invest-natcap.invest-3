import math
import cProfile
import pstats

import gdal
import numpy
import numpy.fft
import scipy.ndimage.morphology


from invest_natcap import raster_utils

def make_distance_kernel(max_distance):
    kernel_size = max_distance * 2 + 1
    distance_kernel = numpy.empty((kernel_size, kernel_size), dtype=numpy.float)
    for row_index in xrange(kernel_size):
        for col_index in xrange(kernel_size):
            distance_kernel[row_index, col_index] = numpy.sqrt(
                (row_index - max_distance) ** 2 + (col_index - max_distance) ** 2)
    return distance_kernel

def make_linear_kernel(max_distance):
    distance_kernel = make_distance_kernel(max_distance)
    kernel = numpy.where(
        distance_kernel > max_distance, 0.0, 1 - distance_kernel / max_distance)
    return kernel / numpy.sum(kernel)


def make_exponential_kernel(max_distance):
    kernel = make_distance_kernel(max_distance)
    kernel = numpy.where(
        distance_kernel > max_distance, 0.0, numpy.exp(-2.99 / max_distance * dist))
    return kernel / numpy.sum(kernel)


if __name__ == '__main__':
    weight_uri = "C:/Users/rsharp/Box Sync/Unilever/Input_MatoGrosso_global_Unilever_10_09_2014/Input_MatoGrosso_global_Unilever_10_09_2014/SRTM_90m_MatoGrosso_final_basins.tif"
    #weight_uri = "C:/InVEST_dev107_3_0_1 [61c19dc4b887]_x86/Base_Data/Freshwater/dem"
    output_uri = "C:/Users/rsharp/Documents/convolution/result.tif"
    max_distance = 100
    print 'make kernel'
    kernel = make_linear_kernel(max_distance)
    print 'convolve 2d'

    cProfile.run('raster_utils.convolve_2d(weight_uri, kernel, output_uri)', 'stats')
    p = pstats.Stats('stats')
    p.sort_stats('time').print_stats(20)
    p.sort_stats('cumulative').print_stats(20)


    
