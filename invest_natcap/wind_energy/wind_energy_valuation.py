"""InVEST Wind Energy model file handler module"""
import os.path
import logging
import csv

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

    aoi = ogr.Open(args['aoi_uri'])
    biophysical_points = ogr.Open(args['biophysical_data_uri'])
    
    biophysical_points_proj = clip_and_project_datasource(
            biophysical_points, aoi, os.path.join(inter_dir, 'val_bio_points'))
    
    valuation_args['biophysical_data'] = biophysical_points_proj
    
    # Number of machines
    valuation_args['number_of_machines'] = int(args['number_of_machines'])
    # Dollar per kiloWatt hour
    valuation_args['dollar_per_kWh'] = float(args['dollar_per_kWh'])

    LOGGER.info('Read in turbine information from CSV')
    # Open the turbine CSV file 
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
        grid_file = open(args['grid_points_uri'])
    except KeyError:
        LOGGER.info('Grid points not provided')
        LOGGER.info('Reading in land polygon')

        land_poly = ogr.Open(args['land_polygon_uri'])
        
        land_poly_proj = clip_and_project_datasource(
                land_poly, aoi, os.path.join(inter_dir, 'val_land_poly'))

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
                grid_point_ds, aoi, os.path.join(inter_dir, 'val_grid_point'))
        land_point_prj = clip_and_project_datasource(
                land_point_ds, aoi, os.path.join(inter_dir, 'val_land_point'))

        valuation_args['grid_points'] = grid_point_prj
        valuation_args['land_points'] = land_point_prj
    # call on the core module
    wind_energy_core.valuation(valuation_args)

def clip_and_project_datasource(shape_a, shape_b, out_uri):
    """Clips and reprojects one OGR datasource to another
        
        shape_a - an OGR datasource to clip and reproject
        shape_b - an OGR datasource to use as the bounds for clipping and
            reprojecting
        out_uri - a string for the full path of the output, including the
            directory tree. However, no extension should be provided

        returns - shape_a clipped and reprojected to shape_b, an OGR datasource
    """
    # Get the basename and directory name of the uri to help create future uri's
    basename = os.path.basename(out_uri)
    dir_name = os.path.dirname(out_uri)
    
    shape_a_sr = shape_a.GetLayer().GetSpatialRef()
    shape_a_wkt = shape_a_sr.ExportToWkt()
    shape_b_sr = shape_b.GetLayer().GetSpatialRef()
    shape_b_wkt = shape_b_sr.ExportToWkt()

    shape_b_proj_to_shape_a_uri = os.path.join(
            dir_name, basename + 'b_to_a.shp')
    
    shape_b_proj_to_shape_a = raster_utils.reproject_datasource(
            shape_b, shape_a_wkt, shape_b_proj_to_shape_a_uri)

    shape_a_clipped_uri = os.path.join(
            dir_name, basename + '_clipped.shp')
   
    shape_a_clipped = wind_energy_biophysical.clip_datasource(
            shape_b_proj_to_shape_a, shape_a, shape_a_clipped_uri)

    shape_a_proj_uri = os.path.join(
            dir_name, basename + '_projected.shp')

    shape_a_proj = raster_utils.reproject_datasource(
        shape_a_clipped, shape_b_wkt, shape_a_proj_uri)

    return shape_a_proj

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

