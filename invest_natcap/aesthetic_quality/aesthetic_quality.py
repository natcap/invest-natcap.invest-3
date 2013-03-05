import os
from osgeo import gdal
from invest_natcap import raster_utils
import logging

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('aesthetic_quality')

def execute(args):
    """DOCSTRING"""
    LOGGER.info("Start Aesthetic Quality Model")

    #create copy of args
    aq_args=args.copy()

    #validate input
    dem_cell_size=raster_utils.get_cell_size_from_uri(args['dem_uri'])
    LOGGER.debug("DEM cell size: %f" % dem_cell_size)
    if aq_args['cellSize'] < dem_cell_size:
        raise ValueError, "The cell size cannot be downsampled below %f" % dem_cell_size

    #local variables
    if aq_args['workspace_dir'][-1]!=os.sep:
        aq_args['workspace_dir']=aq_args['workspace_dir']+os.sep

    z_factor=1
    curvature_correction=aq_args['refraction']
    
    visible_feature_count_uri=aq_args['workspace_dir']+"vshed"
        
    #calculate viewshed
    LOGGER.debug("Starting viewshed analysis.")
    raster_utils.viewshed(aq_args['dem_uri'],
                          aq_args['aoi_uri'],
                          z_factor,
                          curvature_correction,
                          aq_args['refraction'],
                          aq_args['structure_uri'])

    #rank viewshed
    LOGGER.debug("Ranking viewshed.")
    
    #find areas with no data for population
    LOGGER.debug("Tabulating population impact.")
    nodata_pop = raster_utils.get_nodata_from_uri(aq_args["pop_uri"])
    nodata_visible_feature_count = raster_utils.get_nodata_from_uri(visible_feature_count_uri)
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
                                    nodata_masked_op,
                                    aq_args['cellSize'],
                                    "intersection",
                                    dataset_to_align_index=0,
                                    aoi_uri=args['aoi_uri'])

    #perform overlap analysis
    LOGGER.debug("Performing overlap analysis.")
