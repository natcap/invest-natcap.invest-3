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

    #Load and copy relevant inputs from args into a dictionary that
    #can be passed to the biophysical core model
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
        fsencoding = sys.getfilesystemencoding()
        for x in ['hwp_cur_shape', 'hwp_fut_shape']:
            biophysicalArgs[x] = ogr.Open(args[x + '_uri'].encode(fsencoding))

    #Always need carbon pools, if uncertainty calculation they also need
    #to have range columns in them, but no need to check at this level.
    biophysicalArgs['carbon_pools'] = dbf.Dbf(args['carbon_pools_uri'])


    #At this point all inputs are loaded into biophysicalArgs.  The 
    #biophysical model also needs temporary and output files to do its
    #calculation.  These are calculated next.

    #These lines sets up the output directory structure for the workspace
    outputDirectoryPrefix = args['workspace_dir'] + os.sep + 'Output'
    intermediateDirectoryPrefix = args['workspace_dir'] + os.sep + \
        'Intermediate'

    #This defines a dictionary that links output/temporary GDAL/OAL objects
    #to their locations on disk.  Helpful for creating the objects in the next 
    #step
    outputURIs = {}
    outputURIs['tot_C_cur'] = outputDirectoryPrefix + 'tot_C_cur.tif'
    if args['calculate_sequestration'] or args['calculate_hwp']:
        outputURIs['tot_C_fut'] = outputDirectoryPrefix + 'tot_C_fut.tif'
        outputURIs['sequest'] = outputDirectoryPrefix + 'sequest.tif'

    #If we calculate uncertainty, we need to generate the colorized map that
    #Highlights the percentile ranges
    if args['calculate_uncertainty']:
        outputURIs['uncertainty_percentile_map'] = outputDirectoryPrefix + \
            'uncertainty_colormap.tif'

    #If we're doing a HWP calculation, we need temporary rasters to hold the
    #HWP pools
    if args['calculate_hwp']:
        outputURIs['bio_hwp_cur'] = intermediateDirectoryPrefix + \
            'bio_hwp_cur.tif'
        outputURIs['bio_hwp_fut'] = intermediateDirectoryPrefix + \
            'bio_hwp_fut.tif'
        outputURIs['vol_hwp_cur'] = intermediateDirectoryPrefix + \
            'vol_hwp_cur.tif'
        outputURIs['vol_hwp_fut'] = intermediateDirectoryPrefix + \
            'vol_hwp_fut.tif'

    #Create the output and intermediate rasters to be the same size/format as
    #the base LULC
    for datasetName, datasetPath in outputURIs.iteritems():
        biophysicalArgs[datasetName] = mimic(args['lulc_cur'], datasetPath,
                                             'GTiff', -5.0, gdal.GDT_Float32)

    #run the carbon model.
    #carbon.execute(biophysicalArgs)

    #close all newly created raster datasets (is this required?)
    for dataset in biophysicalArgs:
        biophysicalArgs[dataset] = None

    #close the pools DBF file
    args['carbon_pools'].close()


def mimic(base, outputURI, format, nodata, datatype):
    """Create a new, empty GDAL raster dataset with the spatial references,
        dimensions and geotranforms of the base GDAL raster dataset.
        
        base - a the GDAL raster dataset to base output size, and transforms on
        outputURI - a string URI to the new output raster dataset.
        format - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata - a value that will be set as the nodata value for the 
            output raster.  Should be the same type as 'datatype'
        datatype - the pixel datatype of the output raster, for example 
            gdal.GDT_Float32.  See the following header file for supported 
            pixel types:
            http://www.gdal.org/gdal_8h.html#22e22ce0a55036a96f652765793fb7a4
                
        returns a new GDAL raster dataset."""

    cols = base.RasterXSize
    rows = base.RasterYSize
    projection = base.GetProjection()
    geotransform = base.GetGeoTransform()

    driver = gdal.GetDriverByName(format)
    newRaster = driver.Create(outputURI, cols, rows, 1, datatype)
    newRaster.SetProjection(projection)
    newRaster.SetGeoTransform(geotransform)
    newRaster.GetRasterBand(1).SetNoDataValue(nodata)

    return newRaster

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
