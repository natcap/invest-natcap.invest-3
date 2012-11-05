"""InVEST Wind Energy model file handler module"""
import os.path
import logging
import csv

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap.wind_energy import wind_energy_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_valuation')

def execute(args):
    """Takes care of all file handling for the valuation part of the wind
        energy model
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved (required)
        args[aoi_uri] - a uri to an OGR datasource of type polygon covering the
            area of interest. Must be projected in meters (required)
        args[biophysical_data_uri] - a uri to an OGR datasource of type point
            from the output of the biophysical model run (required) 
        args[turbine_info_uri] - a uri to a CSV file that has the parameters
            for the type of turbine (required)
        args[grid_points_uri] - a uri to a CSV file that specifies the landing
            and grid point locations (optional)
        args[land_polygon_uri] - a uri to an OGR datasource of type polygon to
            use for distance calculations if grid points were not provided 
            (required if grid_points_uri is not provided)
        args[number_of_machines] - an integer value for the number of machines
            for the wind farm (required)
        args[dollar_per_kWh] - a float value for the amount of dollars per
            kilowatt hour (kWh) (required)
        args[suffix] - a string for the suffix to be appended to the output
            names (optional) 
    
        returns - nothing"""

    LOGGER.info('Entering Wind Energy Valuation')

    valuation_args = {}
    
    # Create output folders
    workspace = args['workspace_dir']
    valuation_args['workspace_dir'] = workspace

    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')

    for folder in [inter_dir, out_dir]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

    # handle suffix
    try:
        suffix = '_' + args['suffix']
    except KeyError:
        suffix = ''

    valuation_args['suffix'] = suffix

    # Number of machines
    valuation_args['number_of_machines'] = int(args['number_of_machines'])
    # Dollar per kiloWatt hour
    valuation_args['dollar_per_kWh'] = float(args['dollar_per_kWh'])

    LOGGER.info('Read in turbine information from CSV')
    # handle opening of relevant files
    turbine_dict = {}
    turbine_file = open(args['turbine_info_uri'])
    reader = csv.DictReader(turbine_file)

    # Making a shallow copy of the attribute 'fieldnames' explicitly to edit to
    # all the fields to lowercase because it is more readable and easier than
    # editing the attribute itself
    field_names = reader.fieldnames

    for index in range(len(field_names)):
        field_names[index] = field_names[index].lower()

    for row in reader:
        turbine_dict[row['type']] = row
    reader = None
    turbine_file.close()
    LOGGER.debug('Turbine Dictionary: %s', turbine_dict)
    valuation_args['turbine_dict'] = turbine_dict

    # Handle Grid Points
    try:
        grid_dict = {}
        grid_file = open(args['grid_points_uri'])
        LOGGER.info('Reading in the grid points')
        reader = csv.DictReader(grid_file)

        # Making a shallow copy of the attribute 'fieldnames' explicitly to edit to
        # all the fields to lowercase because it is more readable and easier than
        # editing the attribute itself
        field_names = reader.fieldnames

        for index in range(len(field_names)):
            field_names[index] = field_names[index].lower()

        for row in reader:
            grid_dict[row['id']] = row
        grid_file.close()
        LOGGER.debug('Grid_Points_Dict : %s', grid_dict)
        valuation_args['grid_dict'] = grid_dict
    except KeyError:
        LOGGER.info('Grid points not provided')
        LOGGER.info('Reading in land polygon')
        try:
            land_poly = ogr.Open(args['land_polygon_uri'])
        except KeyError:
            raise KeyError('Something has gone horribly wrong')

    # handle any pre-processing that must be done

    LOGGER.info('Clipping and handling wind energy points')
    biophysical_points = ogr.Open(args['biophysical_data_uri'])
    driver = ogr.GetDriverByName('ESRI Shapefile')
    points_copy_uri = os.path.join(inter_dir, 'copy_biophysical_points.shp')
    
    if os.path.isfile(points_copy_uri):
        os.remove(points_copy_uri)
    
    biophysical_points_copy = driver.CopyDataSource(
            biophysical_points, str(points_copy_uri))
    LOGGER.debug('biophysical_points_copy : %s', biophysical_points_copy)
    valuation_args['biophysical_data'] = biophysical_points_copy
    
    valuation_args['harvested_energy'] = gdal.Open(args['harvested_energy_uri'])
    valuation_args['distance'] = gdal.Open(args['distance_uri'])
    
    # call on the core module
    wind_energy_core.valuation(valuation_args)
