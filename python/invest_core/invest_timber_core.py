"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json
import timber
from osgeo import ogr
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the timber model given uri
    inputs of files.
    
    args - a dictionary object of arguments
    
    args['output_dir'] - The file location where the output will be written
    args['timber_shp_uri'] - The shape file location
    args['plant_prod_uri'] - The DBF attribute table location
    args['market_disc_rate'] - The market discount rate as a string
    """
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    filesystemencoding = sys.getfilesystemencoding()
    #ogr.AllRegister()
    timber_shp_file = args['timber_shp_uri']
    timber_shp = ogr.Open(args['timber_shp_uri'].encode(filesystemencoding), 1)
    copy = ogr.GetDriverByName('ESRI Shapefile').\
        CopyDataSource(timber_shp, args['output_dir'])
    timber_shp.Destroy()
    copy.Destroy()
    output_source = args['output_dir']+os.sep+'plantation.shp'
    timber_shp_copy = ogr.Open(output_source.encode(filesystemencoding), 1)
    
    if timber_shp_copy is None:
        print output_source
        sys.exit(1)
    timber_layer = timber_shp_copy.GetLayerByName('plantation')
    
    args = { 'timber_shape': timber_shp,
            'timber_layer': timber_layer,
            'plant_prod': dbf.Dbf(args['plant_prod_uri']),
            'timber_shp_copy': timber_shp_copy,
            'output_dir': args['output_dir'],
            'mdr': args['market_disc_rate']}

    timber.execute(args)

    #This is how GDAL closes its datasets in python
    
    output_seq = None




#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)