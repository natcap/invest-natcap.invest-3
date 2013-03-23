import os
import logging

from osgeo import gdal
import numpy

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
    flow_threshold -- a floating point value indicating where streams 
        occur (running water)
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
    flow_accumulation_uri = os.path.join(output_dir, 'flow_accumulation.tif')
    routing_utils.flow_accumulation(args['dem_uri'], flow_accumulation_uri)

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

    LOGGER.info('calculating slope')
    slope_uri = os.path.join(output_dir, 'slope.tif')
    raster_utils.calculate_slope(args['dem_uri'], slope_uri)

    LOGGER.info('calculating breeding site suitability')
    suitability_nodata = raster_utils.get_nodata_from_uri(suitability_uri)
    flow_accumulation_nodata = raster_utils.get_nodata_from_uri(flow_accumulation_uri)
    slope_nodata = raster_utils.get_nodata_from_uri(slope_uri)
    breeding_suitability_nodata = -1.0

    def breeding_suitability_op(suitability_index, slope, flow_accumulation):
        if (suitability_index == suitability_nodata or
            slope == slope_nodata or 
            flow_accumulation == flow_accumulation_nodata):
            return breeding_suitability_nodata
        #If there's a stream, zero it out
        if flow_accumulation >= args['flow_threshold']:
            return 0.0
        return suitability_index * numpy.exp(-slope) * numpy.log(flow_accumulation)

    breeding_suitability_uri = os.path.join(output_dir, 'breeding_suitability.tif')
    pixel_size_out = raster_utils.get_cell_size_from_uri(args['lulc_uri'])
    raster_utils.vectorize_datasets(
        [suitability_uri, slope_uri, flow_accumulation_uri], 
        breeding_suitability_op, breeding_suitability_uri, gdal.GDT_Float32,
        breeding_suitability_nodata, pixel_size_out, "intersection", dataset_to_align_index=0)


    LOGGER.info('calculating breeding site influence')
    breeding_site_influence_uri = os.path.join(
        output_dir, 'breeding_site_influence.tif')
    breeding_site_influence_nodata = breeding_suitability_nodata
    #Dividing by pixel_size out so the blur is in pixels, not meters
    raster_utils.gaussian_filter_dataset_uri(
        breeding_suitability_uri, args['max_vector_flight']/float(pixel_size_out),
        breeding_site_influence_uri, breeding_site_influence_nodata)

