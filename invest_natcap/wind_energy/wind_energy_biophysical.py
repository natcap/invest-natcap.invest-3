"""InVEST Wind Energy Biophysical model file handler"""
import logging
import os
import csv
import json

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import shapely.wkt
from shapely.ops import unary_union
from shapely.wkb import dumps
from shapely.wkb import loads
from shapely import speedups

from invest_natcap.wind_energy import wind_energy_core
from invest_natcap import raster_utils

speedups.enable()

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_biophysical')

def execute(args):
    """Takes care of all file handling for the biophysical part of the wind
        energy model
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved (required)
        args[wind_data_uri] - a text file where each row is a location with at
            least the Longitude, Latitude, Scale and Shape parameters (required)
        args[aoi_uri] - a uri to an OGR datasource that is of type polygon and 
            projected in linear units of meters. The polygon specifies the 
            area of interest for the wind data points. If limiting the wind 
            farm bins by distance, then the aoi should also cover a portion 
            of the land polygon that is of interest (optional)
        args[bathymetry_uri] - a uri to a GDAL dataset that has the depth
            values of the area of interest (required)
        args[bottom_type_uri] - a uri to an OGR datasource of type polygon
            that depicts the subsurface geology type (optional)
        args[turbine_parameters_uri] - a uri to a CSV file that holds the
            turbines biophysical parameters as well as valuation parameters 
            (required)
        args[hub_height] - an integer value for the hub height of the turbines
            as a factor of ten (meters) (required)
        args[num_days] - an integer value for the number of days for harvested
            wind energy calculation (days) (required)
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
            for offshore wind farm installation (meters) The AOI must be
            selected for this input to be active (optional)
        args[max_distance] - a float value for the maximum distance from shore
            for offshore wind farm installation (meters) The AOI must be
            selected for this input to be active (optional)

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

    bathymetry = gdal.Open(str(args['bathymetry_uri']))
  
    # Using the hub height to generate the proper field name for the scale 
    # value that is found in the wind data file
    hub_height = args['hub_height']

    scale_key = str(int(hub_height))
    if len(scale_key) <= 2:
        scale_key = 'Ram-0' + scale_key + 'm'
    else:
        scale_key = 'Ram-' + scale_key + 'm'
   
    # Define a list of the fields that of interest in the wind data file
    wind_data_field_list = ['LATI', 'LONG', scale_key, 'K-010m']

    # Read the wind points from a text file into a dictionary and create a point
    # shapefile from that dictionary
    wind_point_shape_uri = os.path.join(
            inter_dir, 'wind_points_shape' + suffix + '.shp')
    
    LOGGER.info('Read wind data from text file')
    wind_data = read_wind_data(str(args['wind_data_uri']), wind_data_field_list)
    
    LOGGER.info('Create point shapefile from wind data')
    wind_data_points = wind_data_to_point_shape(
            wind_data, 'wind_data', wind_point_shape_uri)

    try:
        LOGGER.info('Trying to open the AOI')
        aoi = ogr.Open(str(args['aoi_uri']))
        
        LOGGER.info('Checking AOIs projection')
        # Check to make sure that the AOI is projected and in meters
        if not check_datasource_projections([aoi]):
            # Creating a unique exception on the fly to provide better feedback
            # to the user
            class ProjectionError(Exception):
                """A self defined Exception for a bad projection"""
                pass

            raise ProjectionError('The AOI is not projected properly. Please '
                   'refer to the user guide or help icon on the user interface')

        wind_pts_uris = os.path.join(inter_dir, 'wind_points' + suffix)
        bathymetry_uris = os.path.join(inter_dir, 'bathymetry' + suffix)
        
        LOGGER.info('Clip and project wind points to AOI')
        wind_pts_prj = clip_and_reproject_maps(
                wind_data_points, aoi, wind_pts_uris) 
    
        LOGGER.info('Clip and project bathymetry to AOI')
        clip_and_proj_bath = clip_and_reproject_maps(
                bathymetry, aoi, bathymetry_uris)

        biophysical_args['bathymetry'] = clip_and_proj_bath
        biophysical_args['wind_data_points'] = wind_pts_prj
        biophysical_args['aoi'] = aoi 
        
        # Try to handle the distance inputs and land datasource if they 
        # are present
        if args['distance_container']:
            LOGGER.info('Handling distance parameters')
            land_polygon = ogr.Open(str(args['land_polygon_uri']))

            land_poly_uris = os.path.join(inter_dir, 'land_poly' + suffix)
        
            LOGGER.info('Clip and project land poly to AOI')
            projected_land = clip_and_reproject_maps(
                    land_polygon, aoi, land_poly_uris)

            biophysical_args['land_polygon'] = projected_land
            biophysical_args['min_distance'] = float(args['min_distance']) 
            biophysical_args['max_distance'] = float(args['max_distance'])

        else:
            LOGGER.info('Distance information not provided')
    except KeyError:
        LOGGER.debug("AOI argument was not selected")
        biophysical_args['bathymetry'] = bathymetry
        biophysical_args['wind_data_points'] = wind_data_points
    
    # Add biophysical inputs to the dictionary
    biophysical_args['workspace_dir'] = workspace
    biophysical_args['hub_height'] = int(args['hub_height'])
    biophysical_args['num_days'] = int(args['num_days'])
    
    # Create a list of the biophysical parameters we are looking for from the
    # input files
    biophysical_params = ['cut_in_wspd', 'cut_out_wspd', 'rated_wspd',
                          'turbine_rated_pwr', 'air_density',
                          'exponent_power_curve']
    # Get the biophysical turbine parameters from the CSV file
    bio_turbine_param_file = open(args['turbine_parameters_uri'])
    bio_turbine_reader = csv.reader(bio_turbine_param_file)
    bio_turbine_dict = {}
    for field_value_row in bio_turbine_reader:
        # Only get the biophysical parameters and leave out the valuation ones
        if field_value_row[0].lower() in biophysical_params:
            bio_turbine_dict[field_value_row[0].lower()] = field_value_row[1]

    # Get the global biophysical parameters from the JSON file
    bio_global_params_file = open(
           os.path.join(workspace, 'input/global_wind_energy_attributes.json'))

    bio_global_params_dict = json.load(bio_global_params_file)
    for key, val in bio_global_params_dict.iteritems():
        # Only get the biophysical parameters and leave out the valuation ones
        if key.lower() in biophysical_params:
            bio_turbine_dict[key.lower()] = val

    LOGGER.debug('Biophysical Turbine Parameters: %s', bio_turbine_dict)
    
    if len(bio_turbine_dict.keys()) != len(biophysical_params):
        class FieldError(Exception):
            pass
        raise FieldError('An Error occured from reading in a field value from '
        'either the turbine CSV file or the global parameters JSON file. ' 
        'Please make sure all the necessary fields are present and spelled '
        'correctly.')

    biophysical_args['biophysical_turbine_dict'] = bio_turbine_dict
    # Pass in the depth values as negative, since it should be a negative
    # elevation
    biophysical_args['min_depth'] = abs(float(args['min_depth'])) * -1.0
    biophysical_args['max_depth'] = abs(float(args['max_depth'])) * -1.0
    biophysical_args['suffix'] = suffix
   
    # Call on the core module
    wind_energy_core.biophysical(biophysical_args)

    LOGGER.info('Leaving Wind_Energy_Biophysical')

def check_datasource_projections(dsource_list):
    """Checks if a list of OGR Datasources are projected and projected in the
        linear units of 1.0 which is meters

        dsource_list - a list of OGR Datasources

        returns - True if all Datasources are projected and projected in meters,
            otherwise returns False"""
    LOGGER.info('Entering check_datasource_projections')
    # Loop through all the datasources and check the projection
    for dsource in dsource_list:
        srs = dsource.GetLayer().GetSpatialRef()
        if not srs.IsProjected():
            return False
        # Compare linear units against 1.0 because that identifies units are in
        # meters
        if srs.GetLinearUnits() != 1.0:
            return False

    LOGGER.info('Leaving check_datasource_projections')
    return True

def read_wind_data(wind_data_uri, field_list):
    """Unpack the wind data into a dictionary

        wind_data_uri - a uri for the wind data text file
        field_list - a list of strings referring to the column headers from
            the text file that are to be included in the dictionary

        returns - a dictionary where the keys are lat/long tuples which point
            to dictionaries that hold wind data at that location"""

    LOGGER.debug('Entering read_wind_data')
    
    # The 'rU' flag is to mark ensure the file is open as read only and with
    # Universal newline support
    wind_file = open(wind_data_uri, 'rU')
    
    # Read in the file as a CSV in dictionary format such that the first row of
    # the file is treated as the list of keys for the respective values on the
    # following rows
    file_reader = csv.DictReader(wind_file)
    
    wind_dict = {}
    
    for row in file_reader:
        # Create the key for the dictionary based on the unique lat/long
        # coordinate
        key = (row['LATI'], row['LONG'])
        wind_dict[key] = {}
        
        for row_key in row:
            # Only add the values specified in the list to the dictionary. This
            # allows some flexibility in removing columns that are not cared
            # about 
            if row_key in field_list:
                wind_dict[key][row_key] = row[row_key]

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

def clip_and_reproject_maps(data_obj, aoi, output_uri):
    """Clip and project a Dataset/DataSource to an area of interest

        data_obj - a gdal Dataset or ogr Datasource
        aoi - an ogr DataSource of geometry type polygon
        output_uri - a string of the desired base output name without the
            extension (.tif, .shp, etc...) 

        returns - a Dataset or DataSource clipped and projected to an area
            of interest"""

    LOGGER.info('Entering clip_and_reproject_maps')
    # Get the AOIs spatial reference as strings in Well Known Text
    aoi_sr = aoi.GetLayer().GetSpatialRef()
    aoi_wkt = aoi_sr.ExportToWkt()

    data_obj_wkt = None
    extension = None
    
    # Get the basename and directory name of the uri to help create future uri's
    basename = os.path.basename(output_uri)
    dirname = os.path.dirname(output_uri)

    # Get the Well Known Text of the data object and set the appropriate
    # extension for future uri's
    if isinstance(data_obj, ogr.DataSource):
        data_obj_layer = data_obj.GetLayer()
        data_obj_sr = data_obj_layer.GetSpatialRef()
        data_obj_wkt = data_obj_sr.ExportToWkt()
    
        extension = '.shp'
    else:
        data_obj_wkt = data_obj.GetProjection()
        
        extension = '.tif'

    # Reproject the AOI to the spatial reference of the data_obj so that the
    # AOI can be used to clip the data_obj properly
    
    aoi_prj_to_obj_uri = os.path.join(
            dirname, 'aoi_prj_to_' + basename + '.shp')
    
    aoi_prj_to_obj = raster_utils.reproject_datasource(
            aoi, data_obj_wkt, aoi_prj_to_obj_uri)
    
    data_obj_clipped_uri = output_uri + '_clipped' + extension
    data_obj_reprojected_uri = output_uri + '_reprojected' + extension

    data_obj_prj = None
    
    if isinstance(data_obj, ogr.DataSource):
        LOGGER.info('Clipping datasource')
        # Clip the data_obj to the AOI
        data_obj_clipped = clip_datasource(
                aoi_prj_to_obj, data_obj, data_obj_clipped_uri)
        
        LOGGER.info('Reprojecting datasource')
        # Reproject the clipped data obj to that of the AOI
        data_obj_prj = raster_utils.reproject_datasource(
            data_obj_clipped, aoi_wkt, data_obj_reprojected_uri)
    else:
        LOGGER.info('Clipping dataset')
        # Clip the data obj to the AOI
        data_obj_clipped = raster_utils.clip_dataset(
                data_obj, aoi_prj_to_obj, data_obj_clipped_uri)

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
                data_obj_reprojected_uri)
    
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

    LOGGER.info('Creating new datasource')
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

    LOGGER.info('Creating new fields')
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
    
    LOGGER.info('Starting iteration over geometries')
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

#def clip_datasource_new(aoi_ds, orig_ds, output_uri):
#   """Clip an OGR Datasource of geometry type polygon by another OGR Datasource
#       geometry type polygon. The aoi_ds should be a shapefile with a layer
#       that has only one polygon feature

#       aoi_ds - an OGR Datasource that is the clipping bounding box
#       orig_ds - an OGR Datasource to clip
#       out_uri - output uri path for the clipped datasource

#       returns - a clipped OGR Datasource """
#  
#   LOGGER.info('Entering clip_datasource_new')

#   orig_layer = orig_ds.GetLayer()
#   aoi_layer = aoi_ds.GetLayer()

#   # If the file already exists remove it
#   if os.path.isfile(output_uri):
#       os.remove(output_uri)

#   LOGGER.info('Creating new datasource')
#   # Create a new shapefile from the orginal_datasource 
#   output_driver = ogr.GetDriverByName('ESRI Shapefile')
#   output_datasource = output_driver.CreateDataSource(output_uri)

#   # Get the original_layer definition which holds needed attribute values
#   original_layer_dfn = orig_layer.GetLayerDefn()

#   # Create the new layer for output_datasource using same name and geometry
#   # type from original_datasource as well as spatial reference
#   output_layer = output_datasource.CreateLayer(
#           original_layer_dfn.GetName(), orig_layer.GetSpatialRef(), 
#           original_layer_dfn.GetGeomType())

#   # Get the number of fields in original_layer
#   original_field_count = original_layer_dfn.GetFieldCount()

#   LOGGER.info('Creating new fields')
#   # For every field, create a duplicate field and add it to the new 
#   # shapefiles layer
#   for fld_index in range(original_field_count):
#       original_field = original_layer_dfn.GetFieldDefn(fld_index)
#       output_field = ogr.FieldDefn(
#               original_field.GetName(), original_field.GetType())
#       # NOT setting the WIDTH or PRECISION because that seems to be unneeded
#       # and causes interesting OGR conflicts
#       output_layer.CreateField(output_field)

#   # A list to hold the aoi shapefiles geometries
#   aoi_datasource_geoms = []

#   LOGGER.info('Build up AOI datasources geometries with Shapely')
#   for aoi_feat in aoi_layer:
#       aoi_geom = shapely.wkt.loads(aoi_feat.GetGeometryRef().ExportToWkt())
#       aoi_datasource_geoms.append(aoi_geom)
#   
#   LOGGER.info('Taking Unary Union on AOI geometries')
#   # Calculate the union on the list of geometries to get one collection of
#   # geometries
#   aoi_geom_collection = unary_union(aoi_datasource_geoms)
#   
#   LOGGER.info('Starting iteration over geometries')
#   # Iterate over each feature in original layer
#   for orig_feat in orig_layer:
#       # Get the geometry for the feature
#       orig_geom_wkb = orig_feat.GetGeometryRef().ExportToWkb()
#       orig_geom_shapely = loads(orig_geom_wkb) 
#       
#       intersect_geom = aoi_geom_collection.intersection(orig_geom_shapely)
#       
#       if not intersect_geom.is_empty:
#           # Copy original_datasource's feature and set as new shapes feature
#           output_feature = ogr.Feature(
#                   feature_def=output_layer.GetLayerDefn())
#           output_layer.CreateFeature(output_feature)
#       
#           output_feature.SetFrom(orig_feat, False)
#           output_layer.SetFeature(output_feature)
#           output_feature = None
#   
#   LOGGER.info('Leaving clip_datasource_new')
#   return output_datasource

#def clip_datasource_fast(aoi_ds, orig_ds, output_uri):
#   """Clip an OGR Datasource of geometry type polygon by another OGR Datasource
#       geometry type polygon. The aoi_ds should be a shapefile with a layer
#       that has only one polygon feature

#       aoi_ds - an OGR Datasource that is the clipping bounding box
#       orig_ds - an OGR Datasource to clip
#       out_uri - output uri path for the clipped datasource

#       returns - a clipped OGR Datasource """
#  
#   LOGGER.info('Entering clip_datasource_fast')

#   orig_layer = orig_ds.GetLayer()
#   aoi_layer = aoi_ds.GetLayer()

#   # If the file already exists remove it
#   if os.path.isfile(output_uri):
#       os.remove(output_uri)

#   LOGGER.info('Creating new datasource')
#   # Create a new shapefile from the orginal_datasource 
#   output_driver = ogr.GetDriverByName('ESRI Shapefile')
#   output_datasource = output_driver.CreateDataSource(output_uri)

#   # Get the original_layer definition which holds needed attribute values
#   original_layer_dfn = orig_layer.GetLayerDefn()

#   # Create the new layer for output_datasource using same name and geometry
#   # type from original_datasource as well as spatial reference
#   output_layer = output_datasource.CreateLayer(
#           original_layer_dfn.GetName(), orig_layer.GetSpatialRef(), 
#           original_layer_dfn.GetGeomType())

#   LOGGER.info('Creating new field')
#   # We only create one general field here because this function assumes that
#   # only the geometries and shapes themselves matter. It uses a faster
#   # clipping approach such that the specific field values can not be tracked
#   output_field = ogr.FieldDefn('id', ogr.OFTReal)
#   output_layer.CreateField(output_field)

#   # A list to hold the original shapefiles geometries
#   original_datasource_geoms = []
#   LOGGER.info('Build up original datasources geometries with Shapely')
#   for original_feat in original_layer:
#       original_geom = shapely.wkt.loads(
#               original_feat.GetGeometryRef().ExportToWkt())
#       # The commented line below simplies the geometry by smoothing it which
#       # allows the union operation to run much faster. Until accuracy is
#       # decided upon, we will do it straight up
#       #original_datasource_geoms.append(geom.simplify(0.001, preserve_topology=False))
#       
#       original_datasource_geoms.append(geom)

#   LOGGER.info('Taking Unary Union on original geometries')
#   # Calculate the union on the list of geometries to get one collection of
#   # geometries
#   original_geom_collection = unary_union(original_datasource_geoms)

#   # A list to hold the aoi shapefiles geometries
#   aoi_datasource_geoms = []

#   LOGGER.info('Build up AOI datasources geometries with Shapely')
#   for aoi_feat in aoi_layer:
#       aoi_geom = shapely.wkt.loads(aoi_feat.GetGeometryRef().ExportToWkt())
#       aoi_datasource_geoms.append(aoi_geom)
#   
#   LOGGER.info('Taking Unary Union on AOI geometries')
#   # Calculate the union on the list of geometries to get one collection of
#   # geometries
#   aoi_geom_collection = unary_union(aoi_datasource_geoms)

#   LOGGER.info('Take the intersection of the AOI geometry collection and the original geometry collection')
#   # Take the intersection of the geometry collections which will give us our
#   # 'clipped' geometry set
#   clipped_geom = aoi_geom_collection.intersection(original_geom_collection)

#   LOGGER.debug('Dump the Shapely geometry to Well Known Binary format')
#   # Dump the unioned Shapely geometry into a Well Known Binary format so that
#   # it can be read and used by OGR
#   wkb_geom = dumps(clipped_geom)

#   # Create a new OGR geometry from the Well Known Binary
#   ogr_geom = ogr.CreateGeometryFromWkb(wkb_geom)
#   output_feature = ogr.Feature(output_layer.GetLayerDefn())
#   output_layer.CreateFeature(output_feature)
#   
#   field_index = output_feature.GetFieldIndex('id')
#   # Arbitrarily set the field to 1 since there is just one feature that has
#   # the clipped geometry
#   output_feature.SetField(field_index, 1)
#   output_feature.SetGeometry(ogr_geom)
#   
#   output_layer.SetFeature(output_feature)
#   output_feature = None
#   
#   LOGGER.info('Leaving clip_datasource_fast')
#   return output_datasource
