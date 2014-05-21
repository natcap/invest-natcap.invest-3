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
   
    projection = input_mask_ds.GetProjection()
    geotransform = input_mask_ds.GetGeoTransform()
    driver = gdal.GetDriverByName('GTiff')
    output_raster = driver.Create(
        output_distance_uri.encode('utf-8'), n_cols, n_rows, 1, gdal.GDT_Float32,
        options=['COMPRESS=LZW', 'BIGTIFF=YES'])
    output_raster.SetProjection(projection)
    output_raster.SetGeoTransform(geotransform)
    output_band = output_raster.GetRasterBand(1)
    output_band.SetNoDataValue(-1)
    
    numerical_inf = n_cols + n_rows
    
    g_array = numpy.empty(input_mask_array.shape, dtype=numpy.int)
    print g_array.shape
    print n_rows
    print 'phase 1'
    #phase one, calculate column G(x,y)
    for col_index in xrange(n_cols):
        b_array = input_mask_array[:, col_index] == 0
        if b_array[0]:
            g_array[0, col_index] = 0
        else:
            g_array[0, col_index] = numerical_inf
        
        for row_index in xrange(1, n_rows):
            if b_array[row_index]:
                g_array[row_index, col_index] = 0.0
            else:
                g_array[row_index, col_index] = (
                    1 + g_array[row_index - 1, col_index])
    
        for row_index in xrange(n_rows-2, -1, -1):
            if (g_array[row_index + 1, col_index] < 
                g_array[row_index, col_index]):
                g_array[row_index, col_index] = (
                    1 + g_array[row_index + 1, col_index])
    
    #phase 2
    print 'phase 2'
    
    dt = numpy.zeros(input_mask_array.shape)
    for row_index in xrange(n_rows):
    
        def f(x, i):
            return (x - i)**2 + g_array[row_index, i]**2
        
        def sep(i, u):
            return (u**2 - i**2 + g_array[row_index, u]**2 - g_array[row_index, i]**2) / (2 * (u - i))
            
        q_index = 0
        s_array = numpy.zeros(n_cols)
        t_array = numpy.zeros(n_cols)
        for u_index in xrange(1, n_cols):
            while q_index >= 0 and f(t_array[q_index], s_array[q_index]) > f(t_array[q_index], u_index):
                q_index -= 1
            if q_index < 0:
               q_index = 0
               s_array[0] = u_index
            else:
                w = 1 + sep(s_array[q_index], u_index)
                if w < n_cols:
                    q_index += 1
                    s_array[q_index] = u_index
                    t_array[q_index] = w
        
        for u_index in xrange(n_cols-1, -1, -1):
            dt[row_index, u_index] = f(u_index, s_array[q_index])
            if u_index == t_array[q_index]:
                q_index -= 1
    
    output_band.WriteArray(dt)
    
if __name__ == '__main__':    
    input_mask_uri = 'C:/Users/rich/Documents/HabitatSuitability/output/oyster_habitat_suitability_mask.tif'
    output_mask_uri = 'dt.tif'
    distance_transform_edt(input_mask_uri, output_mask_uri)