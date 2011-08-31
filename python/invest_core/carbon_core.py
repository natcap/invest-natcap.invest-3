import numpy as np
import data_handler
import carbon_seq
import osgeo.gdal
import osgeo.osr as osr
from dbfpy import dbf

def execute(args):
    #args is a dictionary
    #GDAL URI is handled before this function is called, so GDAL object should be passed with args
    #carbon pool should have been processed from its file into a dictionary, passed with args
    #output file URI should also have been passed with args
    #The purpose of this function is to assemble calls to the various carbon components into a conhesive result

    area = pixelArea(args['lulc'])

    lulc = args['lulc'].GetRasterBand(1)
    #args['output'].GetRasterBand(1).SetNoDataValue(-1.0)

    inNoData = lulc.GetNoDataValue()
    outNoData = args['output'].GetRasterBand(1).GetNoDataValue() 
    
    pools = build_pools_dict(args['carbon_pools'], area, inNoData, outNoData)



    for i in range(0, lulc.YSize):
        data = lulc.ReadAsArray(0, i, lulc.XSize - 1, 1)
        out_array = carbon_seq.execute(data, pools)
        args['output'].GetRasterBand(1).WriteArray(out_array, 0, i)
        
    args['output'] = None
    
    

def pixelArea(dataset):
    """Calculates the pixel area of the given dataset.
    
        dataset - GDAL dataset
    
        returns area in Ha of each pixel in dataset"""

    srs = osr.SpatialReference()
    srs.SetProjection(dataset.GetProjection())
    linearUnits = srs.GetLinearUnits()
    geotransform = dataset.GetGeoTransform()
    #take absolute value since sometimes negative widths/heights
    areaMeters = abs(geotransform[1] * geotransform[5] * (linearUnits ** 2))
    return areaMeters / (10 ** 4) #convert m^2 to Ha

def build_pools_dict(dbf, area, inNoData, outNoData):
    """Build a dict for the carbon pool data accessible for each lulc classification.
    
        dbf - the database file describing pools
        area - the area in Ha of each pixel
    
        returns a dictionary calculating total carbon sequestered per lulc type"""

    poolsDict = {int(inNoData): outNoData}
    for i in range(dbf.recordCount):
        sum = 0
        for field in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD'):
            sum += dbf[i][field]
        poolsDict[dbf[i]['LULC']] = sum * area
    return poolsDict
