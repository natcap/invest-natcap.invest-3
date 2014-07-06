import cProfile
import pstats
import sys

import gdal
import numpy

from invest_natcap import raster_utils


if __name__ == '__main__':
    
    lulc_uri = "C:\\Users\\rich\\Desktop\\am.tif"
    #lulc_uri = "C:\\Users\\rich\\Documents\\Base_Data\\Freshwater\\landuse_90"
    '''biomass_uri = "C:\\Users\\rich\\Desktop\\am_biov2ct1.tif"'''
    '''biomass_uri = "C:\\Users\\rich\\Desktop\\am_biov2ct1.tif"'''
    
    lulc_nodata = raster_utils.get_nodata_from_uri(
        lulc_uri)
    '''biomass_nodata = raster_utils.get_nodata_from_uri(
        biomass_uri)'''
    forest_lulc_codes = [1, 2, 3, 4, 5]
    #forest_lulc_codes = [22, 23, 24, 25, 26]
    
    mask_uri = "C:\\Users\\rich\\Desktop\\mask.tif"
    mask_nodata = 2
    cell_size = raster_utils.get_cell_size_from_uri(lulc_uri)
    
    def mask_forest(lulc):
        mask = numpy.empty(lulc.shape, dtype=numpy.int8)
        mask[:] = 1
        for lulc_code in forest_lulc_codes:
            mask[lulc == lulc_code] = 0
        mask[lulc == lulc_nodata] = mask_nodata
        return mask
        
    raster_utils.vectorize_datasets(
        [lulc_uri,], mask_forest, mask_uri, gdal.GDT_Byte,
        mask_nodata, cell_size, 'intersection', dataset_to_align_index=0,
        dataset_to_bound_index=None, aoi_uri=None,
        assert_datasets_projected=True, process_pool=None, vectorize_op=False,
        datasets_are_pre_aligned=True)
    
    forest_edge_distance_uri = "C:\\Users\\rich\\Desktop\\forest_edge.tif"
    cProfile.runctx("raster_utils.distance_transform_edt(mask_uri, forest_edge_distance_uri)", globals(), locals(), 'stats')

    p = pstats.Stats('stats')
    p.sort_stats('time').print_stats(20)
    p.sort_stats('cumulative').print_stats(20)
