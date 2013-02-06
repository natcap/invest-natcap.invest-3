"""InVEST Wind Energy model file handler module"""
import os.path
import logging
import csv
import json

from osgeo import ogr
from osgeo import osr

from invest_natcap.wind_energy import wind_energy_biophysical
from invest_natcap.wind_energy import wind_energy_core
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_valuation')

def execute(args):
    """Takes care of all file handling for the valuation part of the wind
        energy model
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved (required)
        args[aoi_uri] - a uri to an OGR datasource that is of type polygon and 
            projected in linear units of meters. The polygon specifies the 
            area of interest for the wind data points. The aoi should also 
            cover a portion of the land polygon that is of interest for
            calculating the near shore distances if the grid points input is not
            provided (required)
        args[turbine_parameters_uri] - a uri to a CSV file that holds the
            turbines biophysical parameters as well as valuation parameters 
            (required)
        args[global_wind_parameters_uri] - a uri to a CSV file that holds the
            global parameter values for both the biophysical and valuation
            module (required)        
        args[grid_points_uri] - a uri to a CSV file that specifies the landing
            and grid point locations (optional)
        args[land_polygon_uri] - a uri to an OGR datasource of type polygon to
            use for distance calculations if grid points were not provided 
            (required if grid_points_uri is not provided)
        args[foundation_cost] - a float representing how much the foundation
            will cost for the specific type of turbine (required)
        args[number_of_machines] - an integer value for the number of machines
            for the wind farm (required)
        args[dollar_per_kWh] - a float value for the amount of dollars per
            kilowatt hour (kWh) (required)
        args[discount_rate] - a float value for the discount rate (required for
            valuation)
        args[avg_grid_distance] - a float for the average distance in kilometers
            from a grid connection point to a land connection point 
            (required if grid connection points are not provided)
        args[suffix] - a String to append to the end of the output files
            (optional)
    
        returns - nothing"""

    LOGGER.info('Entering Wind Energy Valuation')

    valuation_args = {}
    
    # Create output folders
    workspace = str(args['workspace_dir'])
    valuation_args['workspace_dir'] = workspace

    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')

    for folder in [inter_dir, out_dir]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

    # handle suffix
    try:
        suffix = '_' + str(args['suffix'])
    except KeyError:
        suffix = ''

    valuation_args['suffix'] = suffix

    aoi = ogr.Open(str(args['aoi_uri']))
    
    biophysical_points_uri = os.path.join(
            out_dir, 'wind_energy_points' + suffix + '.shp')
    # Open the wind energy points from the biophsyical run to be updated and
    # edited
    biophysical_points = ogr.Open(biophysical_points_uri, 1)
    
    valuation_args['biophysical_data'] = biophysical_points
    
    # Number of machines
    valuation_args['number_of_machines'] = int(args['number_of_machines'])
    # Dollar per kiloWatt hour
    valuation_args['dollar_per_kWh'] = float(args['dollar_per_kWh'])

    # Create a list of the valuation parameters we are looking for from the
    # input files 
    valuation_turbine_params = ['turbine_cost', 'turbine_rated_pwr',
                                'turbines_per_circuit', 'rotor_diameter']
    valuation_global_params = [
            'carbon_coefficient', 'time_period', 'infield_cable_cost', 
            'infield_cable_length', 'installation_cost',
            'miscellaneous_capex_cost', 'operation_maintenance_cost',
            'decommission_cost', 'ac_dc_distance_break', 'mw_coef_ac',
            'mw_coef_dc', 'cable_coef_ac', 'cable_coef_dc',
            'rotor_diameter_factor']

    # Get the valuation turbine parameters from the CSV file
    LOGGER.info('Read in turbine information from CSV')
    val_turbine_param_file = open(args['turbine_parameters_uri'])
    val_turbine_reader = csv.reader(val_turbine_param_file)
    val_turbine_dict = {}

    # Get the valuation turbine parameters from the CSV file
    for field_value_row in val_turbine_reader:
        # Only get the valuation parameters and leave out the biophysical ones
        if field_value_row[0].lower() in valuation_turbine_params:
            val_turbine_dict[field_value_row[0].lower()] = field_value_row[1]
    
    # Get the global parameters for valuation from the CSV file
    global_val_param_file = open(args['global_wind_parameters_uri'])
    global_val_reader = csv.reader(global_val_param_file)
    for field_value_row in global_val_reader:
        # Only get the valuation parameters and leave out the biophysical ones
        if field_value_row[0].lower() in valuation_global_params:
            val_turbine_dict[field_value_row[0].lower()] = field_value_row[1]

    LOGGER.debug('Valuation Turbine Parameters: %s', val_turbine_dict)
    val_param_len = len(valuation_turbine_params) + len(valuation_global_params)
    if len(val_turbine_dict.keys()) != val_param_len:
        class FieldError(Exception):
            """A custom error message for fields that are missing"""
            pass
        raise FieldError('An Error occured from reading in a field value from '
                'either the turbine CSV file or the global parameters JSON '
                'file. Please make sure all the necessary fields are present '
                'and spelled correctly.')
    
    val_turbine_dict['foundation_cost'] = float(args['foundation_cost'])
    val_turbine_dict['avg_grid_distance'] = float(args['avg_grid_distance'])
    val_turbine_dict['discount_rate'] = float(args['discount_rate'])
    LOGGER.debug('Turbine Dictionary: %s', val_turbine_dict)
    valuation_args['turbine_dict'] = val_turbine_dict

    # Handle Grid Points
    try:
        grid_file = open(str(args['grid_points_uri']))
    except KeyError:
        LOGGER.info('Grid points not provided')
        LOGGER.info('Reading in land polygon')

        land_poly = ogr.Open(str(args['land_polygon_uri']))
        
        land_poly_clipped_uri = os.path.join(
                inter_dir, 'val_land_poly_clipped' + suffix + '.shp')
        land_poly_projected_uri = os.path.join(
                inter_dir, 'val_land_poly_projected' + suffix + '.shp')
        aoi_proj_to_land_poly_uri = os.path.join(
                inter_dir, 'val_aoi_proj_to_land_poly' + suffix + '.shp')
        
        land_poly_proj = clip_and_project_datasource(
                land_poly, aoi, land_poly_clipped_uri, land_poly_projected_uri,
                aoi_proj_to_land_poly_uri)

        valuation_args['land_polygon'] = land_poly_proj
    else:
        LOGGER.info('Reading in the grid points')
        reader = csv.DictReader(grid_file)

        grid_dict = {}
        land_dict = {}
        # Making a shallow copy of the attribute 'fieldnames' explicitly to
        # edit to all the fields to lowercase because it is more readable 
        # and easier than editing the attribute itself
        field_names = reader.fieldnames

        for index in range(len(field_names)):
            field_names[index] = field_names[index].lower()
        # Iterate through the CSV file and construct two different dictionaries
        # for grid and land points. 
        for row in reader:
            if row['type'].lower() == 'grid':
                grid_dict[row['id']] = row
            else:
                land_dict[row['id']] = row
        grid_file.close()
        LOGGER.debug('Grid_Points_Dict : %s', grid_dict)
        LOGGER.debug('Land_Points_Dict : %s', land_dict)

        grid_ds_uri = os.path.join(inter_dir, 'val_grid_points' + suffix + '.shp')
        land_ds_uri = os.path.join(inter_dir, 'val_land_points' + suffix + '.shp')
        
        # Create a point shapefile from the grid and land point dictionaries.
        # This makes it easier for future distance calculations and provides a
        # nice intermediate output for users
        grid_point_ds = dictionary_to_shapefile(
                grid_dict, 'grid_points', grid_ds_uri) 
        land_point_ds = dictionary_to_shapefile(
                land_dict, 'land_points', land_ds_uri) 
        # In case any of the above points lie outside the AOI, clip the
        # shapefiles and then project them to the AOI as well.
        # NOTE: There could be an error here where NO points lie within the AOI,
        # what then????????
        grid_clipped_uri = os.path.join(
                inter_dir, 'grid_point_clipped' + suffix + '.shp')
        grid_projected_uri = os.path.join(
                inter_dir, 'grid_point_projected' + suffix + '.shp')
        land_clipped_uri = os.path.join(
                inter_dir, 'land_point_clipped' + suffix + '.shp')
        land_projected_uri = os.path.join(
                inter_dir, 'land_point_projected' + suffix + '.shp')
        aoi_proj_to_grid_uri = os.path.join(
                inter_dir, 'aoi_proj_to_grid_points' + suffix + '.shp')
        aoi_proj_to_land_uri = os.path.join(
                inter_dir, 'aoi_proj_to_land_points' + suffix + '.shp')

        grid_point_prj = clip_and_project_datasource(
                grid_point_ds, aoi, grid_clipped_uri, grid_projected_uri,
                aoi_proj_to_grid_uri)
        land_point_prj = clip_and_project_datasource(
                land_point_ds, aoi, land_clipped_uri, land_projected_uri,
                aoi_proj_to_land_uri)

        valuation_args['grid_points'] = grid_point_prj
        valuation_args['land_points'] = land_point_prj
    # call on the core module
    wind_energy_core.valuation(valuation_args)

def clip_and_project_datasource(
        dsource, aoi, clipped_uri, projected_uri, aoi_proj_to_uri):
    """Clips and reprojects one OGR datasource to another
        
        dsource - an OGR datasource to clip and reproject
        aoi - an OGR datasource to use as the bounds for clipping and
            reprojecting
        clipped_uri - a string URI path for the clipped datasource
        projected_uri - a string URI path for the projected datasource
        aoi_proj_to_uri - a string URI path for projecting the aoi to the
            'dsource' in order to clip

        returns - dsource clipped and reprojected to aoi, an OGR datasource
        """
    LOGGER.info('Entering clip_and_project_datasource')

    dsource_sr = dsource.GetLayer().GetSpatialRef()
    dsource_wkt = dsource_sr.ExportToWkt()
    aoi_sr = aoi.GetLayer().GetSpatialRef()
    aoi_wkt = aoi_sr.ExportToWkt()
    
    aoi_proj_to_dsource = raster_utils.reproject_datasource(
            aoi, dsource_wkt, aoi_proj_to_uri)

    dsource_clipped = wind_energy_biophysical.clip_datasource(
            aoi_proj_to_dsource, dsource, clipped_uri)

    dsource_proj = raster_utils.reproject_datasource(
        dsource_clipped, aoi_wkt, projected_uri)

    LOGGER.info('Leaving clip_and_project_datasource')
    return dsource_proj

def dictionary_to_shapefile(dict_data, layer_name, output_uri):
    """Creates a point shapefile from a dictionary
        
        dict_data - a python dictionary with keys being unique id's that point
            sub-dictionary that has key-value pairs which will represent the
            field-value pair for the point features. At least two fields are
            required in the sub-dictionaries, 'lati' and 'long'. These fields
            determine the geometry of the point
            0 : {'lati':97, 'long':43, 'field_a':6.3, 'field_n':21},
            1 : {'lati':55, 'long':51, 'field_a':6.2, 'field_n':32},
            2 : {'lati':73, 'long':47, 'field_a':6.5, 'field_n':13}
        layer_name - a python string for the name of the layer
        output_uri - a uri for the output destination of the shapefile

        return - a OGR Datasource"""
    LOGGER.info('Entering dictionary_to_shapefile')
    
    # If the output_uri exists delete it
    if os.path.isfile(output_uri):
        os.remove(output_uri)
   
    LOGGER.info('Creating new datasource')
    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_datasource = output_driver.CreateDataSource(output_uri)

    # Set the spatial reference to WGS84 (lat/long)
    source_sr = osr.SpatialReference()
    source_sr.SetWellKnownGeogCS("WGS84")
    
    output_layer = output_datasource.CreateLayer(
            layer_name, source_sr, ogr.wkbPoint)

    # Construct a list of fields to add from the keys of the inner dictionary
    field_list = dict_data[dict_data.keys()[0]].keys()
    LOGGER.debug('field_list : %s', field_list)
    
    # Create a dictionary to store what variable types the fields are
    type_dict = {}
    for field in field_list:
        # Get a value from the field
        val = dict_data[dict_data.keys()[0]][field]
        
        if isinstance(val, str):
            type_dict[field] = 'str'
        else:
            type_dict[field] = 'number'

    LOGGER.info('Creating fields for the datasource')
    for field in field_list:
        field_type = None
        # Distinguish if the field type is of type String or other. If Other, we
        # are assuming it to be a float
        if type_dict[field] == 'str':
            field_type = ogr.OFTString
        else:
            field_type = ogr.OFTReal
        
        output_field = ogr.FieldDefn(field, field_type)   
        output_layer.CreateField(output_field)

    LOGGER.info('Entering iteration to create and set the features')
    # For each inner dictionary (for each point) create a point
    for point_dict in dict_data.itervalues():
        latitude = float(point_dict['lati'])
        longitude = float(point_dict['long'])

        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint_2D(longitude, latitude)

        output_feature = ogr.Feature(output_layer.GetLayerDefn())
        
        for field_name in point_dict:
            field_index = output_feature.GetFieldIndex(field_name)
            output_feature.SetField(field_index, point_dict[field_name])
        
        output_feature.SetGeometryDirectly(geom)
        output_layer.CreateFeature(output_feature)
        output_feature = None

    output_layer.SyncToDisk()
    LOGGER.info('Leaving wind_data_to_point_shape')
    return output_datasource

