"""InVEST carbon biophysical model validator.  Checks that arguments to 
    carbon_biophysical make sense."""

import imp, sys, os
import osgeo
from osgeo import ogr, gdal
import numpy
from dbfpy import dbf
import validator_core

def execute(args, out):
    """This function invokes the timber model given uri inputs specified by 
        the user guide.
    
    args - a dictionary object of arguments 
       
    args - a python dictionary with at the following possible entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['lulc_cur_uri'] - is a uri to a GDAL raster dataset (required)
        args['carbon_pools_uri'] - is a uri to a DBF dataset mapping carbon 
            storage density to the lulc classifications specified in the
            lulc rasters. (required) 
        args['lulc_fut_uri'] - is a uri to a GDAL raster dataset (optional
         if calculating sequestration)
        args['lulc_cur_year'] - An integer representing the year of lulc_cur 
            used in HWP calculation (required if args contains a 
            'hwp_cur_shape_uri', or 'hwp_fut_shape_uri' key)
        args['lulc_fut_year'] - An integer representing the year of  lulc_fut
            used in HWP calculation (required if args contains a 
            'hwp_fut_shape_uri' key)
        args['hwp_cur_shape_uri'] - Current shapefile uri for harvested wood 
            calculation (optional, include if calculating current lulc hwp) 
        args['hwp_fut_shape_uri'] - Future shapefile uri for harvested wood 
            calculation (optional, include if calculating future lulc hwp)
                                
    out - A reference to a list whose elements are textual messages meant for
        human readability about any invalid states in the input parameters.
        Whatever elements are in `out` prior to the call will be removed.
        (required)
    """

    #Initialize out to be an empty list
    out[:] = []

    #Ensure that required arguments exist
    argsList =  [('workspace_dir', 'workspace'), 
                 ('lulc_cur_uri', 'Current LULC raster'), 
                 ('carbon_pools_uri', 'Carbon pools')] 
    validator_core.checkArgsKeys(args, argsList, out)
    
    if 'hwp_cur_shape_uri' in args:
        argsList = [('lulc_fut_year', 'Year of future land cover'),
                    ('lulc_cur_year', 'Year of current land cover')]
        validator_core.checkArgsKeys(args, argsList, out)
        
    if 'hwp_fut_shape_uri' in args:
        argsList = [('lulc_fut_uri', 'Future LULC raster'), 
                    ('lulc_fut_year', 'Year of future land cover')]
        validator_core.checkArgsKeys(args, argsList, out)
        
    #Ensure that arguments that are URIs are accessable
    #verify output directory is indeed a folder and is writeable
    validator_core.checkOutputDir(args['workspace_dir'], out)

    for key, label in [('lulc_cur_uri', 'Current LULC raster '),
                       ('lulc_fut_uri', 'Future LULC raster ')]:
        if key in args:
            if not os.path.exists(args[key]):
                out.append(label + args[key] + ': file not found')
            else:
                raster = gdal.Open(args[key])
                if not isinstance(raster, osgeo.gdal.Dataset):
                    out.append(label + args[key] + ': Must be a raster dataset \
that can be opened with GDAL.')

                    
    
    #verify that the pools dbf exists and can be opened
    prefix = 'Carbon pools table ' + args['carbon_pools_uri'] 
    if not os.path.exists(args['carbon_pools_uri']):
        out.append(prefix + ' does not exist')
        dbfFile = None
    else:
        dbfFile = dbf.Dbf(args['carbon_pools_uri'])
        if not isinstance(dbfFile, dbf.Dbf):
            out.append(prefix + ' must be a dbf file')
        else:            
            #verify that the carbon pools file has all five required attributes
            for field in ['LULC', 'C_above', 'C_below', 'C_soil', 'C_dead']:
                if field.upper() not in dbfFile.fieldNames:
                    out.append(prefix + ': missing field: ' + field )


    #Search for inconsistencies in timber shape file
    #verify that all required attributes exist
    filesystemencoding = sys.getfilesystemencoding()
    for key, layername, time in [('hwp_cur_shape_uri', 'harv_samp_cur', 'Current'),
                                 ('hwp_fut_shape_uri', 'harv_samp_fut', 'Future')]:
        if key in args:
            prefix = time + ' harvested wood products:' +  args[key]
            #verify I can open the file
            if not os.path.exists(args[key]):
                out.append(prefix + ' could not be found')
            else:
                shape = ogr.Open(args[key].encode(filesystemencoding), 1)
                if not isinstance(shape, osgeo.ogr.DataSource):
                    out.append(prefix + ' is not a shapefile compatible with OGR')
                else:
                    layer = shape.GetLayerByName(layername)
                    if not isinstance(layer, osgeo.ogr.Layer):
                        out.append(prefix + ': target layer must be titled ' + layername)
                    else:
                        layer_def = layer.GetLayerDefn()
                        if layername == 'harv_samp_cur':
                            #verify that all required fields exist
                            for field in ['Cut_cur', 'Start_date', 'Freq_cur',
                                          'Decay_cur', 'C_den_cur', 'BCEF_cur']:
                                index = layer_def.GetFieldIndex(field)
                                #-1 is returned if the given field does not exist
                                if index == -1:
                                    out.append(prefix + ': field ' + field + 'must exist')
                                
                        elif layername == 'harv_samp_fut':
                            #verify that all required fields exist
                            for field in ['Cut_fut', 'Freq_fut', 'Decay_fut',
                                          'C_den_fut', 'BCEF_fut']:
                                index = layer_def.GetFieldIndex(field)
                                #-1 is returned if the given field does not exist
                                if index == -1:
                                    out.append(prefix + ': field ' + field + 'must exist')
                            pass
    
    #verify that current year < future year
    if args['lulc_cur_year'] > args['lulc_fut_year']:
        out.append('Current year: ' + str(args['lulc_cur_year']) + ' must be '
                    + 'less than the future year: ' + str(args['lulc_fut_year']))
             

    #Inconsistencies in market discount rate.
    #should be a number, either positive or negative
    #Isn't this handled sufficiently by the UI?  It isn't possible to enter a 
    #number that defies this requirement.

