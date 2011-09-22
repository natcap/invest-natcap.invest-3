import imp, sys, os
import simplejson as json
import carbon_core
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the carbon model given URI inputs of files.
        
        args - a python dictionary with at the following possible entries:
        args['lulc_cur'] - is a uri to a GDAL raster dataset
        args['lulc_fut'] - is a uri to a GDAL raster dataset
        args['carbon_pools'] - is a uri to a DBF dataset mapping carbon 
            sequestration numbers to lulc classifications.
        args['storage_cur'] - a uri to a GDAL raster dataset for outputing the 
            sequestered carbon based on the current lulc
        args['storage_fut'] - a uri to a GDAL raster dataset for outputing the
            sequestered carbon
            based on the future lulc
        args['seq_delta'] - a uri to a GDAL raster dataset for outputing the
             difference between args['storage_cur'] and args['storage_fut']
        args['seq_value'] - a uri to a GDAL raster dataset for outputing the 
            monetary gain or loss in value of sequestered carbon.
        args['calc_value'] - is a Boolean.  True if we wish to perform valuation.
        args['lulc_cur_year'] - is an int.  Represents the year of lulc_cur
        args['lulc_fut_year'] - is an int.  Represents the year of lulc_fut
        args['c_value'] - a float.  Represents the price of carbon in US Dollars.
        args['discount'] - a float.  Represents the annual discount in the 
            price of carbon
        args['rate_change'] - a float.  Represents the rate of change in the 
            price of carbon

        returns nothing."""
        
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    gdal.AllRegister()
    
    lulc_cur = gdal.Open(args['lulc_cur'], gdal.GA_ReadOnly)
    lulc_fut = gdal.Open(args['lulc_fut'], gdal.GA_ReadOnly)
    
    args = {'lulc_cur'     : lulc_cur,
            'lulc_fut'     : lulc_fut,
            'carbon_pools' : dbf.Dbf(args['carbon_pools']),
            'storage_cur'  : mimic(lulc_cur, args['storage_cur']),
            'seq_delta'    : mimic(lulc_cur, args['seq_delta']),
            'seq_value'    : mimic(lulc_cur, args['seq_value']),
            'lulc_cur_year': args['lulc_cur_year'],
            'lulc_fut_year': args['lulc_fut_year'],
            'c_value'      : args['c_value'],
            'discount'     : args['discount'],
            'rate_change'  : args['rate_change'],
            'hwp_cur_shape': ogr.Open(args['hwp_cur_shape']),
            'hwp_fut_shape': ogr.Open(args['hwp_fut_shape'])}
    
    carbon_core.execute(args)
    
    #close all newly created datasets
    for dataset in ('storage_cur', 'seq_delta', 'seq_value'):
        args[dataset] = None
    
    
def mimic(example, outputURI):
    """Create a new, empty GDAL raster dataset with the spatial references and
        geotranforms of the example GDAL raster dataset.
        
        example - a GDAL raster dataset
        outputURI - a string URI to the new output raster dataset.
        
        returns a new GDAL raster dataset."""
        
    cols         = example.RasterXSize
    rows         = example.RasterYSize
    projection   = example.GetProjection()
    geotransform = example.GetGeoTransform()
    
    driver = gdal.GetDriverByName("GTiff")
    new_ds = driver.Create(outputURI, cols, rows, 1, gdal.GDT_Float32)
    new_ds.SetProjection(projection)
    new_ds.SetGeoTransform(geotransform)
    new_ds.GetRasterBand(1).SetNoDataValue(-5.0)
    
    return new_ds
