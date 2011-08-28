# Some tracer code to see how urlllib and gdal work together

from urllib import urlopen
from dbfpy import dbf
import osgeo

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
    if not 'type' in data:
        return data
    if data['type'] == 'gdal':
        if data['input'] == False:
            return gdal_create(data)
        else:
            return gdal_open(data['uri'])
    if data['type'] == 'dbf':
        return dbf_open(data['uri'])
    

def close(data):
    if isinstance(data, osgeo.gdal.Dataset):
        return None #close the dataset
    elif isinstance(data, dbf.Dbf):
        data.close()
    else:
        return data

def gdal_open(filename):
    gdal.AllRegister()
    raster = gdal.Open(filename, GA_ReadOnly)
    if raster is None:
        raise Exception, 'Could not open image'
    return raster

def dbf_open(filename):
    return dbf.Dbf(filename, readOnly=1)


def gdal_create(data):
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(data['uri'], data['cols'], data['rows'], 1, data['dataType'])
    out_ds.SetProjection(data['projection'])
    out_ds.SetGeoTransform(data['geotransform'])
    return out_ds

def mimic(example, output):
    if isinstance(example, osgeo.gdal.Dataset):
        output['driver']    = example.GetDriver().ShortName
        output['cols']      = example.RasterXSize
        output['rows']      = example.RasterYSize
        output['projection']= example.GetProjection()
        output['geotransform'] = example.GetGeoTransform()
        
        return open(output)
        
        
