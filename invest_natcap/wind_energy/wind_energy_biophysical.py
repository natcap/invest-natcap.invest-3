"""InVEST Wind Energy model file handler module"""
import logging
import os

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap.wind_energy import wind_energy_core
from invest_natcap import raster_utils

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
        args[hub_height] - a float value for the hub height of the turbines
            (meters) (required)
        args[cut_in_wspd] - a float value for the cut in wind speed of the
            (meters / second) turbine (required)
        args[cut_out_wspd] - a float value for the cut out wind speed of the
            (meteres / second) turbine (required)
        args[rated_wspd] - a float value for the rated wind speed of the 
            (meters / second) turbine (required)
        args[turbine_rated_pwr] - a float value for the turbine rated power
            (MW) (required)
        args[exp_out_pwr_curve] - a float value for the exponent output power
            curve (required)
        args[num_days] - an integer value for the number of days for harvested
            wind energy calculation (days) (required)
        args[air_density] - a float value for the air density of standard 
            atmosphere (kilograms / cubic meter) (required)
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

    workspace = args['workspace_dir']
    
    # Create dictionary to hold values that will be passed to the core
    # functionality
    biophysical_args = {}
            
    # If the user has not provided a results suffix, assume it to be an empty
    # string.
    try:
        suffix = '_' + args['suffix']
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

    bathymetry = gdal.Open(args['bathymetry_uri'])
    
    # Read the wind points from a text file into a dictionary and create a point
    # shapefile from that dictionary
    wind_point_shape_uri = os.path.join(
            inter_dir, 'wind_points_shape' + suffix + '.shp')
    
    LOGGER.info('Read wind data from text file')
    wind_data = read_wind_data(args['wind_data_uri'])
    
    LOGGER.info('Create point shapefile from wind data')
    wind_data_points = wind_data_to_point_shape(
            wind_data, 'wind_data', wind_point_shape_uri)

    try:
        aoi = ogr.Open(args['aoi_uri'])
    
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
        try:
            land_polygon = ogr.Open(args['land_polygon_uri'])

            land_poly_uris = os.path.join(inter_dir, 'land_poly' + suffix)
        
            LOGGER.info('Clip and project land poly to AOI')
            projected_land = clip_and_reproject_maps(
                    land_polygon, aoi, land_poly_uris)

            biophysical_args['land_polygon'] = projected_land
            biophysical_args['min_distance'] = float(args['min_distance']) 
            biophysical_args['max_distance'] = float(args['max_distance'])

        except KeyError:
            LOGGER.debug("Distance information not selected")

    except KeyError:
        LOGGER.debug("AOI argument was not selected")
        biophysical_args['bathymetry'] = bathymetry
        biophysical_args['wind_data_points'] = wind_data_points
    
    # Add biophysical inputs to the dictionary
    biophysical_args['workspace_dir'] = workspace
    biophysical_args['hub_height'] = float(args['hub_height'])
    biophysical_args['cut_in_wspd'] = float(args['cut_in_wspd'])
    biophysical_args['cut_out_wspd'] = float(args['cut_out_wspd'])
    biophysical_args['exp_out_pwr_curve'] = float(args['exp_out_pwr_curve'])
    biophysical_args['num_days'] = int(args['num_days'])
    biophysical_args['air_density'] = float(args['air_density'])
    biophysical_args['rated_wspd'] = float(args['rated_wspd'])
    biophysical_args['turbine_rated_pwr'] = float(args['turbine_rated_pwr'])
    
    # Pass in the depth values as negative, since it should be a negative
    # elevation
    biophysical_args['min_depth'] = abs(float(args['min_depth'])) * -1.0
    biophysical_args['max_depth'] = abs(float(args['max_depth'])) * -1.0
    biophysical_args['suffix'] = suffix
   
    # Call on the core module
    wind_energy_core.biophysical(biophysical_args)

def check_datasource_projections(dsource_list):
    """Checks if a list of OGR Datasources are projected and projected in the
        linear units of 1.0 which is meters

        dsource_list - a list of OGR Datasources

        returns - True if all Datasources are projected and projected in meters,
            otherwise returns False"""

    # Loop through all the datasources and check the projection
    for dsource in dsource_list:
        srs = dsource.GetLayer().GetSpatialRef()
        if not srs.IsProjected():
            return False
        # Compare linear units against 1.0 because that identifies units are in
        # meters
        if srs.GetLinearUnits() != 1.0:
            return False

    return True
    
def read_wind_data(wind_data_uri):
    """Unpack the wind data into a dictionary

        wind_data_uri - a uri for the wind data text file

        returns - a dictionary where the keys are the row numbers and the values
            are dictionaries mapping column headers to values """

    wind_file = open(wind_data_uri, 'rU')

    # Read the first line and get the column header names by splitting on the
    # commas
    columns_line = wind_file.readline().split(',')
    
    # Remove the newline character that is attached to the last element
    columns_line[len(columns_line) - 1] = \
            columns_line[len(columns_line) - 1].rstrip('\n')
    LOGGER.debug('COLUMN Line : %s', columns_line)
    
    wind_dict = {}
    
    for line in wind_file.readlines():
        line_array = line.split(',')

        # Remove the newline character that is attached to the last element
        line_array[len(line_array) - 1] = \
                line_array[len(line_array) - 1].rstrip('\n')

        # The key for the dictionary will be the first element on the line
        key = float(line_array[0])
        wind_dict[key] = {}
        
        # Add each value to a sub dictionary of 'key'
        for index in range(1, len(line_array)):
            wind_dict[key][columns_line[index]] = float(line_array[index])

    wind_file.close()

    return wind_dict

def wind_data_to_point_shape(dict_data, layer_name, output_uri):
    """Given a dictionary of the wind data create a point shapefile that
        represents this data
        
        dict_data - a python dictionary with the wind data:
            0 : {'LATI':97, 'LONG':43, ... 'Ram-030m':6.3, ... 'K-010m':2.7},
            1 : {'LATI':55, 'LONG':51, ... 'Ram-030m':6.2, ... 'K-010m':2.4},
            2 : {'LATI':73, 'LONG':47, ... 'Ram-030m':6.5, ... 'K-010m':2.3},
        layer_name - a python string for the name of the layer
        output_uri - a uri for the output destination of the shapefile

        return - a OGR Datasource"""
    # If the output_uri exists delete it
    if os.path.isfile(output_uri):
        os.remove(output_uri)
    
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

    for field in field_list:
        output_field = ogr.FieldDefn(field, ogr.OFTReal)   
        output_layer.CreateField(output_field)

    # For each inner dictionary (for each point) create a point
    for point_dict in dict_data.itervalues():
        latitude = point_dict['LATI']
        longitude = point_dict['LONG']

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

    return output_datasource

def clip_and_reproject_maps(data_obj, aoi, output_uri):
    """Clip and project a Dataset/DataSource to an area of interest

        data_obj - a gdal Dataset or ogr Datasource
        aoi - an ogr DataSource of geometry type polygon
        output_uri - a string of the desired base output name without the
            suffix

        returns - a Dataset or DataSource clipped and projected to an area
            of interest"""

    # Get the AOIs spatial reference as strings in Well Known Text
    aoi_sr = aoi.GetLayer().GetSpatialRef()
    aoi_wkt = aoi_sr.ExportToWkt()

    data_obj_wkt = None
    suffix = None
    basename = os.path.basename(output_uri)
    dirname = os.path.dirname(output_uri)

    # Get the Well Known Text of the data object and set the appropriate
    # suffix for future uri's
    if isinstance(data_obj, ogr.DataSource):
        data_obj_layer = data_obj.GetLayer()
        data_obj_sr = data_obj_layer.GetSpatialRef()
        data_obj_wkt = data_obj_sr.ExportToWkt()
    
        suffix = '.shp'
    else:
        data_obj_wkt = data_obj.GetProjection()
        
        suffix = '.tif'

    # Reproject the AOI to the spatial reference of the data_obj so that the
    # AOI can be used to clip the data_obj properly
    
    aoi_prj_to_obj_uri = os.path.join(
            dirname, 'aoi_prj_to_' + basename + '.shp')
    
    aoi_prj_to_obj = raster_utils.reproject_datasource(
            aoi, data_obj_wkt, aoi_prj_to_obj_uri)
    
    data_obj_clipped_uri = output_uri + '_clipped' + suffix
    data_obj_reprojected_uri = output_uri + '_reprojected' + suffix

    data_obj_prj = None
    
    if isinstance(data_obj, ogr.DataSource):
        # Clip the data_obj to the AOI
        data_obj_clipped = clip_datasource(
                aoi_prj_to_obj, data_obj, data_obj_clipped_uri)
        
        # Reproject the clipped data obj to that of the AOI
        data_obj_prj = raster_utils.reproject_datasource(
            data_obj_clipped, aoi_wkt, data_obj_reprojected_uri)
    else:
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

        # Reproject the data object to the projection of the AOI
        data_obj_prj = raster_utils.reproject_dataset(
                data_obj_clipped, pixel_size[0], aoi_wkt,
                data_obj_reprojected_uri)

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

    # For every field, create a duplicate field and add it to the new 
    # shapefiles layer
    for fld_index in range(original_field_count):
        original_field = original_layer_dfn.GetFieldDefn(fld_index)
        output_field = ogr.FieldDefn(
                original_field.GetName(), original_field.GetType())
        output_field.SetWidth(original_field.GetWidth())
        output_layer.CreateField(output_field)

    # Get the feature and geometry of the aoi
    aoi_feat = aoi_layer.GetFeature(0)
    aoi_geom = aoi_feat.GetGeometryRef()
    
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
            output_feature.SetGeometry(intersect_geom)
        
            # Since the original feature is of interest add it's fields and
            # Values to the new feature from the intersecting geometries
            for fld_index2 in range(output_feature.GetFieldCount()):
                orig_field_value = orig_feat.GetField(fld_index2)
                output_feature.SetField(fld_index2, orig_field_value)
    
            output_layer.CreateFeature(output_feature)
            output_feature = None

    return output_datasource
