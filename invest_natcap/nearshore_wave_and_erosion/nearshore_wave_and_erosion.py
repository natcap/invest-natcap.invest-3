"""InVEST Nearshore Wave and Erosion model non-core."""

import os

from osgeo import gdal
from osgeo import ogr

import nearshore_wave_and_erosion_core

# TODO: Get rid of this function!!!! (in CV too)
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

    # If the file already exists remove it
    if os.path.isfile(output_uri):
        os.remove(output_uri)
    elif os.path.isdir(output_uri):
        shutil.rmtree(output_uri)

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
        output_field.SetPrecision(original_field.GetPrecision())
        output_layer.CreateField(output_field)

    # Get the feature and geometry of the aoi
    aoi_feat = aoi_layer.GetFeature(0)
    aoi_geom = aoi_feat.GetGeometryRef()

    # Iterate over each feature in original layer
    missing_geometries = 0 # Count the number of features without a geometry
    total_geometries = 0
    for orig_feat in orig_layer:
        total_geometries += 1
        # Get the geometry for the feature
        orig_geom = orig_feat.GetGeometryRef()
        if orig_geom is None:
            missing_geometries += 1 # Will report the missing geometries later
            continue
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
    # If missing geometries, report it
    if missing_geometries:
        message = 'Missing ' + str(missing_geometries) + \
        ' features out of' + str(total_geometries) + ' geometries in' + \
        output_uri
        LOGGER.warning(message)

    return output_datasource


# TODO: write a unit test for this function
def adjust_shapefile_to_aoi(data_uri, aoi_uri, output_uri, \
    empty_raster_allowed = False):
    """Adjust the shapefile's data to the aoi, i.e.reproject & clip data points.
    
        Inputs:
            - data_uri: uri to the shapefile to adjust
            - aoi_uri: uir to a single polygon shapefile
            - base_path: directory where the intermediate files will be saved
            - output_uri: dataset that is clipped and/or reprojected to the 
            aoi if necessary.
            - empty_raster_allowed: boolean flag that, if False (default), 
              causes the function to break if output_uri is empty, or return 
              an empty raster otherwise.

        Returns: output_uri
    """
    # Data and aoi are the same URIs, data is good as it is, return it.
    if data_uri == aoi_uri:
        return data_uri
    # Split the path apart from the filename
    head, tail = os.path.split(output_uri)
    # Split the file basename from the file extension
    base, _ = os.path.splitext(tail)
    # Open URIs and get the projections
    data = ogr.Open(data_uri)
    message = "OGR Can't open " + data_uri
    assert data is not None, message
    aoi = ogr.Open(aoi_uri)
    data_wkt = shapefile_wkt(data)
    aoi_wkt = shapefile_wkt(aoi)

    if projections_match([data_wkt, aoi_wkt]):
        # Same projections, just clip
        clip_datasource(aoi, data, output_uri)
    else:    
        # Reproject the aoi to be in data's projection
        projected_aoi_uri = os.path.join(head, base + '_projected_aoi')
        # TODO: include this in raster utils
        # Removing output_uri if it already exists
        if os.path.isdir(projected_aoi_uri):
            shutil.rmtree(projected_aoi_uri)
        raster_utils.reproject_datasource(aoi, data_wkt, projected_aoi_uri)
        # Clip all the shapes outside the aoi
        out_uri = os.path.join(head, base + '_clipped')
        clip_datasource(ogr.Open(projected_aoi_uri), data, out_uri)
        # Convert the datasource back to the original projection (aoi's)
        # TODO: include this in raster utils
        # Removing output_uri if it already exists
        if os.path.isdir(output_uri):
            shutil.rmtree(output_uri)
        raster_utils.reproject_datasource(ogr.Open(out_uri), aoi_wkt, \
        output_uri)
    # Ensure the resulting file's 1st layer is not empty
    out_shapefile = ogr.Open(output_uri)
    out_layer = out_shapefile.GetLayer(0)
    out_feature_count = out_layer.GetFeatureCount()
    out_layer = None
    out_shapefile = None
    # Break if returning an empty raster is not allowed
    if not empty_raster_allowed:
        message = 'Error: first layer of ' + output_uri + ' is empty. Are ' + \
        data_uri + ' and ' + aoi_uri + ' mis-aligned?'
        assert out_feature_count > 0, message
    return output_uri

# TODO: write a unit test for this function
def raster_from_shapefile_uri(shapefile_uri, aoi_uri, cell_size, output_uri, \
    field=None, all_touched=False, nodata = 0., datatype = gdal.GDT_Float32):
    """Burn default or user-defined data from a shapefile on a raster.

        Inputs:
            - shapefile: the dataset to be discretized
            - aoi_uri: URI to an AOI shapefile
            - cell_size: coarseness of the discretization (in meters)
            - output_uri: uri where the raster will be saved
            - field: optional field name (string) where to extract the data 
                from.
            - all_touched: optional boolean that indicates if we use GDAL's
              ALL_TOUCHED parameter when rasterizing.

        Output: A shapefile where:
            If field is specified, the field data is used as burn value.
            If field is not specified, then:
                - shapes on the first layer are encoded as 1s
                - the rest is encoded as 0"""
    shapefile = ogr.Open(shapefile_uri)
    message = "Can't open shapefile " + shapefile_uri
    assert shapefile, message
    if aoi_uri == shapefile_uri:
        aoi = shapefile
    else:
        aoi = ogr.Open(aoi_uri)
    # Create the raster that will contain the new data
    raster = \
        raster_utils.create_raster_from_vector_extents(cell_size, 
        cell_size, datatype, raster_utils.gdal_cast(nodata, datatype), \
        output_uri, aoi)
    layer = shapefile.GetLayer(0)
    # Add the all_touched option
    options = ['ALL_TOUCHED='+str(all_touched).upper()]
    if field:
        # Burn the data in 'field' to a raster
        layer_id, _ = \
        get_layer_and_index_from_field_name(field, shapefile)
        layer = shapefile.GetLayer(layer_id)
        options = ['ATTRIBUTE='+field] + options
        gdal.RasterizeLayer(raster, [1], layer, options = options)
    else:
        gdal.RasterizeLayer(raster, [1], layer, burn_values = [1], \
            options = options)
    return output_uri 
    
def preprocess_polygon_datasource(datasource_uri, aoi_uri, cell_size, \
    output_uri, field_name = None, all_touched = False, nodata = 0., \
    empty_raster_allowed = False):
    """Function that converts a polygon shapefile to a dataset by clipping,
    reprojecting, resampling, burning, and extrapolating burnt values.
    
        Inputs:
            -datasource_uri: uri to the datasource to be pre-processed
            -aoi_uri: uri to an aoi polygon datasource that is used for
                clipping and reprojection.
            -cell_size: output dataset cell size in meters (integer)
            -output_uri: uri to the pre-processed output dataset.
            -field_name: name of the field in the attribute table to get the
            values from. If a number, use it as a constant. If Null, use 1.
            -all_touched: boolean flag used in gdal's vectorize_rasters 
            options flag
            -nodata: float used as nodata in the output raster
            -empty_raster_allowed: flag that allows the function to return an
            empty raster if set to True, or break if set to False. False is the
            default.
        
        Returns output_uri"""
    # Split the path apart from the filename
    head, tail = os.path.split(output_uri)
    # Split the file basename from the file extension
    base, _ = os.path.splitext(tail)
    # Insert a suffix to the file basename and glue the new path together
    aoi_adjusted_uri = os.path.join(head, base + '_aoi_adjusted')
    # Adjust the shapefile to the aoi and save the result
    aoi_adjusted_uri = \
    adjust_shapefile_to_aoi(datasource_uri, aoi_uri, aoi_adjusted_uri, \
    empty_raster_allowed)
    # Burn the adjusted file to a raster
    raster_from_shapefile_uri(aoi_adjusted_uri, aoi_uri, cell_size, \
        output_uri, field_name, all_touched, nodata)
    
    return output_uri



def execute(args):
    """This function invokes the coastal protection model given uri inputs 
        specified by the user's guide.
    
    args - a dictionary object of arguments 
       
    args['workspace_dir']     - The file location where the outputs will 
                                be written (Required)
    """

    # Add the Output directory onto the given workspace
    workspace_dir = os.path.join(args['workspace_dir'], 'output')
    if not os.path.isdir(workspace_dir):
        os.makedirs(workspace_dir)
    # Add the intermediate directory as well
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    if not os.path.isdir(intermediate_dir):
        os.makedirs(intermediate_dir)

    # Preprocess the landmass
    

    nearshore_wave_and_erosion_core.execute(args)


#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
