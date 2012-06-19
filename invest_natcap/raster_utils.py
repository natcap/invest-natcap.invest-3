"""A collection of GDAL dataset and raster utilities"""

import logging
import itertools

from osgeo import gdal
from osgeo import osr
import numpy as np
import scipy.interpolate

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('raster_utils')

def calculate_raster_stats(ds):
    """Calculates and sets the min, max, stdev, and mean for the bands in
       the raster.
    
       ds - a GDAL raster dataset that will be modified by having its band
            statistics set
    
        returns nothing"""

    LOGGER.info('starting calculate_raster_stats')

    for band_number in range(ds.RasterCount):
        band = ds.GetRasterBand(band_number+1)
        nodata = band.GetNoDataValue()
        LOGGER.info('in band %s' % band)
        #Use this for initialization
        min_val = None
        max_val = None
        running_sum = 0.0
        running_sum_square = 0.0
        valid_elements = 0

        for row in range(band.YSize):
            #Read row number 'row'
            row_array = band.ReadAsArray(0,row,band.XSize,1)
            masked_row = np.ma.array(row_array, mask = row_array == nodata)
            
            try:
                #Here we're using the x[~x.mask] notation to cause
                #an exception to be thrown if the entire array is masked
                min_row = np.min(masked_row[~masked_row.mask])
                max_row = np.max(masked_row[~masked_row.mask])

                #This handles the initial case where min and max aren't
                #yet set.  And it's hard to initialize because the first
                #value in the dataset might be nodata.
                if min_val == None and max_val == None:
                    min_val = min_row
                    max_val = max_row

                #By this point min and max_val are valid
                min_val = min(min_val, np.min(min_row))
                max_val = max(max_val, np.max(max_row))

                #Sum and square only valid elements
                running_sum += np.sum(masked_row[~masked_row.mask])
                running_sum_square += np.sum(masked_row[~masked_row.mask]**2)

                #Need to use the masked_row count to count the valid
                #elements for an accurate measure of stdev and mean
                valid_elements += masked_row.count()

            except ValueError:
                #If we get here it means we encountered a fully masked array
                #okay since it just means it's all nodata values.
                pass

        n_pixels = band.YSize * band.XSize
        mean = running_sum / float(n_pixels)
        std_dev = np.sqrt(running_sum_square/float(n_pixels)-mean**2)
        
        LOGGER.debug("min_val %s, max_val %s, mean %s, std_dev %s" %
                     (min_val, max_val, mean, std_dev))

        #Write stats back to the band.  The function SetStatistics needs 
        #all the arguments to be floats and crashes if they are ints thats
        #what this map float deal is.
        band.SetStatistics(*map(float,[min_val, max_val, mean, std_dev]))

    LOGGER.info('finish calculate_raster_stats')

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

    LOGGER.debug('starting vectorize_rasters')

    #We need to ensure that the type of nodata is the same as the raster type so
    #we don't encounter bugs where we return an int nodata for a float raster or
    #vice versa
    gdal_int_types = [gdal.GDT_CInt16, gdal.GDT_CInt32, gdal.GDT_Int16, 
                      gdal.GDT_Int32, gdal.GDT_UInt16, gdal.GDT_UInt32]
    gdal_float_types = [gdal.GDT_CFloat64, gdal.GDT_CFloat32, 
                        gdal.GDT_Float64, gdal.GDT_Float32]
    gdal_bool_types = [gdal.GDT_Byte]

    if datatype in gdal_int_types:
        nodata = int(nodata)
    if datatype in gdal_float_types:
        nodata = float(nodata)
    if datatype in gdal_bool_types:
        nodata = bool(nodata)

    #create a new current_dataset with the minimum resolution of dataset_list and
    #bounding box that contains aoi_box
    #gt: left, pixelxwidth, pixelywidthforx, top, pixelxwidthfory, pixelywidth
    #generally pixelywidthforx and pixelxwidthfory are zero for maps where 
    #north is up if that's not the case for us, we'll have a few bugs to deal 
    #with aoibox is left, top, right, bottom
    LOGGER.debug('calculating the overlapping rectangles')
    aoi_box = calculate_intersection_rectangle(dataset_list, aoi)
    LOGGER.debug('the aoi box: %s' % aoi_box)

    #determine the minimum pixel size
    gt = dataset_list[0].GetGeoTransform()
    pixel_width, pixel_height = gt[1], gt[5]
    for current_dataset in dataset_list:
        gt = current_dataset.GetGeoTransform()
        #This takes the minimum of the absolute value of the current dataset's
        #pixel size versus what we've seen so far.
        pixel_width = min(pixel_width, gt[1], key=abs)
        pixel_height = min(pixel_height, gt[5], key=abs)
    LOGGER.debug('min pixel width and height: %s %s' % (pixel_width,
                                                        pixel_height))

    #Together with the AOI and min pixel size we define the output dataset's 
    #columns and out_n_rows
    out_n_cols = int(np.ceil((aoi_box[2] - aoi_box[0]) / pixel_width))
    out_n_rows = int(np.ceil((aoi_box[3] - aoi_box[1]) / pixel_height))
    LOGGER.debug('number of pixel out_n_cols and out_n_rows %s %s' % \
                 (out_n_cols, out_n_rows))

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
    out_dataset = new_raster(out_n_cols, out_n_rows, out_projection,
        out_gt, format, nodata, datatype, 1, output_uri)
    out_band = out_dataset.GetRasterBand(1)
    out_band.Fill(nodata)

    #left and right coordinates will always be the same for each row so calc
    #them first.
    out_left_coord = out_gt[0]
    out_right_coord = out_left_coord + out_gt[1] * out_band.XSize

    #These are the output coordinates for the interpolator
    out_col_coordinates = np.arange(out_n_cols)
    out_col_coordinates *= out_gt[1]
    out_col_coordinates += out_gt[0]

    try:
        vectorized_op = np.vectorize(op)
    except ValueError:
        #it's possible that the operation is already vectorized, so try that
        vectorized_op = op

    #If there's an AOI, we need to mask out values
    mask_dataset = new_raster_from_base(out_dataset, 'mask.tif', 'GTiff', 255, gdal.GDT_Byte)
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
                int(np.floor((out_left_coord - current_gt[0])/current_gt[1]))
            current_right_index = \
                int(np.ceil((out_right_coord - current_gt[0])/current_gt[1]))

            current_top_index = \
                int(np.floor((out_row_coord - current_gt[3])/current_gt[5]))-1

            #The +1 ensures the count of indexes are correct otherwise subtracting
            #top and bottom index that differ by 1 are always 0 and sometimes -1
            current_bottom_index = \
                int(np.ceil((out_row_coord - current_gt[3])/current_gt[5]))+1

            #We might be at the top or bottom edge, so shift the window up or down
            #We need at least 3 rows because the interpolator requires it.
            if current_top_index < 0:
                current_top_index += 1
                current_bottom_index += 1
            elif current_bottom_index > out_band.YSize:
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
            #    np.array([current_left_coordinate + index * current_gt[1] \
            #         for index in range(current_col_steps)])
            current_col_coordinates = np.arange(current_col_steps)
            current_col_coordinates *= current_gt[1]
            current_col_coordinates += current_left_coordinate

            #Equivalent of
            #    np.array([current_top_coordinate + index * current_gt[5] \
            #         for index in range(current_row_steps)])
            current_row_coordinates = np.arange(current_row_steps)
            current_row_coordinates *= current_gt[5]
            current_row_coordinates += current_top_coordinate

            #If this is true it means the y coordinates aren't in increasing
            #order which freaks out the interpolator.  Reverse them.
            if gt[5] < 0:
                current_row_coordinates = current_row_coordinates[::-1]
                current_array = current_array[::-1]

            interpolator = \
                scipy.interpolate.RectBivariateSpline(current_row_coordinates,
                                                      current_col_coordinates, 
                                                      current_array,
                                                      kx=1, ky=1)

            
            #This does the interpolation for the output row stack later to be
            #vectorized
            interpolated_row = interpolator(np.array([out_row_coord]), 
                                            out_col_coordinates)

            raster_array_stack.append(interpolated_row)

        #Vectorize the stack of rows and write to out_band
        out_row = vectorized_op(*raster_array_stack)
        #Mask out_row based on AOI
        out_row[mask_array == 1] = nodata
        out_band.WriteArray(out_row,xoff=0,yoff=out_row_index)

    #Calculate the min/max/avg/stdev on the out raster
    calculate_raster_stats(out_dataset)

    #return the new current_dataset
    return out_dataset

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

def calculate_intersection_rectangle(rasterList, aoi=None):
    """Return a bounding box of the intersections of all the rasters in the
        list.
        
        rasterList - a list of GDAL rasters in the same projection and 
            coordinate system
        aoi - an OGR polygon datasource which may optionally also restrict
            the extents of the intersection rectangle based on its own
            extents.

            
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

    if aoi != None:
        aoi_layer = aoi.GetLayer(0)
        aoi_extent = aoi_layer.GetExtent()
        LOGGER.debug("aoi_extent %s" % (str(aoi_extent)))
        boundingBox = [max(aoi_extent[0], boundingBox[0]),
                       min(aoi_extent[3], boundingBox[1]),
                       min(aoi_extent[1], boundingBox[2]),
                       max(aoi_extent[2], boundingBox[3])]

    return boundingBox

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

    #Determine the width and height of the tiff in pixels based on desired
    #x and y resolution
    shpExtent = shp.GetLayer(0).GetExtent()
    tiff_width = int(np.ceil(abs(shpExtent[1] - shpExtent[0]) / xRes))
    tiff_height = int(np.ceil(abs(shpExtent[3] - shpExtent[2]) / yRes))

    driver = gdal.GetDriverByName('GTiff')
    raster = driver.Create(rasterFile, tiff_width, tiff_height, 1, format)
    raster.GetRasterBand(1).SetNoDataValue(nodata)

    #Set the transform based on the upper left corner and given pixel
    #dimensions
    raster_transform = [shpExtent[0], xRes, 0.0, shpExtent[3], 0.0, -yRes]
    raster.SetGeoTransform(raster_transform)

    #Use the same projection on the raster as the shapefile
    srs = osr.SpatialReference()
    srs.ImportFromWkt(shp.GetLayer(0).GetSpatialRef().__str__())
    raster.SetProjection(srs.ExportToWkt())

    #Initialize everything to nodata
    raster.GetRasterBand(1).Fill(nodata)
    raster.GetRasterBand(1).FlushCache()

    return raster

def vectorize_points(shapefile, datasource_field, raster):
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

    LOGGER.debug("bounding_box %s" % bounding_box)
    LOGGER.debug("gt %s" % str(gt))

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
    random_array = np.random.randn(layer.GetFeatureCount(),2)
    random_offsets = random_array*delta_difference

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
    point_array = np.array(point_list)
    value_array = np.array(value_list)

    band = raster.GetRasterBand(1)
    nodata = band.GetNoDataValue()

    #Create grid points for interpolation outputs later
    #top-bottom:y_stepsize, left-right:x_stepsize
    grid_y, grid_x = np.mgrid[bounding_box[1]:bounding_box[3]:gt[5],
                              bounding_box[0]:bounding_box[2]:gt[1]]

    band = raster.GetRasterBand(1)
    nodata = band.GetNoDataValue()

    LOGGER.info("Writing interpolating with griddata")
    raster_out_array = scipy.interpolate.griddata(point_array, 
        value_array, (grid_y, grid_x), 'linear', nodata)
    LOGGER.info("Writing result to output array")
    band.WriteArray(raster_out_array,0,0)
