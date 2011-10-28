"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json
import timber
from osgeo import ogr
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the timber model given uri inputs of files.
    
    args - a dictionary object of arguments 
       
    args['output_dir']        - The file location where the outputs will be written
    args['timber_shp_uri']    - The shape file location
    args['plant_prod_uri']    - The DBF attribute table location
    args['market_disc_rate']  - The market discount rate as a string
    
    """    
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    filesystemencoding = sys.getfilesystemencoding()
    
    timber_shp_file = args['timber_shp_uri']
    timber_shp = ogr.Open(args['timber_shp_uri'].encode(filesystemencoding), 1)
    
    #Add the Output directory onto the given workspace
    output_source = args['output_dir']+os.sep+'Output'
    shape_copy_source = output_source + os.sep + 'plantation.shp'
    
    #Overwrite any current output if the workspace is the same
    if os.path.isfile(shape_copy_source): 
        os.remove(shape_copy_source)
        os.remove(output_source+os.sep+'plantation.dbf')
        os.remove(output_source+os.sep+'plantation.prj')
        os.remove(output_source+os.sep+'plantation.shx')
    
    #Copy the input shapefile into the designated output folder
    copy = ogr.GetDriverByName('ESRI Shapefile').\
        CopyDataSource(timber_shp, output_source)

    #OGR closes datasources this way to make sure data gets flushed properly
    timber_shp.Destroy()
    copy.Destroy()
   
    timber_shp_copy = ogr.Open(shape_copy_source.encode(filesystemencoding), 1)
    timber_layer_copy = timber_shp_copy.GetLayerByName('plantation')
    
    args = {'timber_shape_loc':timber_shp_file,
            'output_dir': output_source,
            'timber_layer_copy': timber_layer_copy,
            'plant_prod': dbf.Dbf(args['plant_prod_uri']),
            'plant_prod_loc': args['plant_prod_uri'],
            'timber_shp_copy': timber_shp_copy,
            'mdr': args['market_disc_rate']}

    timber.execute(args)

    #This is how OGR closes its datasources in python
    timber_shp_copy.Destroy()
    
    #close the pools DBF file
    args['plant_prod'].close()
    copy = None
    timber_shp = None
    timber_shp_copy = None
    timber_layer_copy = None



#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)