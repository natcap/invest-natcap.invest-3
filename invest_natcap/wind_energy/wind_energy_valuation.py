"""InVEST Wind Energy model file handler module"""
import os.path
import logging
import csv
import json

from osgeo import gdal
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
        args[aoi_uri] - a uri to an OGR datasource of type polygon covering the
            area of interest. Must be projected in meters (required)
        args[biophysical_data_uri] - a uri to an OGR datasource of type point
            from the output of the biophysical model run (required) 
        args[turbine_parameters_uri] - a uri to a CSV file that has the parameters
            for the type of turbine (required)
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
        args[suffix] - a string for the suffix to be appended to the output
            names (optional) 
    
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
    biophysical_points = ogr.Open(str(args['biophysical_data_uri']))
    
    biophysical_points_proj = clip_and_project_datasource(
            biophysical_points, aoi, os.path.join(inter_dir, 'bio_points'))
    
    valuation_args['biophysical_data'] = biophysical_points_proj
    
    # Number of machines
    valuation_args['number_of_machines'] = int(args['number_of_machines'])
    # Dollar per kiloWatt hour
    valuation_args['dollar_per_kWh'] = float(args['dollar_per_kWh'])

    LOGGER.info('Read in turbine information from CSV')
    # Open the turbine CSV file 
    
    valuation_turbine_params = ['turbine_cost', 'turbine_rated_pwr']
    valuation_global_params = [
            'discount_rate', 'time_period', 'infield_cable_cost', 
            'infield_cable_length', 'installation_cost',
            'miscellaneous_capex_cost', 'operation_maintenance_cost',
            'decommission_cost']
    
    val_turbine_param_file = open(args['turbine_parameters_uri'])
    val_turbine_reader = csv.reader(val_turbine_param_file)
    val_turbine_dict = {}

    for field_value_row in val_turbine_reader:
        if field_value_row[0].lower() in valuation_turbine_params:
            val_turbine_dict[field_value_row[0].lower()] = field_value_row[1]
    
    val_global_params_file = open(
            os.path.join(workspace, 'input/global_wind_energy_attributes.json'))

    val_global_params_dict = json.load(val_global_params_file)
    for key, val in val_global_params_dict.iteritems():
        if key.lower() in valuation_global_params:
            val_turbine_dict[key.lower()] = val

    LOGGER.debug('Valuation Turbine Parameters: %s', val_turbine_dict)
    val_param_len = len(valuation_turbine_params) + len(valuation_global_params)
    if len(val_turbine_dict.keys()) != val_param_len:
        class FieldError(Exception):
            pass
        raise FieldError('An Error occured from reading in a field value from '
                'either the turbine CSV file or the global parameters JSON '
                'file. Please make sure all the necessary fields are present '
                'and spelled correctly.')
    
    val_turbine_dict['foundation_cost'] = float(args['foundation_cost'])
    LOGGER.debug('Turbine Dictionary: %s', val_turbine_dict)
    valuation_args['turbine_dict'] = val_turbine_dict

    # Handle Grid Points
    try:
        grid_file = open(str(args['grid_points_uri']))
    except KeyError:
        LOGGER.info('Grid points not provided')
        LOGGER.info('Reading in land polygon')

        land_poly = ogr.Open(str(args['land_polygon_uri']))
        
        land_poly_proj = clip_and_project_datasource(
                land_poly, aoi, os.path.join(inter_dir, 'land_poly'))

        valuation_args['land_polygon'] = land_poly_proj
    else:
        LOGGER.info('Reading in the grid points')
        reader = csv.DictReader(grid_file)

        grid_dict = {}
        land_dict = {}
        # Making a shallow copy of the attribute 'fieldnames' explicitly to edit to
        # all the fields to lowercase because it is more readable and easier than
        # editing the attribute itself
        field_names = reader.fieldnames

        for index in range(len(field_names)):
            field_names[index] = field_names[index].lower()

        for row in reader:
            if row['type'].lower() == 'grid':
                grid_dict[row['id']] = row
            else:
                land_dict[row['id']] = row
        grid_file.close()
        LOGGER.debug('Grid_Points_Dict : %s', grid_dict)
        LOGGER.debug('Land_Points_Dict : %s', land_dict)

        grid_ds_uri = os.path.join(inter_dir, 'val_grid_points.shp')
        land_ds_uri = os.path.join(inter_dir, 'val_land_points.shp')

        grid_point_ds = dictionary_to_shapefile(
                grid_dict, 'grid_points', grid_ds_uri) 
        land_point_ds = dictionary_to_shapefile(
                land_dict, 'land_points', land_ds_uri) 

        grid_point_prj = clip_and_project_datasource(
                grid_point_ds, aoi, os.path.join(inter_dir, 'grid_point'))
        land_point_prj = clip_and_project_datasource(
                land_point_ds, aoi, os.path.join(inter_dir, 'land_point'))

        valuation_args['grid_points'] = grid_point_prj
        valuation_args['land_points'] = land_point_prj
    # call on the core module
    wind_energy_core.valuation(valuation_args)

def clip_and_project_datasource(dsource, aoi, out_uri):
    """Clips and reprojects one OGR datasource to another
        
        dsource - an OGR datasource to clip and reproject
        aoi - an OGR datasource to use as the bounds for clipping and
            reprojecting
        out_uri - a string for the full path of the output, including the
            directory tree. However, no extension should be provided

        returns - dsource clipped and reprojected to aoi, an OGR datasource
    """
    # Get the basename and directory name of the uri to help create future uri's
    basename = os.path.basename(out_uri)
    dir_name = os.path.dirname(out_uri)
    
    dsource_sr = dsource.GetLayer().GetSpatialRef()
    dsource_wkt = dsource_sr.ExportToWkt()
    aoi_sr = aoi.GetLayer().GetSpatialRef()
    aoi_wkt = aoi_sr.ExportToWkt()

    aoi_proj_to_dsource_uri = os.path.join(
            dir_name, 'val_aoi_proj_to_' + basename + '.shp')
    
    aoi_proj_to_dsource = raster_utils.reproject_datasource(
            aoi, dsource_wkt, aoi_proj_to_dsource_uri)

    dsource_clipped_uri = os.path.join(
            dir_name, 'val_' + basename + '_clipped.shp')
   
    dsource_clipped = wind_energy_biophysical.clip_datasource(
            aoi_proj_to_dsource, dsource, dsource_clipped_uri)

    dsource_proj_uri = os.path.join(
            dir_name, 'val_' + basename + '_projected.shp')

    dsource_proj = raster_utils.reproject_datasource(
        dsource_clipped, aoi_wkt, dsource_proj_uri)

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

    LOGGER.info('Creating fields for the datasource')
    for field in field_list:
        output_field = ogr.FieldDefn(field, ogr.OFTReal)   
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

