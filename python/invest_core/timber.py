"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json
import timber_core
from osgeo import ogr
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the timber model given uri inputs of files.
    
    args - a dictionary object of arguments 
       
    args['output_dir']        - The file location where the outputs will be written
    args['timber_shape_uri']  - The shape file location
    args['attr_table_uri']    - The DBF polygon attribute table location
    args['market_disc_rate']  - The market discount rate as a string
    
    """    
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    filesystemencoding = sys.getfilesystemencoding()
    
    timber_shape = ogr.Open(args['timber_shape_uri'].encode(filesystemencoding), 1)
    
    #Add the Output directory onto the given workspace
    output_source = args['output_dir']+os.sep+'Output/'
    if not os.path.isdir(output_source):
        os.mkdir(output_source)
        
    shape_copy_source = output_source + 'timber.shp'
    
    #If there is already an existing shapefile with the same name and path, delete it
    if os.path.isfile(shape_copy_source): 
        os.remove(shape_copy_source)
    
    #Copy the input shapefile into the designated output folder
    copy = ogr.GetDriverByName('ESRI Shapefile').\
        CopyDataSource(timber_shape, shape_copy_source)

    #OGR closes datasources this way to make sure data gets flushed properly
    timber_shape.Destroy()
    copy.Destroy()
   
    timber_shape_copy = ogr.Open(shape_copy_source.encode(filesystemencoding), 1)
    timber_layer_copy = timber_shape_copy.GetLayerByName('timber')
    
    args = {'timber_shape_loc':args['timber_shape_uri'],
            'output_dir': output_source,
            'timber_layer_copy': timber_layer_copy,
            'attr_table': dbf.Dbf(args['attr_table_uri']),
            'attr_table_loc': args['attr_table_uri'],
            'mdr': args['market_disc_rate']}

    timber.execute(args)

    #This is how OGR closes its datasources in python
    timber_shape_copy.Destroy()
    
    #close the polygon attribute table DBF file and wipe datasources
    args['attr_table'].close()
    copy = None
    timber_shape = None
    timber_shape_copy = None
    timber_layer_copy = None



#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)