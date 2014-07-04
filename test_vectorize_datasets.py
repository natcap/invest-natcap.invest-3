import cProfile
import pstats
import sys

import gdal
import numpy

from invest_natcap import raster_utils


if __name__ == '__main__':
    
    lulc_uri = "C:\\Users\\rich\\Desktop\\am.tif"
    biomass_uri = "C:\\Users\\rich\\Desktop\\am_biov2ct1.tif"
    
    lulc_nodata = raster_utils.get_nodata_from_uri(
        lulc_uri)
    biomass_nodata = raster_utils.get_nodata_from_uri(
        biomass_uri)
    forest_lulc_codes = [1, 2, 3, 4, 5]
    
    mask_uri = "C:\\Users\\rich\\Desktop\\mask.tif"
    mask_nodata = 2
    cell_size = raster_utils.get_cell_size_from_uri(lulc_uri)
    
    def mask_biomass(lulc, biomass):
        mask = numpy.zeros(lulc.shape, dtype=numpy.int8)
        for lulc_code in forest_lulc_codes:
            mask[lulc == lulc_code] = 1
        mask[lulc == lulc_nodata] = mask_nodata
        return mask
        
    raster_utils.vectorize_datasets(
        [lulc_uri, biomass_uri], mask_biomass, mask_uri, gdal.GDT_Byte,
        mask_nodata, cell_size, 'intersection', dataset_to_align_index=0,
        dataset_to_bound_index=None, aoi_uri=None,
        assert_datasets_projected=True, process_pool=None, vectorize_op=False,
        datasets_are_pre_aligned=True)
    sys.exit(1)
    
    forest_edge_distance_uri = "C:\\Users\\rich\\Desktop\\forest_edge.tif"
    cProfile.runctx("raster_utils.distance_transform_edt(mask_uri, forest_edge_distance_uri)", globals(), locals(), 'stats')

    '''subregion_project_uri = "C:\\Users\\rich\\Desktop\\subregion_project.tif"
    reclass_crop_cover_uri = "C:\\Users\\rich\\Desktop\\crop_reclass.tif"
    
    out_list = [
        "C:\\Users\\rich\\Desktop\\subregion_project_align.tif",
        "C:\\Users\\rich\\Desktop\\crop_reclass_align.tif",]
    
    out_pixel_size = raster_utils.get_cell_size_from_uri(subregion_project_uri)
    
    raster_utils.align_dataset_list(
        [reclass_crop_cover_uri, subregion_project_uri],
        out_list,
        ["nearest", "nearest"], cell_size, "dataset", 0,
        dataset_to_bound_index=0)
       ''' 
    p = pstats.Stats('stats')
    p.sort_stats('time').print_stats(20)
    p.sort_stats('cumulative').print_stats(20)
