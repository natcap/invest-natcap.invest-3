cimport numpy
import numpy
cimport cython
from libcpp.map cimport map

@cython.boundscheck(False)
def reclassify_by_dictionary(dataset, rules, output_uri, format,
    float default_value, datatype, output_dataset):
    """Convert all the non-default values in dataset to the values mapped to
        by rules.  If there is no rule for an input value it is replaced by
        the default output value (which may or may not be the raster's nodata
        value ... it could just be any default value).

        dataset - GDAL raster dataset
        rules - a dictionary of the form:
            {'dataset_value1' : 'output_value1', ...
             'dataset_valuen' : 'output_valuen'}
             used to map dataset input types to output
        output_uri - The location to hold the output raster on disk
        format - either 'MEM' or 'GTiff'
        default_value - output raster dataset default value (may be nodata)
        datatype - a GDAL output type

        return the mapped raster as a GDAL dataset"""

    dataset_band = dataset.GetRasterBand(1)

    cdef map[float,float] lookup
    for key in rules.keys():
        lookup[float(key)] = rules[key]

    output_band = output_dataset.GetRasterBand(1)
    
    cdef int n_rows = output_band.YSize
    cdef int n_cols = output_band.XSize
    cdef numpy.ndarray[numpy.float_t, ndim=2] dataset_array = numpy.empty((1, n_cols))
    cdef float value = 0.0

    for row in range(n_rows):
        dataset_band.ReadAsArray(0,row,output_band.XSize,1, buf_obj = dataset_array)
        for col in range(n_cols):
            value = dataset_array[0,col]
            if lookup.count(value) == 1:
                dataset_array[0,col] = lookup[value]
            else:
                dataset_array[0,col] = default_value
        output_band.WriteArray(dataset_array, 0, row)
        
    output_band = None
    output_dataset.FlushCache()
    
    return output_dataset
