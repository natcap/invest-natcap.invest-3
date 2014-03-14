cimport numpy
import numpy
cimport cython
from libcpp.map cimport map

from osgeo import gdal

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
        dataset_band.ReadAsArray(
            0, row, output_band.XSize, 1, buf_obj=dataset_array)
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


def _cython_calculate_slope(dem_dataset_uri, slope_uri):
    """Generates raster maps of slope.  Follows the algorithm described here:
        http://webhelp.esri.com/arcgiSDEsktop/9.3/index.cfm?TopicName=How%20Slope%20works 
        and generates a slope dataset as a percent
        
        dem_dataset_uri - (input) a URI to a  single band raster of z values.
        slope_uri - (input) a path to the output slope uri in percent.

        returns nothing"""

    #Read the DEM directly into an array
    cdef float a,b,c,d,e,f,g,h,i,dem_nodata
    cdef int row_index, col_index, n_rows, n_cols

    dem_dataset = gdal.Open(dem_dataset_uri)
    dem_band = dem_dataset.GetRasterBand(1)
    dem_nodata = dem_band.GetNoDataValue()

    slope_dataset = gdal.Open(slope_uri, gdal.GA_Update)
    slope_band = slope_dataset.GetRasterBand(1)
    slope_nodata = slope_band.GetNoDataValue()

    gt = dem_dataset.GetGeoTransform()
    cdef float cell_size_times_8 = gt[1] * 8

    n_rows = dem_band.YSize
    n_cols = dem_band.XSize

    cdef numpy.ndarray[numpy.float_t, ndim=2] dem_array = numpy.empty((3, n_cols))
    cdef numpy.ndarray[numpy.float_t, ndim=2] slope_array = numpy.empty((1, n_cols))

    #Fill the top and bottom row of the slope since we won't touch it in this loop
    slope_array[0, :] = slope_nodata
    slope_band.WriteArray(slope_array, 0, 0)
    slope_band.WriteArray(slope_array, 0, n_rows - 1)
    
    cdef numpy.ndarray[numpy.float_t, ndim=2] dzdx = numpy.empty((1, n_cols))
    cdef numpy.ndarray[numpy.float_t, ndim=2] dzdy = numpy.empty((1, n_cols))
    
    for row_index in xrange(1, n_rows - 1):
        #Loop through the dataset 3 rows at a time
        dem_array = dem_band.ReadAsArray(0, row_index - 1, n_cols, 3, buf_obj=dem_array)
        slope_array[0, :] = slope_nodata
        dzdx[:] = slope_nodata
        dzdy[:] = slope_nodata
        for col_index in xrange(1, n_cols - 1):
            # abc
            # def
            # ghi

            a = dem_array[0, col_index - 1]
            if a == dem_nodata: continue
            b = dem_array[0, col_index]
            if b == dem_nodata: continue
            c = dem_array[0, col_index + 1]
            if c == dem_nodata: continue
            d = dem_array[1, col_index - 1]
            if d == dem_nodata: continue
            e = dem_array[1, col_index]
            if e == dem_nodata: continue
            f = dem_array[1, col_index + 1]
            if f == dem_nodata: continue
            g = dem_array[2, col_index - 1]
            if g == dem_nodata: continue
            h = dem_array[2, col_index]
            if h == dem_nodata: continue
            i = dem_array[2, col_index + 1]
            if i == dem_nodata: continue

            dzdx[0, col_index] = ((c+2*f+i) - (a+2*d+g)) / (cell_size_times_8)
            dzdy[0, col_index] = ((g+2*h+i) - (a+2*b+c)) / (cell_size_times_8)
            #output in terms of percent
        
        slope_array[:] = numpy.where(dzdx != slope_nodata, numpy.tan(numpy.arctan(numpy.sqrt(dzdx**2 + dzdy**2))) * 100, slope_nodata)
        slope_band.WriteArray(slope_array, 0, row_index)
