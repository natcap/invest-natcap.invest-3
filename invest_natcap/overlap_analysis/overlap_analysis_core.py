'''inVEST core module to handle all actual processing of overlap analysis data.'''

from osgeo import ogr

def execute(args):
    '''This function will take the properly formatted arguments passed to it by
    overlap_analysis.py in the args dictionary, and perform calculations using
    these data to determine the optimal areas for activities.
    
    
    
    '''
    pass
    
    
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
    lhs, rhs, ts, bs = shape.GetLayer(0).GetExtent()
    
    #Move to the intermediate file in order to create our shapefile
    os.chdir(inter_dir)
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    grid_shp = driver.CreateDataSource('gridded_shapefile.shp')
    layer = grid_shp.CreateLayer('Layer 1', spat_ref, ogr.wkbPoint)
    
    field_def = ogr.FieldDefn('ID', ogr.OFTInteger)
    layer.CreateField(field_def)
    
    xsize = abs(rhs - lhs)
    ysize = abs(ts - bs)
    
    #In order to make sure that we cover the ENTIRE area, we will have to "round up"
    #in terms of the number of squares we create. So, we need to cast the dividend to
    #a double in order to get a double out that can be rounded up if not an integer.
    num_x = math.ceil(float(xsize) / dimension)
    num_y = math.ceil(float(ysize) / dimension)
    
    #Now, loop through all potential blocks that need to be created, and add them to our
    #new shapefile. Counter just allows us to give each of the grid cells a unique
    #identifier for a value.
    counter = 1
    
    for i in range (0, num_y):
        for j in range (0, num_x):
            
            #Creating the polygon itself
            out_edge = ogr.Geometry(ogr.wkbLinearRing)
            out_edge.AddPoint(lhs + (i * dimension), ts + j * dimension)
            out_edge.AddPoint(lhs + (i+1) * dimension, ts + j * dimension)
            out_edge.AddPoint(lhs + (i * dimension), ts + (j+1) * dimension)
            out_edge.AddPoint(lhs + (i+1) * dimension, ts + (j+1) * dimension)
            out_edge.CloseRing()
            
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