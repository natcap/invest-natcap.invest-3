"""InVEST Timber model validator.  Checks that arguments to timber module
    make sense.."""

import imp, sys, os
import osgeo
from osgeo import ogr
import numpy
from dbfpy import dbf

def execute(args, out):
    """This function invokes the timber model given uri inputs specified by 
        the user guide.
    
    args - a dictionary object of arguments 
       
    args['output_dir']        - The file location where the outputs will 
                                be written (Required)
    args['timber_shape_uri']  - The shape file describing timber parcels with 
                                fields as described in the user guide (Required)
    args['attr_table_uri']    - The DBF polygon attribute table location with 
                                fields that describe polygons in timber_shape_uri (Required)
    args['market_disc_rate']  - The market discount rate as a float (Required, 
                                Default: 7)
                                
    out - A reference to a list whose elements are textual messages meant for
        human readability about any invalid states in the input parameters.
        Whatever elements are in `out` prior to the call will be removed.
        (required)
    """

    #Initalize out to be an empty list
    out[:] = []

    #Ensure that all arguments exist
    for argument in ['output_dir', 'timber_shape_uri', 'attr_table_uri',
                     'market_disc_rate']:
        if argument not in args:
            out.append('Missing parameter: ' + argument)

    #Ensure that arguments that are URIs are accessable

    #verify that the output directory parameter is indeed a folder
    #only returns true if args['output_dir'] exists and is a folder.
    prefix = 'Output folder: ' + args['output_dir']
    if not os.path.isdir(args['output_dir']):
        out.append(prefix + ' not found or is not a folder.')
    else:
        #Determine if output dir is writable
        if not os.access(args['output_dir'], os.W_OK):
            out.append(prefix + ' must be writeable.')
    
    #verify that the timber shape file exists
    #if it does, try to open it with OGR.
    prefix = 'Managed area map: ' + args['timber_shape_uri']
    filesystemencoding = sys.getfilesystemencoding()
    if not os.path.exists(args['timber_shape_uri']):
        out.append(prefix + ' could not be found')
        shape = None
    else:
        shape = ogr.Open(args['timber_shape_uri'].encode(filesystemencoding), 1)
        if not isinstance(shape, osgeo.ogr.DataSource):
            out.append(prefix + ' is not a shapefile compatible with OGR.')
            layer = None
        else:
            layer = shape.GetLayerByName('plantation')
            if not isinstance(layer, osgeo.ogr.Layer):
                out.append(prefix + ': target layer must be titled \'plantation\'')
            
    #verify that the attribute table exists and can be opened by DBFpy
    prefix = 'Plantation production table ' + args['attr_table_uri'] 
    if not os.path.exists(args['attr_table_uri']):
        out.append(prefix + ' does not exist')
        dbfFile = None
    else:
        dbfFile = dbf.Dbf(args['attr_table_uri'])
        if not isinstance(dbfFile, dbf.Dbf):
            out.append(prefix + ' must be a dbf file')
 

    #Search for inconsistencies in timber shape file
    #ids in shape file must also exist in attr_table
    
    #only check the existence of ids if both the shapefile and the dbf exist.
    if layer != None and dbfFile != None:
        for feature in layer:
            parcel_index = feature.GetFieldIndex('Parcl_ID')
            foundIndex = False
            for i in range(dbfFile.recordCount):
                if dbfFile[i]['Parcel_ID'] == parcel_index:
                    foundIndex = True
                    break
        if foundIndex == False:
            out.append('Parcel ID ' + parcel_index + 'not found\
in plantation production table')
        

    #Search for inconsistencies in attr_table
    #Freq_harv <= T

    #Inconsistencies in market discount rate > 0, 

#    out.append('this is a test error message from timber_validator')
