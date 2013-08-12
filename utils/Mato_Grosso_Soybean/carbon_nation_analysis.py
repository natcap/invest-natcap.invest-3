import gdal
import numpy
import scipy.ndimage
import scipy
import pylab
import matplotlib.pyplot
import glob
import scipy.stats

BASE_BIOMASS_FILENAME = './Carbon_MG_2008/mg_bio_2008'
BASE_LANDCOVER_FILENAME = './Carbon_MG_2008/mg_lulc_2008'
FOREST_LANDCOVER_TYPES = [1, 2, 3, 4, 5]

#Load the base biomass and landcover datasets
biomass_dataset = gdal.Open(BASE_BIOMASS_FILENAME)
biomass_nodata = biomass_dataset.GetRasterBand(1).GetNoDataValue()
landcover_dataset = gdal.Open(BASE_LANDCOVER_FILENAME)
biomass_array = biomass_dataset.GetRasterBand(1).ReadAsArray()
landcover_array = landcover_dataset.GetRasterBand(1).ReadAsArray()
print 'biomass size %s' % (str(biomass_array.shape))
print 'landcover size %s' % (str(biomass_array.shape))

cell_size = landcover_dataset.GetGeoTransform()[1]

#Create a mask of 0 and 1s for all the forest landcover types
#This will be used to calculate edge effects
forest_existance = numpy.zeros(landcover_array.shape)
for landcover_type in FOREST_LANDCOVER_TYPES:
	forest_existance = forest_existance + (landcover_array == landcover_type)
forest_existance[biomass_array == biomass_nodata] = 0.0

edge_distance = scipy.ndimage.morphology.distance_transform_edt(
	forest_existance)
		
#For each forest type, build a regression of biomass based 
#on the distance from the edge of the forest
landcover_regression = {}
for plot_id, landcover_type in enumerate(FOREST_LANDCOVER_TYPES):
	print landcover_type
	landcover_mask = numpy.where(
		(landcover_array == landcover_type) * 
		(biomass_array != biomass_nodata))
	
	landcover_biomass = biomass_array[landcover_mask]
	landcover_edge_distance = edge_distance[landcover_mask] * cell_size

	pylab.subplot(3, len(FOREST_LANDCOVER_TYPES), 2*len(FOREST_LANDCOVER_TYPES) + (plot_id + 1))
	#pylab.plot(landcover_edge_distance, landcover_biomass, '.k', markersize=1)
	#pylab.imshow(landcover_array[0:-1:15,0:-1:15])
	
	#Fit a log function of edge distance to biomass for 
	#landcover_type

	slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(numpy.log(landcover_edge_distance), landcover_biomass)
	
	f = lambda(d): slope * numpy.log(d) + intercept
	
	landcover_biomass_mean = numpy.average(landcover_biomass)
	ss_tot = numpy.sum((landcover_biomass - landcover_biomass_mean) **2)
	
	ss_res = numpy.sum((landcover_biomass - f(landcover_edge_distance)) ** 2)
	
	r_value = 1 - ss_res / ss_tot
	
	
	landcover_regression[landcover_type] = (slope, intercept, r_value, p_value, std_err)
	
	#Plot the original data points
	pylab.subplot(3, len(FOREST_LANDCOVER_TYPES), plot_id + 1)
	pylab.plot(landcover_edge_distance, landcover_biomass, '.k', markersize=1)
	
	#Plot the regression function
	regression_distance = numpy.arange(
		0.0, numpy.max(landcover_edge_distance), 0.05)
	
	regression_biomass = f(regression_distance)
	pylab.plot(regression_distance, regression_biomass, '-r', linewidth=2)
	pylab.axis('tight')
	pylab.ylabel('Biomass (units?)')
	pylab.xlabel('Distance from patch edge (m)')
	pylab.title('Landcover %s\nR^2 = %.4f' % (
	landcover_type, r_value))

#Linear regression follows
for plot_id, landcover_type in enumerate(FOREST_LANDCOVER_TYPES):
	print landcover_type
	landcover_mask = numpy.where(
		(landcover_array == landcover_type) * 
		(biomass_array != biomass_nodata))
	
	landcover_biomass = biomass_array[landcover_mask]
	landcover_edge_distance = edge_distance[landcover_mask] * cell_size
	
	#Fit a log function of edge distance to biomass for 
	#landcover_type

	slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(landcover_edge_distance, landcover_biomass)
	
	landcover_biomass_mean = numpy.average(landcover_biomass)
	ss_tot = numpy.sum((landcover_biomass - landcover_biomass_mean)**2)
	f = lambda(d): slope * d + intercept
	ss_res = numpy.sum((landcover_biomass - f(landcover_edge_distance))**2)
	
	r_value = 1 - ss_res / ss_tot
	
	landcover_regression[landcover_type] = (slope, intercept, r_value, p_value, std_err)
	
	#Plot the original data points
	pylab.subplot(3, len(FOREST_LANDCOVER_TYPES), plot_id + 1 + 2*len(FOREST_LANDCOVER_TYPES))
	pylab.plot(landcover_edge_distance, landcover_biomass, '.k', markersize=1)
	
	#Plot the regression function
	regression_distance = numpy.arange(
		0.0, numpy.max(landcover_edge_distance), 0.05)
	f = lambda(d): slope * d + intercept
	regression_biomass = f(regression_distance)
	pylab.plot(regression_distance, regression_biomass, '-r', linewidth=2)
	pylab.axis('tight')
	pylab.ylabel('Biomass (units?)')
	pylab.xlabel('Distance from patch edge (m)')
	pylab.title('Landcover %s\nR^2 = %.4f' % (
	landcover_type, r_value))
	
print landcover_regression
pylab.show()

LAND_USE_DIRECTORY = 'MG_Soy_Exp_07122013'
for lulc_path in glob.glob(LAND_USE_DIRECTORY + '/mg_*'):
	if '.' in lulc_path:
		continue
	print lulc_path
	lulc_dataset = gdal.Open(lulc_path)
	result = calculate_carbon_stocks(lulc_dataset)
	lulc_array = lulc_dataset.GetRasterBand(1).ReadAsArray()
	
	carbon_stocks = numpy.zero(lulc_array.shape)
	

#loop over each LULC, calculate carbon
	#calc above forest carbon w/ regression
	#calc other carbon w/ table