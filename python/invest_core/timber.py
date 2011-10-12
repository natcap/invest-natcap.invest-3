"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json
import timber_core
from osgeo import gdal
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the timber model given uri
    inputs of files.
    
    args - a dictionary object of arguments
    
    args['output_dir'] - The file location where the output will be written
    args['timber_shp_uri'] - The shape file location
    args['plant_prod_uri'] - The attribute table location
    args['market_disc_rate'] - The market discount rate as a string
    """

    org.AllRegister()
    output_seq = ogr.GetDriverByName('ESRI Shapefile').CopyDataSource(args['timber_shp_uri'], "")
    timber_shp = ogr.Open(args['timber_shp_uri'])
    timber_layer = timber_shp.GetLayerByName("timber_shp_uri")
  
    args = { 'timber_shape': timber_shp,
            'timber_lyr': timber_layer,
            'plant_prod': dbf.Dbf(args['plant_prod_uri']),
            'output_seq': output_seq,
            'output_dir': args['output_dir'],
            'mdr': args['market_discount_rate']}

    timber_core.execute(args)

    #This is how GDAL closes its datasets in python
    
    output_seq = None
