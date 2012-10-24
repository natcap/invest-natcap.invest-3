"""InVEST valuation interface module.  Informally known as the URI level."""

import sys
import os
import logging

import json
from osgeo import gdal

import invest_cython_core
from invest_natcap.carbon import carbon_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
logger = logging.getLogger('carbon_valuation')

def execute(args):
    """This function calculates carbon sequestration valuation.
        
        args - a python dictionary with at the following *required* entries:
        
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['sequest_uri'] - is a uri to a GDAL raster dataset describing the
            amount of carbon sequestered
        args['carbon_price_units'] - a string indicating whether the price is 
            in terms of carbon or carbon dioxide. Can value either as 
            'Carbon (C)' or 'Carbon Dioxide (CO2)'.
        args['V'] - value of a sequestered ton of carbon or carbon dioxide in 
            dollars per metric ton
        args['r'] - the market discount rate in terms of a percentage
        args['c'] - the annual rate of change in the price of carbon
        args['yr_cur'] - the year at which the sequestration measurement 
            started
        args['yr_fut'] - the year at which the sequestration measurement ended
        
        returns nothing."""

    gdal.AllRegister()

    #Load and copy relevant inputs from args into a dictionary that
    #can be passed to the valuation core model
    valuationArgs = {}

    logger.debug('loading %s', args['sequest_uri'])
    valuationArgs['sequest'] = \
        gdal.Open(args['sequest_uri'], gdal.GA_ReadOnly)

    for key in args:
        if key != 'sequest_uri':
            valuationArgs[key] = args[key]

    if args['carbon_price_units'] == 'Carbon Dioxide (CO2)':
        #Cover to price per unit of Carbon do this by dividing
        #the atomic mass of CO2 (15.9994*2+12.0107) by the atomic
        #mass of 12.0107.  Values gotten from the periodic table of
        #elements.
        args['V'] *= (15.9994*2+12.0107)/12.0107

    #These lines sets up the output directory structure for the workspace
    outputDirectoryPrefix = args['workspace_dir'] + os.sep + 'Output' + os.sep
    if not os.path.exists(outputDirectoryPrefix):
        logger.debug('creating directory %s', outputDirectoryPrefix)
        os.makedirs(outputDirectoryPrefix)

    #This defines the sequestration output raster.  Notice the 1e38 value as
    #nodata.  This is something very large that should be outside the range
    #of reasonable valuation values.
    outputURI = outputDirectoryPrefix + "value_seq.tif"

    logger.debug('creating value_seq output raster')
    valuationArgs['value_seq_uri'] = outputURI

    #run the valuation part of the carbon model.
    logger.info('starting sequestration valuation')
    carbon_core.valuation(valuationArgs)
    logger.info('completed sequestration valuation')

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
