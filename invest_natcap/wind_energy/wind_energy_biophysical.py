"""InVEST Wind Energy Biophysical model file handler"""
import logging
import os
import csv
import json
import struct

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap.wind_energy import wind_energy_core
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_biophysical')

# A custom error message for a hub height that is not supported in
# the current wind data
class HubHeightError(Exception): pass

def execute(args):
    """Takes care of all file handling for the biophysical part of the wind
        energy model
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved (required)
        args[wind_data_uri] - a uri to a binary file that has been packed with 
            4 byte floats using big indian '<'. Each row is a location with at
            least the Longitude, Latitude, Scale and Shape parameters (required)
        args[aoi_uri] - a uri to an OGR datasource that is of type polygon and 
            projected in linear units of meters. The polygon specifies the 
            area of interest for the wind data points. If limiting the wind 
            farm bins by distance, then the aoi should also cover a portion 
            of the land polygon that is of interest (optional)
        args[bathymetry_uri] - a uri to a GDAL dataset that has the depth
            values of the area of interest (required)
        args[global_wind_parameters_uri] - a uri to a CSV file that holds the
            global parameter values for both the biophysical and valuation
            module (required)        
        args[bottom_type_uri] - a uri to an OGR datasource of type polygon
            that depicts the subsurface geology type (optional)
        args[turbine_parameters_uri] - a uri to a CSV file that holds the
            turbines biophysical parameters as well as valuation parameters 
            (required)
        args[min_depth] - a float value for the minimum depth for offshore wind
            farm installation (meters) (required)
        args[max_depth] - a float value for the maximum depth for offshore wind
            farm installation (meters) (required)
        args[suffix] - a String to append to the end of the output files
            (optional)
        args[land_polygon_uri] - a uri to an OGR datasource of type polygon that
            provides a coastline for determining distances from wind farm bins.
            AOI must be selected for this input to be active (optional)
        args[min_distance] - a float value for the minimum distance from shore
            for offshore wind farm installation (meters) The land polygon must 
            be selected for this input to be active (optional, required for 
            valuation)
        args[max_distance] - a float value for the maximum distance from shore
            for offshore wind farm installation (meters) The land polygon must
            be selected for this input to be active (optional, required for 
            valuation)

        returns - nothing"""
    
    LOGGER.info('Beginning Wind Energy Biophysical')

    workspace = str(args['workspace_dir'])
    
    # Create dictionary to hold values that will be passed to the core
    # functionality
    biophysical_args = {}
            
    # If the user has not provided a results suffix, assume it to be an empty
    # string.
    try:
        suffix = '_' + str(args['suffix'])
    except KeyError:
        suffix = ''

    # Check to see if each of the workspace folders exists. If not, create the
    # folder in the filesystem.
    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')

    LOGGER.info('Creating workspace directories')
    
    for folder in [inter_dir, out_dir]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

    # Create a list of the biophysical parameters we are looking for from the
    # input files
    biophysical_params = ['cut_in_wspd', 'cut_out_wspd', 'rated_wspd',
                          'hub_height', 'turbine_rated_pwr', 'air_density',
                          'exponent_power_curve', 'air_density_coefficient']
    # Get the biophysical turbine parameters from the CSV file
    bio_turbine_param_file = open(args['turbine_parameters_uri'])
    bio_turbine_reader = csv.reader(bio_turbine_param_file)
    bio_turbine_dict = {}
    for field_value_row in bio_turbine_reader:
        # Only get the biophysical parameters and leave out the valuation ones
        if field_value_row[0].lower() in biophysical_params:
            bio_turbine_dict[field_value_row[0].lower()] = field_value_row[1]

    # Get the global parameters for biophysical from the CSV file
    global_bio_param_file = open(args['global_wind_parameters_uri'])
    global_bio_reader = csv.reader(global_bio_param_file)
    for field_value_row in global_bio_reader:
        # Only get the biophysical parameters and leave out the valuation ones
        if field_value_row[0].lower() in biophysical_params:
            bio_turbine_dict[field_value_row[0].lower()] = field_value_row[1]

    LOGGER.debug('Biophysical Turbine Parameters: %s', bio_turbine_dict)
    
    # Check that all the necessary input fields from the CSV files have been
    # collected by comparing the number of dictionary keys to the number of
    # elements in our known list
    if len(bio_turbine_dict.keys()) != len(biophysical_params):
        class FieldError(Exception):
            """A custom error message for fields that are missing"""
            pass
        raise FieldError('An Error occured from reading in a field value from '
        'either the turbine CSV file or the global parameters JSON file. ' 
        'Please make sure all the necessary fields are present and spelled '
        'correctly.')
    
    biophysical_args['biophysical_turbine_dict'] = bio_turbine_dict
    
    # Using the hub height to generate the proper field name for the scale 
    # value that is found in the wind data file
    hub_height = int(bio_turbine_dict['hub_height'])

    if hub_height % 10 != 0:
        class HubHeightError(Exception):
            """A custom error message for invalid hub heights"""
            pass
        raise HubHeightError('An Error occurred processing the Hub Height. '
                'Please make sure the Hub Height is between the ranges of 10 '
                'and 150 meters and is a multiple of 10. ex: 10,20,...70,80...')

    scale_key = str(hub_height)
    if len(scale_key) <= 2:
        scale_key = 'Ram-0' + scale_key + 'm'
    else:
        scale_key = 'Ram-' + scale_key + 'm'
   
    # Define a list of the fields that of interest in the wind data file
    wind_data_field_list = ['LATI', 'LONG', scale_key, 'K-010m']

    # Read the wind energy data into a dictionary
    LOGGER.info('Read wind data from text file')
    wind_data = read_binary_wind_data(str(args['wind_data_uri']), wind_data_field_list)
   
    # Open the bathymetry DEM to projected and clipped depending on the below
    # conditions
    bathymetry = gdal.Open(str(args['bathymetry_uri']))

    try:
        LOGGER.info('Trying to open the AOI')
        aoi = ogr.Open(str(args['aoi_uri']))
    except KeyError:
        LOGGER.debug("AOI argument was not selected")
        
        # Since no AOI was provided the wind energy points shapefile that is
        # created directly from dictionary will be the final output, so set the
        # uri to point to the output folder
        wind_point_shape_uri = os.path.join(
                out_dir, 'wind_energy_points' + suffix + '.shp')
        
        LOGGER.info('Create point shapefile from wind data')
        
        wind_data_points = wind_data_to_point_shape(
            wind_data, 'wind_data', wind_point_shape_uri)
        
        biophysical_args['bathymetry'] = bathymetry
        biophysical_args['wind_data_points'] = wind_data_points
    else:
        # Since an AOI was provided the wind energy points shapefile will need
        # to be clipped and projected. Thus save the construction of the
        # shapefile from dictionary in the intermediate directory
        wind_point_shape_uri = os.path.join(
                inter_dir, 'wind_energy_points_from_dat' + suffix + '.shp')
        
        LOGGER.info('Create point shapefile from wind data')
        
        wind_data_points = wind_data_to_point_shape(
            wind_data, 'wind_data', wind_point_shape_uri)
        
        # Define the uri's for clipping and projecting the wind energy data
        # points
        wind_points_clip_uri = os.path.join(
                inter_dir, 'wind_points_clipped' + suffix + '.shp')
        wind_points_proj_uri = os.path.join(
                out_dir, 'wind_energy_points' + suffix + '.shp')
        aoi_reprojected_wind_uri = os.path.join(
                inter_dir, 'aoi_proj_to_wind_points' + suffix + '.shp')
        # Clip and project the wind energy points datasource
        LOGGER.info('Clip and project wind points to AOI')
        wind_pts_prj = clip_and_reproject_maps(
                wind_data_points, aoi, wind_points_clip_uri,
                wind_points_proj_uri, aoi_reprojected_wind_uri) 
    
        # Define the uri's for clipping and projecting the bathymetry
        bathymetry_clip_uri = os.path.join(
                inter_dir, 'bathymetry_clipped' + suffix + '.tif')
        bathymetry_proj_uri = os.path.join(
                inter_dir, 'bathymetry_projected' + suffix + '.tif')
        aoi_reprojected_bath_uri = os.path.join(
                inter_dir, 'aoi_proj_to_bath' + suffix + '.shp')
        # Clip and project the bathymetry dataset
        LOGGER.info('Clip and project bathymetry to AOI')
        clip_and_proj_bath = clip_and_reproject_maps(
                bathymetry, aoi, bathymetry_clip_uri, bathymetry_proj_uri,
                aoi_reprojected_bath_uri)

        biophysical_args['bathymetry'] = clip_and_proj_bath
        biophysical_args['wind_data_points'] = wind_pts_prj
        biophysical_args['aoi'] = aoi 
        
        # Try to handle the distance inputs and land datasource if they 
        # are present
        try:
            biophysical_args['min_distance'] = float(args['min_distance'])
            biophysical_args['max_distance'] = float(args['max_distance'])
            land_polygon = ogr.Open(str(args['land_polygon_uri']))
        except KeyError:
            LOGGER.info('Distance information not provided')
        else: 
            LOGGER.info('Handling distance parameters')

            # Define the uri's for clipping and reprojecting the land polygon
            # datasource
            land_poly_clip_uri = os.path.join(
                    inter_dir, 'land_poly_clipped' + suffix + '.shp')
            land_poly_proj_uri = os.path.join(
                    inter_dir, 'land_poly_projected' + suffix + '.shp')
            aoi_reprojected_land_uri = os.path.join(
                    inter_dir, 'aoi_proj_to_land' + suffix + '.shp')
            # Clip and project the land polygon datasource 
            LOGGER.info('Clip and project land poly to AOI')
            projected_land = clip_and_reproject_maps(
                    land_polygon, aoi, land_poly_clip_uri, land_poly_proj_uri,
                    aoi_reprojected_land_uri)

            biophysical_args['land_polygon'] = projected_land
    
    # Add biophysical inputs to the dictionary
    biophysical_args['workspace_dir'] = workspace
    biophysical_args['hub_height'] = hub_height
    biophysical_args['scale_key'] = scale_key
    
    # Pass in the depth values as negative, since it should be a negative
    # elevation
    biophysical_args['min_depth'] = abs(float(args['min_depth'])) * -1.0
    biophysical_args['max_depth'] = abs(float(args['max_depth'])) * -1.0
    biophysical_args['suffix'] = suffix
   
    # Call on the core module
    wind_energy_core.biophysical(biophysical_args)

    LOGGER.info('Leaving Wind_Energy_Biophysical')

def read_binary_wind_data(wind_data_uri, field_list):
    """Unpack the binary wind data into a dictionary. This function only reads
        binary files that are packed using big indian ordering '<'. Each piece
        of data is 4 bytes long and of type float. Each row of the file has data
        that corresponds to the following fields:

            "LONG","LATI","Ram-010m","Ram-020m","Ram-030m","Ram-040m",
            "Ram-050m","Ram-060m","Ram-070m","Ram-080m","Ram-090m","Ram-100m",
            "Ram-110m","Ram-120m","Ram-130m","Ram-140m","Ram-150m","K-010m"
        
        wind_data_uri - a uri for the binary wind data file
        field_list - a list of strings referring to the column headers from
            the text file that are to be included in the dictionary.
            ['LONG', 'LATI', scale_key, 'K-010m']

        returns - a dictionary where the keys are lat/long tuples which point
            to dictionaries that hold wind data at that location"""

    LOGGER.debug('Entering read_wind_data')
   
    wind_dict = {}

    # This is the expected column header list for the binary wind energy file.
    # It is expected that the data will be in this order so that we can properly
    # unpack the information into a dictionary
    param_list = [
            "LONG","LATI","Ram-010m","Ram-020m","Ram-030m","Ram-040m",
            "Ram-050m","Ram-060m","Ram-070m","Ram-080m","Ram-090m","Ram-100m",
            "Ram-110m","Ram-120m","Ram-130m","Ram-140m","Ram-150m","K-010m"]
   
    # Get the scale key from the field list to verify that the hub height given
    # is indeed a valid height handled in the wind energy point data
    scale_key = field_list[2]
    
    if scale_key not in param_list:
        raise HubHeightError('The Hub Height is not supported by the current '
                'wind point data. Please make sure the hub height lies '
                'between 10 and 150 meters')

    # Open the file in reading and binary mode
    wind_file = open(wind_data_uri, 'rb')
    
    # Get the length of the expected parameter list to use in unpacking
    param_list_length = len(param_list)

    # For every line in the file, unpack
    while True:
        # Read in line by line where each piece of data is 4 bytes
        line = wind_file.read(4*param_list_length)
        
        # If we have reached the end of the file, quit
        if len(line) == 0:
            break
        
        # Unpack the data. We are assuming the binary data was packed using the
        # big indian ordering '<' and that the values are floats.
        values_list = struct.unpack('<'+'f'*param_list_length, line)

        # The key of the output dictionary will be a tuple of the latitude,
        # longitude
        key = (values_list[1], values_list[0])
        wind_dict[key] = {}

        for index in range(param_list_length):
            # Only add the field and values we are interested in using
            if param_list[index] in field_list:
                # Build up the dictionary with values
                wind_dict[key][param_list[index]] = values_list[index]

    wind_file.close()

    LOGGER.debug('Leaving read_wind_data')
    return wind_dict

def wind_data_to_point_shape(dict_data, layer_name, output_uri):
    """Given a dictionary of the wind data create a point shapefile that
        represents this data
        
        dict_data - a python dictionary with the wind data, where the keys are
            tuples of the lat/long coordinates:
            {
            (97, 43) : {'LATI':97, 'LONG':43, 'Ram-030m':6.3, 'K-010m':2.7},
            (55, 51) : {'LATI':55, 'LONG':51, 'Ram-030m':6.2, 'K-010m':2.4},
            (73, 47) : {'LATI':73, 'LONG':47, 'Ram-030m':6.5, 'K-010m':2.3}
            }
        layer_name - a python string for the name of the layer
        output_uri - a uri for the output destination of the shapefile

        return - a OGR Datasource"""
    
    LOGGER.info('Entering wind_data_to_point_shape')
    
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
        latitude = float(point_dict['LATI'])
        longitude = float(point_dict['LONG'])

        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint_2D(longitude, latitude)

        output_feature = ogr.Feature(output_layer.GetLayerDefn())
        output_layer.CreateFeature(output_feature)
        
        for field_name in point_dict:
            field_index = output_feature.GetFieldIndex(field_name)
            output_feature.SetField(field_index, point_dict[field_name])
        
        output_feature.SetGeometryDirectly(geom)
        output_layer.SetFeature(output_feature)
        output_feature = None

    LOGGER.info('Leaving wind_data_to_point_shape')
    return output_datasource

def clip_and_reproject_maps(
        data_obj, aoi, clipped_uri, projected_uri, aoi_reprojected_uri):
    """Clip and project a Dataset/DataSource to an area of interest

        data_obj - a gdal Dataset or ogr Datasource
        aoi - an ogr DataSource of geometry type polygon
        clipped_uri - a string of the desired uri path for the clipped
            output step on data_obj 
        projected_uri - a string of the desired uri path for the
            projected output step on data_obj 
        aoi_reprojected_uri - a string of the desired uri path for the
            reprojected output step on the aoi 

        returns - a Dataset or DataSource clipped and projected to an area
            of interest"""

    LOGGER.info('Entering clip_and_reproject_maps')
    # Get the AOIs spatial reference as strings in Well Known Text
    aoi_sr = aoi.GetLayer().GetSpatialRef()
    aoi_wkt = aoi_sr.ExportToWkt()

    data_obj_wkt = None
    extension = None

    # Get the Well Known Text of the data object and set the appropriate
    # extension for future uri's
    if isinstance(data_obj, ogr.DataSource):
        data_obj_layer = data_obj.GetLayer()
        data_obj_sr = data_obj_layer.GetSpatialRef()
        data_obj_wkt = data_obj_sr.ExportToWkt()
    
    else:
        data_obj_wkt = data_obj.GetProjection()

    # Reproject the AOI to the spatial reference of the data_obj so that the
    # AOI can be used to clip the data_obj properly
    
    aoi_prj_to_obj = raster_utils.reproject_datasource(
            aoi, data_obj_wkt, aoi_reprojected_uri)

    data_obj_prj = None
    
    if isinstance(data_obj, ogr.DataSource):
        LOGGER.info('Clipping datasource')
        # Clip the data_obj to the AOI
        data_obj_clipped = clip_datasource(
                aoi_prj_to_obj, data_obj, clipped_uri)
        
        LOGGER.info('Reprojecting datasource')
        # Reproject the clipped data obj to that of the AOI
        data_obj_prj = raster_utils.reproject_datasource(
            data_obj_clipped, aoi_wkt, projected_uri)
    else:
        LOGGER.info('Clipping dataset')
        # Clip the data obj to the AOI
        data_obj_clipped = raster_utils.clip_dataset(
                data_obj, aoi_prj_to_obj, clipped_uri)

        # Get a point from the clipped data object to use later in helping
        # determine proper pixel size
        data_obj_gt = data_obj_clipped.GetGeoTransform()
        point_one = (data_obj_gt[0], data_obj_gt[3])
       
        # Create a Spatial Reference from the data objects WKT
        data_obj_sr = osr.SpatialReference()
        data_obj_sr.ImportFromWkt(data_obj_wkt)
        
        # A coordinate transformation to help get the proper pixel size of
        # the reprojected data object
        coord_trans = osr.CoordinateTransformation(data_obj_sr, aoi_sr)
      
        pixel_size = raster_utils.pixel_size_based_on_coordinate_transform(
                data_obj_clipped, coord_trans, point_one)

        LOGGER.info('Reprojecting dataset')
        # Reproject the data object to the projection of the AOI
        data_obj_prj = raster_utils.reproject_dataset(
                data_obj_clipped, pixel_size[0], aoi_wkt,
                projected_uri)
    
    LOGGER.info('Leaving clip_and_reproject_maps')
    return data_obj_prj

def clip_datasource(aoi_ds, orig_ds, output_uri):
    """Clip an OGR Datasource of geometry type polygon by another OGR Datasource
        geometry type polygon. The aoi_ds should be a shapefile with a layer
        that has only one polygon feature

        aoi_ds - an OGR Datasource that is the clipping bounding box
        orig_ds - an OGR Datasource to clip
        out_uri - output uri path for the clipped datasource

        returns - a clipped OGR Datasource """
   
    LOGGER.info('Entering clip_datasource')

    orig_layer = orig_ds.GetLayer()
    aoi_layer = aoi_ds.GetLayer()

    # If the file already exists remove it
    if os.path.isfile(output_uri):
        os.remove(output_uri)

    LOGGER.debug('Creating new datasource')
    # Create a new shapefile from the orginal_datasource 
    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_datasource = output_driver.CreateDataSource(output_uri)

    # Get the original_layer definition which holds needed attribute values
    original_layer_dfn = orig_layer.GetLayerDefn()

    # Create the new layer for output_datasource using same name and geometry
    # type from original_datasource as well as spatial reference
    output_layer = output_datasource.CreateLayer(
            original_layer_dfn.GetName(), orig_layer.GetSpatialRef(), 
            original_layer_dfn.GetGeomType())

    # Get the number of fields in original_layer
    original_field_count = original_layer_dfn.GetFieldCount()

    LOGGER.debug('Creating new fields')
    # For every field, create a duplicate field and add it to the new 
    # shapefiles layer
    for fld_index in range(original_field_count):
        original_field = original_layer_dfn.GetFieldDefn(fld_index)
        output_field = ogr.FieldDefn(
                original_field.GetName(), original_field.GetType())
        # NOT setting the WIDTH or PRECISION because that seems to be unneeded
        # and causes interesting OGR conflicts
        output_layer.CreateField(output_field)

    # Get the feature and geometry of the aoi
    aoi_feat = aoi_layer.GetFeature(0)
    aoi_geom = aoi_feat.GetGeometryRef()
    
    LOGGER.debug('Starting iteration over geometries')
    # Iterate over each feature in original layer
    for orig_feat in orig_layer:
        # Get the geometry for the feature
        orig_geom = orig_feat.GetGeometryRef()
    
        # Check to see if the feature and the aoi intersect. This will return a
        # new geometry if there is an intersection. If there is not an
        # intersection it will return an empty geometry or it will return None
        # and print an error to standard out
        intersect_geom = aoi_geom.Intersection(orig_geom)
        
        if not intersect_geom == None and not intersect_geom.IsEmpty():
            # Copy original_datasource's feature and set as new shapes feature
            output_feature = ogr.Feature(
                    feature_def=output_layer.GetLayerDefn())
        
            # Since the original feature is of interest add it's fields and
            # Values to the new feature from the intersecting geometries
            # The False in SetFrom() signifies that the fields must match
            # exactly
            output_feature.SetFrom(orig_feat, False)
            output_feature.SetGeometry(intersect_geom)
            output_layer.CreateFeature(output_feature)
            output_feature = None
    
    LOGGER.info('Leaving clip_datasource')
    return output_datasource
