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
        args['output_dir'] - a uri to the output directory.
        args['storage_cur'] - for outputing the sequestered carbon based on the 
            current lulc
        args['storage_fut'] - for outputing the sequestered carbon based on the 
            future lulc
        args['seq_delta'] - for outputing the difference between 
            args['storage_cur'] and args['storage_fut']
        args['seq_value'] - for outputing the monetary gain or loss in value 
            of sequestered carbon. 
        args['biomass_cur'] - for outputing the biomass of harvested HWP
            parcels on the current landscape
        args['biomass_fut'] - for outputing the biomass of harvested HWP
            parcels on the future landscape
        args['volume_cur'] - for outputing the volume of HWP on the current
            landscape
        args['volume_fut'] - for outputing the volume of HWP on the future
            landscape
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

    #specify generated URIs
    directoryPrefix = args['output_dir'] + os.sep
    defaultURI = {'storage_cur' : directoryPrefix + 'tot_C_cur.tif',
                  'storage_fut' : directoryPrefix + 'tot_C_fut.tif',
                  'seq_delta' : directoryPrefix + 'sequest.tif',
                  'seq_value' : directoryPrefix + 'value_seq.tif',
                  'biomass_cur' : directoryPrefix + 'bio_hwp_cur.tif',
                  'biomass_fut' : directoryPrefix + 'bio_hwp_fut.tif',
                  'volume_cur'  : directoryPrefix + 'vol_hwp_cur.tif',
                  'volume_fut'  : directoryPrefix + 'vol_hwp_fut.tif', }

    #open the two required elements.
    lulc_cur = gdal.Open(args['lulc_cur'], gdal.GA_ReadOnly)
    args['lulc_cur'] = lulc_cur
    args['carbon_pools'] = dbf.Dbf(args['carbon_pools'])

    #open the future LULC if it has been provided
    if 'lulc_fut' in args:
        args['lulc_fut'] = gdal.Open(args['lulc_fut'], gdal.GA_ReadOnly)

    #open any necessary output datasets, using user-provided URI if it exists
    for dataset in ('seq_delta', 'seq_value', 'storage_cur', 'storage_fut',
                    'biomass_cur', 'biomass_fut', 'volume_cur', 'volume_fut'):
        if dataset in args:
            args[dataset] = mimic(lulc_cur, args[dataset])
        else:
            args[dataset] = mimic(lulc_cur, defaultURI[dataset])

    #Set other values the user provides for valuation
    for item in ('lulc_cur_year', 'lulc_fut_year', 'c_value', 'discount', 'rate_change'):
        if item in args:
            args[item] = args[item]

    #Open the harvest maps
    for shape in ('hwp_cur_shape', 'hwp_fut_shape'):
        if shape in args:
            args[shape] = ogr.Open(args[shape])

    #run the carbon model.
    carbon_core.execute(args)

    #close all newly created raster datasets
    for dataset in ('storage_cur', 'storage_fut', 'seq_delta', 'seq_value'):
        args[dataset] = None

    #close the pools DBF file
    args['carbon_pools'].close()


def mimic(example, outputURI, format='GTiff'):
    """Create a new, empty GDAL raster dataset with the spatial references and
        geotranforms of the example GDAL raster dataset.
        
        example - a GDAL raster dataset
        outputURI - a string URI to the new output raster dataset.
        format='GTiff' - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        
        returns a new GDAL raster dataset."""

    cols = example.RasterXSize
    rows = example.RasterYSize
    projection = example.GetProjection()
    geotransform = example.GetGeoTransform()

    driver = gdal.GetDriverByName(format)
    new_ds = driver.Create(outputURI, cols, rows, 1, gdal.GDT_Float32)
    new_ds.SetProjection(projection)
    new_ds.SetGeoTransform(geotransform)
    new_ds.GetRasterBand(1).SetNoDataValue(-5.0)

    return new_ds
