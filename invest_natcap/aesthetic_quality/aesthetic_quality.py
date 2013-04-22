import os
from osgeo import gdal, ogr
gdal.UseExceptions()
from invest_natcap import raster_utils

import logging

import scipy.stats

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('aesthetic_quality')

def reclassify_quantile_dataset_uri(dataset_uri, quantile_list, dataset_out_uri, datatype_out, nodata_out):
    nodata_ds = raster_utils.get_nodata_from_uri(dataset_uri)

    memory_file_uri = raster_utils.temporary_filename()
    memory_array = raster_utils.load_memory_mapped_array(dataset_uri, memory_file_uri)

    quantile_breaks = [0]
    for quantile in quantile_list:
        quantile_breaks.append(scipy.stats.scoreatpercentile(memory_array, quantile))

    def reclass(value):
        if value == nodata_ds:
            return nodata_out
        else:
            for new_value,quantile_break in enumerate(quantile_breaks):
                if value <= quantile_break:
                    return new_value
        raise ValueError, "Value was not within quantiles."

    cell_size = raster_utils.get_cell_size_from_uri(dataset_uri)
    
    raster_utils.vectorize_datasets([dataset_uri],
                                    reclass,
                                    dataset_out_uri,
                                    datatype_out,
                                    nodata_out,
                                    cell_size,
                                    "union",
                                    dataset_to_align_index=0)

def execute(args):
    """DOCSTRING"""
    LOGGER.info("Start Aesthetic Quality Model")

    #create copy of args
    aq_args=args.copy()

    #validate input
    LOGGER.debug("Validating parameters.")
    dem_cell_size=raster_utils.get_cell_size_from_uri(args['dem_uri'])
    LOGGER.debug("DEM cell size: %f" % dem_cell_size)
    if aq_args['cellSize'] < dem_cell_size:
        raise ValueError, "The cell size cannot be downsampled below %f" % dem_cell_size

    if not os.path.isdir(args['workspace_dir']):
        os.makedirs(args['workspace_dir'])

    #local variables
    LOGGER.debug("Setting local variables.")
    z_factor=1
    curvature_correction=aq_args['refraction']

    aoi_prj_uri=os.path.join(aq_args['workspace_dir'],"aoi_prj.shp")
    visible_feature_count_uri=os.path.join(aq_args['workspace_dir'],"vshed.tif")
    visible_feature_quality_uri=os.path.join(aq_args['workspace_dir'],"vshed_qual.tif")
##    viewshed_dem_uri=os.path.join(aq_args['workspace_dir'],"dem_vs.tif")

    #clip DEM to AOI
    LOGGER.debug("Start clip DEM by AOI.")

    LOGGER.debug("Reprojecting AOI to match DEM projection.")

    dem=gdal.Open(aq_args['dem_uri'])    
    projection = dem.GetProjection()
    aoi=ogr.Open(aq_args['aoi_uri'])
    raster_utils.reproject_datasource(aoi, projection, aoi_prj_uri)
    aoi=None
    
##    LOGGER.debug("Clip DEM by reprojected AOI.")
##    aoi_prj=ogr.Open(aoi_prj_uri)
##    raster_utils.clip_dataset(dem, aoi_prj, viewshed_dem_uri)
##    dem=None
##    aoi_prj=None
    

    #portions of the DEM that are below sea-level are converted to a value of "0"
    LOGGER.debug("Reclass DEM.")
        
    #calculate viewshed
    LOGGER.debug("Start viewshed analysis.")
    LOGGER.debug("Saving viewshed to: %s" % visible_feature_count_uri)
    raster_utils.viewshed(aq_args['dem_uri'],
                          aq_args['structure_uri'],
                          z_factor,
                          curvature_correction,
                          aq_args['refraction'],
                          visible_feature_count_uri,
                          aq_args['cellSize'],
                          aoi_prj_uri)

    #rank viewshed
    nodata_out = -1
    quantile_list = [25,50,75,100]
    datatype_out = gdal.GDT_Int32
    reclassify_quantile_dataset_uri(visible_feature_count_uri, quantile_list, visible_feature_quality_uri, datatype_out, nodata_out)
    
    #find areas with no data for population
    LOGGER.debug("Tabulating population impact.")
    nodata_pop = raster_utils.get_nodata_from_uri(aq_args["pop_uri"])
    LOGGER.debug("The nodata value from the population raster is: %f" % nodata_pop)
    nodata_visible_feature_count = raster_utils.get_nodata_from_uri(visible_feature_count_uri)
    LOGGER.debug("The nodata value from the viewshed raster is: %f" % nodata_visible_feature_count)
    nodata_masked_pop = 0

    masked_pop_uri = ''

    def mask_pop_by_view(pop, view):
        if pop == nodata_pop or view == nodata_visible_feature_count:
            return nodata_masked_pop
        if view > 0:
            return pop
        return 0

    raster_utils.vectorize_datasets([aq_args["pop_uri"], visible_feature_count_uri],
                                    mask_pop_by_view,
                                    masked_pop_uri,
                                    gdal.GDT_Float32,
                                    nodata_masked_pop,
                                    aq_args['cellSize'],
                                    "intersection",
                                    dataset_to_align_index=0,
                                    aoi_uri=args['aoi_uri'],
                                    assert_datasets_projected=False)

    #perform overlap analysis
    LOGGER.debug("Performing overlap analysis.")
