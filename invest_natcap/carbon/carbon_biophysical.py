"""InVEST Carbon biophysical module at the "uri" level"""

import sys, os

from osgeo import gdal, ogr
import json

try:
    import carbon_core
except ImportError:
    from invest_natcap.carbon import carbon_core
from invest_natcap.dbfpy import dbf
from invest_natcap import raster_utils

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

    output_dir = os.path.join(args['workspace_dir'], 'output')
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            LOGGER.info('creating directory %s', directory)
            os.makedirs(directory)

    #1) load carbon pools into dictionary indexed by LULC
    LOGGER.debug("building carbon pools")
    pools = raster_utils.get_lookup_from_table(args['carbon_pools_uri'], 'LULC')
    LOGGER.debug(pools)

    #2) map lulc_cur and _fut (if availble) to total carbon
    for lulc_uri in ['lulc_cur_uri', 'lulc_fut_uri']:
        if lulc_uri in args:
            scenario_type = lulc_uri.split('_')[-2] #get the 'cur' or 'fut'
            cell_area_ha = (
                raster_utils.get_cell_area_from_uri(args[lulc_uri]) /
                10000.0)
            LOGGER.debug('cell area %s' % cell_area_ha)

            for lulc_id, lookup_dict in pools.iteritems():
                pools[lulc_id]['total_%s' % lulc_uri] = sum(
                    [pools[lulc_id][pool_type] for pool_type in
                     ['c_above', 'c_below', 'c_soil', 'c_dead']]) * cell_area_ha
            LOGGER.debug(pools)
            nodata = raster_utils.get_nodata_from_uri(args[lulc_uri])
            nodata_out = -1.0
            def map_carbon_pool(lulc):
                if lulc == nodata:
                    return nodata_out
                return pools[lulc]['total_%s' % lulc_uri]
            dataset_out_uri = os.path.join(
                output_dir, 'tot_C_%s.tif' % scenario_type)
            pixel_size_out = raster_utils.get_cell_size_from_uri(args[lulc_uri])
            raster_utils.vectorize_datasets(
                [args[lulc_uri]], map_carbon_pool, dataset_out_uri,
                gdal.GDT_Float32, nodata_out, pixel_size_out,
                "intersection", dataset_to_align_index=0)

        #3) burn hwp_{cur/fut} into rasters


    return

    #TODO:
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
    LOGGER.debug('loading %s', args['lulc_cur_uri'])
    biophysicalArgs['lulc_cur'] = gdal.Open(str(args['lulc_cur_uri']),
                                            gdal.GA_ReadOnly)

    #a future lulc is only required if sequestering or hwp calculating
    if 'lulc_fut_uri' in args:
        LOGGER.debug('loading %s', args['lulc_fut_uri'])
        biophysicalArgs['lulc_fut'] = gdal.Open(str(args['lulc_fut_uri']),
                                            gdal.GA_ReadOnly)

    #Years and harvest shapes are required if doing HWP calculation
    for x in ['lulc_cur_year', 'lulc_fut_year']:
        if x in args: biophysicalArgs[x] = args[x]
    fsencoding = sys.getfilesystemencoding()
    for x in ['hwp_cur_shape', 'hwp_fut_shape']:
        uriName = x + '_uri'
        if uriName in args:
            LOGGER.debug('loading %s', str(args[uriName]))
            biophysicalArgs[x] = ogr.Open(str(args[uriName]).encode(fsencoding))

    #Always need carbon pools, if uncertainty calculation they also need
    #to have range columns in them, but no need to check at this level.
    LOGGER.debug('loading %s', args['carbon_pools_uri'])

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
            LOGGER.debug('creating directory %s', d)
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
        LOGGER.debug('creating output raster %s', rasterPath)
        biophysicalArgs[rasterName] = \
            raster_utils.new_raster_from_base(biophysicalArgs['lulc_cur'],
                              rasterPath, 'GTiff', -5.0, gdal.GDT_Float32)

    #run the biophysical part of the carbon model.
    LOGGER.info('starting carbon biophysical model')
    carbon_core.biophysical(biophysicalArgs)
    LOGGER.info('finished carbon biophysical model')
    
    #Dump some info about total carbon stats
#    carbon_core.calculate_summary(biophysicalArgs)

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':
    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
