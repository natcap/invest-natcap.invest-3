# Some tracer code to see how urlllib and gdal work together

from urllib import urlopen
from dbfpy import dbf

try:
    from osgeo import ogr, gdal
    from osgeo.gdalconst import *
    import numpy
    use_numeric = False
except ImportError:
    import ogr, gdal
    from gdalconst import *
    import Numeric

def open(data):
    """Attempts to open the data object and return a reasonable object if it
    is a dictionary.  Otherwise returns the original object.
    
    LIST OF DATA TYPES:
    -gdal
    -dbf"""

    if not isinstance(data, dict):
        return data
    if data['type'] == 'gdal':
        return gdal.Open(data['uri'], GA_ReadOnly)
    if data['type'] == 'dbf':
        return Dbf().openFile(data['uri'], readOnly=1)

def close(data):
    if isinstance(data, GDALDataset):
        return None #close the dataset
    else:
        return data

def gdal_open(filename):
    gdal.AllRegister()
    raster = gdal.Open(filename, GA_ReadOnly)
    if raster is None:
        raise Exception, 'Could not open image'
    return raster

def dbf_open(filename):
    return dbf.Dbf(filename, True)
