import os
from osgeo import gdal, ogr
from invest_natcap import raster_utils
from invest_natcap.wave_energy import wave_energy_core
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

    if not os.path.isdir(args['workspace_dir']):
        os.makedirs(args['workspace_dir'])

    #local variables
    z_factor=1
    curvature_correction=aq_args['refraction']

    aoi_prj_uri=os.path.join(aq_args['workspace_dir'],"aoi_prj.shp")
    visible_feature_count_uri=os.path.join(aq_args['workspace_dir'],"vshed.tif")
    visible_feature_quality_uri=os.path.join(aq_args['workspace_dir'],"vshed_qual.tif")
    viewshed_dem_uri=os.path.join(aq_args['workspace_dir'],"dem_vs.tif")

    #clip DEM to AOI
    dem=gdal.Open(aq_args['dem_uri'])
    aoi=ogr.Open(aq_args['aoi_uri'])
    
    projection = dem.GetProjection()
    geotransform = dem.GetGeoTransform()    

    in_defn=aoi.GetLayer(0).GetLayerDefn()
    LOGGER.debug("AOI shape type: %s" % in_defn.GetGeomType())
    shp_ds=wave_energy_core.change_shape_projection(aoi,projection,aoi_prj_uri)
    shp_ds.Destroy()
    aoi.Close()

    prj_aoi=ogr.Open(aoi_prj_uri)
    raster_utils.clip_dataset(dem, aoi, viewshed_dem_uri)

    dem.Close()
    prj_aoi.Close()
    

    #portions of the DEM that are below sea-level are converted to a value of "0"
        
    #calculate viewshed
    LOGGER.debug("Starting viewshed analysis.")
    LOGGER.debug("Saving viewshed to: %s" % visible_feature_count_uri)
    raster_utils.viewshed(viewshed_dem_uri,
                          aq_args['structure_uri'],
                          z_factor,
                          curvature_correction,
                          aq_args['refraction'],
                          visible_feature_count_uri,
                          aq_args['cellSize'],
                          aq_args['aoi_uri'])

    #rank viewshed
    visible_feature_count=gdal.Open(visible_feature_count_uri)
    units_short="m"
    units_long="meters"
    start_value="0"
    percentile_list=[25,50,75]
    nodata=-1
    LOGGER.debug("Ranking viewshed.")
    wave_energy_core.create_percentile_rasters(visible_feature_count,
                              visible_feature_quality_uri,
                              units_short,
                              units_long,
                              start_value,
                              percentile_list,
                              nodata)

    
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
                                    nodata_masked_pop,
                                    aq_args['cellSize'],
                                    "intersection",
                                    dataset_to_align_index=0,
                                    aoi_uri=args['aoi_uri'])

    #perform overlap analysis
    LOGGER.debug("Performing overlap analysis.")
