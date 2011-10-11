"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json
import carbon_scenario_uncertainty
from osgeo import gdal
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the timber model given uri
    inputs of files.
    
    args - a dictionary object of arguments
    
    args['output_dir'] - The file location where the output will be written
    args['lulc_cur_uri'] - The shape file location
    args['plant_prod_uri'] - The attribute table location
    args['market_discount_rate'] - The market discount rate as a string
    """

    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    org.AllRegister()
    output_seq = ogr.GetDriverByName("Memory").\
                    CopyDataSource(args['lulc_cur_uri'], "")
    lulc_cur = ogr.Open(args['lulc_cur_uri'])
  
    args = { 'lulc_cur': lulc_cur,
            'plant_prod': dbf.Dbf(args['plant_prod_uri']),
            'output_seq': output_seq,
            'mdr': args['market_discount_rate']}

    timber.execute(args)

    #This is how GDAL closes its datasets in python
    lulc_cur = None
    output_seq = None

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
