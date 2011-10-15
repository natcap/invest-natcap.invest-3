import carbon_core
#import carbon_seq

def execute(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with at least the following entries:
        args['lulc'] - is a GDAL raster dataset
        args['carbon_pools'] - is an uncertainty dictionary that maps LULC type
                               to Mg/Ha of carbon where the field names are
                               appended by 'L', 'A', or 'H', for low, average, 
                               and high measurements.
        args['output'] - a GDAL raster dataset for outputing the sequestered carbon
                         contains 3 bands for low, average, and high
        
        returns nothing"""

    area = carbon_core.pixelArea(args['lulc'])
    lulc = args['lulc'].GetRasterBand(1)
    inNoData = lulc.GetNoDataValue()
    outNoData = args['output'].GetRasterBand(1).GetNoDataValue()

    #This maps pool types to band numbers
    poolTypes = {'L':1, 'A':2, 'H':3}
    pools = {}
    
    uncertaintyRank = None
    
    for poolType in poolTypes:
        pools[poolType] = build_uncertainty_pools_dict(args['carbon_pools'], poolType, area, inNoData, outNoData)
        maxValue,minValue = max(pools[poolType].values()), min(pools[poolType].values())
        if minValue == None:
            minValue = 0
        
        #create uncertainty dictionary with most recent dictionary as reference for keys
        if uncertaintyRank == None:
            uncertaintyRank = {}.fromkeys(pools[poolType].keys(),0.0)
        
        #rank each pooltype
        for type,value in pools[poolType].iteritems():
            if maxValue != minValue and value != None:
                uncertaintyRank[type] += (value-minValue)/(maxValue-minValue)/len(poolTypes)
    
    #add the uncertainty pool so it gets iterated over on the map step
    poolTypes['uncertainty'] = 4
    pools['uncertainty'] = uncertaintyRank

    #map each row in the lulc raster
    for rowNumber in range(0, lulc.YSize):
        data = lulc.ReadAsArray(0, rowNumber, lulc.XSize, 1)
        #create a seq map for each pooltype 
        for poolType, index in poolTypes.iteritems():
            out_array = carbon_core.carbon_seq(data, pools[poolType])
            args['output'].GetRasterBand(index).WriteArray(out_array, 0, rowNumber)
            

def build_uncertainty_pools_dict(dbf, poolType, area, inNoData, outNoData):
    """Build a dict for the carbon pool data accessible for each lulc classification.
    
        dbf - the database file describing pools
        poolType - one of 'L', 'A', or 'H' indicating low average or high
                   pool data
        area - the area in Ha of each pixel
        inNoData - the no data value for the input map
        outNoData - the no data value for the output map
    
        returns a dictionary calculating total carbon sequestered per lulc type"""

    poolsDict = {int(inNoData): outNoData}
    for i in range(dbf.recordCount):
        sum = 0
        for field in [ x + '_' + poolType for x in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD')]:
            sum += dbf[i][field]
        poolsDict[dbf[i]['LULC']] = sum * area
    return poolsDict
