import numpy 
from libcpp.map cimport map

def reclassify_by_dictionary(dataset, rules, output_uri, format, float nodata, datatype,
    output_dataset): 
    """Convert all the non-nodata values in dataset to the values mapped to 
        by rules.  If there is no rule for an input value it is replaced by
        the nodata output value.

        dataset - GDAL raster dataset
        rules - a dictionary of the form: 
            {'dataset_value1' : 'output_value1', ... 
             'dataset_valuen' : 'output_valuen'}
             used to map dataset input types to output
        output_uri - The location to hold the output raster on disk
        format - either 'MEM' or 'GTiff'
        nodata - output raster dataset nodata value
        datatype - a GDAL output type

        return the mapped raster as a GDAL dataset"""

    dataset_band = dataset.GetRasterBand(1)

    def op(x):
        try:
            return rules[x]
        except:
            return nodata

    vop = numpy.vectorize(op)

    output_band = output_dataset.GetRasterBand(1)
    
    cdef int row = 0
    cdef int n_rows = output_band.YSize 

    for row in range(n_rows):
        dataset_array = dataset_band.ReadAsArray(0,row,output_band.XSize,1)
        output_array = vop(dataset_array)
        output_band.WriteArray(output_array, 0, row)
        
    output_band = None
    output_dataset.FlushCache()
    
    return output_dataset
