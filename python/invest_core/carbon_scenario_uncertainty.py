import carbon_core
import carbon_uncertainty
import carbon_seq
import numpy as np

def execute(args):
    """Runs a scenario based uncertainty model for two LULC maps.  Output
        is a 4 band raster for 3 bands indicating carbon sequestration
        change for low, average, and high measurements.  Fourth band is
        the minimum percentage ranking of each pixel in each of the
        three scenarios.
    
        args - is a dictionary with at least the following entries:
        args['lulc_cur'] - is a GDAL raster dataset for current LULC
        args['lulc_fut'] - is a GDAL raster dataset for future LULC
        args['carbon_pools'] - is an uncertainty dictionary that maps LULC type
                               to Mg/Ha of carbon where the field names are
                               appended by 'L', 'A', or 'H', for low, average, 
                               and high measurements.
        args['output'] - a 4 band GDAL raster dataset for outputting the change
                            in sequestered carbon for low, average, and high
                            carbon pool measurements.  The 4th band indicates
                            the minimum rank of that pixel in terms of total
                            carbon sequestered across each of the 3 low, avg,
                            high scenarios.  It is a rough measurement of
                            the uncertainty of the measurement.  For example,
                            a value of .9 would indicate that in the 3 scenarios
                            the amount of carbon sequestered ranked at least 
                            in the top 90% of all 3 scenarios which would
                            indicate a high amount of certainty.
        
        returns nothing"""

    area = carbon_core.pixelArea(args['lulc_cur'])
    lulcCurrent = args['lulc_cur'].GetRasterBand(1)
    lulcFuture = args['lulc_fut'].GetRasterBand(1)
    inNoData = lulcCurrent.GetNoDataValue()
    outNoData = args['output'].GetRasterBand(1).GetNoDataValue()

    #This maps pool types to band numbers
    poolTypes = {'L':1, 'A':2, 'H':3}
    pools = {}

    uncertaintyRank = None

    for poolType in poolTypes:
        pools[poolType] = carbon_uncertainty.build_uncertainty_pools_dict(
            args['carbon_pools'], poolType, area, inNoData, outNoData)

    bandRanges = {1: None,
                  2: None,
                  3: None}

    #map each row in the lulc raster
    for rowNumber in range(0, lulcCurrent.YSize):
        dataCurrent = lulcCurrent.ReadAsArray(0, rowNumber, lulcCurrent.XSize, 1)
        dataFuture = lulcFuture.ReadAsArray(0, rowNumber, lulcFuture.XSize, 1)
        #create a seqestration map for high-low, low-high, and average-average
        for poolTypeA, poolTypeB, outputIndex in [('L', 'H', 1), ('H', 'L', 2), ('A', 'A', 3)]:
            sequesteredCurrent = carbon_seq.execute(dataCurrent, pools[poolTypeA])
            sequesteredFuture = carbon_seq.execute(dataFuture, pools[poolTypeB])
            sequesteredChange = sequesteredCurrent - sequesteredFuture
            #build up the min/max dictionary for each band
            if not bandRanges[outputIndex]:
                bandRanges[outputIndex] = (np.min(sequesteredChange), np.max(sequesteredChange))
            else:
                bandRanges[outputIndex] = (min(np.min(sequesteredChange), bandRanges[outputIndex][0]),
                                       max(np.max(sequesteredChange), bandRanges[outputIndex][1]))

            args['output'].GetRasterBand(outputIndex).WriteArray(sequesteredChange, 0, rowNumber)

    #create the output percentile band
    def convertToPercent(x, min, max):
        if min == max:
            return 0
        return (x - min) / (max - min)
    percentileMapper = np.vectorize(convertToPercent)

    for rowNumber in range(lulcCurrent.YSize):
        outputRow = args['output'].GetRasterBand(1).ReadAsArray(0, rowNumber,
                                                    lulcCurrent.XSize, 1)
        outputPercentile = percentileMapper(outputRow, bandRanges[1][0], bandRanges[1][1])
        for i in [2, 3]:
            outputPercentile = np.minimum(outputPercentile,
                    percentileMapper(args['output'].GetRasterBand(i).ReadAsArray(0,
                    rowNumber, lulcCurrent.XSize, 1), bandRanges[i][0], bandRanges[i][1]))
        args['output'].GetRasterBand(4).WriteArray(outputPercentile, 0, rowNumber)
