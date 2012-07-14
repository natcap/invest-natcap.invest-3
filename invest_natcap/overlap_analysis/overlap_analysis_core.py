'''inVEST core module to handle all actual processing of overlap analysis data.'''
import os
import math

from osgeo import ogr
from osgeo import gdal
from invest_natcap import raster_utils

def execute(args):
    '''This function will take the properly formatted arguments passed to it by
    overlap_analysis.py in the args dictionary, and perform calculations using
    these data to determine the optimal areas for activities.
    
    Input:
        args['workspace_dir'] - The directory in which all output and intermediate
            files should be placed.
        args['zone_layer_file'] - This is the shapefile representing our area of
            interest. If 'do_grid' is true, this will be a series of square polygons
            of size 'grid_size' that span the entire bounding envelope of the AOI.
            If 'do_grid' is false, then this is a file with management zones instead
            of identical grids. 
        args['do_grid'] - This tells us whether the area of interest file that was
            being passed in was a management zone divided shapefile, or was
            pre-gridded into identical squares.
        args['grid_size'] - This is the size of 1 side of each of the square polygons
            present on 'zone_layer_file'. This can be used to set the size of the
            pixels for the intermediate rasters.
        args['overlap_files'] - A dictionary which maps the name of the shapefile
            (excluding the .shp extension) to the open datasource itself. This can
            be used directly.
        args['over_layer_dict'] - A dictionary which contains the weights of each
            of the various shapefiles included in the 'overlap_files' dictionary.
            The dictionary key is the ID number of each shapefile. This ID maps
            to a list containing the two values, with the form being as follows:
                ({ID: [inter-activity weight, buffer], ...}):    
        args['import_field']- string which corresponds to a field within the
           layers being passed in within overlap analysis directory. This is
           the intra-activity importance for each activity.
        args['hum_use_hubs_loc']- An open shapefile of major hubs of human 
            activity. This would allow you to degrade the weight of activity
            zones as they get farther away from these locations.
        args['decay']- float between 0 and 1, representing the decay of interest
           in areas as you get farther away from human hubs.
    
    Intermediate:
        Rasterized Shapefiles- For each shapefile that we passed in 'overlap_files'
            we are creating a raster with the shape burned onto a band of the same
            size as our AOI. 
        <Some Other Things>
    
    Output:
        <Insert Raster Name Here>- This is a raster output which depicts the
            unweighted frequency of activity within a gridded area or management
            zone.
        <Insert Raster Name Here>- This is a raster depicting the importance scores
            for each grid or management zone in the area of interest.
        Parameters Text File- A file created every time the model is run listing
            all variable parameters used during that run.
            
    Returns nothing.
    '''
    output_dir = os.join(args['workspace_dir'], 'Output')
    inter_dir = os.join(args['workspace_dir'], 'Intermediate')
    
    aoi_shp_layer = args['zone_layer_file'].GetLayer()
    aoi_rast_file = os.join(inter_dir, 'AOI_Raster.tif')
    #Need to figure out what to do with management zones
    aoi_raster = raster_utils.create_raster_from_vector_extents(args['grid_size'], 
                                    args['grid_size'], gdal.GDT_Int32, -1, aoi_rast_file,
                                    args['zone_layer_file'])
    aoi_band, aoi_nodata = raster_utils.extract_band_and_nodata(aoi_rast_file)
    aoi_band.Fill(aoi_nodata)
    
    gdal.RasterizeLayer(aoi_rast_file, [1], aoi_shp_layer, burn_value = [1]) 
    
def gridder(inter_dir, URI, dimension):
    '''This function will take in the URI to a shapefile, and will return an
    open shapefile that contains polygons of size dimension x dimension, and
    conforms to the bounding box of the original shape passed.
    
    Input:
        inter_dir- The intermediate directory in which our shapefile output
            can be stored.
        URI- This is the location of a shapefile that is the desired base for
            the gridded output.
        dimension- This is an int that describes the desired length and height
            for the square ("grid") polygons on the new shapefile.
            
    Returns:
        grid_shp- The URI to a .shp file that contains multiple polygons of 
        dimension x dimension size that cover the same area as the original shapes 
        in URI.
    '''
    #Get the spatial reference for the current shapefile, and pass it in as part
    #of the new shapefile that we're creating
    shape = ogr.Open(URI)
    spat_ref = shape.GetLayer().GetSpatialRef().Clone()
    lhs, rhs, ts, bs = shape.GetLayer().GetExtent()
    
    #Move to the intermediate file in order to create our shapefile
    os.chdir(inter_dir)
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    
    if os.path.exists('gridded_shapefile.shp'):
            driver.DeleteDataSource('gridded_shapefile.shp')
            
    grid_shp = driver.CreateDataSource('gridded_shapefile.shp')
    layer = grid_shp.CreateLayer('Layer 1', spat_ref, ogr.wkbPolygon)
    
    field_def = ogr.FieldDefn('ID', ogr.OFTInteger)
    layer.CreateField(field_def)
    
    xsize = abs(rhs - lhs)
    ysize = abs(ts - bs)
    
    #In order to make sure that we cover the ENTIRE area, we will have to "round up"
    #in terms of the number of squares we create. So, we need to cast the dividend to
    #a double in order to get a double out that can be rounded up if not an integer.
    num_x = int(math.ceil(float(xsize) / dimension))
    num_y = int(math.ceil(float(ysize) / dimension))
    
    #Now, loop through all potential blocks that need to be created, and add them to our
    #new shapefile. Counter just allows us to give each of the grid cells a unique
    #identifier for a value.
    counter = 0
    
    for i in range (0, num_y):
        for j in range (0, num_x):
            
            #Creating the polygon itself
            #Note, these have to be y, x (row, then column)
            out_edge = ogr.Geometry(ogr.wkbLinearRing)
            #top left
            out_edge.AddPoint(ts + j * dimension, lhs + (i * dimension))
            #bottom left
            out_edge.AddPoint(ts + (j+1) * dimension, lhs + (i * dimension))
            #bottom right
            out_edge.AddPoint(ts + (j+1) * dimension, lhs + (i+1) * dimension)
            #top right
            out_edge.AddPoint(ts + j * dimension, lhs + (i+1) * dimension)
            out_edge.CloseRings()
            
            square = ogr.Geometry(ogr.wkbPolygon)
            square.AddGeometry(out_edge)
            
            
            counter += 1
            
            #Create a feature with the geometry of our square and an ID according
            #to our counter, add it to the layer, then delete the non-essentials so we
            #don't pile them as we create new ones.
            feat_def = layer.GetLayerDefn()
            feature = ogr.Feature(feat_def)
            feature.SetGeometry(square)
            feature.SetField('ID', counter)
            
            layer.CreateFeature(feature)
            
            square.Destroy()
            feature.Destroy()
    
    #Want to return the location of our new shapefile. Need to know the name of our data
    #source before we destroy it.
    file_name = os.path.join(inter_dir, grid_shp.GetName())
            
    #When done with adding all features to our file, also want to close the file. We do
    #this by calling destroy. You know, because heart attacks are fun.
    grid_shp.Destroy()
    
    return file_name