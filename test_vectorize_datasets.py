import cProfile
import pstats

import gdal
import numpy

from invest_natcap import raster_utils


if __name__ == '__main__':
    gdal.SetCacheMax(2**27)

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
        mask = (lulc == forest_lulc_codes[0])
        for lulc_code in forest_lulc_codes[1::]:
            mask = mask | (lulc == lulc_code)
        
        return numpy.where((lulc != lulc_nodata) & (biomass != biomass_nodata),
            mask, mask_nodata)
            
    cProfile.runctx("raster_utils.vectorize_datasets([lulc_uri, biomass_uri], mask_biomass, mask_uri, gdal.GDT_Byte, mask_nodata, cell_size, 'intersection', dataset_to_align_index=0, dataset_to_bound_index=None, aoi_uri=None, assert_datasets_projected=True, process_pool=None, vectorize_op=False, datasets_are_pre_aligned=False)", globals(), locals(), 'stats')
            
    '''raster_utils.vectorize_datasets(
        [lulc_uri, biomass_uri], mask_biomass, mask_uri, gdal.GDT_Byte,
        mask_nodata, cell_size, 'intersection', dataset_to_align_index=0,
        dataset_to_bound_index=None, aoi_uri=None,
        assert_datasets_projected=True, process_pool=None, vectorize_op=False,
        datasets_are_pre_aligned=False)'''
        
    p = pstats.Stats('stats')
    p.sort_stats('time').print_stats(20)
    p.sort_stats('cumulative').print_stats(20)
