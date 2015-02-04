import os
import logging

from osgeo import gdal
from osgeo import osr
import numpy

from invest_natcap import raster_utils
from invest_natcap.routing import routing_utils
from invest_natcap.optimization import optimization

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('sediment')

def execute(args):
    execute_30(**args)

def execute_30(**args):
    """Malarial ecosystem disservice model.
    
    Keyword arguments:
    lulc_uri -- a uri to a gdal dataset specifying land cover types
    results_suffix -- an optional string to append to the output files
    breeding_suitability_table_uri -- a uri to a csv table mapping lulc
        types to suitability values.
    dem_uri -- a uri to a gdal dataset specifying the DEM
    threshold_flow_accumulation -- a floating point value indicating where streams 
        occur (running water)
    max_vector_flight -- a floating point number specifying the flight 
        distance of a vector from a breeding site
    population_uri -- a uri to a gdal dataset specifying population density
    area_to_convert -- (optional) a floating point number indicating the
        area able to be converted in Ha

    returns nothing
    """
    area_to_convert = float(args.pop('area_to_convert', 0.0))
    max_vector_flight = float(args.pop('max_vector_flight'))
    threshold_flow_accumulation = float(args.pop('threshold_flow_accumulation'))
    results_suffix = args.pop('results_suffix', '')
    if len(results_suffix) > 0 and not results_suffix.startswith('_'):
        results_suffix = '_' + results_suffix

    #Sets up the intermediate and output directory structure for the workspace
    output_dir = os.path.join(args['workspace_dir'], 'output')
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            LOGGER.info('creating directory %s', directory)
            os.makedirs(directory)

    LOGGER.info('calculating flow accumulation')
    flow_accumulation_uri = os.path.join(intermediate_dir, 'flow_accumulation%s.tif' % results_suffix)
    routing_utils.flow_accumulation(args['dem_uri'], flow_accumulation_uri)

    LOGGER.info('mapping breeding suitability to lulc')

    #Parse out the table
    lucode_table = raster_utils.get_lookup_from_csv(
        args['breeding_suitability_table_uri'], 'lucode')
    #Get a dictionary that maps lucode to suitability indexes
    lucode_to_suitability = dict(
        [(lucode, val['suitability_index']) for lucode, val in 
         lucode_table.iteritems()])
    suitability_uri = os.path.join(intermediate_dir, 'suitability%s.tif' % results_suffix)
    #and reclassify the lulc dataset
    raster_utils.reclassify_dataset_uri(
        args['lulc_uri'], lucode_to_suitability, suitability_uri, 
        gdal.GDT_Float32, -1.0, exception_flag='values_required')

    LOGGER.info('calculating slope')
    slope_uri = os.path.join(intermediate_dir, 'slope%s.tif' % results_suffix)
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
        if flow_accumulation >= threshold_flow_accumulation:
            return 0.0
        return suitability_index * numpy.exp(-slope) * numpy.log(flow_accumulation)

    breeding_suitability_uri = os.path.join(output_dir, 'breeding_suitability%s.tif' % results_suffix)
    pixel_size_out = raster_utils.get_cell_size_from_uri(args['lulc_uri'])
    raster_utils.vectorize_datasets(
        [suitability_uri, slope_uri, flow_accumulation_uri], 
        breeding_suitability_op, breeding_suitability_uri, gdal.GDT_Float32,
        breeding_suitability_nodata, pixel_size_out, "intersection", dataset_to_align_index=0)


    LOGGER.info('calculating breeding site influence')
    breeding_site_influence_uri = os.path.join(
        output_dir, 'breeding_site_influence%s.tif' % results_suffix)
    filtered_breeding_site_uri = os.path.join(intermediate_dir, 'filtered_breeding_site_influence%s.tif' % results_suffix)
    breeding_site_influence_nodata = breeding_suitability_nodata
    #Dividing by pixel_size out so the blur is in pixels, not meters
    raster_utils.gaussian_filter_dataset_uri(
        breeding_suitability_uri, max_vector_flight/float(pixel_size_out),
        filtered_breeding_site_uri, breeding_site_influence_nodata)

    #Clipping the population URI to the breeding sutability dataset
    clipped_population_uri = os.path.join(intermediate_dir, 'clipped_population%s.tif' % results_suffix)
    reproject_and_clip_dataset_uri(
        args['population_uri'], breeding_suitability_uri, pixel_size_out, clipped_population_uri)

    population_density_nodata = raster_utils.get_nodata_from_uri(clipped_population_uri)

    def multiply_op(breeding_site, population_density):
        if (breeding_site == breeding_site_influence_nodata or
            population_density == population_density_nodata):
            return breeding_site_influence_nodata

        return breeding_site * population_density

    raster_utils.vectorize_datasets(
        [filtered_breeding_site_uri, clipped_population_uri],
        multiply_op, breeding_site_influence_uri, gdal.GDT_Float32,
        breeding_site_influence_nodata, pixel_size_out, "intersection",
        dataset_to_align_index=0)


    LOGGER.info('calculating influential breeding areas')
    
    filtered_breeding_site_influence_uri = os.path.join(intermediate_dir, 'filtered_breeding_site_influence%s.tif' % results_suffix)

    raster_utils.gaussian_filter_dataset_uri(
        breeding_site_influence_uri, max_vector_flight/float(pixel_size_out),
        filtered_breeding_site_influence_uri, breeding_site_influence_nodata)

    def multiply_breeding_op(breeding_suitability, breeding_influence):
        if (breeding_suitability == breeding_site_influence_nodata or
            breeding_influence == breeding_site_influence_nodata):
            return breeding_site_influence_nodata
        return breeding_suitability * breeding_influence
    
    influential_breeding_site_uri = os.path.join(output_dir, 'influential_breeding_site%s.tif' % results_suffix)

    raster_utils.vectorize_datasets(
        [breeding_suitability_uri, filtered_breeding_site_influence_uri],
        multiply_breeding_op, influential_breeding_site_uri, gdal.GDT_Float32,
        breeding_site_influence_nodata, pixel_size_out, "intersection",
        dataset_to_align_index=0)

    if area_to_convert > 0.0:
        area_to_convert_uri = os.path.join(output_dir, 'optimial_conversion%s.tif' % results_suffix)
        base_cell_size_in_ha = raster_utils.get_cell_size_from_uri(influential_breeding_site_uri) * 0.0001
        optimization.static_max_marginal_gain(
            influential_breeding_site_uri, area_to_convert/base_cell_size_in_ha, area_to_convert_uri, sigma=max_vector_flight/float(pixel_size_out))


def reproject_and_clip_dataset_uri(
    original_dataset_uri, base_dataset_uri, pixel_size, output_uri):

    """A function to reproject and clip a GDAL dataset

       original_dataset_uri - the uri to the original gdal dataset
       base_dataset_uri - a uri to a gdal dataset that contains the 
           desired output projection as well as the bounds
       pixel_size - output dataset pixel size in projected linear units
           in base_dataset_uri
       output_uri - uri location for output dataset"""

    original_dataset = gdal.Open(original_dataset_uri)
    original_band = original_dataset.GetRasterBand(1)
    original_sr = osr.SpatialReference(original_dataset.GetProjection())
    base_dataset = gdal.Open(base_dataset_uri)
    base_band = base_dataset.GetRasterBand(1)
    base_sr = osr.SpatialReference(base_dataset.GetProjection())

    output_dataset = raster_utils.new_raster_from_base(base_dataset, output_uri, 'GTiff', base_band.GetNoDataValue(), original_band.DataType)

    # Perform the projection/resampling 
    gdal.ReprojectImage(original_dataset, output_dataset,
                        original_sr.ExportToWkt(), base_sr.ExportToWkt(),
                        gdal.GRA_Bilinear)

