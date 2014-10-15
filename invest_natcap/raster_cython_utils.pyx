import os
import tempfile
import logging
import time
import sys
import traceback

cimport numpy
import numpy
cimport cython
from libcpp.map cimport map

from libc.math cimport sqrt
from libc.math cimport exp
from libc.math cimport ceil

from osgeo import gdal

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('raster_cython_utils')


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
        
    dem_band = None
    slope_band = None
    gdal.Dataset.__swig_destroy__(dem_dataset)
    gdal.Dataset.__swig_destroy__(slope_dataset)
    dem_dataset = None
    slope_dataset = None
    

cdef long long _f(long long x, long long i, long long gi):
    return (x-i)*(x-i)+ gi*gi


@cython.cdivision(True)
cdef long long _sep(long long i, long long u, long long gu, long long gi):
    return (u*u - i*i + gu*gu - gi*gi) / (2*(u-i))
        
        
#@cython.boundscheck(False)
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
    cdef int n_cols = input_mask_ds.RasterXSize
    cdef int n_rows = input_mask_ds.RasterYSize
    cdef int block_size = input_mask_band.GetBlockSize()[0]
    cdef int input_nodata = input_mask_band.GetNoDataValue()

    #create a transposed g function
    file_handle, g_dataset_uri = tempfile.mkstemp()
    os.close(file_handle)
    cdef int g_nodata = -1
    
    input_projection = input_mask_ds.GetProjection()
    input_geotransform = input_mask_ds.GetGeoTransform()
    driver = gdal.GetDriverByName('GTiff')
    #invert the rows and columns since it's a transpose
    g_dataset = driver.Create(
        g_dataset_uri.encode('utf-8'), n_cols, n_rows, 1, gdal.GDT_Int32,
        options=['TILED=YES', 'BLOCKXSIZE=%d' % block_size, 'BLOCKYSIZE=%d' % block_size])
        
    g_dataset.SetProjection(input_projection)
    g_dataset.SetGeoTransform(input_geotransform)
    g_band = g_dataset.GetRasterBand(1)
    g_band.SetNoDataValue(g_nodata)
    
    cdef float output_nodata = -1.0
    output_dataset = driver.Create(
        output_distance_uri.encode('utf-8'), n_cols, n_rows, 1, 
        gdal.GDT_Float64, options=['TILED=YES', 'BLOCKXSIZE=%d' % block_size,
        'BLOCKYSIZE=%d' % block_size])
    output_dataset.SetProjection(input_projection)
    output_dataset.SetGeoTransform(input_geotransform)
    output_band = output_dataset.GetRasterBand(1)
    output_band.SetNoDataValue(output_nodata)
    
    #the euclidan distance will be less than this
    cdef int numerical_inf = n_cols + n_rows

    LOGGER.info('Distance Transform Phase 1')
    output_blocksize = output_band.GetBlockSize()
    if output_blocksize[0] != block_size or output_blocksize[1] != block_size:
        raise Exception(
            "Output blocksize should be %d,%d, instead it's %d,%d" % (
                block_size, block_size, output_blocksize[0], output_blocksize[1]))
    
    #phase one, calculate column G(x,y)
    
    cdef numpy.ndarray[numpy.int32_t, ndim=2] g_array
    cdef numpy.ndarray[numpy.uint8_t, ndim=2] b_array
    
    cdef int col_index, row_index, q_index, u_index
    cdef long long w
    cdef int n_col_blocks = int(numpy.ceil(n_cols/float(block_size)))
    cdef int col_block_index, local_col_index, win_xsize
    cdef double current_time, last_time
    last_time = time.time()
    for col_block_index in xrange(n_col_blocks):
        current_time = time.time()
        if current_time - last_time > 5.0:
            LOGGER.info(
                'Distance transform phase 1 %.2f%% complete' %
                (col_block_index/float(n_col_blocks)*100.0))
            last_time = current_time
        local_col_index = col_block_index * block_size
        if n_cols - local_col_index < block_size:
            win_xsize = n_cols - local_col_index
        else:
            win_xsize = block_size
        b_array = input_mask_band.ReadAsArray(
            xoff=local_col_index, yoff=0, win_xsize=win_xsize,
            win_ysize=n_rows)
        g_array = numpy.empty((n_rows, win_xsize), dtype=numpy.int32)

        #initalize the first element to either be infinate distance, or zero if it's a blob
        for col_index in xrange(win_xsize):
            if b_array[0, col_index] and b_array[0, col_index] != input_nodata:
                g_array[0, col_index] = 0
            else:
                g_array[0, col_index] = numerical_inf

            #pass 1 go down
            for row_index in xrange(1, n_rows):
                if b_array[row_index, col_index] and b_array[row_index, col_index] != input_nodata:
                    g_array[row_index, col_index] = 0
                else:
                    g_array[row_index, col_index] = (
                        1 + g_array[row_index - 1, col_index])

            #pass 2 come back up
            for row_index in xrange(n_rows-2, -1, -1):
                if (g_array[row_index + 1, col_index] <
                    g_array[row_index, col_index]):
                    g_array[row_index, col_index] = (
                        1 + g_array[row_index + 1, col_index])
        g_band.WriteArray(
            g_array, xoff=local_col_index, yoff=0)

    g_band.FlushCache()
    LOGGER.info('Distance Transform Phase 2')
    cdef numpy.ndarray[numpy.int64_t, ndim=2] s_array
    cdef numpy.ndarray[numpy.int64_t, ndim=2] t_array
    cdef numpy.ndarray[numpy.float64_t, ndim=2] dt
    

    cdef int n_row_blocks = int(numpy.ceil(n_rows/float(block_size)))
    cdef int row_block_index, local_row_index, win_ysize

    for row_block_index in xrange(n_row_blocks):
        current_time = time.time()
        if current_time - last_time > 5.0:
            LOGGER.info(
                'Distance transform phase 2 %.2f%% complete' %
                (row_block_index/float(n_row_blocks)*100.0))
            last_time = current_time

        local_row_index = row_block_index * block_size
        if n_rows - local_row_index < block_size:
            win_ysize = n_rows - local_row_index
        else:
            win_ysize = block_size

        g_array = g_band.ReadAsArray(
            xoff=0, yoff=local_row_index, win_xsize=n_cols,
            win_ysize=win_ysize)

        s_array = numpy.zeros((win_ysize, n_cols), dtype=numpy.int64)
        t_array = numpy.zeros((win_ysize, n_cols), dtype=numpy.int64)
        dt = numpy.empty((win_ysize, n_cols), dtype=numpy.float64)

        for row_index in xrange(win_ysize):
            q_index = 0
            s_array[row_index, 0] = 0
            t_array[row_index, 0] = 0
            for u_index in xrange(1, n_cols):
                while (q_index >= 0 and
                    _f(t_array[row_index, q_index], s_array[row_index, q_index],
                        g_array[row_index, s_array[row_index, q_index]]) >
                    _f(t_array[row_index, q_index], u_index, g_array[row_index, u_index])):
                    q_index -= 1
                if q_index < 0:
                   q_index = 0
                   s_array[row_index, 0] = u_index
                else:
                    w = 1 + _sep(
                        s_array[row_index, q_index], u_index, g_array[row_index, u_index],
                        g_array[row_index, s_array[row_index, q_index]])
                    if w < n_cols:
                        q_index += 1
                        s_array[row_index, q_index] = u_index
                        t_array[row_index, q_index] = w

            for u_index in xrange(n_cols-1, -1, -1):
                dt[row_index, u_index] = _f(
                    u_index, s_array[row_index, q_index],
                    g_array[row_index, s_array[row_index, q_index]])
                if u_index == t_array[row_index, q_index]:
                    q_index -= 1
        
        b_array = input_mask_band.ReadAsArray(
            xoff=0, yoff=local_row_index, win_xsize=n_cols,
            win_ysize=win_ysize)
        
        dt = numpy.sqrt(dt)
        dt[b_array == input_nodata] = output_nodata
        output_band.WriteArray(dt, xoff=0, yoff=local_row_index)

    input_mask_band = None
    gdal.Dataset.__swig_destroy__(input_mask_ds)
    input_mask_ds = None
    g_band = None
    gdal.Dataset.__swig_destroy__(g_dataset)
    g_dataset = None
    try:
        os.remove(g_dataset_uri)
    except OSError:
        LOGGER.warn("couldn't remove file %s" % g_dataset_uri)
        
        
def new_raster_from_base_uri(base_uri, *args, **kwargs):
    """A wrapper for the function new_raster_from_base that opens up
        the base_uri before passing it to new_raster_from_base.

        base_uri - a URI to a GDAL dataset on disk.

        All other arguments to new_raster_from_base are passed in.

        Returns nothing.
        """
    base_raster = gdal.Open(base_uri)
    if base_raster is None:
        raise IOError("%s not found when opening GDAL raster")
    new_raster = new_raster_from_base(base_raster, *args, **kwargs)

    gdal.Dataset.__swig_destroy__(new_raster)
    gdal.Dataset.__swig_destroy__(base_raster)
    new_raster = None
    base_raster = None


def new_raster_from_base(
    base, output_uri, gdal_format, nodata, datatype, fill_value=None,
    n_rows=None, n_cols=None, dataset_options=None):
    """Create a new, empty GDAL raster dataset with the spatial references,
        geotranforms of the base GDAL raster dataset.

        base - a the GDAL raster dataset to base output size, and transforms on
        output_uri - a string URI to the new output raster dataset.
        gdal_format - a string representing the GDAL file format of the
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata - a value that will be set as the nodata value for the
            output raster.  Should be the same type as 'datatype'
        datatype - the pixel datatype of the output raster, for example
            gdal.GDT_Float32.  See the following header file for supported
            pixel types:
            http://www.gdal.org/gdal_8h.html#22e22ce0a55036a96f652765793fb7a4
        fill_value - (optional) the value to fill in the raster on creation
        n_rows - (optional) if set makes the resulting raster have n_rows in it
            if not, the number of rows of the outgoing dataset are equal to
            the base.
        n_cols - (optional) similar to n_rows, but for the columns.
        dataset_options - (optional) a list of dataset options that gets
            passed to the gdal creation driver, overrides defaults

        returns a new GDAL raster dataset."""

    if n_rows is None:
        n_rows = base.RasterYSize
    if n_cols is None:
        n_cols = base.RasterXSize
    projection = base.GetProjection()
    geotransform = base.GetGeoTransform()
    driver = gdal.GetDriverByName(gdal_format)
    
    base_band = base.GetRasterBand(1)
    block_size = base_band.GetBlockSize()
    base_band = None
    

    if dataset_options == None:
        #make a new list to make sure we aren't ailiasing one passed in
        dataset_options = []
        #first, should it be tiled?  yes if it's not striped
        if block_size[0] != n_cols:
            #just do 256x256 blocks
            dataset_options = [
                'TILED=YES',
                'BLOCKXSIZE=256',
                'BLOCKYSIZE=256',
                'BIGTIFF=IF_SAFER']
    new_raster = driver.Create(
        output_uri.encode('utf-8'), n_cols, n_rows, 1, datatype,
        options=dataset_options)
    new_raster.SetProjection(projection)
    new_raster.SetGeoTransform(geotransform)
    band = new_raster.GetRasterBand(1)

    band.SetNoDataValue(nodata)
    if fill_value != None:
        band.Fill(fill_value)
    else:
        band.Fill(nodata)
    band = None

    return new_raster


@cython.boundscheck(False)
def convolve_2d(weight_uri, kernel, output_uri):
    """Does a direct convolution on a predefined kernel with the values in weight_uri

        weight_uri - this is the source raster
        kernel - 2d numpy integrating kernel
        output_uri - the raster output of same size and projection of
            weight_uri

        returns nothing"""

    output_nodata = -9999
    new_raster_from_base_uri(
        weight_uri, output_uri, 'GTiff', output_nodata, gdal.GDT_Float32)

    file_handle, tmp_weight_uri = tempfile.mkstemp()
    os.close(file_handle)
    new_raster_from_base_uri(
        weight_uri, tmp_weight_uri, 'GTiff', output_nodata, gdal.GDT_Float32)
    cdef int block_row_size, block_col_size

    weight_ds = gdal.Open(weight_uri)
    weight_band = weight_ds.GetRasterBand(1)
    block_col_size, block_row_size = weight_band.GetBlockSize()

    tmp_weight_ds = gdal.Open(tmp_weight_uri, gdal.GA_Update)
    tmp_weight_band = tmp_weight_ds.GetRasterBand(1)

    output_ds = gdal.Open(output_uri, gdal.GA_Update)
    output_band = output_ds.GetRasterBand(1)

    cdef int n_rows, n_cols
    n_rows, n_cols = weight_band.YSize, weight_band.XSize
    cdef int global_block_row, global_block_col, xoff, yoff

    cdef double last_time = time.time()
    cdef double current_time
    for global_block_row in xrange(int(numpy.ceil(float(n_rows) / block_row_size))):
        for global_block_col in xrange(int(numpy.ceil(float(n_cols) / block_col_size))):
            current_time = time.time()
            if current_time - last_time > 5.0:
                LOGGER.info("convert to float %.1f%% complete", (global_block_row) / int(numpy.ceil(float(n_rows) / block_row_size)) * 100)
                last_time = current_time
            xoff = global_block_col * block_col_size
            yoff = global_block_row * block_row_size
            
            weight_array = weight_band.ReadAsArray(
                xoff=xoff, yoff=yoff,
                win_xsize=min(block_col_size, n_cols - xoff),
                win_ysize=min(block_row_size, n_rows - yoff))
            tmp_weight_band.WriteArray(
                weight_array, xoff=xoff, yoff=yoff)
    
    cdef int kernel_rows = kernel.shape[0]
    cdef int kernel_cols = kernel.shape[1]

    
    cdef int n_global_block_rows = int(ceil(float(n_rows) / block_row_size))
    cdef int n_global_block_cols = int(ceil(float(n_cols) / block_col_size))

    cdef int n_block_rows = 3, n_block_cols = 3 #the number of blocks we'll cache

    #define all the caches
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] weight_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)
    cdef numpy.ndarray[numpy.npy_float32, ndim=4] output_block = numpy.zeros(
        (n_block_rows, n_block_cols, block_row_size, block_col_size), dtype=numpy.float32)

    cdef numpy.ndarray[numpy.npy_float32, ndim=2] kernel_copy = kernel.astype(numpy.float32)

    band_list = [tmp_weight_band, output_band]
    block_list = [weight_block, output_block]
    update_list = [False, True]
    cdef numpy.ndarray[numpy.npy_byte, ndim=2] cache_dirty = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.byte)

    cdef BlockCache block_cache = BlockCache(
        n_block_rows, n_block_cols, n_rows, n_cols, block_row_size, block_col_size, band_list, block_list, update_list, cache_dirty)

    

    cdef int global_row_kernel, global_col_kernel, global_row_kernel_index, global_col_kernel_index, global_row_kernel_offset, global_col_kernel_offset
    cdef int kernel_row, kernel_col, global_row, global_col, global_row_index, global_col_index, global_row_offset, global_col_offset
    cdef double weight_value, output_sum, kernel_sum

    cdef float weight_nodata = output_nodata

    for global_block_row in xrange(n_global_block_rows):
        for global_block_col in xrange(n_global_block_cols):
            for global_row in xrange(global_block_row*block_row_size, min((global_block_row+1)*block_row_size, n_rows)):
                for global_col in xrange(global_block_col*block_col_size, min((global_block_col+1)*block_col_size, n_cols)):
                    current_time = time.time()
                    if current_time - last_time > 5.0:
                        LOGGER.info("convolve 2d %.1f%% complete", (global_block_row + 1.0) / n_global_block_rows * 100)
                        last_time = current_time

                    kernel_sum = 0.0
                    output_sum = 0.0
                    #loop across the kernel
                    for kernel_row in xrange(kernel_rows):
                        for kernel_col in xrange(kernel_cols):
                            global_row_kernel = global_row - kernel_row + kernel_rows / 2
                            global_col_kernel = global_row - kernel_col + kernel_cols / 2

                            if global_row_kernel < 0 or global_row_kernel >= n_rows or global_col_kernel < 0 or global_col_kernel >= n_cols:
                                continue

                            #block_cache.update_cache(global_row_kernel, global_col_kernel, &global_row_kernel_index, &global_col_kernel_index, &global_row_kernel_offset, &global_col_kernel_offset)
                            weight_value = weight_block[global_row_kernel_index, global_col_kernel_index, global_row_kernel_offset, global_col_kernel_offset]
                            if weight_value == weight_nodata:
                                continue
                            output_sum += weight_value * kernel_copy[kernel_row, kernel_col]
                            kernel_sum += kernel_copy[kernel_row, kernel_col]

                    block_cache.update_cache(global_row, global_col, &global_row_index, &global_col_index, &global_row_offset, &global_col_offset)
                    if kernel_sum != 0:
                        output_block[global_row_index, global_col_index, global_row_offset, global_col_offset] = output_sum / kernel_sum
                    else:
                        output_block[global_row_index, global_col_index, global_row_offset, global_col_offset] = output_nodata
                    cache_dirty[global_row_index, global_col_index] = 1


    LOGGER.info('convolve 2d 100% complete')
    
    weight_band = None
    gdal.Dataset.__swig_destroy__(weight_ds)
    weight_ds = None
    
    output_band = None
    gdal.Dataset.__swig_destroy__(output_ds)
    output_ds = None
    

cdef class BlockCache:
    cdef numpy.int32_t[:,:] row_tag_cache
    cdef numpy.int32_t[:,:] col_tag_cache
    cdef numpy.int8_t[:,:] cache_dirty
    cdef int n_block_rows
    cdef int n_block_cols
    cdef int block_col_size
    cdef int block_row_size
    cdef int n_rows
    cdef int n_cols
    band_list = []
    block_list = []
    update_list = []

    def __cinit__(
        self, int n_block_rows, int n_block_cols, int n_rows, int n_cols, int block_row_size, int block_col_size, band_list, block_list, update_list, numpy.int8_t[:,:] cache_dirty):
        self.n_block_rows = n_block_rows
        self.n_block_cols = n_block_cols
        self.block_col_size = block_col_size
        self.block_row_size = block_row_size
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.row_tag_cache = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.int32)
        self.col_tag_cache = numpy.zeros((n_block_rows, n_block_cols), dtype=numpy.int32)
        self.cache_dirty = cache_dirty
        self.row_tag_cache[:] = -1
        self.col_tag_cache[:] = -1
        self.band_list[:] = band_list
        self.block_list[:] = block_list
        self.update_list[:] = update_list

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    cdef void update_cache(self, int global_row, int global_col, int *row_index, int *col_index, int *row_block_offset, int *col_block_offset):
        cdef int cache_row_size, cache_col_size
        cdef int global_row_offset, global_col_offset
        cdef int row_tag, col_tag

        row_block_offset[0] = global_row % self.block_row_size
        row_index[0] = (global_row // self.block_row_size) % self.n_block_rows
        row_tag = (global_row // self.block_row_size) // self.n_block_rows

        col_block_offset[0] = global_col % self.block_col_size
        col_index[0] = (global_col // self.block_col_size) % self.n_block_cols
        col_tag = (global_col // self.block_col_size) // self.n_block_cols

        cdef int current_row_tag = self.row_tag_cache[row_index[0], col_index[0]]
        cdef int current_col_tag = self.col_tag_cache[row_index[0], col_index[0]]

        if current_row_tag != row_tag or current_col_tag != col_tag:
            if self.cache_dirty[row_index[0], col_index[0]]:
                global_col_offset = (current_col_tag * self.n_block_cols + col_index[0]) * self.block_col_size
                cache_col_size = self.n_cols - global_col_offset
                if cache_col_size > self.block_col_size:
                    cache_col_size = self.block_col_size
                
                global_row_offset = (current_row_tag * self.n_block_rows + row_index[0]) * self.block_row_size
                cache_row_size = self.n_rows - global_row_offset
                if cache_row_size > self.block_row_size:
                    cache_row_size = self.block_row_size
                
                for band, block, update in zip(self.band_list, self.block_list, self.update_list):
                    if update:
                        band.WriteArray(block[row_index[0], col_index[0], 0:cache_row_size, 0:cache_col_size],
                            yoff=global_row_offset, xoff=global_col_offset)
                self.cache_dirty[row_index[0], col_index[0]] = 0
            self.row_tag_cache[row_index[0], col_index[0]] = row_tag
            self.col_tag_cache[row_index[0], col_index[0]] = col_tag
                
            global_col_offset = (col_tag * self.n_block_cols + col_index[0]) * self.block_col_size
            global_row_offset = (row_tag * self.n_block_rows + row_index[0]) * self.block_row_size

            cache_col_size = self.n_cols - global_col_offset
            if cache_col_size > self.block_col_size:
                cache_col_size = self.block_col_size
            cache_row_size = self.n_rows - global_row_offset
            if cache_row_size > self.block_row_size:
                cache_row_size = self.block_row_size
            
            for band, block in zip(self.band_list, self.block_list):
                band.ReadAsArray(
                    xoff=global_col_offset, yoff=global_row_offset,
                    win_xsize=cache_col_size, win_ysize=cache_row_size,
                    buf_obj=block[row_index[0], col_index[0], 0:cache_row_size, 0:cache_col_size])

    cdef void flush_cache(self):
        cdef int global_row_offset, global_col_offset
        cdef int cache_row_size, cache_col_size
        cdef int row_index, col_index
        for row_index in xrange(self.n_block_rows):
            for col_index in xrange(self.n_block_cols):
                row_tag = self.row_tag_cache[row_index, col_index]
                col_tag = self.col_tag_cache[row_index, col_index]

                if self.cache_dirty[row_index, col_index]:
                    global_col_offset = (col_tag * self.n_block_cols + col_index) * self.block_col_size
                    cache_col_size = self.n_cols - global_col_offset
                    if cache_col_size > self.block_col_size:
                        cache_col_size = self.block_col_size
                    
                    global_row_offset = (row_tag * self.n_block_rows + row_index) * self.block_row_size
                    cache_row_size = self.n_rows - global_row_offset
                    if cache_row_size > self.block_row_size:
                        cache_row_size = self.block_row_size
                    
                    for band, block, update in zip(self.band_list, self.block_list, self.update_list):
                        if update:
                            band.WriteArray(block[row_index, col_index, 0:cache_row_size, 0:cache_col_size],
                                yoff=global_row_offset, xoff=global_col_offset)
        for band in self.band_list:
            band.FlushCache()
