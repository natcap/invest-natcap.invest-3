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
        grid_shp- A .shp file that contains multiple polygons of dimension x
            dimension size that cover the same area as the original shapes in
            URI.
    '''
    #Get the spatial reference for the current shapefile, and pass it in as part
    #of the new shapefile that we're creating
    shape = ogr.Open(URI)
    spat_ref = shape.GetLayer().GetSpatialRef().Clone()
    lhs, rhs, ts, bs = shape.GetLayer(0).GetExtent()
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    grid_shp = driver.CreateDataSource('gridded_shapefile.shp')
    layer = grid_shp.CreateLayer('Layer 1', spat_ref, ogr.wkbPoint)
    
    xsize = abs(rhs - lhs)
    ysize = abs(ts - bs)