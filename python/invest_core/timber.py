"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json
import timber_core
from osgeo import ogr
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the timber model given uri inputs specified by the user guide.
    
    args - a dictionary object of arguments 
       
    args['output_dir']        - The file location where the outputs will 
                                be written (Required)
    args['timber_shape_uri']  - The shape file describing timber parcels with 
                                fields as described in the user guide (Required)
    args['attr_table_uri']    - The DBF polygon attribute table location with 
                                fields that describe polygons in timber_shape_uri (Required)
    args['market_disc_rate']  - The market discount rate as a float (Required, Default: 7)
    
    """
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    filesystemencoding = sys.getfilesystemencoding()

    timber_shape = ogr.Open(args['timber_shape_uri'].encode(filesystemencoding), 1)

    #Add the Output directory onto the given workspace
    output_dir = args['output_dir'] + os.sep + 'Output/'
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    shape_source = output_dir + 'timber.shp'

    #If there is already an existing shapefile with the same name and path, delete it
    if os.path.isfile(shape_source):
        os.remove(shape_source)

    #Copy the input shapefile into the designated output folder
    copy = ogr.GetDriverByName('ESRI Shapefile').\
        CopyDataSource(timber_shape, shape_source)

    #OGR closes datasources this way to make sure data gets flushed properly
    timber_shape.Destroy()
    copy.Destroy()

    timber_output_shape = ogr.Open(shape_source.encode(filesystemencoding), 1)

    args = {'timber_shape': timber_output_shape,
            'attr_table': dbf.Dbf(args['attr_table_uri']),
            'mdr': args['market_disc_rate']}

    timber_core.execute(args)

    #OGR closes datasources this way to make sure data gets flushed properly
    timber_output_shape.Destroy()

    #Close the polygon attribute table DBF file and wipe datasources
    args['attr_table'].close()
    copy = None
    timber_shape = None
    timber_output_shape = None

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
