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
BASE_BIOMASS_FILENAME = './Carbon_MG_2008/mg_bio_2008'
BASE_LANDCOVER_FILENAME = './Carbon_MG_2008/mg_lulc_2008'
CARBON_POOL_TABLE_FILENAME = './mato_grosso_carbon.csv'


#These are the landcover types that define clusters of forest for the distance from edge calculation
FOREST_LANDCOVER_TYPES = [1, 2, 3, 4, 5]
#These are the landcover types that should use the log regression
REGRESSION_TYPES = [2]
#These are the LULCs to take directly from table, everything else is mean from regression
FROM_TABLE = [10, 12, 120, 0]

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
	
	landcover_biomass = biomass_array[landcover_mask]
	
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
	landcover_biomass_mean = numpy.average(landcover_biomass)
	
	#calcualte R^2
	ss_tot = numpy.sum((landcover_biomass - landcover_biomass_mean) **2)
	ss_res = numpy.sum((landcover_biomass - landcover_regression[landcover_type](landcover_edge_distance)) ** 2)
	r_value = 1 - ss_res / ss_tot
	std_dev = numpy.std(landcover_biomass)
	n_count = landcover_biomass.size
	print '%s, %.2f, %.2f, %.2f, %s, %s' % (landcover_type, landcover_biomass_mean, r_value, std_dev, n_count, landcover_regression[landcover_type](1))
	
	
	landcover_mean[landcover_type] = landcover_biomass_mean
	
	#plot_regression(biomass_array, landcover_edge_distance, plot_id, 5, 4, landcover_regression[landcover_type])
	#plot_id += 1
	
#pylab.show()

#Parse out the landcover pool table
carbon_pool_table = get_lookup_from_csv(CARBON_POOL_TABLE_FILENAME, 'LULC')
print landcover_regression
for landcover_type, f in landcover_regression.iteritems():
	print landcover_type, f(1)

LAND_USE_DIRECTORY = 'MG_Soy_Exp_07122013'

output_table = open('carbon_stock_change.csv', 'wb')
output_table.write('Percent Soy Expansion,Total Above Ground Carbon Stocks (Mg)\n')
for lulc_path in glob.glob(LAND_USE_DIRECTORY + '/mg_*'):
	if '.' in lulc_path:
		continue
	print '\n*** Calculating carbon stocks in %s' % os.path.basename(lulc_path)
	lulc_dataset = gdal.Open(lulc_path)
	landcover_array = lulc_dataset.GetRasterBand(1).ReadAsArray()
	
	landcover_mask = numpy.where(landcover_array == landcover_type)
	forest_existance = numpy.zeros(landcover_array.shape)
	for landcover_type in FOREST_LANDCOVER_TYPES:
		forest_existance = forest_existance + (landcover_array == landcover_type)

#This calculates an edge distance for the clusters of forest
	edge_distance = scipy.ndimage.morphology.distance_transform_edt(
		forest_existance)
	carbon_stocks = numpy.zeros(landcover_array.shape)
	
	for landcover_type in REGRESSION_TYPES:
		print 'mapping landcover_type %s from biomass regression function' % landcover_type
		landcover_mask = numpy.where((landcover_array == landcover_type) * (edge_distance > 0))
		carbon_stocks[landcover_mask] = landcover_regression[landcover_type](edge_distance[landcover_mask])
	
	landcover_id_set = numpy.unique(landcover_array)
	
	for landcover_type in landcover_id_set:
		if landcover_type in REGRESSION_TYPES:
			continue
		
		if landcover_type in FROM_TABLE:
			#convert from Mg/Ha to Mg/Pixel
			print 'mapping landcover type %s from table %s' % (landcover_type, os.path.basename(CARBON_POOL_TABLE_FILENAME))
			carbon_per_pixel = carbon_pool_table[landcover_type]['C_ABOVE_MEAN'] * cell_size ** 2 / 10000
		else:
			#look it up in the mean table
			print 'mapping landcover type %s from mean of biomass raster %s' % (landcover_type, os.path.basename(BASE_BIOMASS_FILENAME))
			try:
				carbon_per_pixel = landcover_mean[landcover_type] * cell_size ** 2 / 10000
			except KeyError:
				print 'can\'t find a data entry for landcover type %s, treating that landcover type as 0 biomass' % landcover_type
		
		landcover_mask = numpy.where(landcover_array == landcover_type)
		carbon_stocks[landcover_mask] = carbon_per_pixel
	
	total_stocks = numpy.sum(carbon_stocks)
	percent = re.search('[0-9]+$', lulc_path).group(0)
	output_table.write('%s,%.2f\n' % (percent, total_stocks))
	output_table.flush()