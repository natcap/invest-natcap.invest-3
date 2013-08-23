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
	pylab.title('Landcover %s\nR^2 = %.4f' % (landcover_type, r_value))


#Units of base biomass in the raster pixels are are Mg/Ha
BASE_BIOMASS_FILENAME = './braz_bio_08'
BASE_LANDCOVER_FILENAME = './braz_lulc_08'

#These are the landcover types that define clusters of forest for the distance from edge calculation
FOREST_LANDCOVER_TYPES = [1, 2, 3, 4, 5]
#These are the landcover types that should use the log regression
REGRESSION_TYPES = [2]

#Load the base biomass and landcover datasets
biomass_dataset = gdal.Open(BASE_BIOMASS_FILENAME)
biomass_nodata = biomass_dataset.GetRasterBand(1).GetNoDataValue()
landcover_dataset = gdal.Open(BASE_LANDCOVER_FILENAME)
biomass_array = biomass_dataset.GetRasterBand(1).ReadAsArray()
landcover_array = landcover_dataset.GetRasterBand(1).ReadAsArray()

#This gets us the cell size in projected units, should be meters if the raster is projected
cell_size = landcover_dataset.GetGeoTransform()[1]

#Create a mask of 0 and 1s for all the forest landcover types
#This will be used to calculate edge effects
forest_existance = numpy.zeros(landcover_array.shape)
for landcover_type in FOREST_LANDCOVER_TYPES:
	forest_existance = forest_existance + (landcover_array == landcover_type)
forest_existance[biomass_array == biomass_nodata] = 0.0

#This calculates an edge distance for the clusters of forest
edge_distance = scipy.ndimage.morphology.distance_transform_edt(
	forest_existance)

#For each forest type, build a regression of biomass based 
#on the distance from the edge of the forest
landcover_regression = {}
landcover_mean = {}

plot_id = 1
print 'building biomass regression'
print 'landcover type, biomass mean, r^2, stddev, pixel count, regression_fn(1px), regression_fn(10px)'
for landcover_type in REGRESSION_TYPES:
	landcover_mask = numpy.where(
		(landcover_array == landcover_type) * 
		(biomass_array != biomass_nodata))
	
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
	ss_res = numpy.sum((landcover_biomass - landcover_regression[landcover_type](landcover_edge_distance)) ** 2)
	r_value = 1 - ss_res / ss_tot
	std_dev = numpy.std(landcover_biomass)
	n_count = landcover_biomass.size
	print '%s, %.2f, %.2f, %.2f, %s, %s, %s' % (landcover_type, landcover_biomass_mean, r_value, std_dev, n_count, landcover_regression(cell_size), landcover_regression(10*cell_size))
	
	
	landcover_mean[landcover_type] = landcover_biomass_mean
	
	plot_regression(biomass_array, landcover_edge_distance, plot_id, 5, 1, landcover_regression[landcover_type])
	plot_id += 1
	
pylab.show()
