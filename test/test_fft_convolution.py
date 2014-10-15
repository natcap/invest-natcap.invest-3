import math

import gdal
import numpy
import numpy.fft
import scipy.ndimage.morphology


from invest_natcap import raster_utils


def distance(row_index, col_index, kernel_size, kernel_type, max_distance):
    """closure for an euclidan distance calc"""
    dist = math.sqrt(
        (row_index - kernel_size - 1) ** 2 +
        (col_index - kernel_size - 1) ** 2)
    if dist > max_distance:
        return 0.0
    if kernel_type == 0: #'linear'
        return 1 - dist/max_distance
    elif kernel_type == 1: #'exponential'
        return  math.exp(-(2.99/max_distance) * dist)

def fft_convolution(weight_uri, output_uri, kernel_type, max_distance):
	#weight_uri = "C:/InVEST_dev107_3_0_1 [61c19dc4b887]_x86/Sedimentation/3/intermediate/stream.tif"
	for uri in [output_uri]:
		raster_utils.new_raster_from_base_uri(
		    weight_uri, uri, 'GTiff', -1, gdal.GDT_Float32)

	weight_nodata = raster_utils.get_nodata_from_uri(weight_uri)
	weight_ds = gdal.Open(weight_uri)
	weight_band = weight_ds.GetRasterBand(1)
	weight_array = weight_band.ReadAsArray()
	weight_array[weight_array == weight_nodata] = 0.0
	
	kernel_size = max_distance * 2 + 1
	kernel = numpy.empty((kernel_size, kernel_size), dtype=numpy.float)
	if kernel_type == 'linear':
	    kernel_type_id = 0
	if kernel_type == 'exponential':
	    kernel_type_id = 1
	print 'preping kernel'
	for row_index in xrange(kernel_size):
	    for col_index in xrange(kernel_size):
	        kernel[row_index, col_index] = distance(
	            row_index, col_index, kernel_size, kernel_type_id, max_distance)

	kernel /= numpy.sum(kernel)

	print 'scipy fft convolve'
	result_array = scipy.signal.fftconvolve(weight_array, kernel, 'valid')

	result_ds = gdal.Open(output_uri, gdal.GA_Update)
	result_band = result_ds.GetRasterBand(1)
	result_band.WriteArray(result_array)


if __name__ == '__main__':
	#weight_uri = "C:/Users/rpsharp/Box Sync/Unilever/Input_MatoGrosso_global_Unilever_10_09_2014/Input_MatoGrosso_global_Unilever_10_09_2014/SRTM_90m_MatoGrosso_final_basins.tif"
	weight_uri = "C:/InVEST_dev107_3_0_1 [61c19dc4b887]_x86/Base_Data/Freshwater/dem"
	output_uri = "C:/Users/rpsharp/Documents/convolution/result.tif"
	kernel_type = 'linear'
	max_distance = 5
	try:
		print 'trying fft convolution'
		fft_convolution(weight_uri, output_uri, kernel_type, max_distance)
	except MemoryError:
		print 'backup convolve 2d'
		raster_utils.convolve_2d(weight_uri, kernel_type, max_distance, output_uri)