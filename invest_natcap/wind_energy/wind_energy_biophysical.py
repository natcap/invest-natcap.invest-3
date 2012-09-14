"""InVEST Wind Energy model file handler module"""
import os.path
import logging
import csv
import os

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import numpy as np

from invest_natcap.wind_energy import wind_energy_core
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_biophysical')

def execute(args):
    """This is where the doc string lives
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved
        args[aoi_uri] - a uri to an OGR shapefile that specifies the area of
            interest for the wind data points
        args[bathymetry_uri] - a uri to a GDAL raster dataset that has the depth
            values of the area of interest
        args[bottom_type_uri] - a uri to an OGR shapefile that depicts the
            subsurface geology type
        args[hub_height] - a float value that is the hub height
        args[pwr_law_exponent] - a float value for the power law exponent
        args[cut_in_wspd] - a float value for the cut in wind speed of the
            turbine
        args[rated_wspd] - a float value for the rated wind speed
        args[cut_out_wspd] - a float value for the cut out wind speed of the
            turbine
        args[turbine_rated_pwr] - a float value for the turbine rated power
        args[exp_output_pwr_curve] - a float value exponent output power curve
        args[days] - a float value for the number of days
        args[air_density] - a float value for the air density constant
        args[min_depth] - a float value minimum depth of the device
        args[max_depth] - a float value maximum depth of the device
        args[min_distance] - 
        args[max_distance] - 
        args[land_polygon_uri] -

        returns -  
    """

    workspace = args['workspace_dir']
    
    # create dictionary to hold values that will be passed to the core
    # functionality
    biophysical_args = {}
    biophysical_args['workspace_dir'] = workspace

    # if the user has not provided a results suffix, assume it to be an empty
    # string.
    try:
        suffix = '_' + args['suffix']
    except:
        suffix = ''

    biophysical_args['suffix'] = suffix

    # Check to see if each of the workspace folders exists.  If not, create the
    # folder in the filesystem.
    inter_dir = os.path.join(workspace, 'intermediate')
    out_dir = os.path.join(workspace, 'output')

    for folder in [inter_dir, out_dir]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

    # handle opening of relevant files
    bathymetry = gdal.Open(args['bathymetry_uri'])
    aoi = ogr.Open(args['aoi_uri'])
    
    # check to make sure that the AOI is projected and in meters
    if not check_datasource_projections([aoi]):
        raise Exception('The AOI is not projected properly')

    biophysical_args['aoi'] = aoi 
    
    # read the wind points from a text file into a dictionary and create a point
    # shapefile from that dictionary
    wind_point_shape_uri = os.path.join(inter_dir, 'wind_points_shape.shp')
    wind_data = read_wind_data(args['wind_data_uri'])
    wind_data_points = wind_data_to_point_shape(
            wind_data, 'wind_data', wind_point_shape_uri)

    # get the AOI spatial reference as a string in Well Known Text
    AOI_wkt = aoi.GetLayer().GetSpatialRef().ExportToWkt()
   
    dset_out_uri = os.path.join(inter_dir, 'clipped_projected_bathymetry.tif')

    # clip the bathymetry dataset from the AOI and then project the clipped
    # bathymetry dataset to the AOI projection
    clip_and_proj_bath = clip_and_project_dataset_from_datasource(
        bathymetry, aoi, dset_out_uri, inter_dir)

    wind_shape_reprojected_uri = os.path.join(
            inter_dir, 'wind_points_reprojected.shp')
  
    # reproject the data points shapefile to that of the AOI
    wind_data_points = raster_utils.reproject_datasource(
        wind_data_points, AOI_wkt, wind_shape_reprojected_uri)
   
    # add biophysical inputs to the dictionary
    biophysical_args['wind_data_points'] = wind_data_points
    biophysical_args['bathymetry'] = clip_and_proj_bath
    biophysical_args['min_depth'] = float(args['min_depth']) 
    biophysical_args['max_depth'] = float(args['max_depth'])
   
    # try to handle the distance inputs and datasource if they are present
    try:
        biophysical_args['min_distance'] = float(args['min_distance']) 
        biophysical_args['max_distance'] = float(args['max_distance'])
        
        land_polygon = ogr.Open(args['land_polygon_uri'])
        projected_land_uri = os.path.join(inter_dir, 'projected_land_poly.shp')  
    
        # back project AOI so that the land polygon can be clipped properly
        back_proj_aoi_uri = os.path.join(inter_dir, 'back_proj_aoi.shp')
        land_wkt = land_polygon.GetLayer().GetSpatialRef().ExportToWkt()
        back_proj_aoi = raster_utils.reproject_datasource(aoi, land_wkt,
                back_proj_aoi_uri)
        # clip the land polygon to the AOI
        clipped_land_uri = os.path.join(inter_dir, 'clipped_land.shp')
        clipped_land = clip_datasource(
                back_proj_aoi, land_polygon, clipped_land_uri)

        # reproject the land polygon to the AOI projection
        projected_land = raster_utils.reproject_datasource(
                clipped_land, AOI_wkt, projected_land_uri) 

        biophysical_args['land_polygon'] = projected_land

    except KeyError:
        LOGGER.debug("Distance information not selected")
        pass
    
    # call on the core module
    wind_energy_core.biophysical(biophysical_args)

def check_datasource_projections(dsource_list):
    """Checks if a list of OGR Datasources are projected and projected in the
        linear units of 1.0 which is meters

        dsource_list - a list of OGR Datasources

        returns - True if all Datasources are projected and projected in meters,
            otherwise returns False"""

    # loop through all the datasources and check the projection
    for dsource in dsource_list:
        srs = dsource.GetLayer().GetSpatialRef()
        if not srs.IsProjected():
            return False
        # compare linear units against 1.0 because that identifies units are in
        # meters
        if srs.GetLinearUnits() != 1.0:
            return False

    return True
    
def read_wind_data(wind_data_uri):
    """Unpack the wind data into a dictionary

        wind_data_uri - a uri for the wind data text file

        returns - a dictionary where the keys is the row number and the values
            are dictionaries mapping column headers to values """

    wind_file = open(wind_data_uri)
    # read the first line and get the column header names by splitting on the
    # commas
    columns_line = wind_file.readline().split(',')
    wind_dict = {}
    
    for line in wind_file.readlines():
        line_array = line.split(',')
        # the key for the dictionary will be the first element on the line
        key = line_array[0]
        wind_dict[key] = {}
        # add each value to a sub dictionary of 'key'
        for index in range(1, len(line_array) - 1):
            wind_dict[key][columns_line[index]] = float(line_array[index])

    wind_file.close()

    LOGGER.debug(
        'wind_dict keys : %s', np.sort(np.array(wind_dict.keys()).astype(int)))
    
    return wind_dict


def wind_data_to_point_shape(dict_data, layer_name,  output_uri):
    """Given a dictionary of the wind data create a point shapefile that
        represents this data
        
        dict_data - a python dictionary with the wind data:
            0 : {'Lat':97, 'Long':43, ...},
            1 : {'Lat':97, 'Long':43, ...},
            2 : {'Lat':97, 'Long':43, ...}
        layer_name - the name of the layer
        output_uri - a uri for the output destination of the shapefile

        return - a OGR Datasource 
        """
    # if the output_uri exists delete it
    if os.path.isfile(output_uri):
        os.remove(output_uri)
    
    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_datasource = output_driver.CreateDataSource(output_uri)

    # set the spatial reference to WGS84 (lat/long)
    source_sr = osr.SpatialReference()
    source_sr.SetWellKnownGeogCS("WGS84")
    
    output_layer = output_datasource.CreateLayer(
            layer_name, source_sr, ogr.wkbPoint)

    # construct a list of fields to add from the keys of the inner dictionary
    field_list = dict_data[dict_data.keys()[0]].keys()

    for field in field_list:
        output_field = ogr.FieldDefn(field, ogr.OFTReal)   
        output_layer.CreateField(output_field)

    # for each inner dictionary (for each point) create a point
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

def clip_and_project_dataset_from_datasource(
        orig_dset, orig_dsource, dset_out_uri, inter_dir):
    """Clips and reprojects a gdal Dataset to the size and projection of the ogr
        datasource

        orig_dset - a GDAL dataset
        orig_dsource - an OGR datasource
        dset_out_uri - a python string for the output uri
        inter_dir - a directory path to save intermediate files to

        return - a GDAL dataset    
    """
    back_projected_dsource_uri = os.path.join(
            inter_dir, 'back_projected_dsource.shp')
    
    clipped_dset_uri = os.path.join(inter_dir, 'clipped_dset.tif')
    
    dset_wkt = orig_dset.GetProjection()
    out_wkt = orig_dsource.GetLayer().GetSpatialRef().ExportToWkt()

    # reproject the datasource to the projection of the dataset, this is so we
    # can clip before reprojecting the dataset
    back_projected_dsource = raster_utils.reproject_datasource(
            orig_dsource, dset_wkt, back_projected_dsource_uri)

    # clip the dataset from the datasource
    clipped_dset = raster_utils.clip_dataset(
            orig_dset, back_projected_dsource, clipped_dset_uri)

    # at the moment this is all done to determine the pixel size. It is found by
    # taking a point from the dataset, creating another poing by adding the cell
    # size and then transforming those points to the new projection. The two x
    # and y values are then subtracted to get the new pixel size
    gt = clipped_dset.GetGeoTransform()
    x_size, y_size = gt[1], gt[5]
    point_one = (gt[0], gt[3])
    point_two = (gt[0] + x_size, gt[3] + y_size)
   
    srs_in = osr.SpatialReference()
    srs_in.ImportFromWkt(dset_wkt)
    srs_out = osr.SpatialReference()
    srs_out.ImportFromWkt(out_wkt)
    coord_trans = osr.CoordinateTransformation(srs_in, srs_out)

    proj_point_one = coord_trans.TransformPoint(point_one[0], point_one[1])
    proj_point_two = coord_trans.TransformPoint(point_two[0], point_two[1])

    width = abs(proj_point_two[0] - proj_point_one[0])
    height = abs(proj_point_two[1] - proj_point_one[1])
   
    LOGGER.debug('raster pixel sizes : %s, %s', width, height)
    # reproject the dataset from the datasource
    clipped_projected_dset = raster_utils.reproject_dataset(
            clipped_dset, width, out_wkt, dset_out_uri)

    return clipped_projected_dset

def clip_datasource(aoi_ds, orig_ds, output_uri):
    """Clip an OGR Datasource of geometry type polygon by another OGR Datasource
        geometry type polygon. The aoi_ds should be a shapefile with a layer
        that has only one polygon feature

        aoi_ds - an OGR Datasource that is the clipping bounding box
        orig_ds - an OGR Datasource to clip
        out_uri - output uri path for the clipped datasource

        returns - a clipped OGR Datasource """
    
    orig_layer = orig_ds.GetLayer()
    aoi_layer = aoi_ds.GetLayer()

    # if the file already exists remove it
    if os.path.isfile(output_uri):
        os.remove(output_uri)

    # create a new shapefile from the orginal_datasource 
    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_datasource = output_driver.CreateDataSource(output_uri)

    #Get the original_layer definition which holds needed attribute values
    original_layer_dfn = orig_layer.GetLayerDefn()

    #Create the new layer for output_datasource using same name and geometry
    #type from original_datasource as well as spatial reference
    output_layer = output_datasource.CreateLayer(
            original_layer_dfn.GetName(), orig_layer.GetSpatialRef(), 
            original_layer_dfn.GetGeomType())

    #Get the number of fields in original_layer
    original_field_count = original_layer_dfn.GetFieldCount()

    #For every field, create a duplicate field and add it to the new 
    #shapefiles layer
    for fld_index in range(original_field_count):
        original_field = original_layer_dfn.GetFieldDefn(fld_index)
        output_field = ogr.FieldDefn(original_field.GetName(), original_field.GetType())
        output_field.SetWidth(original_field.GetWidth())
        output_field.SetPrecision(original_field.GetPrecision())
        output_layer.CreateField(output_field)

    # get the feature and geometry of the aoi
    aoi_feat = aoi_layer.GetFeature(0)
    aoi_geom = aoi_feat.GetGeometryRef()

    # iterate over each feature in original layer
    for orig_feat in orig_layer:
        # get the geometry for the feature
        orig_geom = orig_feat.GetGeometryRef()
        # check to see if the feature and the aoi intersect. this will return a
        # new geometry if there is an intersection. If there is not an
        # intersection it will return an empty geometry or it will return None
        # and print an error to standard out
        intersect_geom = aoi_geom.Intersection(orig_geom)
       
        if not intersect_geom == None and not intersect_geom.IsEmpty():
            # copy original_datasource's feature and set as new shapes feature
            output_feature = ogr.Feature(feature_def=output_layer.GetLayerDefn())
            output_feature.SetGeometry(intersect_geom)
            # since the original feature is of interest add it's fields and
            # values to the new feature from the intersecting geometries
            for fld_index2 in range(output_feature.GetFieldCount()):
                orig_field_value = orig_feat.GetField(fld_index2)
                output_feature.SetField(fld_index2, orig_field_value)

            output_layer.CreateFeature(output_feature)
            output_feature = None

    return output_datasource
