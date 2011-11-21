"""InVEST carbon valuation model validator.  Checks that arguments to 
    carbon_valuation make sense."""

import imp, sys, os
from osgeo import ogr
import numpy
from dbfpy import dbf
import validator_core

def execute(args, out):
    """This function invokes the timber model given uri inputs specified by 
        the user guide.
    
    args - a dictionary object of arguments 
       
    args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['sequest_uri'] - is a uri to a GDAL raster dataset describing the
            amount of carbon sequestered
        args['V'] - value of a sequestered ton of carbon in dollars per metric
            ton
        args['r'] - the market discount rate in terms of a percentage
        args['c'] - the annual rate of change in the price of carbon
        args['yr_cur'] - the year at which the sequestration measurement 
            started
        args['yr_fut'] - the year at which the sequestration measurement ended
                                
    out - A reference to a list whose elements are textual messages meant for
        human readability about any invalid states in the input parameters.
        Whatever elements are in `out` prior to the call will be removed.
        (required)
    """

    #Initialize out to be an empty list
    out[:] = []

    #Ensure that all arguments exist (all arguments are required)
    argsList = [('workspace_dir', 'Workspace'),
                ('sequest_uri' 'Carbon sequestration raster'), 
                ('V', 'Value of Carbon'), 
                ('r', 'Discount rate'), 
                ('c', 'Annual rate of change in price of Carbon'), 
                ('yr_cur', 'Start year of sequestration measurement'), 
                ('yr_fut', 'Final year of sequestration measurement')]
    validator_core.checkArgsKeys(args, argsList, out)

    #Ensure that arguments that are URIs are accessable

    #Determine of output dir is writable

    #Search for inconsistencies in timber shape file

    #Search for inconsistencies in attr_table

    #Inconsistencies in market discount rate

    out.append('this is a test error message from carbon_valuation_validator')
