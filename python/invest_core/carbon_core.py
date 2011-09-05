import numpy as np
import data_handler
import carbon_seq
import carbon_diff
import carbon_value
import osgeo.gdal
import osgeo.osr as osr
from dbfpy import dbf
from math import exp

def execute(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with at least the following entries:
        args['lulc_cur'] - is a GDAL raster dataset
        args['lulc_fut'] - is a GDAL raster dataset
        args['carbon_pools'] - is a DBF dataset mapping carbon sequestration numbers to lulc classifications.
        args['seq_cur'] - a GDAL raster dataset for outputing the sequestered carbon
                          based on the current lulc
        args['seq_fut'] - a GDAL raster dataset for outputing the sequestered carbon
                          based on the future lulc
        args['seq_delta'] - a GDAL raster dataset for outputing the difference between
                            args['seq_cur'] and args['seq_fut']
        args['seq_value'] - a GDAL raster dataset for outputing the monetary gain or loss in
                            value of sequestered carbon.
        args['calc_value'] - is a Boolean.  True if we wish to perform valuation.
        args['lulc_cur_year'] - is an int.  Represents the year of lulc_cur
        args['lulc_fut_year'] - is an int.  Represents the year of lulc_fut
        args['c_value'] - a float.  Represents the price of carbon in US Dollars.
        args['discount'] - a float.  Represents the annual discount in the price of carbon
        args['rate_change'] - a float.  Represents the rate of change in the price of carbon
        
        returns nothing"""

    if args['calc_value']:
        valuate(args)
    else:
        sequester(args)
    

def sequester(args):
    """Executes the carbon sequestration model only.
    
        args - is a dictionary with at least the following entries:
        args['lulc_cur'] - is a GDAL raster dataset
        args['seq_cur'] - is a GDAL raster dataset
        args['carbon_pools'] - is a DBF dataset mapping sequestration numbers to lulc classifications
        
        No return value."""

    pools = build_pools(args['carbon_pools'], args['lulc_cur'], args['seq_cur'])

    rasterSeq(pools, args['lulc_cur'], args['seq_cur'])
    args['seq_cur'] = None #close the dataset

def valuate(args):
    """Executes the economic valuation model.
        
        args is a dictionary with all of the options detailed in execute()
        
        No return value"""
        
    numYears = float(args['lulc_fut_year'] - args['lulc_cur_year'])
    
    pools = build_pools(args['carbon_pools'], args['lulc_cur'], args['seq_cur'])
    
    rasterSeq(pools, args['lulc_cur'], args['seq_cur'])
    rasterSeq(pools, args['lulc_fut'], args['seq_fut'])
    
    rasterDiff(args['seq_cur'], args['seq_fut'], args['seq_delta'])
    
    rasterValue(args['seq_delta'], args['seq_value'], args['c_value'], args['discount'], args['rate_change'], numYears)
    
    for dataset in ('seq_value', 'seq_delta', 'seq_cur', 'seq_fut'):
        args[dataset] = None
    
    
    
def rasterValue(inputRaster, outputRaster, carbonValue, discount, rateOfChange, numYears):
    """iterates through the rows in a raster and applies the carbon valuation model
        to all values.
        
        inputRaster - is a GDAL raster dataset
        outputRaster - is a GDAL raster dataset for outputing the value of carbon sequestered
        carbonValue - is a float representing the price of carbon per metric ton
        discount - is a float representing the market discount rate for Carbon
        rateOfChange - is a float representing the annual rate of change in the price of Carbon.
        numYears - an int representing the number of years between current and future land cover maps
        
        No return value."""
        
    nodataDict = build_nodata_dict(inputRaster, outputRaster)
    lulc = inputRaster.GetRasterBand(1)
    
    multiplier = 0.
    #for n in np.arange(0, numYears-1., 1.0):
    for n in range(int(numYears)-1):
        multiplier += 1./(((1.+rateOfChange)**n)*(1.+discount)**n)
    
    for i in range(0, lulc.YSize):
        data = lulc.ReadAsArray(0, i, lulc.XSize, 1)
        out_array = carbon_value.execute(nodataDict, data, numYears, carbonValue, multiplier)
        outputRaster.GetRasterBand(1).WriteArray(out_array, 0, i)
        
    

def rasterSeq(pools, inputRaster, outputRaster):
    """Iterate through the rows in a raster and map carbon sequestration values
        to the output raster.
        
        pools - a python dict mapping lulc indices to sequestration data
        inputRaster - a GDAL raster dataset
        outputRaster - a GDAL raster dataset
        
        No return value."""
        
    lulc = inputRaster.GetRasterBand(1)
    for i in range(0, lulc.YSize):
        data = lulc.ReadAsArray(0, i, lulc.XSize, 1)
        out_array = carbon_seq.execute(data, pools)
        outputRaster.GetRasterBand(1).WriteArray(out_array, 0, i)
    

def rasterDiff(seq_cur, seq_fut, outputRaster):
    """Iterate through the rows in the two sequestration rasters and calculate the 
        difference in each pixel.  Maps the difference to the output raster.
        
        seq_cur - a GDAL raster dataset
        seq_fut - a GDAL raster dataset
        outputRaster - a GDAL raster dataset"""
    
    nodataDict = build_nodata_dict(seq_cur, outputRaster)
    lulc_cur_band = seq_cur.GetRasterBand(1)
    lulc_fut_band = seq_fut.GetRasterBand(1)
    for i in range(0, lulc_cur_band.YSize):
        cur_data = lulc_cur_band.ReadAsArray(0, i, lulc_cur_band.XSize, 1)
        fut_data = lulc_fut_band.ReadAsArray(0, i, lulc_cur_band.XSize, 1)
        out_array = carbon_diff.execute(nodataDict, cur_data, fut_data)
        outputRaster.GetRasterBand(1).WriteArray(out_array, 0, i)

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

def build_nodata_dict(inputRaster, outputRaster):
    inNoData = inputRaster.GetRasterBand(1).GetNoDataValue()
    outNoData = outputRaster.GetRasterBand(1).GetNoDataValue()
    
    nodata = {'cur': inNoData, 'fut': outNoData}
    return nodata

def build_pools(dbf, inputRaster, outputRaster):
    """Extract the nodata values from the input and output rasters and build
        the carbon pools dict.
        
        dbf - an open DBF dataset
        inputRaster - a GDAL dataset (representing an LULC)
        outputRaster - a GDAL dataset
        
        returns a dictionary calculating total carbon sequestered per lulc type.
        """
    area = pixelArea(inputRaster)
    lulc = inputRaster.GetRasterBand(1)
    
    inNoData = lulc.GetNoDataValue()
    outNoData = outputRaster.GetRasterBand(1).GetNoDataValue()
    
    return build_pools_dict(dbf, area, inNoData, outNoData)

def build_pools_dict(dbf, area, inNoData, outNoData):
    """Build a dict for the carbon pool data accessible for each lulc classification.
    
        dbf - the database file describing pools
        area - the area in Ha of each pixel
        inNoData - the no data value for the input map
        outNoData - the no data value for the output map
    
        returns a dictionary calculating total carbon sequestered per lulc type"""

    poolsDict = {int(inNoData): outNoData}
    for i in range(dbf.recordCount):
        sum = 0
        for field in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD'):
            sum += dbf[i][field]
        poolsDict[dbf[i]['LULC']] = sum * area
    return poolsDict
