import carbon_core
import carbon_uncertainty
import carbon_seq
import numpy as np
from osgeo import gdal

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
        args['percentile'] - cuts the output to be the top and bottom
                             percentile of sequestered carbon based on
                             the uncertainty scenarios
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
    outNoData = args['output_seq'].GetRasterBand(1).GetNoDataValue()

    #This maps pool types to band numbers
    poolTypes = {'L':1, 'A':2, 'H':3}
    pools = {}

    uncertaintyRank = None

    for poolType in poolTypes:
        pools[poolType] = carbon_uncertainty.build_uncertainty_pools_dict(
            args['carbon_pools'], poolType, area, inNoData, outNoData)

    def singleSelector(a, b, c):
        if c == 0: return outNoData
        return min(a, b)

    vectorSelector = np.vectorize(singleSelector)

    maxMin = None
    output_seq = args['output_seq'].GetRasterBand(1)
    #map each row in the lulc raster
    for rowNumber in range(lulcCurrent.YSize):
        dataCurrent = lulcCurrent.ReadAsArray(0, rowNumber, lulcCurrent.XSize, 1)
        dataFuture = lulcFuture.ReadAsArray(0, rowNumber, lulcFuture.XSize, 1)
        #create a seqestration map for high-low, low-high, and average-average
        sequesteredChangeArray = []
        for poolTypeA, poolTypeB in [('L', 'H'), ('H', 'L'), ('A', 'A')]:
            sequesteredCurrent = carbon_seq.execute(dataCurrent, pools[poolTypeA])
            sequesteredFuture = carbon_seq.execute(dataFuture, pools[poolTypeB])
            sequesteredChange = sequesteredCurrent - sequesteredFuture

            if maxMin is None:
                maxMin = (np.max(sequesteredChange), np.min(sequesteredChange))
            else:
                maxMin = (max(np.max(sequesteredChange), maxMin[0]),
                      min(np.min(sequesteredChange), maxMin[1]))

            sequesteredChangeArray.append(sequesteredChange)

        #Output the min value of l-h or h-l if average is >=0 or max value if < 0
        output_seq.WriteArray(vectorSelector(sequesteredChangeArray[0],
                                              sequesteredChangeArray[1],
                                              sequesteredChangeArray[2]), 0, rowNumber)

    #Cutoff output_seq based on percentile cutoff
    def percentileCutoff(val, percentCutoff, max, min):
        if max == min: return val
        p = (val - min) / (max - min)
        if p < percentCutoff or p > 1 - percentCutoff:
            return val
        return outNoData
    percentileCutoffFun = np.vectorize(percentileCutoff)
    for rowNumber in range(output_seq.YSize):
        rowData = output_seq.ReadAsArray(0, rowNumber, output_seq.XSize, 1)
        output_seq.WriteArray(percentileCutoffFun(rowData, args['percentile'],
                              maxMin[0], maxMin[1]), 0, rowNumber)

    #create colorband
    band = args['output_seq'].GetRasterBand(1)
    minSeq = band.GetMinimum()
    maxSeq = band.GetMinimum()
    if minSeq is None or maxSeq is None:
        (minSeq, maxSeq) = band.ComputeRasterMinMax()


    steps = 11
    mid = steps / 2
    def mapIndexFun(x):
        if x == 0: return 255
        if x < 0:
            return int((minSeq - x) / minSeq * mid)
        return int(steps - (maxSeq - x) / maxSeq * mid)

    #Make a simple color table that ranges from red to green
    colorTable = gdal.ColorTable()
    negColor = (255, 0, 0)
    posColor = (100, 255, 0)
    for i in range(mid):
        frac = 1 - float(i) / mid
        colorTable.SetColorEntry(i, (int(negColor[0] * frac), int(negColor[1] * frac), int(negColor[2] * frac)))
        colorTable.SetColorEntry(steps - i, (int(posColor[0] * frac), int(posColor[1] * frac), int(posColor[2] * frac)))
    colorTable.SetColorEntry(mid, (0, 0, 0))
    args['output_map'].GetRasterBand(1).SetColorTable(colorTable)

    maxIndex = np.vectorize(mapIndexFun)
    for rowNumber in range(0, band.YSize):
        seqRow = band.ReadAsArray(0, rowNumber, band.XSize, 1)
        args['output_map'].GetRasterBand(1).WriteArray(maxIndex(seqRow), 0, rowNumber)
