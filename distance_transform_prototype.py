"""Distance transform prototype"""

from invest_natcap import raster_utils

if __name__ == '__main__':    
    input_mask_uri = 'v_stream.tif'
    output_mask_uri = 'dt.tif'
    raster_utils.distance_transform_edt(input_mask_uri, output_mask_uri)
