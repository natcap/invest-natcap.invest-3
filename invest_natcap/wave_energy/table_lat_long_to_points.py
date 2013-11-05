import csv
from osgeo import ogr
from osgeo import osr
import os
import sys

def create_wave_point_ds(wave_point_data_uri, layer_name, output_uri):
    """Creates a point shapefile from a dictionary. The point shapefile created
        is not projected and uses latitude and longitude for its geometry.
        
        wave_point_data_uri - a URI to a commas separated file of wave point data
        
        layer_name - a python string for the name of the layer
        
        output_uri - a uri for the output path of the point shapefile

        return - Nothing"""
    
    dict_data = {}

    point_file = open(wave_point_data_uri)

    reader = csv.DictReader(point_file)
    #reader.fieldnames = [f.lower() for f in reader.fieldnames]
    int_list = ['ID', 'I', 'J']

    for row in reader:
        for k,v in row.iteritems():
            if k != int_list:
                row[k] = float(v)
            else:
                row[k] = int(v)
        dict_data[row['ID']] = row
    
    # If the output_uri exists delete it
    if os.path.isfile(output_uri):
        os.remove(output_uri)
    elif os.path.isdir(output_uri):
        shutil.rmtree(output_uri)

    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_datasource = output_driver.CreateDataSource(output_uri)

    # Set the spatial reference to WGS84 (lat/long)
    source_sr = osr.SpatialReference()
    source_sr.SetWellKnownGeogCS("WGS84")
   
    output_layer = output_datasource.CreateLayer(
            layer_name, source_sr, ogr.wkbPoint)

    # Outer unique keys
    outer_keys = dict_data.keys()
    
    # Construct a list of fields to add from the keys of the inner dictionary
    field_list = dict_data[outer_keys[0]].keys()
    
    # Create a dictionary to store what variable types the fields are
    type_dict = {}
    for field in field_list:
        # Get a value from the field
        val = dict_data[outer_keys[0]][field]
        # Check to see if the value is a String of characters or a number. This
        # will determine the type of field created in the shapefile
        if isinstance(val, str):
            type_dict[field] = 'str'
        else:
            type_dict[field] = 'number'

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

    # For each inner dictionary (for each point) create a point and set its
    # fields
    for point_dict in dict_data.itervalues():
        latitude = float(point_dict['LATI'])
        longitude = float(point_dict['LONG'])

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

wave_point_data_uri = sys.argv[1]
out_uri = sys.argv[2]
create_wave_point_ds(wave_point_data_uri, 'layer', out_uri)

