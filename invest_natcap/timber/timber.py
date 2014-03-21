"""InVEST Timber model at the "uri" level.  No separation between
    biophysical and valuation since the model is so simple."""

import sys
import os

from osgeo import ogr

import json
from invest_natcap.dbfpy import dbf
import timber_core

def execute(args):
    """This function invokes the timber model given uri inputs specified by 
        the user guide.
    
    args - a dictionary object of arguments 
       
    args['workspace_dir']     - The file location where the outputs will 
                                be written (Required)
    args['timber_shape_uri']  - The shape file describing timber parcels with 
                                fields as described in the user guide (Required)
    args['attr_table_uri']    - The DBF polygon attribute table location with 
                                fields that describe polygons in 
                                timber_shape_uri (Required)
    args['market_disc_rate']  - The market discount rate as a float
                                (Required, Default: 7)
    """
    filesystemencoding = sys.getfilesystemencoding()

    timber_shape = ogr.Open(
            args['timber_shape_uri'].encode(filesystemencoding), 1)

    #Add the Output directory onto the given workspace
    workspace_dir = args['workspace_dir'] + os.sep + 'output/'
    if not os.path.isdir(workspace_dir):
        os.makedirs(workspace_dir)

    #CopyDataSource expects a python string, yet some versions of json load a 
    #'unicode' object from the dumped command line arguments.  The cast to a 
    #python string here should ensure we are able to proceed.
    shape_source = str(workspace_dir + 'timber.shp')

    #If there is already an existing shapefile with the same name 
    #and path, delete it
    if os.path.isfile(shape_source):
        os.remove(shape_source)

    #Copy the input shapefile into the designated output folder
    driver = ogr.GetDriverByName('ESRI Shapefile')
    copy = driver.CopyDataSource(timber_shape, shape_source)

    #OGR closes datasources this way to make sure data gets flushed properly
    timber_shape.Destroy()
    copy.Destroy()

    timber_output_shape = ogr.Open(shape_source.encode(filesystemencoding), 1)


    args = {'timber_shape': timber_output_shape,
            #Making readOnly because dbf will not be written to
            'attr_table': dbf.Dbf(args['attr_table_uri'], readOnly = True),
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
