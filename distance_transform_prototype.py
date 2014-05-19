"""Distance transform prototype"""

import gdal
import numpy

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
    
    input_mask_ds = gdal.Open(input_mask_uri)
    input_mask_band = input_mask_ds.GetRasterBand(1)
    input_mask_array = input_mask_band.ReadAsArray()
    
    n_cols = input_mask_ds.RasterXSize
    n_rows = input_mask_ds.RasterYSize
    
    numerical_inf = n_cols + n_rows
    
    g_array = numpy.empty(input_mask_array.shape, dtype=numpy.float)
    print g_array.shape
    print n_rows
    for col_index in xrange(n_cols):
        b_array = input_mask_array[:, col_index] == 0
        if b_array[0]:
            g_array[0, col_index] = 0.0
        else:
            g_array[0, col_index] = numerical_inf
        
        for row_index in xrange(1, n_rows):
            if b_array[0]:
                g_array[row_index, col_index] = 0.0
            else:
                g_array[row_index, col_index] = (
                    1.0 + g_array[row_index - 1, col_index])
    
        for row_index in xrange(n_rows-2, -1, -1):
            if (g_array[row_index + 1, col_index] < 
                g_array[row_index, col_index]):
                g_array[row_index, col_index] = (
                    1.0 + g_array[row_index + 1, col_index])
    
    #phase one, calculate column G(x,y)
    
    
    
    
    pass
    
    
if __name__ == '__main__':    
    input_mask_uri = 'C:/Users/rich/Documents/HabitatSuitability/output/oyster_habitat_suitability_mask.tif'
    output_mask_uri = 'dt.tif'
    distance_transform_edt(input_mask_uri, output_mask_uri)