from invest_natcap import raster_utils
import logging

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

    lucode_to_suitability = raster_utils.get_lookup_from_csv(
        args['breeding_suitability_table_uri'], 'lucode')
