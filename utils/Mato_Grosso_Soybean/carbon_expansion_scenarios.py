"""This script calculates a log regresion function to predict forest carbon
    stocks based on the distance from the edge of the forest.  It has several
    options to simulate soybean expansion scenarios including:

    1) predefined scenarios as LULC GIS rasters
    2) forest erosion from edges inward
    3) grassland expansion, then forest erosion

    The program writes to a file called
    grassland_expansion_carbon_stock_change.csv that contains two columns, the
    first the soybean expansion percent and the second, the amount of carbon
    stocks on the landscape under that scenario."""

import gdal
import numpy
import scipy.ndimage
import scipy
import scipy.stats
import csv


def regression_builder(slope, intercept):
    """A function to use as a closure for a slope/intercept log function"""
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
        for cast_fn in cast_functions:
            try:
                return cast_fn(value)
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

def calculate_forest_edge_distance(lulc_array, forest_lucodes, cell_size):
    """Generates an array that contains the distance from the edge of
        a forest inside the forest.

        lulc_array - an array of land cover codes
        forest_lucodes - a list of lucodes that are forest types
        cell_size - the size of a cell

        returns an array of same shape as lulc_array that contains the distance
            from a forest pixel to its edge."""

    forest_existance = numpy.zeros(lulc_array.shape)
    for landcover_type in forest_lucodes:
        forest_existance = forest_existance + (lulc_array == landcover_type)

    #This calculates an edge distance for the clusters of forest
    edge_distance = scipy.ndimage.morphology.distance_transform_edt(
        forest_existance) * cell_size

    return edge_distance


def build_biomass_forest_edge_regression(
    landcover_array, biomass_array, biomass_nodata, edge_distance, cell_size,
    regression_lucodes):
    """Builds a log regression function to fit biomass to edge distance for a
        set of given lucodes.

        landcover_array - a numpy array of lucodes
        biomass_array - a numpy array of same size as landcover array indicating
            a density of biomass per Ha
        biomass_nodata - the value that indicates a nodata value for the
            biomass array
        edge_distance - a numpy array of same size as landcover_array indicating
            distance from forest edge
        cell_size - the cell size in meters
        regression_lucodes - a list of lucodes to build a regression for

        returns a dictionary mapping lucode to regression function"""

    landcover_regression = {}

    print 'building biomass regression'
    for landcover_type in regression_lucodes:
        
        landcover_mask = numpy.where(
            (landcover_array == landcover_type) *
            (biomass_array != biomass_nodata) * 
            (edge_distance != 0))

        landcover_biomass = (
            biomass_array[landcover_mask] * cell_size ** 2 / 10000)
        landcover_edge_distance = edge_distance[landcover_mask]
        
        #Fit a log function of edge distance to biomass for
        #landcover_type
        try:
            slope, intercept, r_value, p_value, std_err = (
                scipy.stats.linregress(numpy.log(landcover_edge_distance.flat),
                landcover_biomass.flat))
        except ValueError:
            print (
                "skipping landcover type %s because regression failed, "
                "likely no data" % landcover_type)
            continue
        print ('regression for lucode(%s) f(d)=%.2f * d + %.2f' %
            (landcover_type, slope, intercept))
        landcover_regression[landcover_type] = (
            regression_builder(slope, intercept))

    return landcover_regression

    
def calculate_landcover_means(
    landcover_array, biomass_array, biomass_nodata, cell_size):
    """Calculates the mean biomass for all the landcover types.

        landcover_array - a numpy array of lucodes
        biomass_array - a numpy array of same size as landcover array indicating
            a density of biomass per Ha
        biomass_nodata - the value that indicates a nodata value for the
            biomass array
        cell_size - the cell size in meters

        returns a dictionary mapping lucode to biomass mean"""

    landcover_mean = {}
    for landcover_type in numpy.unique(landcover_array):
        landcover_mask = numpy.where(
            (landcover_array == landcover_type) *
            (biomass_array != biomass_nodata))

        landcover_biomass = (
            biomass_array[landcover_mask] * cell_size ** 2 / 10000)
        if landcover_biomass.size > 0:
            landcover_mean[landcover_type] = numpy.average(landcover_biomass)
        else:
            landcover_mean[landcover_type] = 0.0
    return landcover_mean


def analyze_premade_lulc_scenarios():
    pass


def analyze_forest_erosion():
    pass


def analyze_grassland_expansion_forest_erosion(args):
    """This function does a simulation of cropland expansion by first
        consuming grassland, then expanding into the forest edges.

        args['base_biomass_filename'] - a raster that contains carbon densities
            per Ha.
        args['base_landcover_filename'] - a raster of same dimensions as
            'base_biomass_filename' that contains lucodes for the landscape
            regression analysis
        args['carbon_pool_table_filename'] - a CSV file containing carbon
            biomass values for given lucodes.  Must contain at least the
            columns 'LULC' and 'C_ABOVE_MEAN'
        args['forest_lucodes'] - a list of lucodes that are used to determine
            forest landcover types
        args['regression_lucodes'] - a list of lucodes that will use the
            linear regression to determine forest biomass given edge
            distance
        args['biomass_from_table_lucodes'] - a list of lucodes that will use
            the carbon pool csv table to determine biomass
        args['converting_crop'] - when a pixel is converted to crop, it uses
            this lucode.
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['grassland_lucode'] - this is the lucode for grassland used to
            determine what we should convert to.
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_lulc_base_map_filename'] - the base LULC map used for
            the scenario runs
        """

    #Load the base biomass and landcover datasets
    biomass_dataset = gdal.Open(args['base_biomass_filename'])
    biomass_nodata = biomass_dataset.GetRasterBand(1).GetNoDataValue()
    landcover_dataset = gdal.Open(args['base_landcover_filename'])
    biomass_array = biomass_dataset.GetRasterBand(1).ReadAsArray()
    landcover_array = landcover_dataset.GetRasterBand(1).ReadAsArray()

    #This gets us the cell size in projected units
    cell_size = landcover_dataset.GetGeoTransform()[1]

    #This calculates an edge distance for the clusters of forest
    regression_edge_distance = calculate_forest_edge_distance(
        landcover_array, args['forest_lucodes'], cell_size)

    #For each regression type, build a regression of biomass based
    #on the distance from the edge of the forest
    landcover_regression = build_biomass_forest_edge_regression(
        landcover_array, biomass_array, biomass_nodata,
        regression_edge_distance, cell_size, args['regression_lucodes'])

    #We'll use the biomass means in case we don't ahve a lookup value in the
    #table
    landcover_mean = calculate_landcover_means(
        landcover_array, biomass_array, biomass_nodata, cell_size)

    #Parse out the landcover pool table
    carbon_pool_table = get_lookup_from_csv(
        args['carbon_pool_table_filename'], 'LULC')

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()
    total_grassland_pixels = numpy.count_nonzero(
        scenario_lulc_array == args['grassland_lucode'])

    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    print 'total grassland pixels %s' % total_grassland_pixels

    #We want to visit the edge pixels in increasing distance order starting
    #from the fist pixel in.  Set the pixels outside to at a distance of
    #infinity so that we visit the inner edge forest pixels first
    scenario_edge_distance[scenario_edge_distance == 0] = numpy.inf
    increasing_distances = numpy.argsort(scenario_edge_distance.flat)

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion,Total Above Ground Carbon Stocks (Mg)\n')

    #These two indexes will keep track of the number of grassland, and later
    #how deep into the forest we've converted.
    grassland_pixels_converted = 0
    deepest_edge_index = 0
    #the 401 comes from converting 0-400 percent expansion, it's what Brad had
    #in the original scenario
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'percent %s' % percent

        #We have to recalculate the forest edge distances if we've eaten up
        #some of the forest so we can use the regression function to predict
        #the amount of carbon storage
        edge_distance = calculate_forest_edge_distance(
            scenario_lulc_array, args['forest_lucodes'], cell_size)
        #Add up the carbon stocks
        carbon_stocks = numpy.zeros(scenario_lulc_array.shape)
        for landcover_type in args['regression_lucodes']:
            #This bit of code converts all the landcover types that map their
            #carbon storage with a regression function
            landcover_mask = numpy.where(
                (scenario_lulc_array == landcover_type) * (edge_distance > 0))
            carbon_stocks[landcover_mask] = (
                landcover_regression[landcover_type](
                edge_distance[landcover_mask]))

        #This section will calculate carbon stocks either from the mean
        #calculated during regression building, or from the table, depending
        #on how the parameters are set
        for landcover_type in numpy.unique(landcover_array):
            if landcover_type in args['regression_lucodes']:
                #we already calculated earlier
                continue

            #since this kind of mapping is spatially independant, we only need
            #one variable to keep track of it
            carbon_per_pixel = 0.0
            if landcover_type in args['biomass_from_table_lucodes']:
                #convert from Mg/Ha to Mg/Pixel
                carbon_per_pixel = (
                    carbon_pool_table[landcover_type]['C_ABOVE_MEAN'] *
                    cell_size ** 2 / 10000)
            else:
                #look it up in the mean table
                try:
                    carbon_per_pixel = landcover_mean[landcover_type]
                except KeyError:
                    print (
                        'can\'t find a data entry for landcover type %s, '
                        'treating that landcover type as 0 biomass'
                        % landcover_type)

            #Map the carbon stocks of the current landcover type to the array
            landcover_mask = numpy.where(scenario_lulc_array == landcover_type)
            carbon_stocks[landcover_mask] = carbon_per_pixel

        #Dump the current percent iteration's carbon stocks to the csv file
        total_stocks = numpy.sum(carbon_stocks)
        output_table.write('%s,%.2f\n' % (percent, total_stocks))
        output_table.flush()
        
        #Convert lulc for the next iteration
        if grassland_pixels_converted < total_grassland_pixels:
            #This section converts grassland
            landcover_mask = numpy.where(
                scenario_lulc_array.flat == args['grassland_lucode'])
            print landcover_mask[0][0:args['pixels_to_convert_per_step']]
            scenario_lulc_array.flat[landcover_mask[0][
                0:args['pixels_to_convert_per_step']]] = args['converting_crop']
            grassland_pixels_converted += args['pixels_to_convert_per_step']
        else:
            #Converts forest pixels edge in if grassland is all converted
            deepest_edge_index += args['pixels_to_convert_per_step']
            scenario_lulc_array.flat[
                increasing_distances[0:deepest_edge_index]] = (
                    args['converting_crop'])

if __name__ == '__main__':


    ARGS = {
        #the locations for the various filenames needed for the simulations
        'base_biomass_filename': './Carbon_MG_2008/mg_bio_2008',
        'base_landcover_filename': './Carbon_MG_2008/mg_lulc_2008',
        'carbon_pool_table_filename': './mato_grosso_carbon.csv',
        #these are the landcover types that are used when determining edge
        #effects from forests
        'forest_lucodes': [1, 2, 3, 4, 5],
        #These are the landcover types that should use the log regression
        #when calculating storage biomass
        'regression_lucodes': [2],
        #These are the LULCs to take directly from table, everything else is
        #mean from regression
        'biomass_from_table_lucodes': [10, 12, 120, 0],
        #This is the crop we convert into
        'converting_crop': 120,
        'scenario_conversion_steps': 400,
        'pixels_to_convert_per_step': 2608,
        'grassland_lucode': 10,
        'output_table_filename': 'grassland_expansion_carbon_stock_change.csv',
        'scenario_lulc_base_map_filename': 'MG_Soy_Exp_07122013/mg_lulc0',

    }

    #analyze_premade_lulc_scenarios()
    #analyze_forest_erosion()
    analyze_grassland_expansion_forest_erosion(ARGS)
