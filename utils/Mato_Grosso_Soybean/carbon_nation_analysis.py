import gdal
import numpy
import scipy.ndimage
import scipy
import pylab
import matplotlib.pyplot
import glob

BASE_BIOMASS_FILENAME = './Carbon_MG_2008/mg_bio_2008'
BASE_LANDCOVER_FILENAME = './Carbon_MG_2008/mg_lulc_2008'
FOREST_LANDCOVER_TYPES = set([1, 2, 3, 4, 5])

#Load the base biomass and landcover datasets
biomass_dataset = gdal.Open(BASE_BIOMASS_FILENAME)
biomass_nodata = biomass_dataset.GetRasterBand(1).GetNoDataValue()
landcover_dataset = gdal.Open(BASE_LANDCOVER_FILENAME)
biomass_array = biomass_dataset.GetRasterBand(1).ReadAsArray()
landcover_array = landcover_dataset.GetRasterBand(1).ReadAsArray()
print 'biomass size %s' % (str(biomass_array.shape))
print 'landcover size %s' % (str(biomass_array.shape))

#Create a mask of 0 and 1s for all the forest landcover types
#This will be used to calculate edge effects
forest_existance = numpy.zeros(landcover_array.shape)
for landcover_type in FOREST_LANDCOVER_TYPES:
	forest_existance = forest_existance + (landcover_array == landcover_type)
forest_existance[biomass_array == biomass_nodata] = 0.0

edge_distance = scipy.ndimage.morphology.distance_transform_edt(
	forest_existance)
		
N_POINTS = 500000
#For each forest type, build a regression
landcover_regression = {}
for landcover_type in FOREST_LANDCOVER_TYPES:
	print landcover_type
	landcover_mask = numpy.where((landcover_array == landcover_type) * (biomass_array != biomass_nodata))
	
	landcover_biomass = biomass_array[landcover_mask]
	#print landcover_biomass
	landcover_edge_distance = edge_distance[landcover_mask]
	#print landcover_edge_distance
	
	(a_biomass, b_biomass) = scipy.polyfit(
		numpy.log(landcover_edge_distance), landcover_biomass, 1)
	
	landcover_regression[landcover_type] = (a_biomass, b_biomass)
	pylab.plot(landcover_edge_distance, landcover_biomass, '.')
	
	regression_distance = numpy.arange(numpy.max(landcover_edge_distance))
	print regression_distance
	f = lambda(d): a_biomass * numpy.log(d) + b_biomass
	regression_biomass = f(regression_distance)

	pylab.plot(regression_distance, regression_biomass, '-')
	break
	

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