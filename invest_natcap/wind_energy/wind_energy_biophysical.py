"""InVEST Wind Energy model file handler module"""
import os.path
import logging
import csv
import os

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap.wind_energy import wind_energy_core
import raster_utils

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
    biophysical_args['bathymetry'] = bathymetry

    aoi = ogr.Open(args['aoi_uri'])
    biophysical_args['aoi'] = aoi 

    wind_point_shape_uri = os.path.join(inter_dir, 'wind_points_shape.shp')
    wind_data = read_wind_data(args['wind_data_uri'])
    wind_data_points = wind_data_to_point_shape(
            wind_data, 'wind_data', wind_point_shape_uri)

    biophysical_args['min_depth'] = float(args['min_depth']) 
    biophysical_args['max_depth'] = float(args['max_depth'])
   
   try:
        LOGGER.debug('Distances : %s:%s',
                float(args['min_distance']), float(args['max_distance']))
        biophysical_args['min_distance'] = float(args['min_distance']) 
        biophysical_args['max_distance'] = float(args['max_distance'])
        
        land_polygon = gdal.Open(args['land_polygon_uri'])
        projected_sr = land_polygon.GetLayer().GetSpatialRef()
        projected_sr.ExportToWkt()
        wind_shape_reprojected_uri = os.path.join(
                inter_dir, 'wind_points_reprojected.shp'
        wind_data_points = raster_utils.reproject_datasource(
            wind_data_points, projected_sr, wind_shape_reprojected_uri)

        biophysical_args['land_polygon'] = gdal.Open(args['land_polygon_uri'])

    except KeyError:
        LOGGER.debug("Distance information not selected")
        pass

    
    
    biophysical_args['wind_point_shape'] = wind_data_points
    

    # handle any pre-processing that must be done

    # call on the core module
    wind_energy_core.biophysical(biophysical_args)

def read_wind_data(wind_data_uri):
    """Unpack the wind data into a dictionary

        wind_data_uri - a uri for the wind data text file

        returns - a dictionary where the keys is the row number and the values
            are dictionaries mapping column headers to values """

    wind_file = open(wind_data_uri)
    columns_line = wind_file.readline().split(',')
    wind_dict = {}
    
    for line in wind_file.readlines():
        line_array = line.split(',')
        key = line_array[0]
        wind_dict[key] = {}
        for index in range(1, len(line_array) - 1):
            wind_dict[key][columns_line[index]] = float(line_array[index])

    wind_file.close()

    LOGGER.debug(
        'wind_dict keys : %s', np.sort(np.array(wind_dict.keys()).astype(int)))
    
    return wind_dict


def wind_data_to_point_shape(dict_data, layer_name,  output_uri):
    """Given a dictionary of the wind data create a point shapefile that
        represents this data
        
        dict_data - a python dictionary with the wind data
        layer_name - the name of the layer
        output_uri - a uri for the output destination of the shapefile

        return - a OGR Datasource 
        """
    
    if os.path.isfile(output_uri):
        os.remove(output_uri)
    
    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_datasource = output_driver.CreateDataSource(output_uri)

    source_sr = osr.SpatialReference()
    source_sr.SetWellKnownGeogCS("WGS84")
    
    output_layer = output_datasource.CreateLayer(
            layer_name, source_sr, ogr.wkbPoint)

    field_list = dict_data[dict_data.keys()[0]].keys()

    for field in field_list:
        output_field = ogr.FieldDefn(field, ogr.OFTReal)   
        output_layer.CreateField(output_field)

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

    back_projected_dsource = raster_utils.reproject_datasource(
            orig_dsource, dset_wkt, back_projected_dsource_uri)

    clipped_dset = raster_utils.clip_dataset(
            orig_dset, back_projected_dsource, clipped_dset_uri)

    clipped_projected_dset = raster_utils.reproject_dataset(
            clipped_dset, out_wkt, pixel_size, dset_out_uri)

    return clipped_projected_dset

def clip_and_project_dataset_from_datasource(
        orig_dset, clip_dsource, project_dsource, dset_out_uri, inter_dir):
    """Clips and reprojects a gdal Dataset to the size and projection of the ogr
        datasources given. One of the datasources is used for the clipping while
        the other is used for the reprojecting

        orig_dset - a GDAL dataset
        clip_dsource - an OGR datasource to clip from
        projected_dsource - an OGR datasource to reproject from
        dset_out_uri - a python string for the output uri
        inter_dir - a directory path to save intermediate files to

        return - a GDAL dataset    
    """
    
    clipped_dset_uri = os.path.join(inter_dir, 'clipped_dset.tif')
    
    out_wkt = project_dsource.GetLayer().GetSpatialRef().ExportToWkt()

    clipped_dset = raster_utils.clip_dataset(
            orig_dset, clip_dsource, clipped_dset_uri)

    clipped_projected_dset = raster_utils.reproject_dataset(
            clipped_dset, out_wkt, pixel_size, dset_out_uri)

    return clipped_projected_dset


