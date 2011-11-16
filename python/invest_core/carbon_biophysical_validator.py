"""InVEST carbon biophysical model validator.  Checks that arguments to 
    carbon_biophysical make sense."""

import imp, sys, os
from osgeo import ogr
import numpy
from dbfpy import dbf

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

    #Ensure that all arguments exist

    #Ensure that arguments that are URIs are accessable

    #Determine of output dir is writable

    #Search for inconsistencies in timber shape file

    #Search for inconsistencies in attr_table

    #Inconsistencies in market discount rate

    out.append('this is a test error message from carbon_bipohysical_validator')
