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
import os
import sys
import collections
import errno
from multiprocessing import Pool
import time
from invest_natcap import raster_utils

def lowpriority():
    """ Set the priority of the process to below-normal."""

    import sys
    try:
        sys.getwindowsversion()
    except:
        isWindows = False
    else:
        isWindows = True

    if isWindows:
        # Based on:
        #   "Recipe 496767: Set Process Priority In Windows" on ActiveState
        #   http://code.activestate.com/recipes/496767/
        import win32api,win32process,win32con

        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.IDLE_PRIORITY_CLASS)
    else:
        import os

        os.nice(1)

def new_raster_from_base_uri(
    base_uri, output_uri, gdal_format, nodata, datatype, fill_value=None):

    base = gdal.Open(base_uri)
    
    n_cols = base.RasterXSize
    n_rows = base.RasterYSize
    projection = base.GetProjection()
    geotransform = base.GetGeoTransform()
    driver = gdal.GetDriverByName(gdal_format)
    new_raster = driver.Create(
        output_uri.encode('utf-8'), n_cols, n_rows, 1, datatype)
    new_raster.SetProjection(projection)
    new_raster.SetGeoTransform(geotransform)
    band = new_raster.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    if fill_value != None:
        band.Fill(fill_value)
    else:
        band.Fill(nodata)
    band = None

    return new_raster

    
def expand_lu_type(
    base_array, nodata, expansion_id, converting_id_list, current_step, 
    pixels_per_step, land_cover_start_fractions=None,
    land_cover_end_fractions=None, end_step=None):
    """Given a base array, and a number of pixels to expand
        from, buffer out a conversion of that number of pixels
        
        base_array - a 2D array of integers that represent
            land cover IDs
        nodata - value in base_array to ignore
        expansion_id - the ID type to expand
        converting_id_list - a list of land cover types that the simulation will
            calculate distances from
        expansion_pixel_count - convert this number of pixels
        land_cover_start_percentages/land_cover_end_percentages -
            optional, if defined is a dictionary of land cover types
            that are used for conversion during the start step
        end_expansion_pixel_count - defined if land_cover_*_percentages are defined.  use to know what % of total conversion has been reached
        
        returns the new expanded array, the number of pixels per type that were converted to expansion_id
        """
        
    def step_percent(lu_code):
        total_pixels = 0
        for step_id in range(current_step):
            if end_step != 1:
                current_percent = float(step_id) / (end_step - 1)
            else:
                current_percent = 0.0
            #print current_percent, pixels_per_step
            total_pixels += pixels_per_step * (
                land_cover_start_fractions[lu_code] * (1-current_percent) + 
                land_cover_end_fractions[lu_code] * current_percent)
        return total_pixels
            
    expansion_pixel_count = pixels_per_step * current_step
    
    #Calculate the expansion distance
    expansion_existance = base_array != nodata
    for converting_id in converting_id_list:
        expansion_existance = (base_array != converting_id) & expansion_existance
    edge_distance = scipy.ndimage.morphology.distance_transform_edt(
        expansion_existance)
        
    zero_distance_mask = edge_distance == 0
    edge_distance = scipy.ndimage.filters.gaussian_filter(edge_distance, 2.0)
    edge_distance[zero_distance_mask] = numpy.inf
    
    result_array = base_array.copy()
    pixels_converted_so_far = 0
    pixel_count = collections.defaultdict(int)
    for lu_code in land_cover_start_fractions:
        lu_edge_distance = edge_distance.copy()
        lu_edge_distance[base_array != lu_code] = numpy.inf
        increasing_distances = numpy.argsort(lu_edge_distance.flat)
        lu_pixels_to_convert = int(round(step_percent(lu_code)))
        result_array.flat[increasing_distances[0:lu_pixels_to_convert]] = expansion_id
        pixels_converted_so_far += int(lu_pixels_to_convert)
        pixel_count[lu_code] += int(lu_pixels_to_convert)
    edge_distance[result_array == expansion_id] = numpy.inf
    increasing_distances = numpy.argsort(edge_distance.flat)
    #print expansion_pixel_count - pixels_converted_so_far
    
    remaining_pixels = result_array.flat[increasing_distances[0:(expansion_pixel_count - pixels_converted_so_far)]]
    for lu_code in numpy.unique(remaining_pixels):
        pixel_count[lu_code] += numpy.count_nonzero(remaining_pixels == lu_code)
    result_array.flat[increasing_distances[0:(expansion_pixel_count - pixels_converted_so_far)]] = expansion_id
        
    return result_array, pixel_count


def analyze_composite_carbon_stock_change(args):
    """This function loads scenarios from disk and calculates the carbon stocks
        on them.

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
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['scenario_path'] - the path to the directory that holds the
            scenarios
        args['converting_crop'] - when a pixel is converted to crop, it uses
            this lucode.
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['land_cover_start_fractions'] - a dictionary of landcover
            types to conversion fractions per step for the first step
            of land cover conversion.  The fractional amounts should
            add up to less than or equal to 1.  If less than 1
            land cover nearest to agriculture will be converted.
        args['land_cover_end_fractions'] - a dictionary of landcover
            types to conversion fractions per step for the last step
            of land cover conversion.  Percent of landcover will be
            linearly interpolated between 'start' and 'end' fractions.
        args['output_pixel_count_filename'] - a report of the number of pixel
            types changed per step
        """
    lowpriority()
    print 'starting composite expansion scenario'
    landcover_regression, landcover_mean, carbon_pool_table = (
        load_base_datasets(args))

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()
    scenario_nodata = scenario_lulc_dataset.GetRasterBand(1).GetNoDataValue()
    
    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Crop Expansion,Number of Pixels Converted,Total Above Ground Carbon Stocks (Mg),Total Above Ground Carbon Stocks (Mg) (lower tail),Total Above Ground Carbon Stocks (Mg) (upper tail)\n')
    
    output_count_table = open(args['output_pixel_count_filename'], 'wb')
    unique_lucodes = sorted(numpy.unique(scenario_lulc_array))
    output_count_table.write(','.join(map(str,unique_lucodes)) + '\n')

    expansion_existance = (scenario_lulc_array != args['converting_crop']) & (scenario_lulc_array != scenario_nodata)

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating carbon stocks for composite expansion step %s' % percent
        try:
            expanded_lulc_array, pixel_count = expand_lu_type(
                scenario_lulc_array, scenario_nodata, args['converting_crop'], 
                args['converting_id_list'], percent, args['pixels_to_convert_per_step'], 
                args['land_cover_start_fractions'], 
                args['land_cover_end_fractions'], 
                args['scenario_conversion_steps'])
        except Exception as e:
            print e
            return
        for lu_code in unique_lucodes:
            output_count_table.write('%s,' % pixel_count[lu_code])
        output_count_table.write('\n')
        output_count_table.flush()
        #Calculate the carbon stocks based on the regression functions, lookup
        #tables, and land cover raster.
        output_table.write('%s,%s' % (percent, args['pixels_to_convert_per_step']*percent))
        #Calcualte the carbon stocks based on the regression functions, lookup
        #tables, and land cover raster.
        for tail_type in ['median', 'lower', 'upper']:
            carbon_stocks = calculate_carbon_stocks(
                scenario_lulc_array, args['forest_lucodes'],
                args['regression_lucodes'],
                args['biomass_from_table_lucodes'], carbon_pool_table,
                landcover_regression, landcover_mean, cell_size, tail=tail_type)

            #Dump the current percent iteration's carbon stocks to the csv file
            total_stocks = numpy.sum(carbon_stocks)
            print 'total %s stocks %.2f' % (tail_type, total_stocks)
            output_table.write(',%.2f' % (total_stocks))
        output_table.write('\n')
        output_table.flush()
        
        if percent % 100 == 0:
            print 'dumping a raster at percent %s%%' % percent
            output_uri = os.path.join(os.path.dirname(args['output_table_filename']), 'composite_lulc_80_20_%ss.tif' % percent)
            lulc_out_ds = new_raster_from_base_uri(
                args['scenario_lulc_base_map_filename'], output_uri, 'GTiff', -1, gdal.GDT_Int32)
            lulc_band = lulc_out_ds.GetRasterBand(1)
            lulc_band.WriteArray(expanded_lulc_array)
            lulc_band = None
            lulc_out_ds = None

    
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
        
            x = numpy.log(landcover_edge_distance.flat)
            y = landcover_biomass.flat
            
            slope, intercept, r_value, p_value, std_err = (
                scipy.stats.linregress(x, y))
                
            landcover_regression[landcover_type] = {
                'median': regression_builder(slope, intercept),
            }
            
            landcover_regression[landcover_type]['lower'] = (
                regression_builder_confidence(x, y, slope, intercept, 'lower'))
            landcover_regression[landcover_type]['upper'] = (
                regression_builder_confidence(x, y, slope, intercept, 'upper'))
                
        except ValueError:
            print (
                "skipping landcover type %s because regression failed, "
                "likely no data" % landcover_type)
            continue
        print ('regression for lucode(%s) f(d)=%.2f * d + %.2f' %
            (landcover_type, slope, intercept))

    return landcover_regression

def regression_builder_confidence(x, y, slope, intercept, mode):
    """Builds a confidence interval function given the log'd x's and y
        along with the slope and intercept calculated from the linear
        regression."""
        
    x_mean = numpy.mean(x)
    n = x.size
    denom = numpy.sum(numpy.power(x-x_mean, 2.0))
    t_star = scipy.stats.t.ppf(0.975, n-2)
    p_y = slope * x + intercept
    y_err = y - p_y
    sigma_e = numpy.sqrt(numpy.sum(numpy.power(y_err, 2)))
    if mode == 'lower':
        return lambda x_star: slope * numpy.log(x_star) + intercept - numpy.abs(t_star * sigma_e * numpy.sqrt(1.0/n + numpy.power(numpy.log(x_star) - x_mean, 2) / denom))
    elif mode == 'upper':
        return lambda x_star: slope * numpy.log(x_star) + intercept + numpy.abs(t_star * sigma_e * numpy.sqrt(1.0/n + numpy.power(numpy.log(x_star) - x_mean, 2) / denom))
    

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


def load_base_datasets(args):
    """Loads the base regression and mean functions

        returns biomass_regression_dictionary, landcover_mean_dictionary,
            carbon_pool_table"""

    #Load the base biomass and landcover datasets
    biomass_dataset = gdal.Open(args['base_biomass_filename'])
    biomass_nodata = biomass_dataset.GetRasterBand(1).GetNoDataValue()
    landcover_dataset = gdal.Open(args['base_landcover_filename'])
    landcover_nodata = landcover_dataset.GetRasterBand(1).GetNoDataValue()
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
    carbon_pool_table_raw = get_lookup_from_csv(
        args['carbon_pool_table_filename'], 'LULC')
        
    carbon_pool_table_confidence = {}
    for lu_code in carbon_pool_table_raw:
        try:
            sd = float(carbon_pool_table_raw[lu_code]['C_ABOVE_SD'])
            mn = float(carbon_pool_table_raw[lu_code]['C_ABOVE_MEAN'])
            print lu_code, mn, sd
            if sd == 0:
                ci = (0.0, 0.0)
            else:
                ci = scipy.stats.norm.interval(0.95, loc=mn, scale=sd)
            carbon_pool_table_confidence[lu_code] = {
                'median': mn,
                'lower': ci[0] if ci[0] > 0 else 0,
                'upper': ci[1],
                }
        except ValueError:
            print '%s not in table' % lu_code

    return landcover_regression, landcover_mean, carbon_pool_table_confidence


def calculate_carbon_stocks(
    scenario_lulc_array, forest_lucodes, regression_lucodes,
    biomass_from_table_lucodes, carbon_pool_table, landcover_regression,
    landcover_mean, cell_size, tail='median'):
    """A helper function to calculate carbon stocks based on all the parameters
        that commonly go into each scenario.

        scenario_lulc_array - numpy array of lucodes
        forest_lucodes - a list of the lucodes that are forest.  used for
            edge detection
        regression_lucodes - a list of the lucodes that will be calculated by
            regression analysis
        biomass_from_table_lucodes - a list of the lucodes that will be
            calculated from a lookup table
        carbon_pool_table - a dictionary of lucode to biomass
        landcover_regression - a dictionary mapping lucode to biomass regression
            with both lower, median, and upper error limits 'lower', 'median', 'upper'
        landcover_mean - a dictionary mapping lucode to biomas mean
        cell_size - the cell size in meters
        tail - (optional) can be 'lower' 'upper' or 'median' to give a CI on 
            carbon stocks

        return array of carbon stocks in Mg/pixel the same size as
            scenario_lulc_array"""

    #We have to recalculate the forest edge distances if we've eaten up
    #some of the forest so we can use the regression function to predict
    #the amount of carbon storage
    edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, forest_lucodes, cell_size)
    #Add up the carbon stocks
    carbon_stocks = numpy.zeros(scenario_lulc_array.shape)
    for landcover_type in regression_lucodes:
        #This bit of code converts all the landcover types that map their
        #carbon storage with a regression function
        landcover_mask = numpy.where(
            (scenario_lulc_array == landcover_type) * (edge_distance > 0))
        carbon_stocks[landcover_mask] = (
            landcover_regression[landcover_type][tail](
            edge_distance[landcover_mask]))

    #This section will calculate carbon stocks either from the mean
    #calculated during regression building, or from the table, depending
    #on how the parameters are set
    print carbon_pool_table
    for landcover_type in numpy.unique(scenario_lulc_array):
        if landcover_type in regression_lucodes:
            #we already calculated earlier
            continue

        #since this kind of mapping is spatially independant, we only need
        #one variable to keep track of it
        carbon_per_pixel = 0.0
        if landcover_type in biomass_from_table_lucodes:
            #convert from Mg/Ha to Mg/Pixel
            carbon_per_pixel = (
                carbon_pool_table[landcover_type][tail] *
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
        carbon_stocks[scenario_lulc_array == landcover_type] = (
            carbon_per_pixel)

    return carbon_stocks


def analyze_forest_edge_erosion(args):
    """This function does a simulation of cropland expansion by
        expanding into the forest edges.

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
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_lulc_base_map_filename'] - the base LULC map used for
            the scenario runs
        """
    lowpriority()
    print 'starting forest edge expansion scenario'
    landcover_regression, landcover_mean, carbon_pool_table = (
        load_base_datasets(args))

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()

    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #We want to visit the edge pixels in increasing distance order starting
    #from the fist pixel in.  Set the pixels outside to at a distance of
    #infinity so that we visit the inner edge forest pixels first
    scenario_edge_distance[scenario_edge_distance == 0] = numpy.inf
    increasing_distances = numpy.argsort(scenario_edge_distance.flat)

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Crop Expansion,Number of Pixels Converted,Total Above Ground Carbon Stocks (Mg),Total Above Ground Carbon Stocks (Mg) (lower tail),Total Above Ground Carbon Stocks (Mg) (upper tail)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating carbon stocks for expansion step %s' % percent
        output_table.write('%s,%s' % (percent, args['pixels_to_convert_per_step']*percent))
        #Calcualte the carbon stocks based on the regression functions, lookup
        #tables, and land cover raster.
        for tail_type in ['median', 'lower', 'upper']:
            carbon_stocks = calculate_carbon_stocks(
                scenario_lulc_array, args['forest_lucodes'],
                args['regression_lucodes'],
                args['biomass_from_table_lucodes'], carbon_pool_table,
                landcover_regression, landcover_mean, cell_size, tail=tail_type)

            #Dump the current percent iteration's carbon stocks to the csv file
            total_stocks = numpy.sum(carbon_stocks)
            print 'total %s stocks %.2f' % (tail_type, total_stocks)
            output_table.write(',%.2f' % (total_stocks))
        output_table.write('\n')
        output_table.flush()

        deepest_edge_index += args['pixels_to_convert_per_step']
        if scenario_edge_distance.flat[increasing_distances[deepest_edge_index - 1]] == numpy.inf:
            print 'WARNING: All the forest has been converted, stopping at step %s' % percent
            return
        scenario_lulc_array.flat[
            increasing_distances[0:deepest_edge_index]] = (
                args['converting_crop'])
                
        if percent % 100 == 0:
            print 'dumping a raster at percent %s%%' % percent
            output_uri = os.path.join(os.path.dirname(args['output_table_filename']), 'edge_lulc_%s.tif' % percent)
            lulc_out_ds = new_raster_from_base_uri(
                args['scenario_lulc_base_map_filename'], output_uri, 'GTiff', -1, gdal.GDT_Int32)
            lulc_band = lulc_out_ds.GetRasterBand(1)
            lulc_band.WriteArray(scenario_lulc_array)
            lulc_band = None
            lulc_out_ds = None


def analyze_forest_core_expansion(args):
    """This function does a simulation of cropland expansion by
        expanding into the forest edges.

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
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_lulc_base_map_filename'] - the base LULC map used for
            the scenario runs
        """
    lowpriority()
    print 'starting forest core expansion scenario'
    landcover_regression, landcover_mean, carbon_pool_table = (
        load_base_datasets(args))

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()

    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #We want to visit the edge pixels in decreasing distance order starting
    #from the core pixel in.
    decreasing_distances = numpy.argsort(scenario_edge_distance.flat)[::-1]

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Crop Expansion,Number of Pixels Converted,Total Above Ground Carbon Stocks (Mg),Total Above Ground Carbon Stocks (Mg) (lower tail),Total Above Ground Carbon Stocks (Mg) (upper tail)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0
    for percent in range(0, args['scenario_conversion_steps'] + 1):
        print 'calculating carbon stocks for expansion step %s' % percent
        output_table.write('%s,%s' % (percent, args['pixels_to_convert_per_step']*percent))
        #Calcualte the carbon stocks based on the regression functions, lookup
        #tables, and land cover raster.
        for tail_type in ['median', 'lower', 'upper']:
            carbon_stocks = calculate_carbon_stocks(
                scenario_lulc_array, args['forest_lucodes'],
                args['regression_lucodes'],
                args['biomass_from_table_lucodes'], carbon_pool_table,
                landcover_regression, landcover_mean, cell_size, tail=tail_type)

            #Dump the current percent iteration's carbon stocks to the csv file
            total_stocks = numpy.sum(carbon_stocks)
            print 'total %s stocks %.2f' % (tail_type, total_stocks)
            output_table.write(',%.2f' % (total_stocks))
        output_table.write('\n')
        output_table.flush()

        deepest_edge_index += args['pixels_to_convert_per_step']
        if scenario_edge_distance.flat[decreasing_distances[deepest_edge_index - 1]] == 0.0:
            print 'WARNING: All the forest has been converted, stopping at step %s' % percent
            return
        scenario_lulc_array.flat[
            decreasing_distances[0:deepest_edge_index]] = (
                args['converting_crop'])
                
        if percent % 100 == 0:
            print 'dumping a raster at percent %s%%' % percent
            output_uri = os.path.join(os.path.dirname(args['output_table_filename']), 'core_lulc_%s.tif' % percent)
            lulc_out_ds = new_raster_from_base_uri(
                args['scenario_lulc_base_map_filename'], output_uri, 'GTiff', -1, gdal.GDT_Int32)
            lulc_band = lulc_out_ds.GetRasterBand(1)
            lulc_band.WriteArray(scenario_lulc_array)
            lulc_band = None
            lulc_out_ds = None


def analyze_forest_core_fragmentation(args):
    """This function does a simulation of cropland expansion by
        expanding into the most core regions of the forest on every simulation
        step.

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
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_lulc_base_map_filename'] - the base LULC map used for
            the scenario runs
        """
    lowpriority()
    print 'starting forest core fragmentation scenario'
    landcover_regression, landcover_mean, carbon_pool_table = (
        load_base_datasets(args))

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()


    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Crop Expansion,Number of Pixels Converted,Total Above Ground Carbon Stocks (Mg)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0
    for percent in range(0, args['scenario_conversion_steps'] + 1):
        print 'calculating carbon stocks for expansion step %s' % percent
        output_table.write('%s,%s' % (percent, args['pixels_to_convert_per_step']*percent))
        #Calcualte the carbon stocks based on the regression functions, lookup
        #tables, and land cover raster.
        for tail_type in ['median', 'lower', 'upper']:
            carbon_stocks = calculate_carbon_stocks(
                scenario_lulc_array, args['forest_lucodes'],
                args['regression_lucodes'],
                args['biomass_from_table_lucodes'], carbon_pool_table,
                landcover_regression, landcover_mean, cell_size, tail=tail_type)

            #Dump the current percent iteration's carbon stocks to the csv file
            total_stocks = numpy.sum(carbon_stocks)
            print 'total %s stocks %.2f' % (tail_type, total_stocks)
            output_table.write(',%.2f' % (total_stocks))
        output_table.write('\n')
        output_table.flush()

        deepest_edge_index = args['pixels_to_convert_per_step']

        scenario_edge_distance = calculate_forest_edge_distance(
            scenario_lulc_array, args['forest_lucodes'], cell_size)

        #We want to visit the edge pixels in decreasing distance order starting
        #from the core pixel in.
        decreasing_distances = numpy.argsort(scenario_edge_distance.flat)[::-1]
        if scenario_edge_distance.flat[decreasing_distances[deepest_edge_index - 1]] == 0:
            print 'WARNING: All the forest has been converted, stopping at step %s' % percent
            return
        scenario_lulc_array.flat[
            decreasing_distances[0:deepest_edge_index]] = (
                args['converting_crop'])
                
        if percent % 100 == 0:
            print 'dumping a raster at percent %s%%' % percent
            output_uri = os.path.join(os.path.dirname(args['output_table_filename']), 'frag_lulc_%s.tif' % percent)
            lulc_out_ds = new_raster_from_base_uri(
                args['scenario_lulc_base_map_filename'], output_uri, 'GTiff', -1, gdal.GDT_Int32)
            lulc_band = lulc_out_ds.GetRasterBand(1)
            lulc_band.WriteArray(scenario_lulc_array)
            lulc_band = None
            lulc_out_ds = None


def analyze_lu_expansion(args):
    """This function does a simulation of cropland expansion by
        consuming a static landcover (not forest).

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
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['conversion_lucode'] - this is the non-forest lucode for to convert
            to ag.
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_lulc_base_map_filename'] - the base LULC map used for
            the scenario runs
        """
    lowpriority()
    print 'starting lucode expansion scenario'
    #Load the base biomass and landcover datasets
    landcover_regression, landcover_mean, carbon_pool_table = (
        load_base_datasets(args))

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()
    total_converting_pixels = numpy.count_nonzero(
        scenario_lulc_array == args['conversion_lucode'])

    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    print 'total converting pixels %s' % total_converting_pixels

    #We want to visit the edge pixels in increasing distance order starting
    #from the fist pixel in.  Set the pixels outside to at a distance of
    #infinity so that we visit the inner edge forest pixels first
    scenario_edge_distance[scenario_edge_distance == 0] = numpy.inf
    increasing_distances = numpy.argsort(scenario_edge_distance.flat)

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Crop Expansion,Number of Pixels Converted,Total Above Ground Carbon Stocks (Mg),Total Above Ground Carbon Stocks (Mg) (lower tail),Total Above Ground Carbon Stocks (Mg) (upper tail)\n')


    #These two indexes will keep track of the number of grassland, and later
    #how deep into the forest we've converted.
    pixels_converted = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating carbon stocks for expansion step %s' % percent
        output_table.write('%s,%s' % (percent, args['pixels_to_convert_per_step']*percent))
        #Calcualte the carbon stocks based on the regression functions, lookup
        #tables, and land cover raster.
        for tail_type in ['median', 'lower', 'upper']:
            carbon_stocks = calculate_carbon_stocks(
                scenario_lulc_array, args['forest_lucodes'],
                args['regression_lucodes'],
                args['biomass_from_table_lucodes'], carbon_pool_table,
                landcover_regression, landcover_mean, cell_size, tail=tail_type)

            #Dump the current percent iteration's carbon stocks to the csv file
            total_stocks = numpy.sum(carbon_stocks)
            print 'total %s stocks %.2f' % (tail_type, total_stocks)
            output_table.write(',%.2f' % (total_stocks))
        output_table.write('\n')
        output_table.flush()

        #Convert lulc for the next iteration
        #This section converts grassland
        landcover_mask = numpy.where(
            scenario_lulc_array.flat == args['conversion_lucode'])
        scenario_lulc_array.flat[landcover_mask[0][
            0:args['pixels_to_convert_per_step']]] = args['converting_crop']

            
def run_mgds(number_of_steps, pool):
    output_dir = './carbon_mgds_output'
    args = {
        #the locations for the various filenames needed for the simulations
        'base_biomass_filename': './inputs/Carbon_MG_2008/mg_bio_2008',
        'base_landcover_filename': './inputs/Carbon_MG_2008/mg_lulc_2008',
        'carbon_pool_table_filename': './inputs/brazil_carbon.csv',
        #these are the landcover types that are used when determining edge
        #effects from forests
        'forest_lucodes': [1, 2, 3, 4, 5],
        #These are the landcover types that should use the log regression
        #when calculating storage biomass
        'regression_lucodes': [2],
        #These are the LULCs to take directly from table, everything else is
        #mean from regression
        'biomass_from_table_lucodes': [10, 12, 17, 0],
        'converting_crop': 17,
        'scenario_lulc_base_map_filename': 'inputs/mgds_lulc_base',
        'scenario_conversion_steps': number_of_steps,
        'converting_id_list': [12, 17, 120],
        #Becky wants the average between MGDS and MG
        'pixels_to_convert_per_step': 932,
    }

    #set up args for the composite scenario
    raster_utils.create_directories([output_dir])
    args['output_table_filename'] = (
        os.path.join(output_dir, 'composite_carbon_stock_change_20_80_mgds.csv'))
    args['output_pixel_count_filename'] = (
        os.path.join(output_dir, 'composite_carbon_stock_change_20_80_pixel_count_mgds.csv'))
    args['land_cover_start_fractions'] = {
        2: .2,
        9: .8
        }
    args['land_cover_end_fractions'] = {
        2: .8,
        9: .2
        }
    pool.apply_async(analyze_composite_carbon_stock_change, args=[args.copy()])
    #analyze_composite_carbon_stock_change(args)
    
    #Set up args for the forest core scenario
    args['output_table_filename'] = (
        os.path.join(output_dir, 'forest_core_fragmentation_carbon_stock_change_mgds.csv'))
    pool.apply_async(analyze_forest_core_fragmentation, args=[args.copy()])
    
    #Set up args for the forest core scenario
    args['output_table_filename'] = (
        os.path.join(output_dir, 'forest_core_degredation_carbon_stock_change_mgds.csv'))
    pool.apply_async(analyze_forest_core_expansion, args=[args.copy()])
    
    #Set up args for the savanna scenario
    args['output_table_filename'] = (
        os.path.join(output_dir, 'savanna_expansion_carbon_stock_change_mgds.csv'))
    args['conversion_lucode'] = 9 #woody savannna    
    pool.apply_async(analyze_lu_expansion, args=[args.copy()])
    
    #Set up args for the forest edge erosion scenario
    args['output_table_filename'] = (
        os.path.join(output_dir, 'forest_edge_erosion_carbon_stock_change_mgds.csv'))
    pool.apply_async(analyze_forest_edge_erosion, args=[args.copy()])
    
    
def run_mg(number_of_steps, pool):
    output_dir = './carbon_mg_output'
    args = {
        #the locations for the various filenames needed for the simulations
        'base_biomass_filename': './inputs/Carbon_MG_2008/mg_bio_2008',
        'base_landcover_filename': './inputs/Carbon_MG_2008/mg_lulc_2008',
        'carbon_pool_table_filename': './inputs/brazil_carbon.csv',
        #these are the landcover types that are used when determining edge
        #effects from forests
        'forest_lucodes': [1, 2, 3, 4, 5],
        #These are the landcover types that should use the log regression
        #when calculating storage biomass
        'regression_lucodes': [2],
        #These are the LULCs to take directly from table, everything else is
        #mean from regression
        'biomass_from_table_lucodes': [10, 12, 120, 0],
        'converting_crop': 120,
        'scenario_lulc_base_map_filename': 'inputs/mg_lulc_base',
        'scenario_conversion_steps': number_of_steps,
        'converting_id_list': [12, 17, 120],
        #Becky calculated this for MG
        'pixels_to_convert_per_step': 932,
    }

    #set up args for the composite scenario
    raster_utils.create_directories([output_dir])
    
    args['output_table_filename'] = (
        os.path.join(output_dir, 'composite_carbon_stock_change_20_80_mg.csv'))
    args['output_pixel_count_filename'] = (
        os.path.join(output_dir, 'composite_carbon_stock_change_20_80_pixel_count_mg.csv'))
    args['land_cover_start_fractions'] = {
        2: .2,
        9: .8
        }
    args['land_cover_end_fractions'] = {
        2: .8,
        9: .2
        }
    pool.apply_async(analyze_composite_carbon_stock_change, args=[args.copy()])
    #analyze_composite_carbon_stock_change(args)
    
    #Set up args for the forest core scenario
    args['output_table_filename'] = (
        os.path.join(output_dir, 'forest_core_fragmentation_carbon_stock_change_mg.csv'))
    pool.apply_async(analyze_forest_core_fragmentation, args=[args.copy()])
    
    #Set up args for the forest core scenario
    args['output_table_filename'] = (
        os.path.join(output_dir, 'forest_core_degredation_carbon_stock_change_mg.csv'))
    pool.apply_async(analyze_forest_core_expansion, args=[args.copy()])
    
    #Set up args for the savanna scenario
    args['output_table_filename'] = (
        os.path.join(output_dir, 'savanna_expansion_carbon_stock_change_mg.csv'))
    args['conversion_lucode'] = 9 #woody savannna    
    pool.apply_async(analyze_lu_expansion, args=[args.copy()])
    
    #Set up args for the forest edge erosion scenario
    args['output_table_filename'] = (
        os.path.join(output_dir, 'forest_edge_erosion_carbon_stock_change_mg.csv'))
    pool.apply_async(analyze_forest_edge_erosion, args=[args.copy()])
    
if __name__ == '__main__':
    start = time.clock()
    NUMBER_OF_STEPS = 200
    POOL = Pool(3)
    run_mg(NUMBER_OF_STEPS, POOL)
    run_mgds(NUMBER_OF_STEPS, POOL)
    POOL.close()
    POOL.join()
    elapsed = (time.clock() - start)
    print 'elsapsed time %ss' % elapsed
