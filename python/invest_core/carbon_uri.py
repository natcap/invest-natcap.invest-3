import numpy as np
#from osgeo import *
#import carbon_core
import os
from osgeo import *
#import gdal
#from gdalconst import *

environList = os.environ['PATH'].split(';')
environList.insert(0, r'C:\gdalwin32-1.6\bin')
os.environ['PATH'] = ';'.join(environList)

#import gdal
import osgeo.gdal
#from osgeo import gdal

def carbon_uri(in_args):
    #preprocess in_args
    out_args = {}
    for key, value in in_args.iteritems():
        if type(value) == 'dict':
            #probably need to process a gdal object hee
            out_args[key] = dst_ds = driver.Create(value['uri'], 10, 10, 1, gdal.GDT_Byte)
        else:
            out_args[key] = value

        driver = gdal.GetDriverByName('AIG')
        out_args['driver'] = dst_ds = driver.Create(in_args['lulc']['uri'], 10, 10, 1, gdal.GDT_Byte)
    #invoke core function
#    carbon_core.execute(out_args)

    #process any return result (save to disk)
    print 'TODO: save stuff'
