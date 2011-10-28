"""InVEST Carbon Modle file handler module"""

import sys, os
import simplejson as json
import carbon_core
from osgeo import gdal, ogr
from osgeo.gdalconst import *
import numpy
from dbfpy import dbf

def execute(args):
    """This function invokes the carbon model given URI inputs of files.
        It will do filehandling and open/create appropriate objects to 
        pass to the core carbon biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at the following possible entries:
        
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
            
        args['calculate_sequestration'] - a boolean, True if sequestration
            is to be calculated.  Infers that args['lulc_fut_uri'] should be 
            set.
            
        args['calculate_hwp'] - a boolean, True if harvested wood product
            calcuation is to be done.  Also implies a sequestration 
            calculation.  Thus args['lulc_fut_uri'], args['hwp_cur_shape_uri'],
            args['hwp_fut_shape_uri'], args['lulc_cur_year'], and 
            args['lulc_fut_year'] should be set.
            
        args['calc_uncertainty'] - a Boolean.  True if we wish to calculate 
            uncertainty in the carbon model.  Implies that carbon pools should
            have value ranges
            
        args['uncertainty_percentile'] - the percentile cutoff desired for 
            uncertainty calculations (required if args['calc_uncertainty'] is 
            True) 
            
        args['lulc_cur_uri'] - is a uri to a GDAL raster dataset (required)
            
        args['lulc_fut_uri'] - is a uri to a GDAL raster dataset (required
         if calculating sequestration or HWP)
         
        args['lulc_cur_year'] - An integer representing the year of lulc_cur 
            used in HWP calculation (required if args['calculate_hwp'] is True)
            
        args['lulc_fut_year'] - An integer representing the year of  lulc_fut
            used in HWP calculation (required if args['calculate_hwp'] is True)
            
        args['carbon_pools_uri'] - is a uri to a DBF dataset mapping carbon 
            storage density to the lulc classifications specified in the
            lulc rasters.  If args['calc_uncertainty'] is True the columns
            should have additional information about min, avg, and max carbon
            pool measurements. 
            
        args['hwp_cur_shape_uri'] - Current shapefile uri for harvested wood 
            calculation (required if args['calculate_hwp'] is True) 
            
        args['hwp_fut_shape_uri'] - Future shapefile uri for harvested wood 
            calculation (required if args['calculate_hwp'] is True)
        
        returns nothing."""

    #This ensures we are not in Arc's python directory so that when
    #we import gdal stuff we don't get the wrong GDAL version.
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    gdal.AllRegister()

    #define biophysical model inputs
    biophysicalArgs = {}

    #Uncertainty percentage is required if calculating uncertainty
    if args['calc_uncertainty']:
        biophysicalArgs['uncertainty_percentile'] = \
            args['uncertainty_percentile']

    #lulc_cur is always required
    biophysicalArgs['lulc_cur'] = gdal.Open(args['lulc_cur_uri'],
                                            gdal.GA_ReadOnly)

    #a future lulc is only required if sequestering or hwp calculating
    if args['calculate_sequestration'] or args['calculate_hwp']:
        biophysicalArgs['lulc_fut'] = gdal.Open(args['lulc_fut_uri'],
                                            gdal.GA_ReadOnly)

    #Years and harvest shapes are required if doing HWP calculation
    if args['calculate_hwp']:
        for x in ['lulc_cur_year', 'lulc_fut_year']:
            biophysicalArgs[x] = args[x]
        for x in ['hwp_cur_shape', 'hwp_fut_shape']:
            biophysicalArgs[x] = args[x + '_uri']

    #Always need carbon pools, if uncertainty calculation they also need
    #to have range columns in them.  No need to check that in file handler 
    #though
    biophysicalArgs['carbon_pools'] = dbf.Dbf(args['carbon_pools_uri'])





    #Create GIS objects for input and output
    outputDirectoryName = 'Output'
    directoryPrefix = args['workspace_dir'] + os.sep + outputDirectoryName

    defaultURI = {'storage_cur' : directoryPrefix + 'tot_C_cur.tif'}



                  'storage_fut' : directoryPrefix + 'tot_C_fut.tif',
                  'seq_delta' : directoryPrefix + 'sequest.tif',
                  'seq_value' : directoryPrefix + 'value_seq.tif',
                  'biomass_cur' : directoryPrefix + 'bio_hwp_cur.tif',
                  'biomass_fut' : directoryPrefix + 'bio_hwp_fut.tif',
                  'volume_cur'  : directoryPrefix + 'vol_hwp_cur.tif',
                  'volume_fut'  : directoryPrefix + 'vol_hwp_fut.tif',
                  'output_seq' : directoryPrefix + 'uncertainty_sequestration.tif',
                  'output_map' : directoryPrefix + 'uncertainty_colormap.tif'}


    makeRasters(('storage_cur',), defaultURI, args)

    #open the future LULC if it has been provided
    if 'lulc_fut' in args:
        args['lulc_fut'] = gdal.Open(args['lulc_fut'], gdal.GA_ReadOnly)
        makeRasters(('storage_fut', 'seq_delta'), defaultURI, args)

    if args['calc_uncertainty'] == True:
        #create the uncertainty sequestration raster        
        args['output_seq'] = mimic(lulc_cur, defaultURI['output_seq'], nodata=0)

        #create the uncertainty colormap raster
        args['output_map'] = mimic(lulc_cur, defaultURI['output_map'],
                                    nodata=255, datatype=gdal.GDT_Byte)

    #Open the harvest maps
    if 'hwp_cur_shape' in args:
        fsencoding = sys.getfilesystemencoding()
        args['hwp_cur_shape'] = ogr.Open(args['hwp_cur_shape'].encode(fsencoding))
        makeRasters(('biomass_cur', 'volume_cur'), defaultURI, args)

        if 'hwp_fut_shape' in args:
            args['hwp_fut_shape'] = ogr.Open(args['hwp_fut_shape'].encode(fsencoding))
            makeRasters(('biomass_fut', 'volume_fut'), defaultURI, args)

    if args['calc_value'] == True:
        makeRasters(('seq_value',), defaultURI, args)

    #run the carbon model.
    carbon.execute(args)

    #run the carbon uncertainty code
#   carbon_scenario_uncertainty.execute(args)

    #close all newly created raster datasets
    for dataset in ('storage_cur', 'storage_fut', 'seq_delta', 'seq_value',
                    'biomass_cur', 'biomass_fut', 'volume_cur', 'volume_fut',
                    'output_seq', 'output_map'):
        if dataset in args:
            args[dataset] = None

    #close the pools DBF file
    args['carbon_pools'].close()


def makeRasters(dsList, defaultURI, args):
    """Create a new, blank raster at the correct URI for each raster in dsList.
        
        - dsList - a Python list or array of args dict keys to be created
        - defaultURI - a Python dict mapping args keys of datasets to their
            default URIs
        - args - a python dictionary with possible entries specified in
            invest_carbon_core.execute.  This function assumes that all entries
            used in this function are strings representing the URI to the desired
            dataset."""

    for dataset in dsList:
        if dataset in args:
            args[dataset] = mimic(args['lulc_cur'], args[dataset])
        else:
            args[dataset] = mimic(args['lulc_cur'], defaultURI[dataset])

def mimic(example, outputURI, format='GTiff', nodata= -5.0, datatype=gdal.GDT_Float32):
    """Create a new, empty GDAL raster dataset with the spatial references and
        geotranforms of the example GDAL raster dataset.
        
        example - a GDAL raster dataset
        outputURI - a string URI to the new output raster dataset.
        format='GTiff' - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata='-5.0 - a number that will be set as the nodata value for the 
            output raster
        datatype=gdal.GDT_Float32 - the datatype of the raster.
                
        returns a new GDAL raster dataset."""

    cols = example.RasterXSize
    rows = example.RasterYSize
    projection = example.GetProjection()
    geotransform = example.GetGeoTransform()

    driver = gdal.GetDriverByName(format)
    new_ds = driver.Create(outputURI, cols, rows, 1, datatype)
    new_ds.SetProjection(projection)
    new_ds.SetGeoTransform(geotransform)
    new_ds.GetRasterBand(1).SetNoDataValue(nodata)

    return new_ds

def uncertainty(args):
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
        maxValue, minValue = max(pools[poolType].values()), min(pools[poolType].values())
        if minValue == None:
            minValue = 0

        #create uncertainty dictionary with most recent dictionary as reference for keys
        if uncertaintyRank == None:
            uncertaintyRank = {}.fromkeys(pools[poolType].keys(), 0.0)

        #rank each pooltype
        for type, value in pools[poolType].iteritems():
            if maxValue != minValue and value != None:
                uncertaintyRank[type] += (value - minValue) / (maxValue - minValue) / len(poolTypes)

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

def carbon_scenario_uncertainty(args):
    """Runs a scenario based uncertainty model for two LULC maps.  Output
        is a 4 output_seq raster for 3 bands indicating carbon sequestration
        change for low, average, and high measurements.  Fourth output_seq is
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
        args['output_seq'] - a GDAL raster dataset for outputting the conservative
                            amount of carbon sequestered.
        args['output_map'] - a colorized map indicating the regions of
                            output_seq that fall into the percentile
                            ranges given in args['percentile'].  Green
                            is carbon sequestered increase and red is a
                            decrease.
        
        returns nothing"""

    area = carbon_core.pixelArea(args['lulc_cur'])
    lulcCurrent = args['lulc_cur'].GetRasterBand(1)
    lulcFuture = args['lulc_fut'].GetRasterBand(1)
    inNoData = lulcCurrent.GetNoDataValue()
    outNoData = args['output_seq'].GetRasterBand(1).GetNoDataValue()

    #This maps pool types to output_seq numbers
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
            sequesteredCurrent = carbon_core.carbon_seq(dataCurrent, pools[poolTypeA])
            sequesteredFuture = carbon_core.carbon_seq(dataFuture, pools[poolTypeB])
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

    #create colorband
    (minSeq, maxSeq) = output_seq.ComputeRasterMinMax()

    steps = 31
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

    #Cutoff output_seq based on percentile cutoff
    def percentileCutoff(val, percentCutoff, max, min):
        if max == min: return val
        p = (val - min) / (max - min)
        if p < percentCutoff or p > 1 - percentCutoff:
            return val
        return outNoData
    percentileCutoffFun = np.vectorize(percentileCutoff)

    maxIndex = np.vectorize(mapIndexFun)
    for rowNumber in range(0, output_seq.YSize):
        seqRow = output_seq.ReadAsArray(0, rowNumber, output_seq.XSize, 1)
        #select only those elements which lie within the range percentile
        seqRow = percentileCutoffFun(seqRow, args['percentile'], maxMin[0], maxMin[1])
        #map them to colors
        args['output_map'].GetRasterBand(1).WriteArray(maxIndex(seqRow), 0, rowNumber)


#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
