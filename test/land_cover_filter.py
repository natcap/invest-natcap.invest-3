"""This script filters land cover type. Woah!"""

from osgeo import gdal

def newRasterFromBase(base, outputURI, format, nodata, datatype):
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
    return newRaster(cols, rows, projection, geotransform, format, nodata,
                     datatype, base.RasterCount, outputURI)
    
def newRaster(cols, rows, projection, geotransform, format, nodata, datatype,
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
    newRaster = driver.Create(str(outputURI), cols, rows, bands, datatype)
    newRaster.SetProjection(projection)
    newRaster.SetGeoTransform(geotransform)
    for i in range(bands):
        newRaster.GetRasterBand(i + 1).SetNoDataValue(nodata)
        newRaster.GetRasterBand(i + 1).Fill(nodata)

    return newRaster

#Open this file, this will return a data set, returns a gdal DataSet
ds = gdal.Open('data/base_data/terrestrial/lulc_samp_cur')

band = ds.GetRasterBand(1)

#Can actually specify where you want to start reading, 
#but leaving w/o anything just opens the whole thing
matrix = band.ReadAsArray()

#this is the land cover Id that I want to keep
filter_id = 71

#this creates a new matrix that sets true if equal to the given value, false else
mask = matrix != filter_id

#use the above new matrix as an index to a matrix
#this will only change the values that are true to 255
matrix[mask] = 255

print matrix

#this should return a data set that we can write to of the same size 
#and projection as the input data set
output_ds = newRasterFromBase(ds, 'filter.tif', 'GTiff', 255, gdal.GDT_Byte)

#write to disk
output_ds.GetRasterBand(1).WriteArray(matrix)

#print band
#print ds