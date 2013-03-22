import os
import logging

from osgeo import gdal

from invest_natcap import raster_utils
from invest_natcap.routing import routing_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('sediment')

def execute(args):
    execute_30(**args)

def execute_30(**args):
    """Malarial ecosystem disservice model.
    
    Keyword arguments:
    lulc_uri -- a uri to a gdal dataset specifying land cover types
    breeding_suitability_table_uri -- a uri to a csv table mapping lulc
        types to suitability values.
    dem_uri -- a uri to a gdal dataset specifying the DEM
    max_vector_flight -- a floating point number specifying the flight 
        distance of a vector from a breeding site
    population_uri -- a uri to a gdal dataset specifying population density

    returns nothing
    """

    #Sets up the intermediate and output directory structure for the workspace
    output_dir = os.path.join(args['workspace_dir'], 'output')
    if not os.path.exists(output_dir):
        LOGGER.info('creating directory %s', output_dir)
        os.makedirs(output_dir)


    LOGGER.info('calculating flow accumulation')
    flux_output_uri = os.path.join(output_dir, 'flow_accumulation.tif')
    routing_utils.flow_accumulation(args['dem_uri'], flux_output_uri)

    LOGGER.info('mapping breeding suitability to lulc')

    #Parse out the table
    lucode_table = raster_utils.get_lookup_from_csv(
        args['breeding_suitability_table_uri'], 'lucode')
    #Get a dictionary that maps lucode to suitability indexes
    lucode_to_suitability = dict(
        [(lucode, val['suitability_index']) for lucode, val in 
         lucode_table.iteritems()])
    suitability_uri = os.path.join(output_dir, 'suitability.tif')
    #and reclassify the lulc dataset
    raster_utils.reclassify_dataset_uri(
        args['lulc_uri'], lucode_to_suitability, suitability_uri, 
        gdal.GDT_Float32, -1.0, exception_flag='values_required')

