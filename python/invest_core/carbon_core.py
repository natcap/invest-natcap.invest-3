import numpy as np
import data_handler
import carbon_seq
import osgeo.gdal
from dbfpy import dbf

def execute(args):
    #args is a dictionary
    #GDAL URI is handled before this function is called, so GDAL object should be passed with args
    #carbon pool should have been processed from its file into a dictionary, passed with args
    #output file URI should also have been passed with args
    #The purpose of this function is to assemble calls to the various carbon components into a conhesive result

    lulc = args['lulc'].GetRasterBand(1)

    pools = build_pools_dict(args['carbon_pools'])

    for i in range(1, lulc.YSize):
        data = lulc.ReadAsArray(1, i, lulc.XSize - 1, 1)
        out_array = carbon_seq.execute(data, pools)
        args['output'].GetRasterBand(1).WriteArray(out_array, 0, i)

def build_pools_dict(dbf):
    """Build a dict for the carbon pool data accessible for each lulc classification."""
    poolsDict = {}
    for i in range(dbf.recordCount):
        sum = 0
        for field in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD'):
            sum = sum + dbf[i][field]
        poolsDict[dbf[i]['LULC']] = sum
    return poolsDict
