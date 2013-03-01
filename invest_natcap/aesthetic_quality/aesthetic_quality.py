
from osgeo import gdal
from invest_natcap import raster_utils


def execute(args):
    """DOCSTRING"""
    raster_utils.viewshed(
        dem_uri, shapefile_uri, z_factor, curvature_correction,
        refractivity_coefficient, visible_feature_count_uri)


    pop_uri = ''

    nodata_pop = raster_utils.get_nodata_from_uri(pop_uri)
    nodata_visible_feature_count = raster_utils.get_nodata_from_uri(visible_feature_count_uri)
    nodata_masked_pop = -1
    masked_pop_uri = ''
    out_pixel_size = raster_utils.get_cell_size_from_uri(args['dem_uri'])
    def mask_pop_by_view(pop, view):
        if pop == nodata_pop or view == nodata_visible_feature_count:
            return nodata_masked_pop
        if view > 0:
            return pop
        return 0
    raster_utils.vectorize_datasets(
        [pop_uri, visible_feature_count_uri], mask_pop_by_view, masked_pop_uri,
        gdal.GDT_Float32, nodata_masked_op, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=args['aoi_uri'])
