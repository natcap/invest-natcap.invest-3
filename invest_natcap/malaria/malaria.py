import os
import logging

from osgeo import gdal
from osgeo import osr
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
    filtered_breeding_site_uri = os.path.join(output_dir, 'filtered_breeding_site_influence.tif')
    breeding_site_influence_nodata = breeding_suitability_nodata
    #Dividing by pixel_size out so the blur is in pixels, not meters
    raster_utils.gaussian_filter_dataset_uri(
        breeding_suitability_uri, args['max_vector_flight']/float(pixel_size_out),
        filtered_breeding_site_uri, breeding_site_influence_nodata)

    #Clipping the population URI to the breeding sutability dataset
    clipped_population_uri = os.path.join(output_dir, 'clipped_population.tif')
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

