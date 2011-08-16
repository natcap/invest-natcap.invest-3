import numpy as np
from osgeo import *
import carbon_core


def carbon_uri(in_args):
    #preprocess in_args
    out_args = {}
    for key, value in in_args.iteritems():
        if type(value) == 'dict':
            #probably need to process a gdal object hee
            out_args[key] = dst_ds = driver.Create(value[uri], 10, 10, 1, gdal.GDT_Byte)
        else:
            out_args[key] = value

    #invoke core function
    carbon_core.carbon_core(out_args)

    #process any return result (save to disk)
    print 'TODO: save stuff'
