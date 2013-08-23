import gdal
import numpy
import scipy.ndimage
import scipy
import pylab
import matplotlib.pyplot
import glob
import scipy.stats
import csv
import re
import os
from invest_natcap import raster_utils


def regression_builder(slope, intercept):
	return lambda(d): slope * numpy.log(d) + intercept

def plot_regression(biomass_array, edge_distance_array, plot_id, plot_rows, plot_cols, regression_fn):
	pylab.subplot(plot_rows, plot_cols, plot_id + 1)
	pylab.plot(landcover_edge_distance, landcover_biomass, '.k', markersize=1)
	
	#Plot the regression function
	regression_distance = numpy.arange(
		0.0, numpy.max(landcover_edge_distance), 0.05)
	
	regression_biomass = regression_fn(regression_distance)
	pylab.plot(regression_distance, regression_biomass, '-r', linewidth=2)
	pylab.axis('tight')
	pylab.ylabel('Biomass (units?)')
	pylab.xlabel('Distance from patch edge (m)')
	pylab.title('Bioregion %s\nR^2 = %.4f\ny(dist) = %.2f * ln(dist) + %.2f' % (bioregion_id, r_value, slope, intercept))
	


#Units of base biomass in the raster pixels are are Mg/Ha
BASE_BIOMASS_FILENAME = './clipped_bio.tif'
CLIPPED_BIOMASS_FILENAME = './bio_tmp.tif'
BASE_LANDCOVER_FILENAME = './clipped_lulc.tif'
CLIPPED_BASE_LANDCOVER_FILENAME = './lulc_tmp.tif'
ECOREGIONS_FILENAME = './ecoregions.tif'
CLIPPED_ECOREGIONS_FILENAME = './clipped_ecoregions.tif'


#These are the landcover types that define clusters of forest for the distance from edge calculation
FOREST_LANDCOVER_TYPES = [1, 2, 3, 4, 5]
#This is the landcover types that should use the log regression
REGRESSION_TYPE = 2

BIOREGIONS = {
#	1: 'bio_1.shp', 
#	2: 'bio_2.shp',
	3: 'bio_3.shp',
#	4: 'bio_4.shp',
	5: 'bio_5.shp',
	}

plot_id = 0
for bioregion_id, bioregion_uri in BIOREGIONS.iteritems():
	print 'working on %s' % bioregion_uri
	raster_utils.clip_dataset_uri(
		BASE_BIOMASS_FILENAME, bioregion_uri, CLIPPED_BIOMASS_FILENAME,
		False)
	raster_utils.clip_dataset_uri(
		BASE_LANDCOVER_FILENAME, bioregion_uri, CLIPPED_BASE_LANDCOVER_FILENAME,
		False)
	raster_utils.clip_dataset_uri(
		ECOREGIONS_FILENAME, bioregion_uri, CLIPPED_ECOREGIONS_FILENAME,
		False)

	#Load the base biomass and landcover datasets
	biomass_dataset = gdal.Open(CLIPPED_BIOMASS_FILENAME)
	biomass_nodata = biomass_dataset.GetRasterBand(1).GetNoDataValue()
	landcover_dataset = gdal.Open(CLIPPED_BASE_LANDCOVER_FILENAME)
	landcover_band = landcover_dataset.GetRasterBand(1)
	biomass_array = biomass_dataset.GetRasterBand(1).ReadAsArray()
	landcover_array = landcover_dataset.GetRasterBand(1).ReadAsArray()
	ecoregions_dataset = gdal.Open(CLIPPED_ECOREGIONS_FILENAME)
	ecoregions_array = ecoregions_dataset.GetRasterBand(1).ReadAsArray()
	
	shape = (biomass_dataset.RasterYSize, biomass_dataset.RasterXSize)

	#This gets us the cell size in projected units, should be meters if the raster is projected
	cell_size = landcover_dataset.GetGeoTransform()[1]

	#Create a mask of 0 and 1s for all the forest landcover types
	#This will be used to calculate edge effects
	forest_filename = raster_utils.temporary_filename()
	forest_existance = numpy.zeros(shape)

	print 'making forest cover'
	for row_index in range(biomass_dataset.RasterYSize):
		landcover_array = landcover_band.ReadAsArray(0, row_index, biomass_dataset.RasterXSize, 1)
		for landcover_type in FOREST_LANDCOVER_TYPES:
			forest_existance[row_index,:] = forest_existance[row_index,:] + (landcover_array == landcover_type)

	print 'calculating edge distance'

	#This calculates an edge distance for the clusters of forest
	edge_distance = scipy.ndimage.morphology.distance_transform_edt(
		forest_existance)

#For each forest type, build a regression of biomass based 
#on the distance from the edge of the forest
	landcover_regression = {}
	landcover_mean = {}
	print 'building biomass regression'
	print 'landcover type, biomass mean, r^2, stddev, pixel count, regression_fn(1px), regression_fn(10px)'

	landcover_mask = numpy.where(
		(landcover_array == REGRESSION_TYPE) * 
		(biomass_array != biomass_nodata) *
		(edge_distance != 0) *
		(ecoregions_array == bioregion_id))
	
	landcover_biomass = biomass_array[landcover_mask] * cell_size ** 2 / 10000
	
	landcover_edge_distance = edge_distance[landcover_mask] * cell_size
	#Fit a log function of edge distance to biomass for 
	#landcover_type
	try:
		slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(
			numpy.log(landcover_edge_distance), landcover_biomass)
	except ValueError:
		print "probably didn't have good data for the regression, just skip it"
		continue
	
	landcover_regression = regression_builder(slope, intercept)
	landcover_biomass_mean = numpy.average(landcover_biomass)
	
	#calcualte R^2
	ss_tot = numpy.sum((landcover_biomass - landcover_biomass_mean) **2)
	ss_res = numpy.sum((landcover_biomass - landcover_regression(landcover_edge_distance)) ** 2)
	r_value = 1 - ss_res / ss_tot
	std_dev = numpy.std(landcover_biomass)
	n_count = landcover_biomass.size
	print '%s, %.2f, %.2f, %.2f, %s, %s, %s' % (landcover_type, landcover_biomass_mean, r_value, std_dev, n_count, landcover_regression(cell_size), landcover_regression(10*cell_size))
	landcover_mean[landcover_type] = landcover_biomass_mean
	
	plot_regression(biomass_array, landcover_edge_distance, plot_id, 1, 2, landcover_regression)
	plot_id += 1
	
pylab.show()
