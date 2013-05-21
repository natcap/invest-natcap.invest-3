"""A collection of GDAL dataset and raster utilities"""

import logging
import random
import string
import os
import time
import tempfile
import shutil
import atexit
import functools
import csv
import math
import errno

from osgeo import gdal
from osgeo import osr
from osgeo import ogr
import numpy
import scipy.interpolate
import scipy.sparse
import scipy.signal
import scipy.ndimage

import raster_cython_utils

from invest_natcap.invest_core import fileio

GDAL_TO_NUMPY_TYPE = {
    gdal.GDT_Byte: numpy.byte,
    gdal.GDT_Int16: numpy.int16,
    gdal.GDT_Int32: numpy.int32,
    gdal.GDT_UInt16: numpy.uint16,
    gdal.GDT_UInt32: numpy.uint32,
    gdal.GDT_Float32: numpy.float32,
    gdal.GDT_Float64: numpy.float64
    }

#Used to raise an exception if rasters, shapefiles, or both don't overlap
#in regions that should
class SpatialExtentOverlapException(Exception): pass

#Used to indicate values that are not defined in dictionary structures
class UndefinedValue(Exception): pass

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('raster_utils')

#The following line of code hides some errors that seem important and doesn't
#raise exceptions on them.  FOr example:
#ERROR 5: Access window out of range in RasterIO().  Requested
#(1,15) of size 25x3 on raster of 26x17.
#disappears when this line is turned on.  Probably not a good idea to uncomment
#until we know what's happening
#gdal.UseExceptions()

def get_nodata_from_uri(ds_uri):
    """Returns the nodata value for the first band from a gdal dataset

        ds_uri - a uri to a gdal dataset

        returns nodata value for ds band 1"""

    ds = gdal.Open(ds_uri)
    band = ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    return nodata

def get_datatype_from_uri(ds_uri):
    """Returns the datatype for the first band from a gdal dataset

        ds_uri - a uri to a gdal dataset

        returns the datatype for ds band 1"""

    ds = gdal.Open(ds_uri)
    band = ds.GetRasterBand(1)
    datatype = band.DataType
    return datatype

def get_row_col_from_uri(ds_uri):
    """Returns a tuple of number of rows and columns of that dataset
        uri.

        ds_uri - a uri to a gdal dataset

        returns nodata value for ds band 1"""

    ds = gdal.Open(ds_uri)
    n_rows = ds.RasterYSize
    n_cols = ds.RasterXSize
    ds = None
    return (n_rows, n_cols)
    

def calculate_raster_stats(ds):
    """Calculates and sets the min, max, stdev, and mean for the bands in
       the raster.
    
       ds - a GDAL raster dataset that will be modified by having its band
            statistics set
    
        returns nothing"""

    for band_number in range(ds.RasterCount):
        band = ds.GetRasterBand(band_number + 1)
        band.ComputeStatistics(0)

def calculate_raster_stats_uri(ds_uri):
    """Calculates and sets the min, max, stdev, and mean for the bands in
       the raster.
    
       ds_uri - a uri to a GDAL raster dataset that will be modified by having its band
            statistics set
    
        returns nothing"""

    ds = gdal.Open(ds_uri, gdal.GA_Update)

    for band_number in range(ds.RasterCount):
        band = ds.GetRasterBand(band_number + 1)
        band.ComputeStatistics(0)

def get_statistics_from_uri(dataset_uri):
    """Retrieves the min, max, mean, stdev from a GDAL Dataset

        dataset_uri - a uri to a gdal dataset

        returns min, max, mean, stddev"""

    dataset = gdal.Open(dataset_uri)
    band = dataset.GetRasterBand(1)
    statistics = band.GetStatistics(0,1)
    band = None
    dataset = None
    return statistics

def get_cell_area_from_uri(dataset_uri):
    return pixel_area(gdal.Open(dataset_uri))

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

def get_cell_size_from_uri(dataset_uri):
    return pixel_size(gdal.Open(dataset_uri))

def pixel_size(dataset):
    """Calculates the average pixel size of the given dataset in m.  Saying
       'average' in case we have non-square pixels.
    
        dataset - GDAL dataset
    
        returns the average pixel size in m"""

    srs = osr.SpatialReference()
    srs.SetProjection(dataset.GetProjection())
    linear_units = srs.GetLinearUnits()
    geotransform = dataset.GetGeoTransform()
    #take absolute value since sometimes negative widths/heights
    size_meters = (abs(geotransform[1]) + abs(geotransform[5])) / 2 * \
        linear_units
    return size_meters

def pixel_size_based_on_coordinate_transform(dataset, coord_trans, point):
    """Calculates the pixel width and height in meters given a coordinate 
        transform and reference point on the dataset that's close to the 
        transform's projected coordinate sytem.  This is only necessary
        if dataset is not already in a meter coordinate system, for example
        dataset may be in lat/long (WGS84).  
     
       dataset - A projected GDAL dataset in the form of lat/long decimal degrees
       coord_trans - An OSR coordinate transformation from dataset coordinate
           system to meters
       point - a reference point close to the coordinate transform coordinate
           system.  must be in the same coordinate system as dataset.
       
       returns a tuple containing (pixel width in meters, pixel height in 
           meters)"""
    #Get the first points (x,y) from geoTransform
    geo_tran = dataset.GetGeoTransform()
    pixel_size_x = geo_tran[1]
    pixel_size_y = geo_tran[5]
    top_left_x = point[0]
    top_left_y = point[1]
    LOGGER.debug('pixel_size_x: %s', pixel_size_x)
    LOGGER.debug('pixel_size_x: %s', pixel_size_y)
    LOGGER.debug('top_left_x : %s', top_left_x)
    LOGGER.debug('top_left_y : %s', top_left_y)
    #Create the second point by adding the pixel width/height
    new_x = top_left_x + pixel_size_x
    new_y = top_left_y + pixel_size_y
    LOGGER.debug('top_left_x : %s', new_x)
    LOGGER.debug('top_left_y : %s', new_y)
    #Transform two points into meters
    point_1 = coord_trans.TransformPoint(top_left_x, top_left_y)
    point_2 = coord_trans.TransformPoint(new_x, new_y)
    #Calculate the x/y difference between two points
    #taking the absolue value because the direction doesn't matter for pixel
    #size in the case of most coordinate systems where y increases up and x
    #increases to the right (right handed coordinate system).
    pixel_diff_x = abs(point_2[0] - point_1[0])
    pixel_diff_y = abs(point_2[1] - point_1[1])
    LOGGER.debug('point1 : %s', point_1)
    LOGGER.debug('point2 : %s', point_2)
    LOGGER.debug('pixel_diff_x : %s', pixel_diff_x)
    LOGGER.debug('pixel_diff_y : %s', pixel_diff_y)
    return (pixel_diff_x, pixel_diff_y)

def interpolate_matrix(x, y, z, newx, newy, degree=1):
    """Takes a matrix of values from a rectangular grid along with new 
        coordinates and returns a matrix with those values interpolated along
        the new axis points.
        
        x - an array of x points on the grid
        y - an array of y points on the grid
        z - the values on the grid
        newx- the new x points for the interpolated grid
        newy - the new y points for the interpolated grid
        
        returns a matrix of size len(newx)*len(newy) whose values are 
            interpolated from z"""

    #Create an interpolator for the 2D data.  Here's a reference
    #http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RectBivariateSpline.html
    #not using interp2d because this bug: http://projects.scipy.org/scipy/ticket/898
    spl = scipy.interpolate.RectBivariateSpline(x, y, z.transpose(), kx=degree, ky=degree)
    return spl(newx, newy).transpose()


def vectorize_rasters(dataset_list, op, aoi=None, raster_out_uri=None,
                     datatype=gdal.GDT_Float32, nodata=0.0):
    """Apply the numpy vectorized operation `op` on the first band of the
        datasets contained in dataset_list where the arguments to `op` are 
        brodcasted pixels from each current_dataset in dataset_list in the order they 
        exist in the list
        
        dataset_list - list of GDAL input datasets, requires that they'are all
            in the same projection.
        op - numpy vectorized operation, takes broadcasted pixels from 
            the first bands in dataset_list in order and returns a new pixel.  It is
            critical that the value returned by `op` match datatype in all cases, 
            otherwise the behavior of this function is undefined.
        aoi - an OGR polygon datasource that will clip the output raster to no larger
            than the extent of the file and restricts the processing of op to those
            output pixels that will lie within the polygons.  the rest will be nodata
            values.  Must be in the same projection as dataset_list rasters.
        raster_out_uri - the desired URI to the output current_dataset.  If None then
            resulting current_dataset is only mapped to MEM
        datatype - the GDAL datatype of the output current_dataset.  By default this
            is a 32 bit float.
        nodata - the nodata value for the output current_dataset
        
        returns a single band current_dataset"""

    LOGGER.warn('vectorize_rasters is DEPRECATED.  use vectorize_datasets '
                'and refactor the code that is calling this function.')
    #We need to ensure that the type of nodata is the same as the raster type so
    #we don't encounter bugs where we return an int nodata for a float raster or
    #vice versa
    nodata = gdal_cast(nodata, datatype)

    #create a new current_dataset with the minimum resolution of dataset_list and
    #bounding box that contains aoi_box
    #gt: left, pixelxwidth, pixelywidthforx, top, pixelxwidthfory, pixelywidth
    #generally pixelywidthforx and pixelxwidthfory are zero for maps where 
    #north is up if that's not the case for us, we'll have a few bugs to deal 
    #with aoibox is left, top, right, bottom
    aoi_box = calculate_intersection_rectangle(dataset_list, aoi)

    #determine the minimum pixel size
    gt = dataset_list[0].GetGeoTransform()
    pixel_width, pixel_height = gt[1], gt[5]
    for current_dataset in dataset_list:
        gt = current_dataset.GetGeoTransform()
        #This takes the minimum of the absolute value of the current dataset's
        #pixel size versus what we've seen so far.
        pixel_width = min(pixel_width, gt[1], key=abs)
        pixel_height = min(pixel_height, gt[5], key=abs)

    #Together with the AOI and min pixel size we define the output dataset's 
    #columns and out_n_rows
    out_n_cols = int(numpy.round((aoi_box[2] - aoi_box[0]) / pixel_width))
    out_n_rows = int(numpy.round((aoi_box[3] - aoi_box[1]) / pixel_height))

    #out_geotransform order: 
    #1) left coordinate of top left corner
    #2) pixel width in x direction
    #3) pixel width in y direciton (usually zero)
    #4) top coordinate of top left corner
    #5) pixel height in x direction (usually zero)
    #6) pixel height in y direction 
    out_gt = [aoi_box[0], pixel_width, 0.0, aoi_box[1], 0.0, pixel_height]

    #The output projection will be the same as any in dataset_list, so just take
    #the first one.
    out_projection = dataset_list[0].GetProjection()

    #If no output uri is specified assume 'MEM' format, otherwise GTiff
    format = 'MEM'
    output_uri = ''
    if raster_out_uri != None:
        output_uri = raster_out_uri
        format = 'GTiff'

    #Build the new output dataset and reference the band for later.  the '1'
    #means only 1 output band.
    LOGGER.info("Output dataset is a %s X %s raster" % (out_n_cols, out_n_rows))
    out_dataset = new_raster(out_n_cols, out_n_rows, out_projection,
        out_gt, format, nodata, datatype, 1, output_uri)
    out_band = out_dataset.GetRasterBand(1)
    out_band.Fill(nodata)

    #left and right coordinates will always be the same for each row so calc
    #them first.
    out_left_coord = out_gt[0]
    out_right_coord = out_left_coord + out_gt[1] * out_band.XSize

    #These are the output coordinates for the interpolator
    out_col_coordinates = numpy.arange(out_n_cols, dtype=numpy.float)
    out_col_coordinates *= out_gt[1]
    out_col_coordinates += out_gt[0]

    try:
        vectorized_op = numpy.vectorize(op)
    except ValueError:
        #it's possible that the operation is already vectorized, so try that
        vectorized_op = op

    #If there's an AOI, we need to mask out values
    mask_dataset = new_raster_from_base(out_dataset, '', 'MEM', 255, gdal.GDT_Byte)
    mask_dataset_band = mask_dataset.GetRasterBand(1)

    if aoi != None:
        #Only mask AOI as 0 everything else is 1 to correspond to numpy masked arrays
        #that say '1' is invalid
        mask_dataset_band.Fill(1)
        aoi_layer = aoi.GetLayer()
        gdal.RasterizeLayer(mask_dataset, [1], aoi_layer, burn_values=[0])
    else:
        #No aoi means good to fill everywhere
        mask_dataset_band.Fill(0)
        
    mask_dataset_band = None
    mask_dataset.FlushCache()
    mask_dataset_band = mask_dataset.GetRasterBand(1)

    #Check to see if all the input datasets are equal, if so then we
    #don't need to interpolate them, but if there's an AOI you always need to interpolate, 
    #so initializing to aoi == None (True if no aoi)
    all_equal = aoi == None
    for dim_fun in [lambda ds: ds.RasterXSize, lambda ds: ds.RasterYSize]:
        sizes = map(dim_fun, dataset_list)
        all_equal = all_equal and sizes.count(sizes[0]) == len(sizes)

    if all_equal:
        LOGGER.info("All input rasters are equal size, not interpolating and vectorizing directly")

        #Loop over each row in out_band
        n_cols = mask_dataset_band.XSize
        for out_row_index in range(out_band.YSize):
            out_row_coord = out_gt[3] + out_gt[5] * out_row_index
            raster_array_stack = []
            mask_array = mask_dataset_band.ReadAsArray(0,out_row_index,n_cols,1)
            matrix_array_list = \
                map(lambda x: x.GetRasterBand(1).ReadAsArray(0, out_row_index, n_cols, 1), dataset_list)
            out_row = vectorized_op(*matrix_array_list)
            out_row[mask_array == 1] = nodata
            out_band.WriteArray(out_row, xoff=0, yoff=out_row_index)

        #Calculate the min/max/avg/stdev on the out raster
        calculate_raster_stats(out_dataset)

        #return the new current_dataset
        return out_dataset

    #Otherwise they're misaligned and we need to do lots of interpolation
    LOGGER.info("Input rasters do not align perfectly.  Interpolating the pixel stack.  This is normal behavior.")

    #Loop over each row in out_band
    for out_row_index in range(out_band.YSize):
        out_row_coord = out_gt[3] + out_gt[5] * out_row_index
        raster_array_stack = []
        mask_array = mask_dataset_band.ReadAsArray(0,out_row_index,mask_dataset_band.XSize,1)
        #Loop over each input raster
        for current_dataset in dataset_list:
            current_band = current_dataset.GetRasterBand(1)
            current_gt = current_dataset.GetGeoTransform()
            #Determine left and right indexes by calculating distance from
            #out left edget to current left edge and dividing by the width
            #of current pixel.
            current_left_index = \
                int(numpy.round((out_left_coord - current_gt[0])/current_gt[1]))
            current_right_index = \
                int(numpy.round((out_right_coord - current_gt[0])/current_gt[1]))

            current_top_index = \
                int(numpy.floor((out_row_coord - current_gt[3])/current_gt[5]))-1

            #The +1 ensures the count of indexes are correct otherwise subtracting
            #top and bottom index that differ by 1 are always 0 and sometimes -1
            current_bottom_index = \
                int(numpy.ceil((out_row_coord - current_gt[3])/current_gt[5]))+1

            #We might be at the top or bottom edge, so shift the window up or down
            #We need at least 3 rows because the interpolator requires it.
            if current_top_index < 0:
                current_top_index += 1
                current_bottom_index += 1
            elif current_bottom_index >= current_band.YSize:
                current_top_index -= 1
                current_bottom_index -= 1

            #These steps will tell us the size of the window to read from and
            #later help us determine the row and column coordinates for the 
            #interpolator.
            current_col_steps = current_right_index - current_left_index
            current_row_steps = current_bottom_index - current_top_index

            current_array = \
                current_band.ReadAsArray(current_left_index, current_top_index,
                                         current_col_steps, current_row_steps)

            #These are the basis of the coordinates for the interpolator
            current_left_coordinate = \
                current_gt[0] + current_left_index * current_gt[1]
            current_top_coordinate = \
                current_gt[3] + current_top_index * current_gt[5]

            #Equivalent of
            #    numpy.array([current_left_coordinate + index * current_gt[1] \
            #         for index in range(current_col_steps)])
            current_col_coordinates = numpy.arange(current_col_steps, dtype=numpy.float)
            current_col_coordinates *= current_gt[1]
            current_col_coordinates += current_left_coordinate
            

            #Equivalent of
            #    numpy.array([current_top_coordinate + index * current_gt[5] \
            #         for index in range(current_row_steps)])
            current_row_coordinates = numpy.arange(current_row_steps, dtype=numpy.float)
            current_row_coordinates *= current_gt[5]
            current_row_coordinates += current_top_coordinate

            #If this is true it means the y coordinates aren't in increasing
            #order which freaks out the interpolator.  Reverse them.
            if gt[5] < 0:
                current_row_coordinates = current_row_coordinates[::-1]
                current_array = current_array[::-1]

            #This interpolation scheme comes from a StackOverflow thread
            #http://stackoverflow.com/questions/11144513/numpy-cartesian-product-of-x-and-y-array-points-into-single-array-of-2d-points#comment14610953_11144513
            input_points = \
                numpy.transpose([numpy.repeat(current_row_coordinates, 
                                      len(current_col_coordinates)),
                              numpy.tile(current_col_coordinates, 
                                        len(current_row_coordinates))])

            nearest_interpolator = \
                scipy.interpolate.NearestNDInterpolator(input_points, 
                                                        current_array.flatten())
            output_points = \
                numpy.transpose([numpy.repeat(out_row_coord, len(out_col_coordinates)),
                              out_col_coordinates])

            interpolated_row = nearest_interpolator(output_points)
            raster_array_stack.append(interpolated_row)

        #Vectorize the stack of rows and write to out_band
        out_row = vectorized_op(*raster_array_stack)
        #We need to resize because GDAL expects to write 2D arrays even though our
        #interpolator builds 1D arrays.
        out_row.resize((1,len(out_col_coordinates)))
        #Mask out_row based on AOI
        out_row[mask_array == 1] = nodata
        out_band.WriteArray(out_row,xoff=0,yoff=out_row_index)

    #Calculate the min/max/avg/stdev on the out raster
    calculate_raster_stats(out_dataset)

    out_dataset.FlushCache()
    #return the new current_dataset
    return out_dataset

def new_raster_from_base_uri(base_uri, *args, **kwargs):
    """A wrapper for the function new_raster_from_base that opens up the
        base_uri before passing it to new_raster_from_base.

        base_uri - a URI to a GDAL dataset on disk.

        All other arguments to new_raster_from_base are passed in.

        Returns a GDAL dataset.
        """
    base_raster = gdal.Open(base_uri)
    new_raster_from_base(base_raster, *args, **kwargs)

def new_raster_from_base(base, output_uri, gdal_format, nodata, datatype, fill_value=None):
    """Create a new, empty GDAL raster dataset with the spatial references,
        dimensions and geotranforms of the base GDAL raster dataset.
        
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
                
        returns a new GDAL raster dataset."""

    n_cols = base.RasterXSize
    n_rows = base.RasterYSize
    projection = base.GetProjection()
    geotransform = base.GetGeoTransform()
    driver = gdal.GetDriverByName(gdal_format)
    new_raster = driver.Create(output_uri.encode('utf-8'), n_cols, n_rows, 1, datatype)
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
    new_raster = driver.Create(outputURI.encode('utf-8'), cols, rows, bands, datatype)
    new_raster.SetProjection(projection)
    new_raster.SetGeoTransform(geotransform)
    for i in range(bands):
        new_raster.GetRasterBand(i + 1).SetNoDataValue(nodata)
        new_raster.GetRasterBand(i + 1).Fill(nodata)

    return new_raster

def calculate_intersection_rectangle(dataset_list, aoi=None):
    """Return a bounding box of the intersections of all the rasters in the
        list.
        
        dataset_list - a list of GDAL datasets in the same projection and 
            coordinate system
        aoi - an OGR polygon datasource which may optionally also restrict
            the extents of the intersection rectangle based on its own
            extents.
            
        raises a SpatialExtentOverlapException in cases where the dataset 
            list and aoi don't overlap.

        returns a 4 element list that bounds the intersection of all the 
            rasters in dataset_list.  [left, top, right, bottom]"""

    def valid_bounding_box(bb):
        """Check to make sure bounding box doesn't collapse on itself

        bb - a bounding box of the form [left, top, right, bottom]

        returns True if bb is valid, false otherwise"""

        return bb[0] <= bb[2] and bb[3] <= bb[1]

    #Define the initial bounding box
    gt = dataset_list[0].GetGeoTransform()
    #order is left, top, right, bottom of rasterbounds
    bounding_box = [gt[0], gt[3], gt[0] + gt[1] * dataset_list[0].RasterXSize,
                   gt[3] + gt[5] * dataset_list[0].RasterYSize]

    dataset_files = []
    for dataset in dataset_list:
        dataset_files.append(dataset.GetDescription())
        #intersect the current bounding box with the one just read
        gt = dataset.GetGeoTransform()
        rec = [gt[0], gt[3], gt[0] + gt[1] * dataset.RasterXSize,
               gt[3] + gt[5] * dataset.RasterYSize]
        #This intersects rec with the current bounding box
        bounding_box = [max(rec[0], bounding_box[0]),
                       min(rec[1], bounding_box[1]),
                       min(rec[2], bounding_box[2]),
                       max(rec[3], bounding_box[3])]
        
        #Left can't be greater than right or bottom greater than top
        if not valid_bounding_box(bounding_box):
            raise SpatialExtentOverlapException("These rasters %s don't overlap with this one %s" % \
                                (unicode(dataset_files[0:-1]), dataset_files[-1]))

    if aoi != None:
        aoi_layer = aoi.GetLayer(0)
        aoi_extent = aoi_layer.GetExtent()
        bounding_box = [max(aoi_extent[0], bounding_box[0]),
                       min(aoi_extent[3], bounding_box[1]),
                       min(aoi_extent[1], bounding_box[2]),
                       max(aoi_extent[2], bounding_box[3])]
        if not valid_bounding_box(bounding_box):
            raise SpatialExtentOverlapException("The aoi layer %s doesn't overlap with %s" % \
                                (aoi, unicode(dataset_files)))

    return bounding_box

def create_raster_from_vector_extents_uri(shapefile_uri, pixel_size, gdal_format, nodata_out_value, output_uri):
    """A wrapper for create_raster_from_vector_extents
    
        shapefile_uri - uri to an OGR datasource to use as the extents of the raster
        pixel_size - size of output pixels in the projected units of shapefile_uri
        gdal_format - the raster pixel format, something like gdal.GDT_Float32
        nodata_out_value - the output nodata value
        output_uri - the URI to write the gdal dataset
        
        returns nothing"""

    datasource = ogr.Open(shapefile_uri)
    create_raster_from_vector_extents(
        pixel_size, pixel_size, gdal_format, nodata_out_value, output_uri,
        datasource)

def create_raster_from_vector_extents(xRes, yRes, format, nodata, rasterFile, 
                                      shp):
    """Create a blank raster based on a vector file extent.  This code is
        adapted from http://trac.osgeo.org/gdal/wiki/FAQRaster#HowcanIcreateablankrasterbasedonavectorfilesextentsforusewithgdal_rasterizeGDAL1.8.0
    
        xRes - the x size of a pixel in the output dataset must be a positive 
            value
        yRes - the y size of a pixel in the output dataset must be a positive 
            value
        format - gdal GDT pixel type
        nodata - the output nodata value
        rasterFile - URI to file location for raster
        shp - vector shapefile to base extent of output raster on
        
        returns a blank raster whose bounds fit within `shp`s bounding box
            and features are equivalent to the passed in data"""

    #Determine the width and height of the tiff in pixels based on the 
    #maximum size of the combined envelope of all the features
    shp_extent = None
    for layer_index in range(shp.GetLayerCount()):
        shp_layer = shp.GetLayer(layer_index)
        for feature_index in range(shp_layer.GetFeatureCount()):
            feature = shp_layer.GetFeature(feature_index)
            geometry = feature.GetGeometryRef()
            #feature_extent = [xmin, xmax, ymin, ymax]
            feature_extent = geometry.GetEnvelope()
            #This is an array based way of mapping the right funciton
            #to the right index.
            functions = [min, max, min, max]
            for i in range(len(functions)):
                try:
                    shp_extent[i] = functions[i](shp_extent[i],feature_extent[i])
                except TypeError:
                    #need to cast to list becuase it gets returned as a tuple 
                    #and we can't assign to a tuple's index, also need to 
                    #define this as the initial state
                    shp_extent = list(feature_extent)

    #shp_extent = [xmin, xmax, ymin, ymax]
    tiff_width = int(numpy.ceil(abs(shp_extent[1] - shp_extent[0]) / xRes))
    tiff_height = int(numpy.ceil(abs(shp_extent[3] - shp_extent[2]) / yRes))

    if rasterFile != None:
        driver = gdal.GetDriverByName('GTiff')
    else:
        rasterFile = ''
        driver = gdal.GetDriverByName('MEM')
    #1 means only create 1 band
    raster = driver.Create(rasterFile, tiff_width, tiff_height, 1, format)
    raster.GetRasterBand(1).SetNoDataValue(nodata)

    #Set the transform based on the upper left corner and given pixel
    #dimensions
    raster_transform = [shp_extent[0], xRes, 0.0, shp_extent[3], 0.0, -yRes]
    raster.SetGeoTransform(raster_transform)

    #Use the same projection on the raster as the shapefile
    srs = osr.SpatialReference()
    srs.ImportFromWkt(shp.GetLayer(0).GetSpatialRef().__str__())
    raster.SetProjection(srs.ExportToWkt())

    #Initialize everything to nodata
    raster.GetRasterBand(1).Fill(nodata)
    raster.GetRasterBand(1).FlushCache()

    return raster

def vectorize_points(shapefile, datasource_field, raster, randomize_points=False, mask_convex_hull=False):
    """Takes a shapefile of points and a field defined in that shapefile
       and interpolates the values in the points onto the given raster

       shapefile - ogr datasource of points
       datasource_field - a field in shapefile
       raster - a gdal raster must be in the same projection as shapefile

       returns nothing
       """

    #Define the initial bounding box
    LOGGER.info("vectorizing points")
    gt = raster.GetGeoTransform()
    #order is left, top, right, bottom of rasterbounds
    bounding_box = [gt[0], gt[3], gt[0] + gt[1] * raster.RasterXSize,
                    gt[3] + gt[5] * raster.RasterYSize]

    def in_bounds(point):
        return point[0] <= bounding_box[2] and point[0] >= bounding_box[0] \
            and point[1] <= bounding_box[1] and point[1] >= bounding_box[3]

    layer = shapefile.GetLayer(0)
    count = 0
    point_list = []
    value_list = []

    #Calculate a small amount to perturb points by so that we don't
    #get a linear Delauney triangle, the 1e-6 is larger than eps for
    #floating point, but large enough not to cause errors in interpolation.
    delta_difference = 1e-6 * min(abs(gt[1]),abs(gt[5]))
    if randomize_points:
        random_array = numpy.random.randn(layer.GetFeatureCount(), 2)
        random_offsets = random_array*delta_difference
    else:
        random_offsets = numpy.zeros((layer.GetFeatureCount(), 2))

    for feature_id in range(layer.GetFeatureCount()):
        feature = layer.GetFeature(feature_id)
        geometry = feature.GetGeometryRef()
        #Here the point geometry is in the form x,y (col, row)
        point = geometry.GetPoint()
        if in_bounds(point):
            value = feature.GetField(datasource_field)
            #Add in the numpy notation which is row, col
            point_list.append([point[1]+random_offsets[feature_id,1],
                               point[0]+random_offsets[feature_id,0]])
            value_list.append(value)

    point_array = numpy.array(point_list)
    value_array = numpy.array(value_list)

    band = raster.GetRasterBand(1)
    nodata = band.GetNoDataValue()

    #Create grid points for interpolation outputs later
    #top-bottom:y_stepsize, left-right:x_stepsize
    
    #Make as an integer grid then divide subtract by bounding box parts
    #so we don't get a roundoff error and get off by one pixel one way or 
    #the other
    grid_y, grid_x = numpy.mgrid[0:band.YSize, 0:band.XSize]
    grid_y = grid_y * gt[5] + bounding_box[1]
    grid_x = grid_x * gt[1] + bounding_box[0]

    band = raster.GetRasterBand(1)
    nodata = band.GetNoDataValue()

    LOGGER.info("Writing interpolating with griddata")
    raster_out_array = scipy.interpolate.griddata(point_array,
        value_array, (grid_y, grid_x), 'nearest', nodata)
    LOGGER.info("Writing result to output array")
    band.WriteArray(raster_out_array,0,0)

def aggregate_raster_values(raster, shapefile, shapefile_field, operation, 
                            aggregate_uri = None, intermediate_directory = '',
                            ignore_nodata = True):
    """Collect all the raster values that lie in shapefile depending on the value
        of operation

        raster - a GDAL dataset of some sort of value
        shapefile - an OGR datasource that probably overlaps raster 
        shapefile_field - a string indicating which key in shapefile to associate
           the output dictionary values with whose values are associated with ints
        operation - a string of one of ['mean', 'sum']
        aggregate_uri - (optional) a uri to an output raster that has the aggreate
            values burned onto the masked raster
        intermediate_directory - (optional) a path to a directory to hold 
            intermediate files
        ignore_nodata - (optional) if operation == 'mean' then it does not account
            for nodata pixels when determing the average, otherwise all pixels in
            the AOI are used for calculation of the mean.

        returns a dictionary whose keys are the values in shapefile_field and values
            are the aggregated values over raster.  If no values are aggregated
            contains 0."""
    
    #Generate a temporary mask filename
    temporary_mask_filename = 'aggr_mask_%s.tif' % \
        ''.join([random.choice(string.letters) for i in range(6)])

    temporary_mask_filename = os.path.join(intermediate_directory, 
                                           temporary_mask_filename)

    raster_band = raster.GetRasterBand(1)
    raster_nodata = float(raster_band.GetNoDataValue())

    clipped_raster = vectorize_rasters([raster], lambda x: float(x),
            aoi=shapefile, raster_out_uri='clipped_raster.tif',
            datatype=gdal.GDT_Float32, nodata=raster_nodata)
    clipped_band = clipped_raster.GetRasterBand(1)

    #This should be a value that's not in shapefile[shapefile_field]
    mask_nodata = -1.0
    mask_dataset = new_raster_from_base(clipped_raster, 
        temporary_mask_filename, 'GTiff', mask_nodata, gdal.GDT_Int32)

    mask_band = mask_dataset.GetRasterBand(1)
    mask_band.Fill(mask_nodata)

    shapefile_layer = shapefile.GetLayer()
    gdal.RasterizeLayer(mask_dataset, [1], shapefile_layer,
                        options = ['ATTRIBUTE=%s' % shapefile_field])

    mask_dataset.FlushCache()
    mask_band = mask_dataset.GetRasterBand(1)

    #This will store the sum/count with index of shapefile attribute
    aggregate_dict_values = {}
    aggregate_dict_counts = {}

    #Loop over each row in out_band
    for row_index in range(clipped_band.YSize):
        mask_array = mask_band.ReadAsArray(0,row_index,mask_band.XSize,1)
        clipped_array = clipped_band.ReadAsArray(0,row_index,clipped_band.XSize,1)


        for attribute_id in numpy.unique(mask_array):
            #ignore masked values
            if attribute_id == mask_nodata:
                continue

            #Only consider values which lie in the polygon for attribute_id
            masked_values = clipped_array[mask_array == attribute_id]
            if ignore_nodata:
                #Only consider values which are not nodata values
                masked_values = masked_values[masked_values != raster_nodata]
                attribute_sum = numpy.sum(masked_values)
            else:
                #We leave masked_values alone, but only sum the non-nodata 
                #values
                attribute_sum = \
                    numpy.sum(masked_values[masked_values != raster_nodata])

            try:
                aggregate_dict_values[attribute_id] += attribute_sum
                aggregate_dict_counts[attribute_id] += masked_values.size
            except KeyError:
                aggregate_dict_values[attribute_id] = attribute_sum
                aggregate_dict_counts[attribute_id] = masked_values.size
            
    result_dict = {}
    for attribute_id in aggregate_dict_values:
        if operation == 'sum':
            result_dict[attribute_id] = aggregate_dict_values[attribute_id]
        elif operation == 'mean':
            if aggregate_dict_counts[attribute_id] != 0.0:
                result_dict[attribute_id] = aggregate_dict_values[attribute_id] / \
                    aggregate_dict_counts[attribute_id]
            else:
                result_dict[attribute_id] = 0.0
        else:
            LOGGER.warn("%s operation not defined" % operation)
    
    if aggregate_uri != None:
        def aggregate_map_function(x):
            try:
                return result_dict[x]
            except:
                return raster_nodata

        vop = numpy.vectorize(aggregate_map_function)

        aggregate_dataset = new_raster_from_base(clipped_raster, aggregate_uri,
            'GTiff', raster_nodata, gdal.GDT_Float32)
        aggregate_band = aggregate_dataset.GetRasterBand(1)
        
        for row_index in range(aggregate_band.YSize):
            mask_array = mask_band.ReadAsArray(0,row_index,mask_band.XSize,1)

            aggregate_array = vop(mask_array)
            aggregate_band.WriteArray(aggregate_array, 0,row_index)

        calculate_raster_stats(aggregate_dataset)

    mask_band = None
    mask_dataset = None
    os.remove(temporary_mask_filename)

    return result_dict


def aggregate_raster_values_uri(
    raster_uri, shapefile_uri, shapefile_field, operation, ignore_nodata=True, 
    threshold_amount_lookup=None):
    """Collect all the raster values that lie in shapefile depending on the value
        of operation

        raster - a uri to a GDAL dataset of some sort of value
        shapefile - a uri to a OGR datasource that probably overlaps raster 
        shapefile_field - a string indicating which key in shapefile to associate
           the output dictionary values with whose values are associated with ints
        operation - a string of one of ['mean', 'sum']
        ignore_nodata - (optional) if operation == 'mean' then it does not account
            for nodata pixels when determing the average, otherwise all pixels in
            the AOI are used for calculation of the mean.
        threshold_amount_lookup - (optional) a dictionary indexing the shapefile_field's
            to threshold amounts to subtract from the aggregate value.  The result
            will be clamped to zero.

        returns a dictionary whose keys are the values in shapefile_field and values
            are the aggregated values over raster.  If no values are aggregated
            contains 0."""
    

    #Generate a temporary mask filename
    raster_nodata = get_nodata_from_uri(raster_uri)

    out_pixel_size = get_cell_size_from_uri(raster_uri)
    clipped_raster_uri = temporary_filename()
    vectorize_datasets(
        [raster_uri], float, clipped_raster_uri, gdal.GDT_Float32,
        raster_nodata, out_pixel_size, "intersection", 
        dataset_to_align_index=0, aoi_uri=shapefile_uri)
    clipped_raster = gdal.Open(clipped_raster_uri)

    #This should be a value that's not in shapefile[shapefile_field]
    mask_nodata = -1
    temporary_mask_filename = temporary_filename()
    mask_dataset = new_raster_from_base(
        clipped_raster, temporary_mask_filename, 'GTiff', mask_nodata,
        gdal.GDT_Int32, fill_value=mask_nodata)

    shapefile = ogr.Open(shapefile_uri)
    shapefile_layer = shapefile.GetLayer()
    gdal.RasterizeLayer(
        mask_dataset, [1], shapefile_layer, 
        options=['ATTRIBUTE=%s' % shapefile_field])

    mask_dataset.FlushCache()
    mask_band = mask_dataset.GetRasterBand(1)

    #This will store the sum/count with index of shapefile attribute
    aggregate_dict_values = {}
    aggregate_dict_counts = {}

    #Loop over each row in out_band
    clipped_band = clipped_raster.GetRasterBand(1)
    for row_index in range(clipped_band.YSize):
        mask_array = mask_band.ReadAsArray(0,row_index,mask_band.XSize,1)
        clipped_array = clipped_band.ReadAsArray(0,row_index,clipped_band.XSize,1)

        for attribute_id in numpy.unique(mask_array):
            #ignore masked values
            if attribute_id == mask_nodata:
                continue

            #Only consider values which lie in the polygon for attribute_id
            masked_values = clipped_array[mask_array == attribute_id]
            if ignore_nodata:
                #Only consider values which are not nodata values
                masked_values = masked_values[masked_values != raster_nodata]
                attribute_sum = numpy.sum(masked_values)
            else:
                #We leave masked_values alone, but only sum the non-nodata 
                #values
                attribute_sum = \
                    numpy.sum(masked_values[masked_values != raster_nodata])

            try:
                aggregate_dict_values[attribute_id] += attribute_sum
                aggregate_dict_counts[attribute_id] += masked_values.size
            except KeyError:
                aggregate_dict_values[attribute_id] = attribute_sum
                aggregate_dict_counts[attribute_id] = masked_values.size
            
    result_dict = {}
    for attribute_id in aggregate_dict_values:
        if threshold_amount_lookup != None:
            adjusted_amount = max(
                aggregate_dict_values[attribute_id] - 
                threshold_amount_lookup[attribute_id], 0.0)
        else:
            adjusted_amount = aggregate_dict_values[attribute_id]
        if operation == 'sum':
            result_dict[attribute_id] = adjusted_amount
        elif operation == 'mean':
            if aggregate_dict_counts[attribute_id] != 0.0:
                result_dict[attribute_id] = (
                    adjusted_amount / aggregate_dict_counts[attribute_id])
            else:
                result_dict[attribute_id] = 0.0
        else:
            LOGGER.warn("%s operation not defined" % operation)
    
    mask_band = None
    mask_dataset = None
    return result_dict


def reclassify_by_dictionary(dataset, rules, output_uri, format, nodata,
    datatype, default_value=None):
    """Convert all the non-nodata values in dataset to the values mapped to 
        by rules.  If there is no rule for an input value it is replaced by
        default_value.  If default_value is None, nodata is used.

        If default_value is None, the default_value will only be used if a pixel
        is not nodata and the pixel does not have a rule defined for its value.
        If the user wishes to have nodata values also mapped to the default
        value, this can be achieved by defining a rule such as:

            rules[dataset_nodata] = default_value

        Doing so will override the default nodata behaviour.

        dataset - GDAL raster dataset
        rules - a dictionary of the form: 
            {'dataset_value1' : 'output_value1', ... 
             'dataset_valuen' : 'output_valuen'}
             used to map dataset input types to output
        output_uri - The location to hold the output raster on disk
        format - either 'MEM' or 'GTiff'
        nodata - output raster dataset nodata value
        datatype - a GDAL output type
        default=None - the value to be used if a reclass rule is not defined.

        return the mapped raster as a GDAL dataset"""

    # If a default value is not set, assume that the default value is the
    # used-defined nodata value.
    # If a default value is defined by the user, assume that nodata values
    # should remain nodata.  This check is sensitive to different nodata values
    # between input and output rasters.  This modification is made on a copy of
    # the rules dictionary.
    if default_value == None:
        default_value = nodata
        LOGGER.debug('Default value not user-defined, using nodata value (%s)',
            nodata)
    else:
        LOGGER.debug('User defined default value=%s', default_value)
        rules = rules.copy()
        if nodata not in rules:
            in_nodata = dataset.GetRasterBand(1).GetNoDataValue()
            rules[in_nodata] = nodata
            LOGGER.debug('Creating a nodata mapping rule: {%s: %s}', in_nodata,
                nodata)

    LOGGER.info('Creating a new raster for reclassification')
    output_dataset = new_raster_from_base(dataset, output_uri, format, nodata, 
                                          datatype)
    LOGGER.info('Starting cythonized reclassification')
    raster_cython_utils.reclassify_by_dictionary(
        dataset, rules, output_uri, format, default_value, datatype, output_dataset,)
    LOGGER.info('Finished reclassification')

    calculate_raster_stats(output_dataset)

    return output_dataset

def flow_accumulation_dinf(flow_direction, dem, flow_accumulation_uri):
    """Creates a raster of accumulated flow to each cell.
    
        flow_direction - (input) A raster showing direction of flow out of 
            each cell with directional values given in radians.
        dem - (input) heightmap raster that aligns perfectly for flow_direction
        flow_accumulation_uri - (input) A string to the flow accumulation output
           raster.  The output flow accumulation raster set
        
        returns flow accumulation raster"""

    #Track for logging purposes
    initial_time = time.clock()

    flow_accumulation_dataset = new_raster_from_base(flow_direction, 
        flow_accumulation_uri, 'GTiff', -1.0, gdal.GDT_Float32)
    
    flow_accumulation_band = flow_accumulation_dataset.GetRasterBand(1)
    flow_accumulation_band.Fill(-1.0)

    flow_direction_band = flow_direction.GetRasterBand(1)
    flow_direction_nodata = flow_direction_band.GetNoDataValue()
    flow_direction_array = flow_direction_band.ReadAsArray().flatten()

    n_rows = flow_accumulation_dataset.RasterYSize
    n_cols = flow_accumulation_dataset.RasterXSize

    def calc_index(i, j):
        """used to abstract the 2D to 1D index calculation below"""
        if i >= 0 and i < n_rows and j >= 0 and j < n_cols:
            return i * n_cols + j
        else:
            return -1

    #set up variables to hold the sparse system of equations
    #upper bound  n*m*5 elements
    b_vector = numpy.zeros(n_rows * n_cols)

    #holds the rows for diagonal sparse matrix creation later, row 4 is 
    #the diagonal
    a_matrix = numpy.zeros((9, n_rows * n_cols))
    diags = numpy.array([-n_cols-1, -n_cols, -n_cols+1, -1, 0, 
                       1, n_cols-1, n_cols, n_cols+1])
    
    #Determine the inflow directions based on index offsets.  It's written 
    #in terms of radian 4ths for easier readability and maintaince. 
    #Derived all this crap from page 36 in Rich's notes.
    inflow_directions = {( 0, 1): (4.0/4.0 * numpy.pi, 5, False),
                         (-1, 1): (5.0/4.0 * numpy.pi, 2, True),
                         (-1, 0): (6.0/4.0 * numpy.pi, 1, False),
                         (-1,-1): (7.0/4.0 * numpy.pi, 0, True),
                         ( 0,-1): (0.0, 3, False),
                         ( 1,-1): (1.0/4.0 * numpy.pi, 6, True),
                         ( 1, 0): (2.0/4.0 * numpy.pi, 7, False),
                         ( 1, 1): (3.0/4.0 * numpy.pi, 8, True)}

    LOGGER.info('Building diagonals for linear advection diffusion system.')
    for row_index in range(n_rows):
        for col_index in range(n_cols):
            #diagonal element row_index,j always in bounds, calculate directly
            cell_index = calc_index(row_index, col_index)
            a_matrix[4, cell_index] = 1
            
            #Check to see if the current flow angle is defined, if not then
            #set local flow accumulation to 0
            local_flow_angle = flow_direction_array[cell_index]
            if local_flow_angle == flow_direction_nodata:
                #b_vector already == 0 at this point, so just continue
                continue

            #Otherwise, define 1.0 to indicate base flow from the pixel
            b_vector[cell_index] = 1.0

            #Determine inflow neighbors
            for (row_offset, col_offset), (inflow_angle, diagonal_offset, diagonal_inflow) in \
                    inflow_directions.iteritems():
                try:
                    neighbor_index = calc_index(row_index+row_offset, 
                                                col_index+col_offset)
                    flow_angle = flow_direction_array[neighbor_index]

                    if flow_angle == flow_direction_nodata:
                        continue

                    #If this delta is within pi/4 it means there's an inflow
                    #direction, see diagram on pg 36 of Rich's notes
                    delta = abs(flow_angle - inflow_angle)

                    if delta < numpy.pi/4.0 or (2*numpy.pi - delta) < numpy.pi/4.0:
                        if diagonal_inflow:
                            #We want to measure the far side of the unit triangle
                            #so we measure that angle UP from theta = 0 on a unit
                            #circle
                            delta = numpy.pi/4-delta

                        #Taking absolute value because it might be on a 0,-45 
                        #degree angle
                        inflow_fraction = abs(numpy.tan(delta))
                        if not diagonal_inflow:
                            #If not diagonal then we measure the direct flow in
                            #which is the inverse of the tangent function
                            inflow_fraction = 1-inflow_fraction
                        
                        #Finally set the appropriate inflow variable
                        a_matrix[diagonal_offset, neighbor_index] = \
                            -inflow_fraction

                except IndexError:
                    #This will occur if we visit a neighbor out of bounds
                    #it's okay, just skip it
                    pass


    matrix = scipy.sparse.spdiags(a_matrix, diags, n_rows * n_cols, n_rows * n_cols, 
                                  format="csc")

    LOGGER.info('Solving via sparse direct solver')
    solver = scipy.sparse.linalg.factorized(matrix)
    result = solver(b_vector)
    LOGGER.info('(' + str(time.clock() - initial_time) + 's elapsed)')

    #Result is a 1D array of all values, put it back to 2D
    result.resize(n_rows,n_cols)

    flow_accumulation_band.WriteArray(result)

    return flow_accumulation_dataset


def calculate_slope(dem_dataset_uri, slope_uri, aoi_uri=None):
    """Generates raster maps of slope.  Follows the algorithm described here:
        http://webhelp.esri.com/arcgiSDEsktop/9.3/index.cfm?TopicName=How%20Slope%20works 
        
        dem_dataset_uri - (input) a URI to a  single band raster of z values.
        slope_uri - (input) a path to the output slope uri
        aoi_uri - (optional) a uri to an AOI input

        returns nothing"""

    LOGGER = logging.getLogger('calculateSlope')
    LOGGER.debug(dem_dataset_uri)
    dem_dataset = gdal.Open(dem_dataset_uri)
    out_pixel_size = pixel_size(dem_dataset)
    LOGGER.debug(out_pixel_size)
    _, dem_nodata = extract_band_and_nodata(dem_dataset)

    dem_small_uri = temporary_filename()
    #cast the dem to a floating point one if it's not already
    dem_float_nodata = float(dem_nodata)

    vectorize_datasets(
        [dem_dataset_uri], lambda x: float(x), dem_small_uri,
        gdal.GDT_Float32, dem_float_nodata, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=aoi_uri)

    LOGGER.debug("calculate slope")

    slope_nodata = -1.0
    dem_small_dataset = gdal.Open(dem_small_uri)
    new_raster_from_base(
        dem_small_dataset, slope_uri, 'GTiff', slope_nodata, gdal.GDT_Float32)
    raster_cython_utils._cython_calculate_slope(dem_small_uri, slope_uri)

    slope_dataset = gdal.Open(slope_uri, gdal.GA_Update)
    calculate_raster_stats(slope_dataset)


def clip_dataset_uri(
        source_dataset_uri, aoi_datasource_uri, out_dataset_uri,
        assert_projections):
    """This function will clip source_dataset to the bounding box of the 
        polygons in aoi_datasource and mask out the values in source_dataset
        outside of the AOI with the nodata values in source_dataset.

        source_dataset_uri - uri to single band GDAL dataset to clip
        aoi_datasource_uri - uri to ogr datasource
        out_dataset_uri - path to disk for the clipped datset
        assert_projections - a boolean value for whether the dataset needs to be
            projected
        
        returns nothing"""
    #NOTE: I have altered the signature of this function compared to the
    # previous one because I want to be able to use vectorize_datasets to clip
    # two sources that are not projected
    
    #raise NotImplementedError('clip_dataset_uri is not implemented yet')
    
    # I choose to open up the dataset here because I want to use the
    # calculate_value_not_in_dataset function which requires a datasource. For
    # now I do not want to create a uri version of that function.
    source_dataset = gdal.Open(source_dataset_uri)
    
    band, nodata = extract_band_and_nodata(source_dataset)
    datatype = band.DataType

    if nodata is None:
        nodata = calculate_value_not_in_dataset(source_dataset)

    LOGGER.info("clip_dataset nodata value is %s" % nodata)

    def op(x):
        return x

    source_dataset = None

    pixel_size = get_cell_size_from_uri(source_dataset_uri) 

    vectorize_datasets(
            [source_dataset_uri], op, out_dataset_uri, datatype, nodata,
            pixel_size, 'intersection', aoi_uri=aoi_datasource_uri,
            assert_datasets_projected=assert_projections)

def clip_dataset(source_dataset, aoi_datasource, out_dataset_uri):
    """This function will clip source_dataset to the bounding box of the 
        polygons in aoi_datasource and mask out the values in source_dataset
        outside of the AOI with the nodata values in source_dataset.

        source_dataset - single band GDAL dataset to clip
        aoi_datasource - collection of polygons
        out_dataset_uri - path to disk for the clipped

        returns the clipped dataset that lives at out_dataset_uri"""

    band, nodata = extract_band_and_nodata(source_dataset)

    if nodata is None:
        nodata = calculate_value_not_in_dataset(source_dataset)

    LOGGER.info("clip_dataset nodata value is %s" % nodata)

    def op(x):
        return x

    clipped_dataset = vectorize_rasters([source_dataset], op, aoi=aoi_datasource, 
                      raster_out_uri = out_dataset_uri, 
                      datatype = band.DataType, nodata=nodata)
    return clipped_dataset

def extract_band_and_nodata(dataset, get_array=False):
    """It's often useful to get the first band and corresponding nodata value
        for a dataset.  This function does that.

        dataset - a GDAL dataset
        get_array - if True also returns the dataset as a numpy array

        returns (first GDAL band in dataset, nodata value for that band"""

    band = dataset.GetRasterBand(1)
    nodata = band.GetNoDataValue()

    if get_array:
        array = band.ReadAsArray()
        return band, nodata, array

    #Otherwise just return the band and nodata
    return band, nodata

def calculate_value_not_in_dataset(dataset):
    """Calcualte a value not contained in a dataset.  Useful for calculating
        nodata values.

        dataset - a GDAL dataset

        returns a number not contained in the dataset"""

    band,nodata,array = extract_band_and_nodata(dataset, get_array = True)
    return calculate_value_not_in_array(array)

def calculate_value_not_in_array(array):
    """This function calcualtes a number that is not in the given array, if 
        possible.

        array - a numpy array

        returns a number not in array that is not "close" to any value in array
            ideally calculated in the middle of the maximum delta between any two
            consecutive numbers in the array"""

    sorted_array = numpy.sort(numpy.unique(array.flatten()))
    #Make sure we don't have a single unique value, if we do just go + or - 
    #1 at the end
    if len(sorted_array) > 1:
        array_type = type(sorted_array[0])
        diff_array = numpy.array([-1,1])
        deltas = scipy.signal.correlate(sorted_array, diff_array, mode='valid')
    
        max_delta_index = numpy.argmax(deltas)

        #Try to return the average of the maximum delta
        if deltas[max_delta_index] > 0:
            return array_type((sorted_array[max_delta_index+1] +
                               sorted_array[max_delta_index])/2.0)

    #Else, all deltas are too small so go one smaller or one larger than the 
    #min or max.  Catching an exception in case there's an overflow.
    try:
        return sorted_array[0]-1
    except:
        return sorted_array[-1]+1


def create_rat_uri(dataset_uri, attr_dict, column_name):
    """URI wrapper for create_rat"""
    dataset = gdal.Open(dataset_uri, gdal.GA_Update)
    create_rat(dataset, attr_dict, column_name)
    dataset = None


def create_rat(dataset, attr_dict, column_name):
    """Create a raster attribute table

        dataset - a GDAL raster dataset to create the RAT for 
        attr_dict - a dictionary with keys that point to a primitive type
           {integer_id_1: value_1, ... integer_id_n: value_n}
        column_name - a string for the column name that maps the values
        
        returns - a GDAL raster dataset with an updated RAT
        """

    band = dataset.GetRasterBand(1)

    # If there was already a RAT associated with this dataset it will be blown
    # away and replaced by a new one
    LOGGER.warn('Blowing away any current raster attribute table')
    rat = gdal.RasterAttributeTable()

    rat.SetRowCount(len(attr_dict))
    
    # create columns
    rat.CreateColumn('Value', gdal.GFT_Integer, gdal.GFU_MinMax)
    rat.CreateColumn(column_name, gdal.GFT_String, gdal.GFU_Name)

    row_count = 0
    for key in sorted(attr_dict.keys()):
        rat.SetValueAsInt(row_count, 0, int(key))
        rat.SetValueAsString(row_count, 1, attr_dict[key])
        row_count += 1
    
    band.SetDefaultRAT(rat)
    return dataset


def get_raster_properties(dataset):
    """Get the width, height, X size, and Y size of the dataset and return the
        values in a dictionary. 
        *This function can be expanded to return more properties if needed*

       dataset - a GDAL raster dataset to get the properties from
        
       returns - a dictionary with the properties stored under relevant keys.
           The current list of things returned is:
           width (w-e pixel resolution), height (n-s pixel resolution), 
           XSize, YSize
    """
    dataset_dict = {}
    gt = dataset.GetGeoTransform()
    dataset_dict['width'] = float(gt[1])
    dataset_dict['height'] = float(gt[5])
    dataset_dict['x_size'] = dataset.GetRasterBand(1).XSize    
    dataset_dict['y_size'] = dataset.GetRasterBand(1).YSize    
    LOGGER.debug('Raster_Properties : %s', dataset_dict)
    return dataset_dict

def gdal_cast(value, gdal_type):
    """Cast value to the given gdal type.

        value - some raw python value
        gdal_type - one of: gdal.GDT_CInt16, gdal.GDT_CInt32, gdal.GDT_Int16, 
            gdal.GDT_Int32, gdal.GDT_UInt16, gdal.GDT_UInt32, gdal.GDT_CFloat64, 
            gdal.GDT_CFloat32, gdal.GDT_Float64, gdal.GDT_Float32, gdal.GDT_Byte

        return gdal_type(value) (basterdized cast notation)"""

    gdal_int_types = [gdal.GDT_CInt16, gdal.GDT_CInt32, gdal.GDT_Int16, 
                      gdal.GDT_Int32, gdal.GDT_UInt16, gdal.GDT_UInt32, 
                      gdal.GDT_Byte]
    gdal_float_types = [gdal.GDT_CFloat64, gdal.GDT_CFloat32, 
                        gdal.GDT_Float64, gdal.GDT_Float32]

    if gdal_type in gdal_int_types:
        value = numpy.int(value)
    if gdal_type in gdal_float_types:
        value = numpy.float(value)

    return value


def resample_dataset(
    original_dataset_uri, pixel_size, output_uri,
    resample_method=gdal.GRA_Bilinear):
    """A function to resample a datsaet to larger or smaller pixel sizes

        original_dataset_uri - a GDAL dataset
        pixel_size - the output pixel size in projected units (usually meters)
        output_uri - the location of the new resampled GDAL dataset
        resample_method - (optional) the resampling technique, default is
            gdal.GRA_Bilinear

        returns nothing"""
    original_dataset = gdal.Open(original_dataset_uri)
    original_band, original_nodata = extract_band_and_nodata(original_dataset)

    original_sr = osr.SpatialReference()
    original_sr.ImportFromWkt(original_dataset.GetProjection())
    geo_t = original_dataset.GetGeoTransform()
    x_size = original_dataset.RasterXSize # Raster xsize
    y_size = original_dataset.RasterYSize # Raster ysize

    #create the new x and y size
    new_x_size = int(x_size * geo_t[1] / pixel_size + 0.5)
    new_y_size = int(abs(y_size * geo_t[5] / pixel_size) + 0.5)

    gdal_driver = gdal.GetDriverByName('GTiff')
    output_dataset = gdal_driver.Create(
        output_uri, new_x_size, new_y_size, 1, original_band.DataType)

    output_dataset.GetRasterBand(1).SetNoDataValue(original_nodata)

    # Calculate the new geotransform
    output_geo = (geo_t[0], pixel_size, geo_t[2], geo_t[3], geo_t[4], -pixel_size)

    # Set the geotransform
    output_dataset.SetGeoTransform(output_geo)
    output_dataset.SetProjection(original_sr.ExportToWkt())

    # Perform the projection/resampling 
    gdal.ReprojectImage(original_dataset, output_dataset,
                        original_sr.ExportToWkt(), original_sr.ExportToWkt(),
                        gdal.GRA_Bilinear)

def reproject_dataset_uri(original_dataset_uri, *args, **kwargs):
    """A URI wrapper for reproject dataset that opens the original_dataset_uri
        before passing it to reproject_dataset.

       original_dataset_uri - a URI to a gdal Dataset on disk

       All other arguments to reproject_dataset are passed in.

       return - nothing"""

    original_dataset = gdal.Open(original_dataset_uri)
    reproject_dataset(original_dataset, *args, **kwargs)

def _experimental_reproject_dataset_uri(
        original_dataset_uri, pixel_spacing, output_wkt, output_uri):
    """A function to reproject and resample a GDAL dataset given an output
        pixel size and output reference. Will use the datatype and nodata value
        from the original dataset.

       original_dataset_uri - a URI to a gdal Dataset to written to disk
       pixel_spacing - output dataset pixel size in projected linear units (probably meters)
       output_wkt - output project in Well Known Text (the result of ds.GetProjection())
       output_uri - location on disk to dump the reprojected dataset

       return projected dataset"""
    # Get the nodata value and datatype from the original dataset 
    output_type = get_datatype_from_uri(original_dataset_uri)
    out_nodata = get_nodata_from_uri(original_dataset_uri) 
   
    original_dataset = gdal.Open(original_dataset_uri)

    original_wkt = original_dataset.GetProjection()

    # Create a virtual raster that is projected based on the output WKT. This
    # vrt does not save to disk and is used to get the proper projected bounding
    # box and size. 
    vrt = gdal.AutoCreateWarpedVRT(
            original_dataset, None, output_wkt, gdal.GRA_Bilinear)
    
    geo_t = vrt.GetGeoTransform()
    x_size = vrt.RasterXSize # Raster xsize
    y_size = vrt.RasterYSize # Raster ysize
    
    # Calculate the extents of the projected dataset. These values will be used
    # to properly set the resampled size for the output dataset
    (ulx, uly) = (geo_t[0], geo_t[3])
    (lrx, lry) = (geo_t[0] + geo_t[1] * x_size, geo_t[3] + geo_t[5] * y_size)
    
    LOGGER.debug("ulx %s, uly %s, lrx %s, lry %s" % (ulx, uly, lrx, lry))
   
    gdal_driver = gdal.GetDriverByName('GTiff')

    # Create the output dataset to receive the projected output, with the proper
    # resampled arrangement. 
    output_dataset = gdal_driver.Create(
            output_uri, int((lrx - ulx)/pixel_spacing),
            int((uly - lry)/pixel_spacing), 1, output_type)

    # Set the nodata value for the output dataset  
    output_dataset.GetRasterBand(1).SetNoDataValue(out_nodata)

    # Calculate the new geotransform
    output_geo = (ulx, pixel_spacing, geo_t[2], uly, geo_t[4], -pixel_spacing)

    # Set the geotransform
    output_dataset.SetGeoTransform(output_geo)
    output_dataset.SetProjection(output_wkt)

    # Perform the projection/resampling 
    gdal.ReprojectImage(
            original_dataset, output_dataset, original_wkt, output_wkt,
            gdal.GRA_Bilinear)

    calculate_raster_stats(output_dataset)

def reproject_dataset(original_dataset, pixel_spacing, output_wkt, output_uri,
                      output_type = gdal.GDT_Float32):
    """A function to reproject and resample a GDAL dataset given an output pixel size
        and output reference and uri.

       original_dataset - a gdal Dataset to reproject
       pixel_spacing - output dataset pixel size in projected linear units (probably meters)
       output_wkt - output project in Well Known Text (the result of ds.GetProjection())
       output_uri - location on disk to dump the reprojected dataset
       output_type - gdal type of the output    

       return projected dataset"""

    original_sr = osr.SpatialReference()
    original_sr.ImportFromWkt(original_dataset.GetProjection())

    output_sr = osr.SpatialReference()
    output_sr.ImportFromWkt(output_wkt)

    tx = osr.CoordinateTransformation(original_sr, output_sr)

    # Get the Geotransform vector
    geo_t = original_dataset.GetGeoTransform()
    x_size = original_dataset.RasterXSize # Raster xsize
    y_size = original_dataset.RasterYSize # Raster ysize
    # Work out the boundaries of the new dataset in the target projection
    (ulx, uly, _) = tx.TransformPoint(geo_t[0], geo_t[3])
    (lrx, lry, _) = tx.TransformPoint(geo_t[0] + geo_t[1]*x_size,
                                      geo_t[3] + geo_t[5]*y_size)

    gdal_driver = gdal.GetDriverByName('GTiff')
    # The size of the raster is given the new projection and pixel spacing
    # Using the values we calculated above. Also, setting it to store one band
    # and to use Float32 data type.

    LOGGER.debug("ulx %s, uly %s, lrx %s, lry %s" % (ulx, uly, lrx, lry))

    output_dataset = gdal_driver.Create(output_uri, int((lrx - ulx)/pixel_spacing), 
                              int((uly - lry)/pixel_spacing), 1, output_type)

    # Set the nodata value
    out_nodata = original_dataset.GetRasterBand(1).GetNoDataValue()
    output_dataset.GetRasterBand(1).SetNoDataValue(out_nodata)

    # Calculate the new geotransform
    output_geo = (ulx, pixel_spacing, geo_t[2],
               uly, geo_t[4], -pixel_spacing)

    # Set the geotransform
    output_dataset.SetGeoTransform(output_geo)
    output_dataset.SetProjection (output_sr.ExportToWkt())

    # Perform the projection/resampling 
    gdal.ReprojectImage(original_dataset, output_dataset,
                        original_sr.ExportToWkt(), output_sr.ExportToWkt(),
                        gdal.GRA_Bilinear)

    return output_dataset

def reproject_datasource_uri(original_ds_uri, output_wkt, output_uri):
    """URI wrapper for reproject_datasource that takes in the uri for the
        datasource that is to be projected instead of the datasource itself.
        This function directly calls reproject_datasource.

        original_ds_uri - a uri to an ogr datasource
        
        output_wkt - the desired projection as Well Known Text 
            (by layer.GetSpatialRef().ExportToWkt())
        
        output_uri - The path to where the new shapefile should be
            written to disk.
    
        returns - Nothing."""

    original_ds = ogr.Open(original_ds_uri)
    _ = reproject_datasource(original_ds, output_wkt, output_uri)

def reproject_datasource(original_datasource, output_wkt, output_uri):
    """Changes the projection of an ogr datasource by creating a new 
        shapefile based on the output_wkt passed in.  The new shapefile 
        then copies all the features and fields of the original_datasource 
        as its own.
    
        original_datasource - a ogr datasource
        output_wkt - the desired projection as Well Known Text 
            (by layer.GetSpatialRef().ExportToWkt())
        output_uri - The path to where the new shapefile should be written to disk.
    
        returns - The reprojected shapefile.
    """
    # if this file already exists, then remove it
    if os.path.isfile(output_uri):
        os.remove(output_uri)
    
    output_sr = osr.SpatialReference()
    output_sr.ImportFromWkt(output_wkt)
    
    # create a new shapefile from the orginal_datasource 
    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_datasource = output_driver.CreateDataSource(output_uri)
    
    # loop through all the layers in the orginal_datasource
    for original_layer in original_datasource:
        
        #Get the original_layer definition which holds needed attribute values
        original_layer_dfn = original_layer.GetLayerDefn()
        
        #Create the new layer for output_datasource using same name and geometry
        #type from original_datasource, but different projection
        output_layer = output_datasource.CreateLayer(
                original_layer_dfn.GetName(), output_sr, 
                original_layer_dfn.GetGeomType())
        
        #Get the number of fields in original_layer
        original_field_count = original_layer_dfn.GetFieldCount()
        
        #For every field, create a duplicate field and add it to the new 
        #shapefiles layer
        for fld_index in range(original_field_count):
            original_field = original_layer_dfn.GetFieldDefn(fld_index)
            output_field = ogr.FieldDefn(original_field.GetName(),
                    original_field.GetType())
            output_layer.CreateField(output_field)

        original_layer.ResetReading()
        
        #Get the spatial reference of the original_layer to use in transforming
        original_sr = original_layer.GetSpatialRef()

        #Create a coordinate transformation
        coord_trans = osr.CoordinateTransformation(original_sr, output_sr)

        #Copy all of the features in original_layer to the new shapefile
        for original_feature in original_layer:
            geom = original_feature.GetGeometryRef()
            
            #Transform the geometry into a format desired for the new projection
            geom.Transform(coord_trans)
            
            #Copy original_datasource's feature and set as new shapes feature
            output_feature = ogr.Feature(feature_def=output_layer.GetLayerDefn())
            output_feature.SetFrom(original_feature)
            output_feature.SetGeometry(geom)

            #For all the fields in the feature set the field values from the 
            #source field
            for fld_index2 in range(output_feature.GetFieldCount()):
                original_field_value = original_feature.GetField(fld_index2)
                output_feature.SetField(fld_index2, original_field_value)

            output_layer.CreateFeature(output_feature)
            output_feature = None

            original_feature = None

        original_layer = None

    return output_datasource

def build_contour_raster(dem_dataset, contour_value, out_uri):
    """Builds a raster contour given a DEM and contour value.  The new
        raster has pixels on if the contour would pass through that pixel.

        dem_dataset - gdal height dem
        contour_value - the contour height
        out_uri - a uri to the output file

        returns the new contour dataset"""

    contour_dataset = new_raster_from_base(
        dem_dataset, out_uri, 'GTiff', 255, gdal.GDT_Byte)

    _, _, dem_array = extract_band_and_nodata(dem_dataset, get_array = True)

    #Mask the values in the array to either be less than the contour value or 
    #greater than the contour value.  The result will be a 0 or 1 pixel
    dem_array = (dem_array - contour_value) < 0

    #difference filter to subtract neighboring values from the center
    difference_kernel = numpy.array([[-1, -1, -1],
                                  [-1, 8, -1],
                                  [-1, -1, -1]])
    contour_array = scipy.signal.convolve(
        dem_array, difference_kernel, mode='same')

    #We care about positive pixels with neighboring negative pixels, that's 
    #our definition of a contour
    contour_array = (contour_array > 0) * (contour_array < 8)

    #Write out the result
    contour_band = contour_dataset.GetRasterBand(1)
    contour_band.WriteArray(contour_array)

def unique_raster_values(dataset):
    """Returns a list of the unique integer values on the given dataset

        dataset - a gdal dataset of some integer type

        returns a list of dataset's unique non-nodata values"""

    band, nodata = extract_band_and_nodata(dataset)
    n_rows = band.YSize
    unique_values = numpy.array([])
    for row_index in xrange(n_rows):
        array = band.ReadAsArray(0, row_index, band.XSize, 1)[0]
        array = numpy.append(array, unique_values)
        unique_values = numpy.unique(array)

    unique_list = list(unique_values)
    if nodata in unique_list:
        unique_list.remove(nodata)
    return unique_list

def get_rat_as_dictionary(dataset):
    """Returns the RAT of the first band of dataset as a dictionary.

        dataset - a GDAL dataset that has a RAT associated with the first
            band

        returns a 2D dictionary where the first key is the column name and 
            second is the row number"""

    band = dataset.GetRasterBand(1)
    rat = band.GetDefaultRAT()
    n_columns = rat.GetColumnCount()
    n_rows = rat.GetRowCount()
    rat_dictionary = {}

    for col_index in xrange(n_columns):
        #Initialize an empty list to store row data and figure out the type
        #of data stored in that column.
        col_type = rat.GetTypeOfCol(col_index)
        col_name = rat.GetNameOfCol(col_index)
        rat_dictionary[col_name] = []

        #Now burn through all the rows to populate the column
        for row_index in xrange(n_rows):
            #This bit of python ugliness handles the known 3 types of gdal 
            #RAT fields.
            if col_type == gdal.GFT_Integer:
                value = rat.GetValueAsInt(row_index, col_index)
            elif col_type == gdal.GFT_Real:
                value = rat.GetValueAsDouble(row_index, col_index)
            else: 
                #If the type is not int or real, default to a string, 
                #I think this is better than testing for a string and raising
                #an exception if not
                value = rat.GetValueAsString(row_index, col_index)

            rat_dictionary[col_name].append(value)

    return rat_dictionary

def gaussian_filter_dataset_uri(
    dataset_uri, sigma, out_uri, out_nodata, temp_dir=None):
    """A callthrough to gaussian filter dataset"""

    dataset = gdal.Open(dataset_uri)
    gaussian_filter_dataset(
        dataset, sigma, out_uri, out_nodata, temp_dir=temp_dir)


def gaussian_filter_dataset(
    dataset, sigma, out_uri, out_nodata, temp_dir=None):
    """A memory efficient gaussian filter function that operates on 
       the dataset level and creates a new dataset that's filtered.
       It will treat any nodata value in dataset as 0, and re-nodata
       that area after the filter.

       dataset - a gdal dataset
       sigma - the sigma value of a gaussian filter
       out_uri - the uri output of the filtered dataset
       out_nodata - the nodata value of dataset
       temp_dir - (optional) the directory in which to store the memory
           mapped arrays.  If left off will use the system temp
           directory.  If defined the directory must exist on the
           filesystem (a temporary folder will be created inside of temp_dir).

       returns the filtered dataset created at out_uri"""

    LOGGER.info('setting up files in gaussian_filter_dataset')

    #Create a system temporary directory if one doesn't exist.
    #If the parameter temp_dir is None, the default tempfile location is used.
    #If the parameter temp_dir is a folder, a temp folder is created inside of
    #the defined folder.
    temp_dir = tempfile.mkdtemp(dir=temp_dir)

    source_filename = os.path.join(temp_dir, 'source.dat')
    mask_filename = os.path.join(temp_dir, 'mask.dat')
    dest_filename = os.path.join(temp_dir, 'dest.dat')

    source_band, source_nodata = extract_band_and_nodata(dataset)

    out_dataset = new_raster_from_base(
        dataset, out_uri, 'GTiff', out_nodata, gdal.GDT_Float32)
    out_band, out_nodata = extract_band_and_nodata(out_dataset)

    shape = (source_band.YSize, source_band.XSize)
    LOGGER.info('shape %s' % str(shape))

    LOGGER.info('make the source memmap at %s' % source_filename)
    source_array = numpy.memmap(
        source_filename, dtype='float32', mode='w+', shape=shape)
    LOGGER.info('make the mask memmap at %s' % mask_filename)
    mask_array = numpy.memmap(
        mask_filename, dtype='bool', mode='w+', shape=shape)
    LOGGER.info('make the dest memmap at %s' % dest_filename)
    dest_array = numpy.memmap(
        dest_filename, dtype='float32', mode='w+', shape=shape)

    LOGGER.info('load dataset into source array')
    for row_index in xrange(source_band.YSize):
        #Load a row so we can mask
        row_array = source_band.ReadAsArray(0, row_index, source_band.XSize, 1)
        #Just the mask for this row
        mask_row = row_array == source_nodata
        row_array[mask_row] = 0.0
        source_array[row_index,:] = row_array

        #remember the mask in the memory mapped array
        mask_array[row_index,:] = mask_row

    LOGGER.info('gaussian filter')
    scipy.ndimage.filters.gaussian_filter(
        source_array, sigma = sigma, output = dest_array)

    LOGGER.info('mask the result back to nodata where originally nodata')
    dest_array[mask_array] = out_nodata

    LOGGER.info('write to gdal object')
    out_band.WriteArray(dest_array)

    calculate_raster_stats(out_dataset)

    LOGGER.info('deleting %s' % temp_dir)
    dest_array = None
    mask_array = None
    source_array = None
    out_band = None
    #Turning on ignore_errors = True in case we can't remove the 
    #the temporary directory
    shutil.rmtree(temp_dir, ignore_errors = True)

    out_dataset.FlushCache()
    return out_dataset

def reclassify_dataset_uri(
    dataset_uri, value_map, raster_out_uri, out_datatype, out_nodata,
    exception_flag='none'):
    """A callthrough for the reclassify_dataset function that is uri only"""

    dataset = gdal.Open(dataset_uri)
    reclassify_dataset(
        dataset, value_map, raster_out_uri, out_datatype, out_nodata,
        exception_flag=exception_flag)
    

def reclassify_dataset(
    dataset, value_map, raster_out_uri, out_datatype, out_nodata,
    exception_flag='none'):

    """An efficient function to reclassify values in a positive int dataset type
        to any output type.  If there are values in the dataset that are not in
        value map, they will be mapped to out_nodata.

        dataset - a gdal dataset of some int type
        value_map - a dictionary of values of {source_value: dest_value, ...}
            where source_value's type is a postive integer type and dest_value 
            is of type out_datatype.
        raster_out_uri - the uri for the output raster
        out_datatype - the type for the output dataset
        out_nodata - the nodata value for the output raster.  Must be the same
            type as out_datatype
        exception_flag - either 'none' or 'values_required'.  if 'values_required'
            raise an exception if there is a value in the raster that is not
            found in value_map

       returns the new reclassified dataset GDAL raster, or raises an Exception
           if exception_flag == 'values_required' and the value from
           'key_raster' is not a key in 'attr_dict'"""

    LOGGER.info('Reclassifying')
    out_dataset = new_raster_from_base(
        dataset, raster_out_uri, 'GTiff', out_nodata, out_datatype)
    out_band = out_dataset.GetRasterBand(1)

    calculate_raster_stats(dataset)
    in_band, in_nodata = extract_band_and_nodata(dataset)
    dataset_max = in_band.GetMaximum()

    #Make an array the same size as the max entry in the dictionary of the same
    #type as the output type.  The +2 adds an extra entry for the nodata values
    #The dataset max ensures that there are enough values in the array
    LOGGER.info('Creating lookup numpy array')
    valid_set = set(value_map.keys())
    map_array_size = max(dataset_max, max(valid_set)) + 2
    valid_set.add(map_array_size - 1) #add the index for nodata
    map_array = numpy.empty((1,map_array_size), dtype = type(value_map.values()[0]))
    map_array[:] = out_nodata

    for key, value in value_map.iteritems():
        map_array[0,key] = value

    LOGGER.info('Looping through rows in the input data')
    
    #Doing two loops here for performance purposes, this saves us from
    for row_index in xrange(in_band.YSize):
        row_array = in_band.ReadAsArray(0, row_index, in_band.XSize, 1)
        
        #It's possible for in_nodata to be None if the original raster
        #is none, we need to skip the index trick in that case.
        if in_nodata != None:
            #Remaps pesky nodata values the last index in map_array
            row_array[row_array == in_nodata] = map_array_size - 1

        if exception_flag == 'values_required':
            unique_set = set(row_array[0])
            if not unique_set.issubset(valid_set):
                undefined_set = unique_set.difference(valid_set)
                raise UndefinedValue(
                    "The following values were in the raster but not in the "
                    "value_map %s" % (undefined_set))

        row_array = map_array[numpy.ix_([0],row_array[0])]
        out_band.WriteArray(row_array, 0, row_index)

    LOGGER.info('Flushing the cache and exiting reclassification')
    out_dataset.FlushCache()
    return out_dataset

def align_datasets(datasets, dataset_uris):
    """Takes a list of datasets and writes interpolated aligned versions of
        them in the corresponding dataset_uris list

        datasets - a list of GDAL datasets
        dataset_uris - a list of output dataset uris

        returns a list of the aligned datasets in the same order they are 
            passed in"""

    dataset_list = [None] * len(datasets)
    for index in range(len(datasets)):
        def op(*x):
            return x[index]
        LOGGER.debug("aligning raster %s" % (unicode(dataset_uris[index])))
        band, nodata = extract_band_and_nodata(datasets[index])
        dataset_list[index] = vectorize_rasters(
            datasets, op, raster_out_uri=dataset_uris[index],
            datatype=band.DataType, nodata=nodata)

    return dataset_list

def load_memory_mapped_array(dataset_uri, memory_file, array_type=None):
    """This function loads the first band of a dataset into a memory mapped
        array.

        dataset_uri - the GDAL dataset to load into a memory mapped array
        memory_uri - a path to a file OR a file-like object that will be used
            to hold the memory map. It is up to the caller to create and delete
            this file.
        array_type - the type of the resulting array, if None defaults
            to the type of the raster band in the dataset

        returns a memmap numpy array of the data contained in the first band
            of dataset_uri"""

    dataset = gdal.Open(dataset_uri)
    band = dataset.GetRasterBand(1)
    n_rows = dataset.RasterYSize
    n_cols = dataset.RasterXSize

    if array_type == None:
        try:
            dtype = GDAL_TO_NUMPY_TYPE[band.DataType]
        except KeyError:
            raise TypeError('Unknown GDAL type %s' % band.DataType)
    else:
        dtype = array_type

    memory_array = numpy.memmap(
        memory_file, dtype = dtype, mode = 'w+', shape = (n_rows, n_cols))

    band.ReadAsArray(buf_obj = memory_array)

    return memory_array


def temporary_filename():
    """Returns a temporary filename using mkstemp. The file is deleted
        on exit using the atexit register.

        returns a unique temporary filename"""

    file_handle, path = tempfile.mkstemp()
    os.close(file_handle)

    def remove_file(path):
        """Function to remove a file and handle exceptions to register
            in atexit"""
        try:
            os.remove(path)
        except OSError as exception:
            LOGGER.debug(
                'tried to removing temporary file %s but got %s '
                % (path, exception))

    atexit.register(remove_file, path)
    return path


def temporary_folder():
    """Returns a temporary folder using mkdtemp.  The folder is deleted on exit
        using the atexit register.

        Returns an absolute, unique and temporary folder path."""

    path = tempfile.mkdtemp()

    def remove_folder(path):
        """Function to remove a folder and handle exceptions encountered.  This
        function will be registered in atexit."""
        try:
            shutil.rmtree(path)
        except OSError as exception:
            LOGGER.debug('Tried to remove temp folder %s, but got %s',
                path, exception)

    atexit.register(remove_folder, path)
    return path


class DatasetUnprojected(Exception): 
    """An exception in case a dataset is unprojected"""
    pass


class DifferentProjections(Exception): 
    """An exception in case a set of datasets are not in the same projection"""
    pass


def assert_datasets_in_same_projection(dataset_uri_list):
    """Tests if datasets represented by their uris are projected and in
        the same projection and raises an exception if not.

        raises DatasetUnprojected if one of the datasets is unprojected.
        raises DifferentProjections if at least one of the datasets is in
            a different projection

        otherwise, returns True"""

    dataset_list = [gdal.Open(dataset_uri) for dataset_uri in dataset_uri_list]
    dataset_projections = []

    unprojected_datasets = set()

    for dataset in dataset_list:
        projection_as_str = dataset.GetProjection()
        dataset_sr = osr.SpatialReference()
        dataset_sr.ImportFromWkt(projection_as_str)
        if not dataset_sr.IsProjected():
            unprojected_datasets.add(dataset.GetFileList()[0])
        dataset_projections.append((dataset_sr, dataset.GetFileList()[0]))

    if len(unprojected_datasets) > 0:
        raise DatasetUnprojected(
            "These datasets are unprojected %s" % (unprojected_datasets))

    for index in range(len(dataset_projections)-1):
        if not dataset_projections[index][0].IsSame(dataset_projections[index+1][0]):
            raise DifferentProjections(
                "These two datasets are not in the same projection."
                " The different projections are:\n\n'filename: %s'\n%s\n\nand:\n\n'filename:%s'\n%s\n\n"
                "Note there may be other files not projected, this function reports the first"
                " two that have been seen." %
                (dataset_projections[index][1], dataset_projections[index][0].ExportToPrettyWkt(), 
                 dataset_projections[index+1][1], dataset_projections[index+1][0].ExportToPrettyWkt()))

    return True

def get_bounding_box(dataset_uri):
    """Returns a bounding box where coordinates are in projected units.

        dataset_uri - a uri to a GDAL dataset

        returns [upper_left_x, upper_left_y, lower_right_x, lower_right_y] in projected coordinates"""

    dataset = gdal.Open(dataset_uri)

    geotransform = dataset.GetGeoTransform()
    n_cols = dataset.RasterXSize
    n_rows = dataset.RasterYSize

    bounding_box = [geotransform[0],
                    geotransform[3],
                    geotransform[0] + n_cols * geotransform[1],
                    geotransform[3] + n_rows * geotransform[5]]
    
    return bounding_box

def get_datasource_bounding_box(datasource_uri):
    """Returns a bounding box where coordinates are in projected units.

        dataset_uri - a uri to a GDAL dataset

        returns [upper_left_x, upper_left_y, lower_right_x, lower_right_y] in projected coordinates"""

    datasource = ogr.Open(datasource_uri)
    layer = datasource.GetLayer(0)
    extent = layer.GetExtent()
    #Reindex datasource extents into the upper left/lower right coordinates
    bounding_box = [extent[0],
                    extent[3],
                    extent[1],
                    extent[2]]
    return bounding_box


def resize_and_resample_dataset(
    original_dataset_uri, bounding_box, out_pixel_size, output_uri, 
    resample_method):
    """A function to resample a datsaet to larger or smaller pixel sizes

        original_dataset_uri - a GDAL dataset
        bounding_box - [upper_left_x, upper_left_y, lower_right_x, lower_right_y]
        out_pixel_size - the pixel size in projected linear units
        output_uri - the location of the new resampled GDAL dataset
        resample_method - the resampling technique, one of
            "nearest|bilinear|cubic|cubic_spline|lanczos"

        returns nothing"""

    resample_dict = {
        "nearest": gdal.GRA_NearestNeighbour,
        "bilinear": gdal.GRA_Bilinear,
        "cubic": gdal.GRA_Cubic,
        "cubic_spline": gdal.GRA_CubicSpline,
        "lanczos": gdal.GRA_Lanczos
        }

    original_dataset = gdal.Open(original_dataset_uri)
    original_band, original_nodata = extract_band_and_nodata(original_dataset)

    original_sr = osr.SpatialReference()
    original_sr.ImportFromWkt(original_dataset.GetProjection())

    output_geo_transform = [bounding_box[0], out_pixel_size, 0.0, bounding_box[1], 0.0, -out_pixel_size]
    new_x_size = abs(int(math.ceil((bounding_box[2] - bounding_box[0]) / out_pixel_size)))
    new_y_size = abs(int(math.ceil((bounding_box[3] - bounding_box[1]) / out_pixel_size)))

    #create the new x and y size
    gdal_driver = gdal.GetDriverByName('GTiff')
    output_dataset = gdal_driver.Create(
        output_uri, new_x_size, new_y_size, 1, original_band.DataType)
    output_band = output_dataset.GetRasterBand(1)
    output_band.SetNoDataValue(original_nodata)
    output_band.Fill(original_nodata)

    # Set the geotransform
    output_dataset.SetGeoTransform(output_geo_transform)
    output_dataset.SetProjection(original_sr.ExportToWkt())

    # Perform the projection/resampling
    gdal.ReprojectImage(original_dataset, output_dataset,
                        original_sr.ExportToWkt(), original_sr.ExportToWkt(),
                        resample_dict[resample_method])
    calculate_raster_stats(output_dataset)


def align_dataset_list(
    dataset_uri_list, dataset_out_uri_list, resample_method_list,
    out_pixel_size, mode, dataset_to_align_index, aoi_uri=None,
    assert_datasets_projected=True):
    """Take a list of dataset uris and generates a new set that is completely
        aligned with identical projections and pixel sizes.

        dataset_uri_list - a list of input dataset uris
        dataset_out_uri_list - a parallel dataset uri list whose positions
            correspond to entries in dataset_uri_list
        resample_method_list - a list of resampling methods for each output uri
            in dataset_out_uri list.  Each element must be one of
            "nearest|bilinear|cubic|cubic_spline|lanczos"
        out_pixel_size - the output pixel size
        mode - one of "union" or "intersection" which defines how the output
            output extents are defined as either the union or intersection
            of the input datasets.
        dataset_to_align_index - an int that corresponds to the position in
            one of the dataset_uri_lists that, if positive aligns the output
            rasters to fix on the upper left hand corner of the output
            datasets.  If negative, the bounding box aligns the intersection/
            union without adjustment.
        aoi_uri - (optional) a URI to an OGR datasource to be used for the 
            aoi.  Irrespective of the `mode` input, the aoi will be used
            to intersect the final bounding box.

        returns nothing"""

    #This seems a reasonable precursor for some very common issues, numpy gives
    #me a precedent for this.
    if assert_datasets_projected:
        assert_datasets_in_same_projection(dataset_uri_list)
    if mode not in ["union", "intersection"]:
        raise Exception("Unknown mode %s" % (str(mode)))
    if dataset_to_align_index >= len(dataset_uri_list):
        raise Exception(
            "Alignment index is out of bounds of the datasets index: %s"
            "n_elements %s" % (dataset_to_align_index, len(dataset_uri_list)))

    def merge_bounding_boxes(bb1, bb2, mode):
        """Helper function to merge two bounding boxes through union or 
            intersection"""
        lte = lambda x, y: x if x <= y else y
        gt = lambda x, y: x if x > y else y

        if mode == "union":
            comparison_ops = [lte, gt, gt, lte]
        if mode == "intersection":
            comparison_ops = [gt, lte, lte, gt]

        bb_out = [op(x, y) for op, x, y in zip(comparison_ops, bb1, bb2)]
        return bb_out

    #get the intersecting or unioned bounding box
    bounding_box = reduce(
        functools.partial(merge_bounding_boxes,mode=mode), 
        [get_bounding_box(dataset_uri) for dataset_uri in dataset_uri_list])

    if aoi_uri != None:
        bounding_box = merge_bounding_boxes(
            bounding_box, get_datasource_bounding_box(aoi_uri), "intersection")


    if bounding_box[0] >= bounding_box[2] or \
            bounding_box[1] <= bounding_box[3] and mode == "intersection":
        raise Exception("The datasets' intersection is empty "
                        "(i.e., not all the datasets touch each other).")

    if dataset_to_align_index >= 0:
        #bounding box needs alignment
        align_bounding_box = get_bounding_box(
            dataset_uri_list[dataset_to_align_index])
        align_pixel_size = get_cell_size_from_uri(
            dataset_uri_list[dataset_to_align_index])
        
        for index in [0, 1]:
            n_pixels = int(
                (bounding_box[index] - align_bounding_box[index]) / 
                float(align_pixel_size))
            bounding_box[index] = \
                n_pixels * align_pixel_size + align_bounding_box[index]

    for original_dataset_uri, out_dataset_uri, resample_method in zip(
        dataset_uri_list, dataset_out_uri_list, resample_method_list):
        resize_and_resample_dataset(
            original_dataset_uri, bounding_box, out_pixel_size, out_dataset_uri,
            resample_method)


    #If there's an AOI, mask it out
    if aoi_uri != None:
        first_dataset = gdal.Open(dataset_out_uri_list[0])
        n_rows = first_dataset.RasterYSize
        n_cols = first_dataset.RasterXSize

        mask_uri = temporary_filename()
        mask_dataset = new_raster_from_base(
            first_dataset, mask_uri, 'GTiff', 255, gdal.GDT_Byte)
        first_dataset = None
        mask_band = mask_dataset.GetRasterBand(1)
        mask_band.Fill(0)
        aoi_datasource = ogr.Open(aoi_uri)
        aoi_layer = aoi_datasource.GetLayer()
        gdal.RasterizeLayer(mask_dataset, [1], aoi_layer, burn_values=[1])

        dataset_row = numpy.zeros((1, n_cols))
        mask_row = numpy.zeros((1, n_cols))

        for out_dataset_uri in dataset_out_uri_list:
            nodata_out = get_nodata_from_uri(out_dataset_uri)
            out_dataset = gdal.Open(out_dataset_uri, gdal.GA_Update)
            out_band = out_dataset.GetRasterBand(1)
            for row_index in range(n_rows):
                out_dataset.ReadAsArray(
                    0, row_index, n_cols, 1, buf_obj=dataset_row)
                mask_band.ReadAsArray(0, row_index, n_cols, 1, buf_obj=mask_row)
                dataset_row[mask_row == 0] = nodata_out
                out_band.WriteArray(dataset_row, xoff=0, yoff=row_index)


def vectorize_datasets(
    dataset_uri_list, dataset_pixel_op, dataset_out_uri, datatype_out, nodata_out,
    pixel_size_out, bounding_box_mode, resample_method_list=None, 
    dataset_to_align_index=None, aoi_uri=None, assert_datasets_projected=True):
    """This function applies a user defined function across a stack of
        datasets.  It has functionality align the output dataset grid
        with one of the input datasets, output a dataset that is the union
        or intersection of the input dataset bounding boxes, and control
        over the interpolation techniques of the input datasets, if
        necessary.  The datasets in dataset_uri_list must be in the same
        projection; the function will raise an exception if not.

        dataset_uri_list - a list of file uris that point to files that
            can be opened with gdal.Open.
        dataset_pixel_op - a function that must take in as many arguments as
            there are elements in dataset_uri_list.  The arguments can
            be treated as interpolated or actual pixel values from the
            input datasets and the function should calculate the output
            value for that pixel stack.  The function is a parallel
            paradigmn and does not know the spatial position of the
            pixels in question at the time of the call.  If the
            `bounding_box_mode` parameter is "union" then the values
            of input dataset pixels that may be outside their original
            range will be the nodata values of those datasets.  Known
            bug: if dataset_pixel_op does not return a value in some cases
            the output dataset values are undefined even if the function
            does not crash or raise an exception.
        dataset_out_uri - the uri of the output dataset.  The projection
            will be the same as the datasets in dataset_uri_list.
        datatype_out - the GDAL output type of the output dataset
        nodata_out - the nodata value of the output dataset.
        pixel_size_out - the pixel size of the output dataset in
            projected coordinates.
        bounding_box_mode - one of "union" or "intersection". If union
            the output dataset bounding box will be the union of the
            input datasets.  Will be the intersection otherwise. An
            exception is raised if the mode is "intersection" and the
            input datasets have an empty intersection.
        resample_method_list - (optional) a list of resampling methods
            for each output uri in dataset_out_uri list.  Each element
            must be one of "nearest|bilinear|cubic|cubic_spline|lanczos".
            If None, the default is "nearest" for all input datasets.
        dataset_to_align_index - an int that corresponds to the position in
            one of the dataset_uri_lists that, if positive aligns the output
            rasters to fix on the upper left hand corner of the output
            datasets.  If negative, the bounding box aligns the intersection/
            union without adjustment.
        aoi_uri - (optional) a URI to an OGR datasource to be used for the 
            aoi.  Irrespective of the `mode` input, the aoi will be used
            to intersect the final bounding box.
        assert_datasets_projected - (optional) if True this operation will
            test if any datasets are not projected and raise an exception
            if so."""

    
    #Create a temporary list of filenames whose files delete on the python
    #interpreter exit
    dataset_out_uri_list = [temporary_filename() for _ in dataset_uri_list]

    #Handle the cases where optional arguments are passed in
    if resample_method_list == None:
        resample_method_list = ["nearest"] * len(dataset_uri_list)
    if dataset_to_align_index == None:
        dataset_to_align_index = -1


    #Align and resample the datasets, then load datasets into a list
    align_dataset_list(
        dataset_uri_list, dataset_out_uri_list, resample_method_list,
        pixel_size_out, bounding_box_mode, dataset_to_align_index,
        aoi_uri=aoi_uri, assert_datasets_projected=assert_datasets_projected)
    aligned_datasets = [
        gdal.Open(filename, gdal.GA_Update) for filename in dataset_out_uri_list]
    aligned_bands = [dataset.GetRasterBand(1) for dataset in aligned_datasets]

    #The output dataset will be the same size as any one of the aligned datasets
    output_dataset = new_raster_from_base(
        aligned_datasets[0], dataset_out_uri, 'GTiff', nodata_out, datatype_out)
    output_band = output_dataset.GetRasterBand(1)

    n_rows = aligned_datasets[0].RasterYSize
    n_cols = aligned_datasets[0].RasterXSize

    #Try to numpy vectorize the operation
    try:
        vectorized_op = numpy.vectorize(dataset_pixel_op)
    except ValueError:
        #it's possible that the operation is already vectorized, so try that
        vectorized_op = dataset_pixel_op

    #If there's an AOI, mask it out
    if aoi_uri != None:
        mask_uri = temporary_filename()
        mask_dataset = new_raster_from_base(
            aligned_datasets[0], mask_uri, 'GTiff', 255, gdal.GDT_Byte)
        mask_band = mask_dataset.GetRasterBand(1)
        mask_band.Fill(0)
        aoi_datasource = ogr.Open(aoi_uri)
        aoi_layer = aoi_datasource.GetLayer()
        gdal.RasterizeLayer(mask_dataset, [1], aoi_layer, burn_values=[1])
        mask_array = numpy.zeros((1, n_cols))

    dataset_rows = [numpy.zeros((1, n_cols)) for _ in aligned_bands]
    for row_index in range(n_rows):
        for dataset_index in range(len(aligned_bands)):
            aligned_bands[dataset_index].ReadAsArray(
                0, row_index, n_cols, 1, buf_obj=dataset_rows[dataset_index])
        out_row = vectorized_op(*dataset_rows)
        #Mask out the row if there is a mask
        if aoi_uri != None:
            mask_band.ReadAsArray(0, row_index, n_cols, 1, buf_obj=mask_array)
            out_row[mask_array == 0] = nodata_out
        output_band.WriteArray(out_row, xoff=0, yoff=row_index)

    #Making sure the band and dataset is flushed and not in memory before
    #adding stats
    output_band.FlushCache()
    output_dataset.FlushCache()
    output_dataset = None
    output_band = None
    calculate_raster_stats_uri(dataset_out_uri)

def get_lookup_from_table(table_uri, key_field):
    """Creates a python dictionary to look up the rest of the fields in a
       table file table indexed by the given key_field

        table_uri - a URI to a dbf or csv file containing at
            least the header key_field

        returns a dictionary of the form {key_field_0: 
            {header_1: val_1_0, header_2: val_2_0, etc.}
            depending on the values of those fields"""
    
    table_object = fileio.TableHandler(table_uri)
    raw_table_dictionary = table_object.get_table_dictionary(key_field.lower())

    def smart_cast(value):
        """Attempts to cat value to a float, int, or leave it as string"""
        #If it's not a string, don't try to cast it because i got a bug
        #where all my floats were happily cast to ints
        if type(value) != str:
            return value
        cast_functions = [int, float]
        for fn in cast_functions:
            try:
                return fn(value)
            except ValueError:
                pass
        return value

    lookup_dict = {}
    for key, sub_dict in raw_table_dictionary.iteritems():
        key_value = smart_cast(key)
        #Map an entire row to its lookup values
        lookup_dict[key_value] = (
            dict([(sub_key, smart_cast(value)) for sub_key, value in sub_dict.iteritems()]))
    return lookup_dict

def get_lookup_from_csv(csv_table_uri, key_field):
    """Creates a python dictionary to look up the rest of the fields in a
        csv table indexed by the given key_field

        csv_table_uri - a URI to a csv file containing at
            least the header key_field

        returns a dictionary of the form {key_field_0: 
            {header_1: val_1_0, header_2: val_2_0, etc.}
            depending on the values of those fields"""

    def smart_cast(value):
        """Attempts to cat value to a float, int, or leave it as string"""
        cast_functions = [int, float]
        for fn in cast_functions:
            try:
                return fn(value)
            except ValueError:
                pass
        return value

    with open(csv_table_uri, 'rU') as csv_file:
        csv_reader = csv.reader(csv_file)
        header_row = csv_reader.next()
        key_index = header_row.index(key_field)
        #This makes a dictionary that maps the headers to the indexes they
        #represent in the soon to be read lines
        index_to_field = dict(zip(range(len(header_row)), header_row))

        lookup_dict = {}
        for line in csv_reader:
            key_value = smart_cast(line[key_index])
            #Map an entire row to its lookup values
            lookup_dict[key_value] = (
                dict([(index_to_field[index], smart_cast(value)) 
                      for index, value in zip(range(len(line)), line)]))
        return lookup_dict


def viewshed(dem_uri, shapefile_uri, z_factor, curvature_correction, refractivity_coefficient, visible_feature_count_uri,
             out_cell_size=None, aoi_uri=None):
    """FILL IN"""

    out_pixel_size = get_cell_size_from_uri(dem_uri)
    vectorize_datasets(
        [dem_uri], lambda x: int(abs(x))%10, visible_feature_count_uri,
        gdal.GDT_Byte, 255, out_pixel_size, "intersection",
        dataset_to_align_index=0, aoi_uri=aoi_uri, assert_datasets_projected=False)

def extract_datasource_table_by_key(datasource_uri, key_field):
    """Create a dictionary lookup table of the features in the attribute table
        of the datasource referenced by datasource_uri.

        datasource_uri - a uri to an OGR datasource
        key_field - a field in datasource_uri that refers to a key (unique) value
            for each row; for example, a polygon id.

        returns a dictionary of the form {key_field_0: 
            {field_0: value0, field_1: value1}...}"""

    def smart_cast(value):
        """Attempts to cast value to a float, int, or leave it as string"""
        if type(value) != str: 
            return value

        cast_functions = [int, float]
        for fn in cast_functions:
            try:
                return fn(value)
            except ValueError:
                pass
        return value

    #Pull apart the datasource
    datasource = ogr.Open(datasource_uri)
    layer = datasource.GetLayer()
    layer_def = layer.GetLayerDefn()

    #Build up a list of field names for the datasource table
    field_names = []
    for field_id in xrange(layer_def.GetFieldCount()):
        field_def = layer_def.GetFieldDefn(field_id)
        field_names.append(field_def.GetName())

    #Loop through each feature and build up the dictionary representing the
    #attribute table
    attribute_dictionary = {}
    for feature_index in xrange(layer.GetFeatureCount()):
        feature = layer.GetFeature(feature_index)
        feature_fields = {}
        for field_name in field_names:
            feature_fields[field_name] = feature.GetField(field_name)
        key_value = feature.GetField(key_field)
        attribute_dictionary[key_value] = feature_fields

    return attribute_dictionary
    
def get_geotransform_uri(ds_uri):
    """Get the geotransform from a gdal dataset

        ds_uri - A URI for the dataset

        returns - a dataset geotransform list"""

    raster_ds = gdal.Open(ds_uri)
    raster_gt = raster_ds.GetGeoTransform()
    return raster_gt
    
def get_spatial_ref_uri(ds_uri):
    """Get the spatial reference of an OGR datasource
        
        ds_uri - A URI to an ogr datasource

        returns - a spatial reference"""

    shape_ds = ogr.Open(ds_uri)
    layer = shape_ds.GetLayer()
    spat_ref = layer.GetSpatialRef()
    return spat_ref
        
def copy_datasource_uri(shape_uri, copy_uri):
    """Create a copy of an ogr shapefile

        shape_uri - a uri path to the ogr shapefile that is to be copied
        copy_uri - a uri path for the destination of the copied
            shapefile

        returns - Nothing"""
    if os.path.isfile(copy_uri):
        os.remove(copy_uri)

    shape = ogr.Open(shape_uri)
    drv = ogr.GetDriverByName('ESRI Shapefile')
    drv.CopyDataSource(shape, copy_uri)
    
def vectorize_points_uri(shapefile_uri, field, output_uri):
    """A wrapper function for raster_utils.vectorize_points, that allows for uri
        passing

        shapefile_uri - a uri path to an ogr shapefile
        field - a String for the field name
        output_uri - a uri path for the output raster

        returns - Nothing"""

    datasource = ogr.Open(shapefile_uri)
    output_raster = gdal.Open(output_uri, 1)
    vectorize_points(datasource, field, output_raster)

def create_directories(directory_list):
    """This function is inspired from this thread 
        http://stackoverflow.com/questions/273192/python-best-way-to-create-directory-if-it-doesnt-exist-for-file-write
        it will create any of the directories in the directory list if possible
        and raise exceptions if something Bad happens.

        directory_list - a list of string uri paths

        returns nothing"""

    for dir_name in directory_list:
        try:
            os.makedirs(dir_name)
        except OSError as exception:
            #It's okay if the directory already exists, if it fails for
            #some other reason, raise that exception
            if exception.errno != errno.EEXIST:
                raise

def dictionary_to_point_shapefile(dict_data, layer_name, output_uri):
    """Creates a point shapefile from a dictionary. The point shapefile created
        is not projected and uses latitude and longitude for its geometry.
        
        dict_data - a python dictionary with keys being unique id's that point
            to sub-dictionarys that have key-value pairs. These inner key-value
            pairs will represent the field-value pair for the point features.
            At least two fields are required in the sub-dictionaries, All the
            keys in the sub dictionary should have the same name and order. All
            the values in the sub dictionary should have the same type
            'lati' and 'long'. These fields determine the geometry of the point
            0 : {'lati':97, 'long':43, 'field_a':6.3, 'field_b':'Forest',...},
            1 : {'lati':55, 'long':51, 'field_a':6.2, 'field_b':'Crop',...},
            2 : {'lati':73, 'long':47, 'field_a':6.5, 'field_b':'Swamp',...}
        
        layer_name - a python string for the name of the layer
        
        output_uri - a uri for the output path of the point shapefile

        return - Nothing"""
    
    LOGGER.debug('Entering dictionary_to_shapefile')
    
    # If the output_uri exists delete it
    if os.path.isfile(output_uri):
        os.remove(output_uri)
    elif os.path.isdir(output_uri):
        shutil.rmtree(output_uri)

    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    LOGGER.debug('Create New Datasource')
    output_datasource = output_driver.CreateDataSource(output_uri)

    # Set the spatial reference to WGS84 (lat/long)
    source_sr = osr.SpatialReference()
    source_sr.SetWellKnownGeogCS("WGS84")
   
    LOGGER.debug('Create New Layer')
    output_layer = output_datasource.CreateLayer(
            layer_name, source_sr, ogr.wkbPoint)

    # Outer unique keys
    outer_keys = dict_data.keys()
    
    # Construct a list of fields to add from the keys of the inner dictionary
    field_list = dict_data[outer_keys[0]].keys()
    LOGGER.debug('field_list : %s', field_list)
    
    # Create a dictionary to store what variable types the fields are
    type_dict = {}
    for field in field_list:
        # Get a value from the field
        val = dict_data[outer_keys[0]][field]
        # Check to see if the value is a String of characters or a number. This
        # will determine the type of field created in the shapefile
        if isinstance(val, str):
            type_dict[field] = 'str'
        else:
            type_dict[field] = 'number'

    LOGGER.debug('Creating fields for the datasource')
    for field in field_list:
        field_type = None
        # Distinguish if the field type is of type String or other. If Other, we
        # are assuming it to be a float
        if type_dict[field] == 'str':
            field_type = ogr.OFTString
        else:
            field_type = ogr.OFTReal
        
        output_field = ogr.FieldDefn(field, field_type)   
        output_layer.CreateField(output_field)

    LOGGER.debug('Entering iteration to create and set the features')
    # For each inner dictionary (for each point) create a point and set its
    # fields
    for point_dict in dict_data.itervalues():
        latitude = float(point_dict['lati'])
        longitude = float(point_dict['long'])

        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint_2D(longitude, latitude)

        output_feature = ogr.Feature(output_layer.GetLayerDefn())
        
        for field_name in point_dict:
            field_index = output_feature.GetFieldIndex(field_name)
            output_feature.SetField(field_index, point_dict[field_name])
        
        output_feature.SetGeometryDirectly(geom)
        output_layer.CreateFeature(output_feature)
        output_feature = None

    output_layer.SyncToDisk()

def get_dataset_projection_wkt_uri(ds_uri):
    """Get the projection of a GDAL dataset as well known text (WKT)

        ds_uri - A URI for the GDAL dataset

        returns - a string for the WKT"""

    raster_ds = gdal.Open(ds_uri)
    proj_wkt = raster_ds.GetProjection()
    return proj_wkt
