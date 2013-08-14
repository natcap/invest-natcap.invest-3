import gdal
import numpy
import scipy.ndimage
import scipy
import pylab
import matplotlib.pyplot
import glob
import scipy.stats
import csv

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


def plot_regression(biomass_array, edge_distance_array, plot_id, plot_rows, plot_cols):
	pylab.subplot(plot_rows, plot_cols, plot_id + 1)
	pylab.plot(landcover_edge_distance, landcover_biomass, '.k', markersize=1)
	
	#Plot the regression function
	regression_distance = numpy.arange(
		0.0, numpy.max(landcover_edge_distance), 0.05)
	
	regression_biomass = f(regression_distance)
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
#These are the landcover types that should use the mean from the biophysical raster
MEAN_TYPES = [1, 3, 4, 5]
#All other land cover pool types will come from the data table, units are Mg/Ha

#Load the base biomass and landcover datasets
biomass_dataset = gdal.Open(BASE_BIOMASS_FILENAME)
biomass_nodata = biomass_dataset.GetRasterBand(1).GetNoDataValue()
landcover_dataset = gdal.Open(BASE_LANDCOVER_FILENAME)
biomass_array = biomass_dataset.GetRasterBand(1).ReadAsArray()
landcover_array = landcover_dataset.GetRasterBand(1).ReadAsArray()
print 'biomass size %s' % (str(biomass_array.shape))
print 'landcover size %s' % (str(biomass_array.shape))

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
for landcover_type in numpy.unique(landcover_array):
	print "landcover type: %s " % landcover_type,
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
	
	f = lambda(d): slope * numpy.log(d) + intercept
	
	landcover_biomass_mean = numpy.average(landcover_biomass)
	print ' biomass mean: %.2f' % landcover_biomass_mean,

	#calcualte R^2
	ss_tot = numpy.sum((landcover_biomass - landcover_biomass_mean) **2)
	ss_res = numpy.sum((landcover_biomass - f(landcover_edge_distance)) ** 2)
	r_value = 1 - ss_res / ss_tot
	std_dev = numpy.std(landcover_biomass)
	n_count = landcover_biomass.size
	print ' R^2: %.2f stddev: %.2f, n: %s' % (r_value, std_dev, n_count)
	
	landcover_regression[landcover_type] = numpy.vectorize(f)
	landcover_mean[landcover_type] = landcover_biomass_mean
	
#	plot_regression(biomass_array, landcover_edge_distance, plot_id, 5, 4)
#	plot_id += 1
	
#pylab.show()

#Parse out the landcover pool table
carbon_pool_table = get_lookup_from_csv(CARBON_POOL_TABLE_FILENAME, 'LULC')

print carbon_pool_table

LAND_USE_DIRECTORY = 'MG_Soy_Exp_07122013'
for lulc_path in glob.glob(LAND_USE_DIRECTORY + '/mg_*'):
	if '.' in lulc_path:
		continue
	print lulc_path
	lulc_dataset = gdal.Open(lulc_path)
	
	landcover_mask = numpy.where(
		(landcover_array == landcover_type) * 
		(biomass_array != biomass_nodata))
	
#	result = calculate_carbon_stocks(lulc_dataset)
	lulc_array = lulc_dataset.GetRasterBand(1).ReadAsArray()
	
	
	for landcover_type in FOREST_LANDCOVER_TYPES:
		forest_existance = forest_existance + (landcover_array == landcover_type)
	forest_existance[biomass_array == biomass_nodata] = 0.0

#This calculates an edge distance for the clusters of forest
	edge_distance = scipy.ndimage.morphology.distance_transform_edt(
		forest_existance)
	carbon_stocks = numpy.zeros(lulc_array.shape)
	
	print 'mapping forest carbon stocks with regression function'
	for landcover_type in REGRESSION_TYPES:
		landcover_mask = numpy.where(landcover_array == landcover_type)
		carbon_stocks[landcover_mask] = landcover_regression[landcover_type](edge_distance[landcover_mask])
	


#loop over each LULC, calculate carbon
	#calc above forest carbon w/ regression
	#calc other carbon w/ table