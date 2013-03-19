from osgeo import gdal
import numpy

def static_max_marginal_gain(
	score_dataset_uri, budget, output_datset_uri, aoi_uri=None):
	"""This funciton calculates the maximum marginal gain by selecting pixels
		in a greedy fashion until the entire budget is spent.
		
		score_dataset_uri - gdal dataset to a float raster
		budget - number of pixels to select
		output_dataset_uri - the uri to an output gdal dataset of type gdal.Byte
			values are 0 if not selected, 1 if selected, and nodata if the original
			was nodata.
		aoi_uri - an area to consider selection
	
	returns nothing"""
	dataset = gdal.Open(score_dataset_uri)
	band = dataset.GetRasterBand(1)
	array = band.ReadAsArray()
	ordered_indexes = numpy.argsort(array.flat)
	
static_max_marginal_gain('../../../OYNPP1.tif', 10, 'test.tif')