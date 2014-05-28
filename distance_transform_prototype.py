import cProfile
import pstats

from invest_natcap import raster_utils

if __name__ == '__main__':    
    input_mask_uri = 'v_stream.tif'
    output_mask_uri = 'dt.tif'
    
    cProfile.run('raster_utils.distance_transform_edt(input_mask_uri, output_mask_uri)', 'stats')
    p = pstats.Stats('stats')
    p.sort_stats('time').print_stats(20)
    p.sort_stats('cumulative').print_stats(20)
