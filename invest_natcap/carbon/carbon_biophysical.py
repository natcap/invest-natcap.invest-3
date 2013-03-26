"""InVEST Carbon biophysical module at the "uri" level"""

import sys, os

from osgeo import gdal, ogr
import json

try:
    import carbon_core
except ImportError:
    from invest_natcap.carbon import carbon_core
from invest_natcap.dbfpy import dbf
import invest_natcap.raster_utils as raster_utils

import logging
logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('carbon_biophysical')

def execute(args):
    execute_30(**args)

def execute_30(**args):
    """This function invokes the carbon model given URI inputs of files.
        It will do filehandling and open/create appropriate objects to 
        pass to the core carbon biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
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
        
        returns nothing."""

    cell_area_ha = raster_utils.get_cell_size_from_uri(args['lulc_cur_uri']) ** 2 / 10000.0
    LOGGER.debug("building carbon pools")
    pools = raster_utils.get_lookup_from_table(args['carbon_pools_uri'], 'LULC')
    LOGGER.debug(pools)
    return

    #TODO:
    #1) load carbon pools into dictionary indexed by LULC
    #2) map lulc_cur and _fut (if availble) to total carbon
    #3) burn hwp_{cur/fut} into rasters
    #4) if _fut, calculate sequestration

    inNoData = args['lulc_cur'].GetRasterBand(1).GetNoDataValue()
    outNoData = args['tot_C_cur'].GetRasterBand(1).GetNoDataValue()
    pools = build_pools_dict(args['carbon_pools'], cell_area_ha, inNoData,
                             outNoData)
    LOGGER.debug("built carbon pools")


    gdal.AllRegister()

    #Load and copy relevant inputs from args into a dictionary that
    #can be passed to the biophysical core model
    biophysicalArgs = {}

    #map lulc to carbon pool
#    nodata_carbon = -1.0
#    cur_carbon_uri = os.path.join(args['workspace_dir'], 'cur_carbon.tif')
#    raster_utils.reclassify_dataset_uri(
#        args['lulc_cur_uri'], carbon_pool_map, cur_carbon_uri, gdal.GDT_Float32,
#        nodata_carbon, exception_flag='values_required')

    #lulc_cur is always required
    logger.debug('loading %s', args['lulc_cur_uri'])
    biophysicalArgs['lulc_cur'] = gdal.Open(str(args['lulc_cur_uri']),
                                            gdal.GA_ReadOnly)

    #a future lulc is only required if sequestering or hwp calculating
    if 'lulc_fut_uri' in args:
        logger.debug('loading %s', args['lulc_fut_uri'])
        biophysicalArgs['lulc_fut'] = gdal.Open(str(args['lulc_fut_uri']),
                                            gdal.GA_ReadOnly)

    #Years and harvest shapes are required if doing HWP calculation
    for x in ['lulc_cur_year', 'lulc_fut_year']:
        if x in args: biophysicalArgs[x] = args[x]
    fsencoding = sys.getfilesystemencoding()
    for x in ['hwp_cur_shape', 'hwp_fut_shape']:
        uriName = x + '_uri'
        if uriName in args:
            logger.debug('loading %s', str(args[uriName]))
            biophysicalArgs[x] = ogr.Open(str(args[uriName]).encode(fsencoding))

    #Always need carbon pools, if uncertainty calculation they also need
    #to have range columns in them, but no need to check at this level.
    logger.debug('loading %s', args['carbon_pools_uri'])

    #setting readOnly true because we won't write to it
    biophysicalArgs['carbon_pools'] = dbf.Dbf(args['carbon_pools_uri'], 
                                              readOnly=True)

    #At this point all inputs are loaded into biophysicalArgs.  The 
    #biophysical model also needs temporary and output files to do its
    #calculation.  These are calculated next.

    #These lines sets up the output directory structure for the workspace
    outputDirectoryPrefix = args['workspace_dir'] + os.sep + 'Output' + os.sep
    intermediateDirectoryPrefix = args['workspace_dir'] + os.sep + \
        'Intermediate' + os.sep
    for d in [outputDirectoryPrefix, intermediateDirectoryPrefix]:
        if not os.path.exists(d):
            logger.debug('creating directory %s', d)
            os.makedirs(d)

    #This defines a dictionary that links output/temporary GDAL/OAL objects
    #to their locations on disk.  Helpful for creating the objects in the 
    #next step
    outputURIs = {}

    #make a list of all the rasters that we need to create, it's dependant
    #on what calculation mode we're in (sequestration, HWP, uncertainty, etc.)
    outputRasters = ['tot_C_cur']
    if 'lulc_fut_uri' in args:
        outputRasters.extend(['tot_C_fut', 'sequest'])
    #build the URIs for the output rasters in a single loop
    for key in outputRasters:
        outputURIs[key] = outputDirectoryPrefix + key + '.tif'

    intermediateRasters = ['storage_cur']

    #If we're doing a HWP calculation, we need temporary rasters to hold the
    #HWP pools, name them the same as the key but add a .tif extension
    if 'hwp_cur_shape_uri' in args:
        for key in ['c_hwp_cur', 'bio_hwp_cur', 'vol_hwp_cur']:
            outputURIs[key] = intermediateDirectoryPrefix + key + ".tif"
    if 'hwp_fut_shape_uri' in args:
        for key in ['c_hwp_fut', 'bio_hwp_fut', 'vol_hwp_fut']:
            outputURIs[key] = intermediateDirectoryPrefix + key + ".tif"

    #Create the output and intermediate rasters to be the same size/format as
    #the base LULC
    for rasterName, rasterPath in outputURIs.iteritems():
        logger.debug('creating output raster %s', rasterPath)
        biophysicalArgs[rasterName] = \
            raster_utils.new_raster_from_base(biophysicalArgs['lulc_cur'],
                              rasterPath, 'GTiff', -5.0, gdal.GDT_Float32)

    #run the biophysical part of the carbon model.
    logger.info('starting carbon biophysical model')
    carbon_core.biophysical(biophysicalArgs)
    logger.info('finished carbon biophysical model')
    
    #Dump some info about total carbon stats
#    carbon_core.calculate_summary(biophysicalArgs)

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':
    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
