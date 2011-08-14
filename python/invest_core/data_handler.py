# Some tracer code to see how urlllib and gdal work together

from urllib import urlopen

try:
    from osgeo import ogr, gdal
    from osgeo.gdalconst import *
    import numpy
    use_numeric = False
except ImportError:
    import ogr, gdal
    from gdalconst import *
    import Numeric

def open(url):
    try:
        urlopen(url)
        print 'Opened %s' % url
    except IOError as (errno, strerror):
        print "I/O error({0}): {1}: {2}".format(errno, strerror, url)

def gdalprocess(file):
    gdal.AllRegister()
    raster = gdal.Open(file, GA_ReadOnly)
    if raster is None:
        raise Exception, 'Could not open image'
    else:
        print 'Successfully loaded %s' % file
        print raster.GetDescription()
        print raster.GetMetadata()
        print "rows: {0} col: {1} bands: {2}".format(raster.RasterXSize,raster.RasterYSize,raster.RasterCount)

if __name__ == "__main__":
    file = "../../lulc_samp_cur/" 
    print 'load gdal'
    gdalprocess(file)
    print 'load url'
    open(file)
    