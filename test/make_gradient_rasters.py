from osgeo import gdal
from osgeo import osr
import numpy as np

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

def make_smooth_raster(cols, rows, uribase='smooth', format='GTiff', min_val=0.0, 
                       max_val=1.0, type='float'):
    """Create a new raster with random int values.
        
        cols - an int, the number of columns in the output raster
        rows - an int, the number of rows in the output raster
        uri - a string for the path to the file
        format - a string representing the GDAL format code such as 
            'GTiff' or 'MEM'.  See http://gdal.org/formats_list.html for a
            complete list of formats.
        min_val - the minimum value allowed for a given pixel.
        max_val - the maximum value allowed for a given pixel.
        type - a string. the type of number to be randomized.  Either 'int' or
               'float'.
            
        returns a new dataset with random values."""

    driver = gdal.GetDriverByName(format)

    dataset_type = gdal.GDT_Float32
    if type == 'int':
        dataset_type = gdal.GDT_Int32

#    for suffix in ['right', 'left', 'top', 'bottom']:
#    for suffix in ['bottom_right']:
    for suffix in ['top_left']:
        dataset = driver.Create(uribase+suffix+'.tif', cols, rows, 1, dataset_type)

        #Random spatial reference from http://www.gdal.org/gdal_tutorial.html
        srs = osr.SpatialReference()
        srs.SetUTM( 11, 1 )
        srs.SetWellKnownGeogCS( 'NAD27' )
        dataset.SetProjection( srs.ExportToWkt() )

        #Random geotransform from http://www.gdal.org/gdal_tutorial.html
        dataset.SetGeoTransform( [ 444720, 30, 0, 3751320, 0, -30 ] )

        raster = np.empty([rows,cols])

        if suffix == 'right':
            for col in range(cols):
                alpha = col/float(cols-1)
                value = min_val * (1-alpha) + max_val * alpha
                raster[:,col] = value
        elif suffix == 'left':
            for col in range(cols):
                alpha = col/float(cols-1)
                value = min_val * (alpha) + max_val * (1-alpha)
                raster[:,col] = value
        elif suffix == 'top':
            for row in range(rows):
                alpha = row/float(rows-1)
                value = min_val * (alpha) + max_val * (1-alpha)
                raster[row,:] = value
        elif suffix == 'bottom':
            for row in range(rows):
                alpha = row/float(rows-1)
                value = min_val * (1-alpha) + max_val * (alpha)
                raster[row,:] = value
        elif suffix == 'bottom_right':
            for row in range(rows):
                for col in range(cols):
                    alpha = (col+row)/(float(rows-1)+float(cols-1))
                    value = min_val * (1-alpha) + max_val * (alpha)
                    raster[row,col] = value
        elif suffix == 'top_left':
            for row in range(rows):
                for col in range(cols):
                    alpha = 1-(col+row)/(float(rows-1)+float(cols-1))
                    value = min_val * (1-alpha) + max_val * (alpha)
                    raster[row,col] = value
                    
            
        dataset.GetRasterBand(1).WriteArray(raster)
        dataset.GetRasterBand(1).SetNoDataValue(-1)

        band = dataset.GetRasterBand(1)
        calculate_band_stats(band)

make_smooth_raster(200,300)
