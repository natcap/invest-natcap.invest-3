"""InVEST Sediment biophysical module at the "uri" level"""

import sys, os
import simplejson as json
import sediment_core
import invest_core
from osgeo import gdal, ogr
from dbfpy import dbf

import logging
logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

logger = logging.getLogger('sediment_biophysical')

def execute(args):
    """This function invokes the carbon model given URI inputs of files.
        It will do filehandling and open/create appropriate objects to 
        pass to the core carbon biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at the following possible entries:
        
        returns nothing."""

    biophysicalArgs = {}
    logger.info('starting biophysical model')
    sediment_core.biophysical(biophysicalArgs)
    logger.info('finished biophysical model')

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':
    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
