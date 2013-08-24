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

def get_lookup_from_csv(csv_table_uri, key_field):
	"""Creates a python dictionary to look up the rest of the fields in a
		csv table indexed by the given key_field

		csv_table_uri - a URI to a csv file containing at
			least the header key_field

		returns a dictionary of the form {key_field_0: 
			{header_1: val_1_0, header_2: val_2_0, etc.}
			depending on the values of those fields"""

	def smart_cast(value):
		"""Attempts to cat value to a float, int, or leave it as string"""
		cast_functions = [int, float]
		for fn in cast_functions:
			try:
				return fn(value)
			except ValueError:
				pass
		return value

	with open(csv_table_uri, 'rU') as csv_file:
		csv_reader = csv.reader(csv_file)
		header_row = csv_reader.next()
		key_index = header_row.index(key_field)
		#This makes a dictionary that maps the headers to the indexes they
		#represent in the soon to be read lines
		index_to_field = dict(zip(range(len(header_row)), header_row))

		lookup_dict = {}
		for line in csv_reader:
			key_value = smart_cast(line[key_index])
			#Map an entire row to its lookup values
			lookup_dict[key_value] = (
				dict([(index_to_field[index], smart_cast(value)) 
					  for index, value in zip(range(len(line)), line)]))
		return lookup_dict


#Units of base biomass in the raster pixels are are Mg/Ha
BASE_BIOMASS_FILENAME = './Carbon_MG_2008/mg_bio_2008'
BASE_LANDCOVER_FILENAME = './Carbon_MG_2008/mg_lulc_2008'
CARBON_POOL_TABLE_FILENAME = './mato_grosso_carbon.csv'


#These are the landcover types that define clusters of forest for the distance from edge calculation
FOREST_LANDCOVER_TYPES = [1, 2, 3, 4, 5]
#These are the landcover types that should use the log regression
REGRESSION_TYPES = [2]
#These are the LULCs to take directly from table, everything else is mean from regression
FROM_TABLE = [10, 12, 120, 0]
#This is the crop we convert into
CONVERTING_CROP = 120
GRASSLAND = 10

#All other land cover pool types will come from the data table, units are Mg/Ha

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
print 'landcover type, biomass mean, r^2, stddev, pixel count, regression_fn(1)'
for landcover_type in numpy.unique(landcover_array):
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
	
	landcover_regression[landcover_type] = regression_builder(slope, intercept)
	landcover_mean[landcover_type] = numpy.average(landcover_biomass)
	
#Parse out the landcover pool table
carbon_pool_table = get_lookup_from_csv(CARBON_POOL_TABLE_FILENAME, 'LULC')

#Mark the pixels to convert.  Edge distance in increasing order
PIXELS_TO_CONVERT_PER_STEP = 2608


lulc_path = 'MG_Soy_Exp_07122013/mg_lulc0'
lulc_dataset = gdal.Open(lulc_path)
landcover_array = lulc_dataset.GetRasterBand(1).ReadAsArray()
total_grassland_pixels = numpy.count_nonzero(landcover_array == GRASSLAND)

forest_existance = numpy.zeros(landcover_array.shape)
for landcover_type in FOREST_LANDCOVER_TYPES:
	forest_existance = forest_existance + (landcover_array == landcover_type)


#This calculates an edge distance for the clusters of forest
edge_distance = scipy.ndimage.morphology.distance_transform_edt(
	forest_existance)
	
print 'total grassland pixels %s' % total_grassland_pixels

edge_distance[edge_distance == 0] = numpy.inf

output_table = open('grassland_expansion_carbon_stock_change.csv', 'wb')
output_table.write('Percent Soy Expansion,Total Above Ground Carbon Stocks (Mg)\n')
percent = 0


for deepest_edge_index in range(0, total_grassland_pixels + PIXELS_TO_CONVERT_PER_STEP, PIXELS_TO_CONVERT_PER_STEP):
	print 'percent %s' % percent
	landcover_mask = numpy.where(landcover_array == GRASSLAND)
	landcover_array[landcover_mask[0:PIXELS_TO_CONVERT_PER_STEP]] = CONVERTING_CROP

	carbon_stocks = numpy.zeros(landcover_array.shape)
	
	for landcover_type in REGRESSION_TYPES:
		print 'mapping landcover_type %s from biomass regression function' % landcover_type
		landcover_mask = numpy.where((landcover_array == landcover_type) * (edge_distance > 0))
		carbon_stocks[landcover_mask] = landcover_regression[landcover_type](edge_distance[landcover_mask])
	
	landcover_id_set = numpy.unique(landcover_array)
	
	for landcover_type in landcover_id_set:
		if landcover_type in REGRESSION_TYPES:
			continue
		carbon_per_pixel = 0.0
		if landcover_type in FROM_TABLE:
			#convert from Mg/Ha to Mg/Pixel
			print 'mapping landcover type %s from table %s' % (landcover_type, os.path.basename(CARBON_POOL_TABLE_FILENAME))
			carbon_per_pixel = carbon_pool_table[landcover_type]['C_ABOVE_MEAN'] * cell_size ** 2 / 10000
		else:
			#look it up in the mean table
			print 'mapping landcover type %s from mean of biomass raster %s' % (landcover_type, os.path.basename(BASE_BIOMASS_FILENAME))
			try:
				carbon_per_pixel = landcover_mean[landcover_type]
			except KeyError:
				print 'can\'t find a data entry for landcover type %s, treating that landcover type as 0 biomass' % landcover_type
		
		landcover_mask = numpy.where(landcover_array == landcover_type)
		carbon_stocks[landcover_mask] = carbon_per_pixel
	
	total_stocks = numpy.sum(carbon_stocks)
	percent += 1
	output_table.write('%s,%.2f\n' % (percent, total_stocks))
	output_table.flush()