"""InVEST Sediment biophysical module at the "uri" level"""

import sys, os
#Prepend current directory to search for correct GDAL library
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder)

import simplejson as json
import sediment_core
from osgeo import gdal, ogr
import csv

import logging
logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

logger = logging.getLogger('sediment_biophysical')

def execute(args):
    """This function invokes the biophysical part of the sediment model given
        URI inputs of files. It will do filehandling and open/create
        appropriate objects to pass to the core sediment biophysical 
        processing function.  It may write log, warning, or error messages to 
        stdout.
        
        args - a python dictionary with at the following possible entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['dem_uri'] - a uri to a digital elevation raster file (required)
        args['erosivity_uri'] - a uri to an input raster describing the 
            rainfall eroisivity index (required)
        args['erodibility_uri'] - a uri to an input raster describing soil 
            erodibility (required)
        args['landuse_uri'] - a uri to a land use/land cover raster whose
            LULC indexes correspond to indexs in the biophysical table input.
            Used for determining soil retention and other biophysical 
            properties of the landscape.  (required)
        args['watersheds_uri'] - a uri to an input shapefile of the watersheds
            of interest as polygons. (required)
        args['subwatersheds_uri'] - a uri to an input shapefile of the 
            subwatersheds of interest that are contained in the
            'watersheds_uri' shape provided as input. (required)
        args['reservoir_locations_uri'] - a uri to an input shape file with 
            points indicating reservoir locations with IDs. (optional)
        args['reservoir_properties_uri'] - a uri to an input CSV table 
            describing properties of input reservoirs provided in the 
            reservoirs_uri shapefile (optional)
        args['biophysical_table_uri'] - a uri to an input CSV file with 
            biophysical information about each of the land use classes.
        args['threshold_flow_accumulation'] - an integer describing the number
            of upstream cells that must flow int a cell before it's considered
            part of a stream.  required if 'v_stream_uri' is not provided.
        args['slope_threshold'] - A percentage slope threshold as described in
            the user's guide.
            
        returns nothing."""

    #Sets up the intermediate and output directory structure for the workspace
    outputDirectoryPrefix = args['workspace_dir'] + os.sep + 'Output' + os.sep
    intermediateDirectoryPrefix = args['workspace_dir'] + os.sep + \
        'Intermediate' + os.sep
    for d in [outputDirectoryPrefix, intermediateDirectoryPrefix]:
        if not os.path.exists(d):
            logger.debug('creating directory %s', d)
            os.makedirs(d)

    logger.info('Loading data sources')

    #Load and copy relevant inputs from args into a dictionary that
    #can be passed to the biophysical core model
    biophysicalArgs = {}

    #load rasters
    for rasterName in ['dem', 'erosivity', 'erodibility', 'landuse']:
        biophysicalArgs[rasterName] = gdal.Open(args[rasterName + '_uri'],
                                                gdal.GA_ReadOnly)
        logger.debug('load %s as: %s' % (args[rasterName + '_uri'],
                                         biophysicalArgs[rasterName]))

    #load shapefiles
    for shapeFileName in ['watersheds', 'subwatersheds', 'reservoir_locations']:
        fsencoding = sys.getfilesystemencoding()
        uriName = shapeFileName + '_uri'
        if uriName in args:
            biophysicalArgs[shapeFileName] = \
                ogr.Open(args[uriName].encode(fsencoding))
            logger.debug('load %s as: %s' % (args[uriName],
                                         biophysicalArgs[shapeFileName]))

    #table
    for x, idColumnName in [('reservoir_properties', 'id'),
                            ('biophysical_table', 'lucode')]:
        try:
            uriName = x + '_uri'
            logger.debug('load %s' % args[uriName])
            file = open(args[uriName])
            csvDictReader = csv.DictReader(open(args[x + '_uri']))
            idTable = {}
            for row in csvDictReader:
                idTable[row[idColumnName]] = row
            biophysicalArgs[x] = idTable
        except IOError, e:
            #Get here if file x is not found
            logger.warning(e)

    #primatives
    for x in ['threshold_flow_accumulation', 'slope_threshold']:
        biophysicalArgs[x] = args[x]
        logger.debug('%s=%s' % (x, biophysicalArgs[x]))

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
