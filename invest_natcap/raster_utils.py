"""A collection of GDAL dataset and raster utilities"""

import logging
import math

from osgeo import gdal
from osgeo import osr
import numpy as np
import scipy.interpolate


LOGGER = logging.getLogger('raster_utils')

def calculate_band_stats(band):
    """Calculates and sets the min, max, stdev, and mean for the given band.
    
        band - a GDAL rasterband that will be modified by having its band
            statistics set
    
        returns nothing
    """

    #calculating raster statistics
    rasterMin, rasterMax = band.ComputeRasterMinMax(0)
    #make up stddev and mean
    mean = (rasterMax + rasterMin) / 2.0

    #This is an incorrect standard deviation, but saves us from having to 
    #calculate by hand
    stdev = (rasterMax - mean) / 2.0

    band.SetStatistics(rasterMin, rasterMax, mean, stdev)


def pixel_area(dataset):
    """Calculates the pixel area of the given dataset in m^2
    
        dataset - GDAL dataset
    
        returns area in m ^ 2 of each pixel in dataset"""

    srs = osr.SpatialReference()
    srs.SetProjection(dataset.GetProjection())
    linear_units = srs.GetLinearUnits()
    geotransform = dataset.GetGeoTransform()
    #take absolute value since sometimes negative widths/heights
    area_meters = abs(geotransform[1] * geotransform[5] * (linear_units ** 2))
    return area_meters

def pixel_size(dataset):
    """Calculates the pixel size of the given dataset in m
    
        dataset - GDAL dataset
    
        returns the pixel size in m"""

    srs = osr.SpatialReference()
    srs.SetProjection(dataset.GetProjection())
    linear_units = srs.GetLinearUnits()
    geotransform = dataset.GetGeoTransform()
    #take absolute value since sometimes negative widths/heights
    size_meters = (abs(geotransform[1]) + abs(geotransform[5])) / 2 * \
        linear_units
    return size_meters

def vectorize_rasters(dataset_list, op, raster_out_uri=None,
                     datatype=gdal.GDT_Float32, nodata=0.0):
    """Apply the numpy vectorized operation `op` on the first band of the
        datasets contained in dataset_list where the arguments to `op` are 
        brodcasted pixels from each current_dataset in dataset_list in the order they 
        exist in the list
        
        dataset_list - list of GDAL input datasets
        op - numpy vectorized operation, takes broadcasted pixels from 
            the first bands in dataset_list in order and returns a new pixel
        raster_out_uri - the desired URI to the output current_dataset.  If None then
            resulting current_dataset is only mapped to MEM
        datatype - the GDAL datatype of the output current_dataset.  By default this
            is a 32 bit float.
        nodata - the nodata value for the output current_dataset
        
        returns a single band current_dataset"""

    LOGGER.debug('starting vectorize_rasters')

    #create a new current_dataset with the minimum resolution of dataset_list and
    #bounding box that contains aoi_box
    #gt: left, pixelxwidth, pixelywidthforx, top, pixelxwidthfory, pixelywidth
    #generally pixelywidthforx and pixelxwidthfory are zero for maps where 
    #north is up if that's not the case for us, we'll have a few bugs to deal 
    #with aoibox is left, top, right, bottom
    LOGGER.debug('calculating the overlapping rectangles')
    aoi_box = calculate_intersection_rectangle(dataset_list)
    LOGGER.debug('the aoi box: %s' % aoi_box)
    #determine the minimum pixel size
    gt = dataset_list[0].GetGeoTransform()
    pixel_width, pixel_height = gt[1], gt[5]
    for current_dataset in dataset_list:
        gt = current_dataset.GetGeoTransform()
        pixel_width = min(pixel_width, gt[1], key=abs)
        pixel_height = min(pixel_height, gt[5], key=abs)

    LOGGER.debug('min pixel width and height: %s %s' % (pixel_width,
                                                        pixel_height))

    #These define the output current_dataset's columns and out_n_rows
    out_n_cols = int(math.ceil((aoi_box[2] - aoi_box[0]) / pixel_width))
    out_n_rows = int(math.ceil((aoi_box[3] - aoi_box[1]) / pixel_height))
    LOGGER.debug('number of pixel out_n_cols and out_n_rows %s %s' % \
                 (out_n_cols, out_n_rows))
    #out_geotransform order: 
    #1) left coordinate of top left corner
    #2) pixel width in x direction
    #3) pixel width in y direciton (usually zero)
    #4) top coordinate of top left corner
    #5) pixel height in x direction (usually zero)
    #6) pixel height in y direction 
    out_geotransform = [aoi_box[0], pixel_width, 0.0,
                        aoi_box[1], 0.0, pixel_height]

    projection = dataset_list[0].GetProjection()
    output_uri = ''
    format = 'MEM'
    if raster_out_uri != None:
        output_uri = raster_out_uri
        format = 'GTiff'
    out_dataset = new_raster(out_n_cols, out_n_rows, projection,
        out_geotransform, format, nodata, datatype, 1, output_uri)
    out_band = out_dataset.GetRasterBand(1)
    out_band.Fill(0)

    #Determine the output current_dataset's x and y range
    out_x_range = (np.arange(out_n_cols, dtype=float) * out_geotransform[1]) + \
        out_geotransform[0]
    out_y_range = (np.arange(out_n_rows, dtype=float) * out_geotransform[5]) + \
        out_geotransform[3]

    LOGGER.debug('out_x_range shape %s ' % (out_x_range.shape))
    LOGGER.debug('out_y_range shape %s ' % (out_y_range.shape))
    #create an interpolator for each current_dataset band
    matrix_list = []
    nodata_list = []

    #Check to see if all the input datasets are equal, if so then we
    #don't need to interpolate them
    all_equal = True
    for dim_fun in [lambda ds: ds.RasterXSize, lambda ds: ds.RasterYSize]:
        sizes = map(dim_fun, dataset_list)
        all_equal = all_equal and sizes.count(sizes[0]) == len(sizes)

    if all_equal:
        LOGGER.debug("They're all equal, building matrix_list")
        matrix_list = \
            map(lambda x: x.GetRasterBand(1).ReadAsArray(), dataset_list)
    else:
        #Do some slower interpolation
        for current_dataset in dataset_list:
            LOGGER.debug('building interpolator for %s' % current_dataset)
            gt = current_dataset.GetGeoTransform()
            LOGGER.debug('gt = %s' % (str(gt)))
            band = current_dataset.GetRasterBand(1)
            matrix = band.ReadAsArray(0, 0, band.XSize, band.YSize)

            #Need to set nodata values to something reasonable to avoid weird
            #interpolation issues if nodata is a large value like -3e38.
            nodata_mask = matrix == band.GetNoDataValue()
            matrix[nodata_mask] = nodata

            LOGGER.debug('bandXSize bandYSize %s %s' % (band.XSize, band.YSize))
            xrange = (np.arange(band.XSize, dtype=float) * gt[1]) + gt[0]
            LOGGER.debug('gt[0] + band.XSize * gt[1] = %s' % (gt[0] + band.XSize * gt[1]))
            LOGGER.debug('xrange[-1] = %s' % xrange[-1])
            yrange = (np.arange(band.YSize, dtype=float) * gt[5]) + gt[3]

            #This is probably true if north is up
            if gt[5] < 0:
                yrange = yrange[::-1]
                matrix = matrix[::-1]
            LOGGER.debug('xrange shape %s' % xrange.shape)
            LOGGER.debug('yrange shape %s' % yrange.shape)
            LOGGER.debug('matrix shape %s %s' % matrix.shape)

            #transposing matrix here since numpy 2d array order is matrix[y][x]
            LOGGER.debug('creating RectBivariateSpline interpolator')
            spl = scipy.interpolate.RectBivariateSpline(yrange, xrange,
                                                        matrix,
                                                        kx=1, ky=1)

            LOGGER.debug('interpolating')

            #This handles the case where Y is increasing downwards in the output.
            #We encountered this when writing a testcase for a 50x50 box wih no
            #geotransform.
            if out_geotransform[5] < 0:
                matrix_list.append(spl(out_y_range[::-1], out_x_range)[::-1])
            else:
                matrix_list.append(spl(out_y_range, out_x_range))

            nodata_list.append(band.GetNoDataValue())


    #invoke op with interpolated values that overlap the output current_dataset
    LOGGER.debug('applying operation on matrix stack')
    out_matrix = op(*matrix_list)
    LOGGER.debug('result of operation on matrix stack shape %s %s' %
                 (out_matrix.shape))
    LOGGER.debug('outmatrix size %s current_dataset size %s %s'
                 % (out_matrix.shape, out_band.XSize, out_band.YSize))

    #Nodata out any values in out_band that have corresponding nodata values
    #in the matrix_list
    for band, nodata in zip(matrix_list, nodata_list):
        nodata_index = band == nodata
        out_matrix[nodata_index] = out_band.GetNoDataValue()

    out_band.WriteArray(out_matrix, 0, 0)

    #Calculate the min/max/avg/stdev on out_band
    calculate_band_stats(out_band)

    #return the new current_dataset
    return out_dataset

def vectorize_one_arg_op(rasterBand, op, out_band, bounding_box=None):
    """Applies the function 'op' over rasterBand and outputs to out_band
    
        rasterBand - (input) a GDAL raster
        op - (input) a function that that takes 2 arguments and returns 1 value
        out_band - (output) the result of vectorizing op over rasterBand
        bounding_box - (input, optional) a 4 element list that corresponds
            to the bounds in GDAL's ReadAsArray to limit the vectorization
            over that region in rasterBand and writing to the corresponding
            out_band.  If left None, defaults to the size of the band
            
        returns nothing"""

    vOp = np.vectorize(op, otypes=[np.float])
    if bounding_box == None:
        bounding_box = [0, 0, rasterBand.XSize, rasterBand.YSize]

    #Read one line at a time. Starting line is bounding_box[1], number of lines
    #is bounding_box[3]
    for row_number in range(bounding_box[3]):
        #Here bounding box start col and n col are same, but start row
        #advances on each loop and only 1 row is read at a time
        start_col = bounding_box[0]
        start_row = row_number + bounding_box[1]
        data = rasterBand.ReadAsArray(start_col, start_row,
                                       bounding_box[2], 1)
        out_array = vOp(data)
        out_band.WriteArray(out_array, start_col, start_row)
        #Calculate the min/max/avg/stdev on out_band
        calculate_band_stats(out_band)


def new_raster_from_base(base, outputURI, format, nodata, datatype):
    """Create a new, empty GDAL raster dataset with the spatial references,
        dimensions and geotranforms of the base GDAL raster dataset.
        
        base - a the GDAL raster dataset to base output size, and transforms on
        outputURI - a string URI to the new output raster dataset.
        format - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata - a value that will be set as the nodata value for the 
            output raster.  Should be the same type as 'datatype'
        datatype - the pixel datatype of the output raster, for example 
            gdal.GDT_Float32.  See the following header file for supported 
            pixel types:
            http://www.gdal.org/gdal_8h.html#22e22ce0a55036a96f652765793fb7a4
                
        returns a new GDAL raster dataset."""

    cols = base.RasterXSize
    rows = base.RasterYSize
    projection = base.GetProjection()
    geotransform = base.GetGeoTransform()
    return new_raster(cols, rows, projection, geotransform, format, nodata,
                     datatype, base.RasterCount, outputURI)

def new_raster(cols, rows, projection, geotransform, format, nodata, datatype,
              bands, outputURI):
    """Create a new raster with the given properties.
    
        cols - number of pixel columns
        rows - number of pixel rows
        projection - the datum
        geotransform - the coordinate system
        format - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata - a value that will be set as the nodata value for the 
            output raster.  Should be the same type as 'datatype'
        datatype - the pixel datatype of the output raster, for example 
            gdal.GDT_Float32.  See the following header file for supported 
            pixel types:
            http://www.gdal.org/gdal_8h.html#22e22ce0a55036a96f652765793fb7a4
        bands - the number of bands in the raster
        outputURI - the file location for the outputed raster.  If format
            is 'MEM' this can be an empty string
            
        returns a new GDAL raster with the parameters as described above"""

    driver = gdal.GetDriverByName(format)
    new_raster = driver.Create(str(outputURI), cols, rows, bands, datatype)
    new_raster.SetProjection(projection)
    new_raster.SetGeoTransform(geotransform)
    for i in range(bands):
        new_raster.GetRasterBand(i + 1).SetNoDataValue(nodata)
        new_raster.GetRasterBand(i + 1).Fill(nodata)

    return new_raster

def calculate_intersection_rectangle(rasterList):
    """Return a bounding box of the intersections of all the rasters in the
        list.
        
        rasterList - a list of GDAL rasters in the same projection and 
            coordinate system
            
        returns a 4 element list that bounds the intersection of all the 
            rasters in rasterList.  [left, top, right, bottom]"""

    #Define the initial bounding box
    gt = rasterList[0].GetGeoTransform()
    #order is left, top, right, bottom of rasterbounds
    boundingBox = [gt[0], gt[3], gt[0] + gt[1] * rasterList[0].RasterXSize,
                   gt[3] + gt[5] * rasterList[0].RasterYSize]

    for band in rasterList:
        #intersect the current bounding box with the one just read
        gt = band.GetGeoTransform()
        LOGGER.debug('geotransform on raster band %s %s' % (gt, band))
        LOGGER.debug('pixel x and y %s %s' % (band.RasterXSize,
                                              band.RasterYSize))
        rec = [gt[0], gt[3], gt[0] + gt[1] * band.RasterXSize,
               gt[3] + gt[5] * band.RasterYSize]
        #This intersects rec with the current bounding box
        boundingBox = [max(rec[0], boundingBox[0]),
                       min(rec[1], boundingBox[1]),
                       min(rec[2], boundingBox[2]),
                       max(rec[3], boundingBox[3])]
    return boundingBox
