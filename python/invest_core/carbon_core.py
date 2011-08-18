from numpy import *
import osgeo.gdal
from dbfpy import dbf

def execute(args):
    #args is a dictionary
    #GDAL URI is handled before this function is called, so GDAL object should be passed with args
    #carbon pool should have been processed from its file into a dictionary, passed with args
    #output file URI should also have been passed with args
    #The purpose of this function is to assemble calls to the various carbon components into a conhesive result

    cols = args['lulc'].RasterXSize
    lulc = args['lulc'].GetRasterBand(1)

    #get the carbon pools as an array that we can use
    #The new array uses key -> value pairings as you would expect,
    #where key = LULC index and value = sum of all carbon pools for that key
    pools = args['carbon_pool'] #pools is a dbf object
    poolsArray = None
    for i in range(pools.recordCount):
        sum = 0
        for field in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD'):
            sum = sum + pools[i][field]
        poolsArray[pools[i]['LULC']] = sum
    
    

    #initialize an output array
    #it's the same dimensions as the lulc
    output = zeros(lulc.shape)

    for i in range(rows):
        data = lulc.ReadAsArray(0, i, cols, 1)
        carbon_seq(data, poolsArray, output)

