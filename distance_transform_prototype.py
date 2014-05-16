"""Distance transform prototype"""

import gdal

def distance_transform_edt(input_mask_uri, output_distance_uri):
    """Calculate the Euclidean distance transform on input_mask_uri and output
        the result into an output raster
        
        input_mask_uri - a gdal raster to calculate distance from the 0 value
            pixels
            
        output_distance_uri - will make a float raster w/ same dimensions and
            projection as input_mask_uri where all non-zero values of
            input_mask_uri are equal to the euclidean distance to the closest
            0 pixel.
            
        returns nothing"""
        
    pass
 