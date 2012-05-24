"""A collection of GDAL dataset and raster utilities"""

import logging

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
        LOGGER.info('in band %s' % band)
        #Use this for initialization
        first_value = band.ReadAsArray(0,0,1,1)
        min_val = first_value[0]
        max_val = min_val
        running_sum = 0.0
        running_sum_square = 0.0

        for row in range(band.YSize):
            #Read row number 'row'
            row_array = band.ReadAsArray(0,row,band.XSize,1)
            min_val = min(min_val,np.min(row_array))
            max_val = max(max_val,np.max(row_array))
            running_sum += np.sum(row_array)
            running_sum_square += np.sum(row_array**2)

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

def vectorize_rasters(dataset_list, op, raster_out_uri=None,
                     datatype=gdal.GDT_Float32, nodata=0.0):
    """Apply the numpy vectorized operation `op` on the first band of the
        datasets contained in dataset_list where the arguments to `op` are 
        brodcasted pixels from each current_dataset in dataset_list in the order they 
        exist in the list
        
        dataset_list - list of GDAL input datasets, requires that they'are all
            in the same projection.
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
    out_geotransform = [aoi_box[0], pixel_width, 0.0,
                        aoi_box[1], 0.0, pixel_height]
    #The output projection will be the same as any in dataset_list, so just take
    #the first one.
    out_projection = dataset_list[0].GetProjection()
    output_uri = ''

    #If no output uri is specified assume 'MEM' format, otherwise GTiff
    format = 'MEM'
    if raster_out_uri != None:
        output_uri = raster_out_uri
        format = 'GTiff'

    #Build the new output dataset and reference the band for later
    out_dataset = new_raster(out_n_cols, out_n_rows, projection,
        out_geotransform, format, nodata, datatype, 1, output_uri)
    out_band = out_dataset.GetRasterBand(1)
    out_band.Fill(0)


    #Loop over each row in out_band
      #Loop over each input raster
        #Build an interpolator for the input raster row that matches out_band_row
        #Interpolate a row that aligns with out_band_row and add to list
      #Vectorize the stack of rows and write to out_band

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

def calculateIntersectionRectangle(rasterList):
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
