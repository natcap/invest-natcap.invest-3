import cProfile
import pstats
import sys

import gdal
import numpy

from invest_natcap import raster_utils


if __name__ == '__main__':
    
    lulc_raw_uri = "C:\\Users\\rich\\Desktop\\am.tif"
    biomass_raw_uri = "C:\\Users\\rich\\Desktop\\am_biov2ct1.tif"
    
    cell_size = raster_utils.get_cell_size_from_uri(lulc_raw_uri)
    lulc_uri = "C:\\Users\\rich\\Desktop\\lulc_aligned.tif"
    biomass_uri = "C:\\Users\\rich\\Desktop\\biomass_aligned.tif"
    
    raster_utils.align_dataset_list(
        [lulc_raw_uri, biomass_raw_uri], [lulc_uri, biomass_uri], ['nearest']*2,
        cell_size, 'intersection', 0, dataset_to_bound_index=None,
        aoi_uri=None, assert_datasets_projected=True, process_pool=None)
        
    lulc_nodata = raster_utils.get_nodata_from_uri(lulc_uri)
    biomass_nodata = raster_utils.get_nodata_from_uri(biomass_uri)
    
    forest_lulc_codes = [1, 2, 3, 4, 5]
    
    mask_uri = "C:\\Users\\rich\\Desktop\\mask.tif"
    mask_nodata = 2
    
    
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
    
    forest_edge_nodata = raster_utils.get_nodata_from_uri(forest_edge_distance_uri)
    biomass_stats_uri = "C:\\Users\\rich\\Desktop\\am.csv"
    outfile = open(biomass_stats_uri, 'w')
    
    biomass_ds = gdal.Open(biomass_uri)
    biomass_band = biomass_ds.GetRasterBand(1)
    
    forest_edge_distance_ds = gdal.Open(forest_edge_distance_uri)
    forest_edge_distance_band = forest_edge_distance_ds.GetRasterBand(1)
    
    n_rows, n_cols = raster_utils.get_row_col_from_uri(
        biomass_uri)
    for row_index in xrange(n_rows):
        print row_index, n_rows
        biomass_row = biomass_band.ReadAsArray(0, row_index, n_cols, 1)
        forest_edge_distance_row = forest_edge_distance_band.ReadAsArray(
            0, row_index, n_cols, 1)
        for col_index in xrange(n_cols):
            if forest_edge_distance_row[0, col_index] != forest_edge_nodata:
                outfile.write("%f,%f\n" % (forest_edge_distance_row[0, col_index], biomass_row[0, col_index]))
            
            
