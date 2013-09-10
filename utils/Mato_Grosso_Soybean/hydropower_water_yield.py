import os

import gdal
import numpy

import invest_natcap.hydropower.hydropower_water_yield
from invest_natcap import raster_utils
import carbon_expansion_scenarios

#Premade scenario
def premade_water_yield_scenario(args):
    base_landcover_table_uri = os.path.join(args['workspace_dir'], 'premade_landcover_scenario.csv')
    print base_landcover_table_uri
    base_landcover_table = open(args['output_table_filename'], 'wb')
    base_landcover_table.write('percent expansion,water yield volume\n')

    for percent in xrange(400):
        print 'premade scenarios percent step %s' % percent
        scenario_path = './MG_Soy_Exp_07122013/'
        scenario_file_pattern = 'mg_lulc%n'
        args['lulc_uri'] = os.path.join(
            scenario_path,
            scenario_file_pattern.replace('%n', str(percent)))

        invest_natcap.hydropower.hydropower_water_yield.execute(args)
        water_yield_shapefile_uri = os.path.join(
            args['workspace_dir'], 'output', 'wyield_sheds.shp')
        ws_table = raster_utils.extract_datasource_table_by_key(
            water_yield_shapefile_uri, 'ws_id')
        base_landcover_table.write('%s,%.2f\n' % (percent, ws_table[1]['wyield_vol']))


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

    print 'starting lucode expansion scenario'
    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()
    
    converted_lulc_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base(
        scenario_lulc_dataset, converted_lulc_uri, 'GTiff', -1, gdal.GDT_Int16)

    #Write converted scenario array to dataset
    converted_lulc_dataset = gdal.Open(converted_lulc_uri, gdal.GA_Update)
    converted_lulc_band = converted_lulc_dataset.GetRasterBand(1)
    converted_lulc_band.WriteArray(scenario_lulc_array)
    converted_lulc_band = None
    converted_lulc_dataset = None
    args['lulc_uri'] = converted_lulc_uri
    
    
    total_converting_pixels = numpy.count_nonzero(
        scenario_lulc_array == args['conversion_lucode'])

    print 'total converting pixels %s' % total_converting_pixels

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion,Water Yield\n')

    pixels_converted = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating water yield for expansion step %s' % percent
        
        invest_natcap.hydropower.hydropower_water_yield.execute(args)
        water_yield_shapefile_uri = os.path.join(
            args['workspace_dir'], 'output', 'wyield_sheds.shp')
        ws_table = raster_utils.extract_datasource_table_by_key(
            water_yield_shapefile_uri, 'ws_id')
        output_table.write('%s,%.2f\n' % (percent, ws_table[1]['wyield_vol']))
       
        #Convert lulc for the next iteration
        #This section converts grassland
        landcover_mask = numpy.where(
            scenario_lulc_array.flat == args['conversion_lucode'])
        scenario_lulc_array.flat[landcover_mask[0][
            0:args['pixels_to_convert_per_step']]] = args['converting_crop']
        converted_lulc_dataset = gdal.Open(converted_lulc_uri, gdal.GA_Update)
        converted_lulc_band = converted_lulc_dataset.GetRasterBand(1)
        converted_lulc_band.WriteArray(scenario_lulc_array)
        converted_lulc_band = None
        converted_lulc_dataset = None
        
        
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

    print 'starting forest core fragmentation scenario'
    
    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()

    #Write converted scenario array to dataset
    converted_lulc_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base(
        scenario_lulc_dataset, converted_lulc_uri, 'GTiff', -1, gdal.GDT_Int16)
    converted_lulc_dataset = gdal.Open(converted_lulc_uri, gdal.GA_Update)
    converted_lulc_band = converted_lulc_dataset.GetRasterBand(1)
    converted_lulc_band.WriteArray(scenario_lulc_array)
    converted_lulc_band = None
    converted_lulc_dataset = None
    args['lulc_uri'] = converted_lulc_uri
    
    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion,Total Water Yield Volume\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating water yield for forest fragmentation step %s' % percent

        invest_natcap.hydropower.hydropower_water_yield.execute(args)
        water_yield_shapefile_uri = os.path.join(
            args['workspace_dir'], 'output', 'wyield_sheds.shp')
        ws_table = raster_utils.extract_datasource_table_by_key(
            water_yield_shapefile_uri, 'ws_id')
        output_table.write('%s,%.2f\n' % (percent, ws_table[1]['wyield_vol']))
        output_table.flush()

        deepest_edge_index += args['pixels_to_convert_per_step']
        scenario_edge_distance = carbon_expansion_scenarios.calculate_forest_edge_distance(
            scenario_lulc_array, args['forest_lucodes'], cell_size)

        #We want to visit the edge pixels in decreasing distance order starting
        #from the core pixel in.
        decreasing_distances = numpy.argsort(scenario_edge_distance.flat)[::-1]
        scenario_lulc_array.flat[
            decreasing_distances[0:deepest_edge_index]] = (
                args['converting_crop'])
        #Write converted scenario array to dataset
        converted_lulc_dataset = gdal.Open(converted_lulc_uri, gdal.GA_Update)
        converted_lulc_band = converted_lulc_dataset.GetRasterBand(1)
        converted_lulc_band.WriteArray(scenario_lulc_array)
        converted_lulc_band = None
        converted_lulc_dataset = None
        
                
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

    print 'starting forest core expansion scenario'

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()

    scenario_edge_distance = carbon_expansion_scenarios.calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #We want to visit the edge pixels in decreasing distance order starting
    #from the core pixel in.
    decreasing_distances = numpy.argsort(scenario_edge_distance.flat)[::-1]

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion,Total Water Yield\n')

    #Write converted scenario array to dataset
    converted_lulc_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base(
        scenario_lulc_dataset, converted_lulc_uri, 'GTiff', -1, gdal.GDT_Int16)
    converted_lulc_dataset = gdal.Open(converted_lulc_uri, gdal.GA_Update)
    converted_lulc_band = converted_lulc_dataset.GetRasterBand(1)
    converted_lulc_band.WriteArray(scenario_lulc_array)
    converted_lulc_band = None
    converted_lulc_dataset = None
    args['lulc_uri'] = converted_lulc_uri

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating carbon stocks for expansion step %s' % percent

        #Dump the current percent iteration's carbon stocks to the csv file
        invest_natcap.hydropower.hydropower_water_yield.execute(args)
        water_yield_shapefile_uri = os.path.join(
            args['workspace_dir'], 'output', 'wyield_sheds.shp')
        ws_table = raster_utils.extract_datasource_table_by_key(
            water_yield_shapefile_uri, 'ws_id')
        output_table.write('%s,%.2f\n' % (percent, ws_table[1]['wyield_vol']))
        output_table.flush()

        deepest_edge_index += args['pixels_to_convert_per_step']
        scenario_lulc_array.flat[
            decreasing_distances[0:deepest_edge_index]] = (
                args['converting_crop'])

        #Write converted scenario array to dataset
        converted_lulc_dataset = gdal.Open(converted_lulc_uri, gdal.GA_Update)
        converted_lulc_band = converted_lulc_dataset.GetRasterBand(1)
        converted_lulc_band.WriteArray(scenario_lulc_array)
        converted_lulc_band = None
        converted_lulc_dataset = None

        
def analyze_forest_edge_expansion(args):
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

    print 'starting forest edge expansion scenario'

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['scenario_lulc_base_map_filename'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = scenario_lulc_dataset.GetRasterBand(1).ReadAsArray()

    scenario_edge_distance = carbon_expansion_scenarios.calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #We want to visit the edge pixels in increasing distance order starting
    #from the fist pixel in.  Set the pixels outside to at a distance of
    #infinity so that we visit the inner edge forest pixels first
    scenario_edge_distance[scenario_edge_distance == 0] = numpy.inf
    increasing_distances = numpy.argsort(scenario_edge_distance.flat)

    #Write converted scenario array to dataset
    converted_lulc_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base(
        scenario_lulc_dataset, converted_lulc_uri, 'GTiff', -1, gdal.GDT_Int16)
    converted_lulc_dataset = gdal.Open(converted_lulc_uri, gdal.GA_Update)
    converted_lulc_band = converted_lulc_dataset.GetRasterBand(1)
    converted_lulc_band.WriteArray(scenario_lulc_array)
    converted_lulc_band = None
    converted_lulc_dataset = None
    args['lulc_uri'] = converted_lulc_uri

    
    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion,Total Water Yield\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating water yield for forest edge expansion %s' % percent
        invest_natcap.hydropower.hydropower_water_yield.execute(args)
        water_yield_shapefile_uri = os.path.join(
            args['workspace_dir'], 'output', 'wyield_sheds.shp')
        ws_table = raster_utils.extract_datasource_table_by_key(
            water_yield_shapefile_uri, 'ws_id')
        output_table.write('%s,%.2f\n' % (percent, ws_table[1]['wyield_vol']))
        output_table.flush()


        deepest_edge_index += args['pixels_to_convert_per_step']
        scenario_lulc_array.flat[
            increasing_distances[0:deepest_edge_index]] = (
                args['converting_crop'])
        #Write converted scenario array to dataset
        converted_lulc_dataset = gdal.Open(converted_lulc_uri, gdal.GA_Update)
        converted_lulc_band = converted_lulc_dataset.GetRasterBand(1)
        converted_lulc_band.WriteArray(scenario_lulc_array)
        converted_lulc_band = None
        converted_lulc_dataset = None
                
                
if __name__ == '__main__':
    ARGS = {
        u'biophysical_table_uri': u'Water_Yield/Parameters.csv',
        u'depth_to_root_rest_layer_uri': u'Water_Yield/mg_sdepth_proj.tif',
        u'eto_uri': u'Water_Yield/mg_pet',
        u'lulc_uri': u'Water_Yield/mg_lulc0',
        u'pawc_uri': u'Water_Yield/mg_pawc_proj.tif',
        u'precipitation_uri': u'Water_Yield/mg_precipe',
        u'results_suffix': u'',
        u'seasonality_constant': u'5',
        u'sub_watersheds_uri': u'',
        u'water_scarcity_container': False,
        u'watersheds_uri': u'Water_Yield/mg_boundary.shp',
        u'workspace_dir': u'Water_Yield/workspace',
    }

    #Set up args for the savanna scenario
    ARGS['scenario_lulc_base_map_filename'] = 'Water_Yield/mg_lulc0'
    ARGS['pixels_to_convert_per_step'] = 2608
    ARGS['conversion_lucode'] = 9
    ARGS['converting_crop'] = 120,
    ARGS['output_table_filename'] = os.path.join(
        ARGS['workspace_dir'], 'savanna_expansion_water_yield_change.csv')
    ARGS['scenario_conversion_steps'] = 1
    analyze_lu_expansion(ARGS)

    ARGS['output_table_filename'] = os.path.join(
        ARGS['workspace_dir'], 'premade_landcover_water_yield_change.csv')
    premade_water_yield_scenario(ARGS)
    
    ARGS['forest_lucodes'] = [1, 2, 3, 4, 5]
    ARGS['output_table_filename'] = os.path.join(
        ARGS['workspace_dir'], 'forest_core_fragmentation_water_yield_change.csv')
    analyze_forest_core_fragmentation(ARGS)
    
    ARGS['output_table_filename'] = (
        'forest_core_expansion_water_yield_change.csv')
    analyze_forest_core_expansion(ARGS)

    ARGS['output_table_filename'] = (
        'forest_edge_expansion_water_yield_change.csv')
    analyze_forest_edge_expansion(ARGS)
