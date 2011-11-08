"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json
import carbon
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf
import invest_core
import carbon_core

def execute(args):
    """This function calculates carbon sequestration valuation.
        
        args - a python dictionary with at the following *required* entries:
        
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
        
        returns nothing."""

    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    gdal.AllRegister()

    #Load and copy relevant inputs from args into a dictionary that
    #can be passed to the valuation core model
    valuationArgs = {}

    valuationArgs['sequest'] = \
        gdal.Open(args['sequest_uri'], gdal.GA_ReadOnly)

    for key in args:
        if key != 'sequest_uri':
            valuationArgs[key] = args[key]

    #These lines sets up the output directory structure for the workspace
    outputDirectoryPrefix = args['workspace_dir'] + os.sep + 'Output' + os.sep
    if not os.path.exists(outputDirectoryPrefix):
        os.makedirs(outputDirectoryPrefix)

    #This defines the sequestration output raster.  Notice the 1e38 value as
    #nodata.  This is something very large that should be outside the range
    #of reasonable valuation values.
    outputURI = outputDirectoryPrefix + "value_seq.tif"

    valuationArgs['value_seq'] = \
        invest_core.newRasterFromBase(valuationArgs['sequest'],
              outputURI, 'GTiff', 1e38, gdal.GDT_Float32)

    #run the valuation part of the carbon model.
    carbon_core.valuation(valuationArgs)

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
