"""Module that contains the core computational components for the carbon model
    including the biophysical and valuation functions"""

import math
import logging

import numpy as np
from osgeo import gdal
from osgeo import ogr

import invest_natcap.raster_utils as raster_utils
from invest_natcap.dbfpy import dbf
from invest_natcap.invest_core import invest_core

LOGGER = logging.getLogger('carbon_core')

def biophysical(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.

        args - is a dictionary with at least the following entries:
        args['lulc_cur'] - is a GDAL raster representing the current land 
            use/land cover map (required)
        args['lulc_fut'] - is a GDAL raster dataset representing the future 
            land use/land cover map (required if doing sequestration, HWP, or
            uncertainty calculations)
        args['carbon_pools'] - is a DBF dataset mapping carbon storage density
            to lulc classifications in input LULC rasters.
        args['hwp_cur_shape'] - OAL shapefile representing harvest rates on 
            current lulc (required if calculating HWP)
        args['hwp_fut_shape'] - OAL shapefile representing harvest rates on 
            future lulc (required if calculating HWP)
        args['lulc_cur_year'] - an int represents the year of lulc_cur 
            (required if there's an hwp shape)
        args['lulc_fut_year'] - an int represents the year of lulc_fut
            (required if calculating future HWP)
        args['tot_C_cur'] - an output GDAL raster dataset representing total 
            carbon stored on the current lulc, must be same dimensions as 
            lulc_cur (required)
        args['tot_C_fut'] - an output GDAL raster dataset representing total 
            carbon stored on the future lulc must be same dimensions as 
            lulc_cur (required if doing sequestration)
        args['sequest'] - an output GDAL raster dataset representing carbon 
            sequestration and emissions between current and future landscapes
            (required, if doing sequestration)
        args['c_hwp_cur'] - an output GDAL raster dataset representing 
            carbon stored in harvested wood products for current land cover 
            (required if doing current HWP calculation)
        args['c_hwp_fut'] - an output GDAL raster dataset representing 
            carbon stored in harvested wood products for futureland cover 
            (required if doing future HWP calculation)
        args['bio_hwp_cur'] - an output GDAL raster dataset representing
            biomass of harvested wood products in current land cover
            (required if calculating HWP on a current landscape)
        args['vol_hwp_cur'] - an output GDAL raster dataset representing
            volume of harvested wood products in current land cover
            (required if calculating HWP on a current landscape)
        args['bio_hwp_fut'] - an output GDAL raster dataset representing
            biomass of harvested wood products in future land cover
            (required if calculating HWP on a future landscape)
        args['vol_hwp_fut'] - an output GDAL raster dataset representing
            volume of harvested wood products in future land cover
            (required if calculating HWP on a current landscape)
            
        returns nothing"""

    #Calculate the per pixel carbon storage due to lulc pools, convert
    #area to hectares by dividing by 10000
    cell_area_ha = raster_utils.pixel_area(args['lulc_cur']) / 10000.0

    #Create carbon pool dictionary with appropriate values to handle
    #nodata in the input and nodata in the output
    LOGGER.debug("building carbon pools")
    inNoData = args['lulc_cur'].GetRasterBand(1).GetNoDataValue()
    outNoData = args['tot_C_cur'].GetRasterBand(1).GetNoDataValue()
    pools = build_pools_dict(args['carbon_pools'], cell_area_ha, inNoData,
                             outNoData)
    LOGGER.debug("built carbon pools")


    #calculate carbon storage for the current landscape
    LOGGER.info('calculating carbon storage for the current landscape')
    calculateCarbonStorage(pools, args['lulc_cur'].GetRasterBand(1),
                           args['tot_C_cur'].GetRasterBand(1))
    LOGGER.info('finished calculating carbon storage for the current \
landscape')

    #Calculate HWP pools if a HWP shape is present
    if 'hwp_cur_shape' in args:
        LOGGER.info('calculating HWP storage for the current landscape')
        calculateHWPStorageCur(args['hwp_cur_shape'], args['c_hwp_cur'],
                            args['bio_hwp_cur'], args['vol_hwp_cur'],
                            cell_area_ha, args['lulc_cur_year'])
        LOGGER.info('calculating raster stats for bio_hwp_cur')
        invest_core.calculateRasterStats(args['bio_hwp_cur'].GetRasterBand(1))
        LOGGER.info('calculating raster stats for vol_hwp_cur')
        invest_core.calculateRasterStats(args['vol_hwp_cur'].GetRasterBand(1))
        LOGGER.info('calculating raster stats for c_hwp_cur')
        invest_core.calculateRasterStats(args['c_hwp_cur'].GetRasterBand(1))

        #Add the current hwp carbon storage to tot_C_cur
        invest_core.rasterAdd(args['tot_C_cur'].GetRasterBand(1),
                              args['c_hwp_cur'].GetRasterBand(1),
                              args['tot_C_cur'].GetRasterBand(1))
        LOGGER.info('finished HWP storage for the current landscape')

    LOGGER.info('calculating raster stats for tot_C_cur')
    invest_core.calculateRasterStats(args['tot_C_cur'].GetRasterBand(1))

    if 'lulc_fut' in args:
        #calculate carbon storage for the future landscape if it exists
        LOGGER.info('calculating carbon storage for future landscape')
        calculateCarbonStorage(pools, args['lulc_fut'].GetRasterBand(1),
                               args['tot_C_fut'].GetRasterBand(1))
        LOGGER.info('finished calculating carbon storage for future \
landscape')

        #Calculate a future HWP pool if a future landcover map is present, 
        #this means that a sequestration scenario is happening, so a current 
        #and/or future harvest map could add an additional pool to the future 
        #storage map
        harvestMaps = {}
        if 'hwp_cur_shape' in args:
            harvestMaps['cur'] = args['hwp_cur_shape']
        if 'hwp_fut_shape' in args:
            harvestMaps['fut'] = args['hwp_fut_shape']
        if 'c_hwp_fut' in args:
            LOGGER.info('calculating HWP storage for future landscape')
            calculateHWPStorageFut(harvestMaps, args['c_hwp_fut'],
                args['bio_hwp_fut'], args['vol_hwp_fut'], cell_area_ha,
                args['lulc_cur_year'], args['lulc_fut_year'])
            LOGGER.info('calculating raster stats for bio_hwp_fut')
            invest_core.calculateRasterStats(args['bio_hwp_fut'].
                                            GetRasterBand(1))
            LOGGER.info('calculating raster stats for vol_hwp_fut')
            invest_core.calculateRasterStats(args['vol_hwp_fut'].
                                             GetRasterBand(1))
            LOGGER.info('calculating raster stats for c_hwp_fut')
            invest_core.calculateRasterStats(args['c_hwp_fut'].
                                             GetRasterBand(1))

            #Add the future hwp carbon storage to tot_C_fut
            invest_core.rasterAdd(args['tot_C_fut'].GetRasterBand(1),
                              args['c_hwp_fut'].GetRasterBand(1),
                              args['tot_C_fut'].GetRasterBand(1))
            LOGGER.info('finished calculating HWP storage for future landscape')

        LOGGER.info('calculating raster stats for tot_C_fut')
        invest_core.calculateRasterStats(args['tot_C_fut'].GetRasterBand(1))

        #calculate seq. only after HWP has been added to the storage rasters
        LOGGER.info('calculating carbon sequestration')
        invest_core.rasterDiff(args['tot_C_fut'].GetRasterBand(1),
                               args['tot_C_cur'].GetRasterBand(1),
                               args['sequest'].GetRasterBand(1))

        LOGGER.info('calculating raster stats for sequest')
        invest_core.calculateRasterStats(args['sequest'].GetRasterBand(1))

        LOGGER.info('finished calculating carbon sequestration')

def calculateHWPStorageFut(hwpShapes, c_hwp, bio_hwp, vol_hwp, pixelArea,
                           yr_cur, yr_fut):
    """Calculates carbon storage, hwp biomassPerPixel and volumePerPixel due to 
        harvested wood products in parcels on current landscape.
        
        hwpShapes - a dictionary containing the current and/or future harvest
            maps (or nothing)
            hwpShapes['cur'] - oal shapefile indicating harvest map from the
                current landscape
            hwpShapes['fut'] - oal shapefile indicating harvest map from the
                future landscape
        c_hwp - an output GDAL rasterband representing  carbon stored in 
            harvested wood products for current calculation 
        bio_hwp - an output GDAL rasterband representing carbon stored in 
            harvested wood products for land cover under interest
        vol_hwp - an output GDAL rasterband representing carbon stored in
             harvested wood products for land cover under interest
        pixelArea - area of a pixel to calculate exact 
            carbon/volumePerPixel/biomassPerPixel amounts
        yr_cur - year of the current landcover map
        yr_fut - year of the current landcover map
        
        No return value"""
    #Create a temporary shapefile to hold values of per feature carbon pools
    #HWP biomassPerPixel and volumePerPixel, will be used later to rasterize 
    #those values to output rasters

    #First fill output rasters with nodata
    for raster in [c_hwp, bio_hwp, vol_hwp]:
        raster.GetRasterBand(1).Fill(raster.GetRasterBand(1).GetNoDataValue())

    calculatedAttributeNames = ['c_hwp_pool', 'bio_hwp', 'vol_hwp']
    if 'cur' in hwpShapes:
        hwp_shape_copy = \
            ogr.GetDriverByName('Memory').CopyDataSource(hwpShapes['cur'], '')
        hwp_shape_layer_copy = \
            hwp_shape_copy.GetLayerByName('harv_samp_cur')

        #Create fields in the layers to hold hardwood product pools, 
        #biomassPerPixel and volumePerPixel
        for fieldName in calculatedAttributeNames:
            field_def = ogr.FieldDefn(fieldName, ogr.OFTReal)
            hwp_shape_layer_copy.CreateField(field_def)

        #Visit each feature and calculate the carbon pool, biomassPerPixel, 
        #and volumePerPixel of that parcel
        for feature in hwp_shape_layer_copy:
            #This makes a helpful dictionary to access fields in the feature
            #later in the code
            fieldArgs = getFields(feature)

            #If start date and/or the amount of carbon per cut is zero, it 
            #doesn't make sense to do any calculation on carbon pools or 
            #biomassPerPixel/volumePerPixel
            if fieldArgs['Start_date'] != 0 and fieldArgs['Cut_cur'] != 0:

                timeSpan = (yr_fut + yr_cur) / 2.0 - fieldArgs['Start_date']
                startYears = yr_fut - fieldArgs['Start_date']

                #Calculate the carbon pool due to decaying HWP over the 
                #timeSpan
                featureCarbonStoragePerPixel = pixelArea * \
                    carbonPoolinHWPFromParcel(fieldArgs['Cut_cur'],
                                              timeSpan, startYears,
                                              fieldArgs['Freq_cur'],
                                              fieldArgs['Decay_cur'])

                #Claculate biomassPerPixel and volumePerPixel of harvested wood
                numberOfHarvests = \
                    math.ceil(timeSpan / float(fieldArgs['Freq_cur']))
                #The measure of biomass is in terms of Mg/ha
                biomassInFeaturePerArea = fieldArgs['Cut_cur'] * \
                    numberOfHarvests / float(fieldArgs['C_den_cur'])


                biomassPerPixel = biomassInFeaturePerArea * pixelArea
                volumePerPixel = biomassPerPixel / fieldArgs['BCEF_cur']

                #Copy biomassPerPixel and carbon pools to the temporary 
                #feature for rasterization of the entire layer later
                for field, value in zip(calculatedAttributeNames,
                                        [featureCarbonStoragePerPixel,
                                         biomassPerPixel, volumePerPixel]):
                    feature.SetField(feature.GetFieldIndex(field), value)

                #This saves the changes made to feature back to the shape layer
                hwp_shape_layer_copy.SetFeature(feature)

        #burn all the attribute values to a raster
        for attributeName, raster  in zip(calculatedAttributeNames,
                                          [c_hwp, bio_hwp, vol_hwp]):
            gdal.RasterizeLayer(raster, [1], hwp_shape_layer_copy,
                                    options=['ATTRIBUTE=' + attributeName])

    #handle the future term 
    if 'fut' in hwpShapes:
        hwp_shape_copy = \
            ogr.GetDriverByName('Memory').CopyDataSource(hwpShapes['fut'], '')
        hwp_shape_layer_copy = \
            hwp_shape_copy.GetLayerByName('harv_samp_fut')

        #Create fields in the layers to hold hardwood product pools, 
        #biomassPerPixel and volumePerPixel
        for fieldName in calculatedAttributeNames:
            field_def = ogr.FieldDefn(fieldName, ogr.OFTReal)
            hwp_shape_layer_copy.CreateField(field_def)

        #Visit each feature and calculate the carbon pool, biomassPerPixel, 
        #and volumePerPixel of that parcel
        for feature in hwp_shape_layer_copy:
            #This makes a helpful dictionary to access fields in the feature
            #later in the code
            fieldArgs = getFields(feature)

            #If start date and/or the amount of carbon per cut is zero, it 
            #doesn't make sense to do any calculation on carbon pools or 
            #biomassPerPixel/volumePerPixel
            if fieldArgs['Cut_fut'] != 0:

                timeSpan = yr_fut - (yr_fut + yr_cur) / 2.0
                startYears = timeSpan

                #Calculate the carbon pool due to decaying HWP over the 
                #timeSpan
                featureCarbonStoragePerPixel = pixelArea * \
                    carbonPoolinHWPFromParcel(fieldArgs['Cut_fut'],
                                              timeSpan, startYears,
                                              fieldArgs['Freq_fut'],
                                              fieldArgs['Decay_fut'])

                #Claculate biomassPerPixel and volumePerPixel of harvested wood
                numberOfHarvests = \
                    math.ceil(timeSpan / float(fieldArgs['Freq_fut']))

                biomassInFeaturePerArea = fieldArgs['Cut_fut'] * \
                    numberOfHarvests / float(fieldArgs['C_den_fut'])

                biomassPerPixel = biomassInFeaturePerArea * pixelArea

                volumePerPixel = biomassPerPixel / fieldArgs['BCEF_fut']

                #Copy biomassPerPixel and carbon pools to the temporary 
                #feature for rasterization of the entire layer later
                for field, value in zip(calculatedAttributeNames,
                                        [featureCarbonStoragePerPixel,
                                         biomassPerPixel, volumePerPixel]):
                    feature.SetField(feature.GetFieldIndex(field), value)

                #This saves the changes made to feature back to the shape layer
                hwp_shape_layer_copy.SetFeature(feature)

        #burn all the attribute values to a raster
        for attributeName, raster  in zip(calculatedAttributeNames,
                                          [c_hwp, bio_hwp, vol_hwp]):
            #we might have already written to the raster if we did a 'fut cur'
            #calculation, so rasterize to a temporary layer then add 'em
            tempRaster = raster_utils.new_raster_from_base(raster, '', 'MEM',
                raster.GetRasterBand(1).GetNoDataValue(), gdal.GDT_Float32)
            tempRaster.GetRasterBand(1).Fill(tempRaster.GetRasterBand(1).\
                                             GetNoDataValue())
            gdal.RasterizeLayer(tempRaster, [1], hwp_shape_layer_copy,
                                    options=['ATTRIBUTE=' + attributeName])
            invest_core.rasterAdd(tempRaster.GetRasterBand(1),
                                  raster.GetRasterBand(1),
                                  raster.GetRasterBand(1))

def calculateHWPStorageCur(hwp_shape, c_hwp, bio_hwp, vol_hwp, pixelArea,
                           yr_cur):
    """Calculates carbon storage, hwp biomassPerPixel and volumePerPixel due 
        to harvested wood products in parcels on current landscape.
        
        hwp_shape - oal shapefile indicating harvest map of interest
        c_hwp - an output GDAL rasterband representing  carbon stored in 
            harvested wood products for current calculation 
        bio_hwp - an output GDAL rasterband representing carbon stored in 
            harvested wood products for land cover under interest
        vol_hwp - an output GDAL rasterband representing carbon stored in
             harvested wood products for land cover under interest
        pixelArea - area of a pixel to calculate exact 
            carbon/volumePerPixel/biomassPerPixel amounts
        yr_cur - year of the current landcover map
        
        No return value"""

    #Create a temporary shapefile to hold values of per feature carbon pools
    #HWP biomassPerPixel and volumePerPixel, will be used later to rasterize 
    #those values to output rasters

    hwp_shape_copy = \
        ogr.GetDriverByName('Memory').CopyDataSource(hwp_shape, '')
    hwp_shape_layer_copy = \
        hwp_shape_copy.GetLayerByName('harv_samp_cur')

    #Create fields in the layers to hold hardwood product pools, 
    #biomassPerPixel and volumePerPixel
    calculatedAttributeNames = ['c_hwp_pool', 'bio_hwp', 'vol_hwp']
    for x in calculatedAttributeNames:
        field_def = ogr.FieldDefn(x, ogr.OFTReal)
        hwp_shape_layer_copy.CreateField(field_def)

    #Visit each feature and calculate the carbon pool, biomassPerPixel, and 
    #volumePerPixel of that parcel
    for feature in hwp_shape_layer_copy:
        #This makes a helpful dictionary to access fields in the feature
        #later in the code
        fieldArgs = getFields(feature)

        #If start date and/or the amount of carbon per cut is zero, it doesn't
        #make sense to do any calculation on carbon pools or 
        #biomassPerPixel/volumePerPixel
        if fieldArgs['Start_date'] != 0 and fieldArgs['Cut_cur'] != 0:

            timeSpan = yr_cur - fieldArgs['Start_date']
            startYears = timeSpan

            #Calculate the carbon pool due to decaying HWP over the timeSpan
            featureCarbonStoragePerPixel = pixelArea * \
                carbonPoolinHWPFromParcel(fieldArgs['Cut_cur'],
                                          timeSpan, startYears,
                                          fieldArgs['Freq_cur'],
                                          fieldArgs['Decay_cur'])

            #Next lines caculate biomassPerPixel and volumePerPixel of 
            #harvested wood
            numberOfHarvests = \
                math.ceil(timeSpan / float(fieldArgs['Freq_cur']))

            biomassInFeature = fieldArgs['Cut_cur'] * numberOfHarvests / \
                float(fieldArgs['C_den_cur'])

            biomassPerPixel = biomassInFeature * pixelArea

            volumePerPixel = biomassPerPixel / fieldArgs['BCEF_cur']

            #Copy biomassPerPixel and carbon pools to the temporary feature 
            #for rasterization of the entire layer later
            for field, value in zip(calculatedAttributeNames,
                                    [featureCarbonStoragePerPixel,
                                     biomassPerPixel, volumePerPixel]):
                feature.SetField(feature.GetFieldIndex(field), value)

            #This saves the changes made to feature back to the shape layer
            hwp_shape_layer_copy.SetFeature(feature)

    #burn all the attribute values to a raster
    for attributeName, raster  in zip(calculatedAttributeNames,
                                      [c_hwp, bio_hwp, vol_hwp]):
        raster.GetRasterBand(1).Fill(raster.GetRasterBand(1).GetNoDataValue())
        gdal.RasterizeLayer(raster, [1], hwp_shape_layer_copy,
                                options=['ATTRIBUTE=' + attributeName])

def carbonPoolinHWPFromParcel(carbonPerCut, startYears, timeSpan, harvestFreq,
                              decay):
    """This is the summation equation that appears in equations 1, 5, 6, and 7
        from the user's guide
        
        carbonPerCut - The amount of carbon removed from a parcel during a
            harvest period
        startYears - The number of years ago that the harvest first started
        timeSpan - The number of years to calculate the harvest over
        harvestFreq - How many years between harvests
        decay - the rate at which carbon is decaying from HWP harvested from
            parcels
        
        returns a float indicating the amount of carbon stored from HWP
            harvested in units of Mg/ha"""

    carbonSum = 0.0
    omega = math.log(2) / decay
    #Recall that xrange is nonexclusive on the upper bound, so it corresponds
    #to the -1 in the summation terms given in the user's manual
    for t in xrange(int(math.ceil(startYears / harvestFreq))):
        carbonSum += (1 - math.exp(-omega)) / (omega *
            math.exp((timeSpan - t * harvestFreq) * omega))
    return carbonSum * carbonPerCut

def getFields(feature):
    """Return a dict with all fields in the given feature.
        
        feature - an OGR feature.
        
        Returns an assembled python dict with a mapping of 
        fieldname -> fieldvalue"""

    fields = {}
    for i in range(feature.GetFieldCount()):
        field_def = feature.GetFieldDefnRef(i)
        name = field_def.GetNameRef()
        value = feature.GetField(i)
        fields[name] = value

    return fields

def calculateCarbonStorage(pools, lulcRasterBand, storageRasterBand):
    """Iterate through the rows in an LULC raster and map carbon storage 
        values to the output raster.
        
        pools - a python dict mapping lulc indices to carbon storage/pixel
        lulcRasterBand - a GDAL raster dataset representing lulc 
        storageRasterBand - a GDAL raster dataset representing carbon storage
        
        No return value."""

    #Vectorize an operation that maps pixel values to carbon storage values
    def mapPool(x, dict):
        return dict[x]
    mapFun = np.vectorize(mapPool)

    #Iterate through lulc and map storage to the storage raster band
    for i in range(0, lulcRasterBand.YSize):
        data = lulcRasterBand.ReadAsArray(0, i, lulcRasterBand.XSize, 1)
        out_array = mapFun(data, pools)
        storageRasterBand.WriteArray(out_array, 0, i)

def build_pools_dict(dbf, area, inNoData, outNoData):
    """Build a dict for the carbon pool data accessible for each lulc classification.
    
        dbf - the database file describing pools
        area - the area in Ha of each pixel
        inNoData - the no data value for the input map
        outNoData - the no data value for the output map
    
        returns a dictionary calculating total carbon sequestered per lulc type"""

    poolsDict = {int(inNoData): outNoData}
    for i in range(dbf.recordCount):
        total_carbon_pools = 0
        for field in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD'):
            #casting to a float here in case dbf stored as a textual float
            total_carbon_pools += float(dbf[i][field])
        poolsDict[dbf[i]['LULC']] = total_carbon_pools * area
    return poolsDict

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

    area = invest_core.pixelArea(args['lulc'])
    lulc = args['lulc'].GetRasterBand(1)
    inNoData = lulc.GetNoDataValue()
    outNoData = args['output'].GetRasterBand(1).GetNoDataValue()

    #This maps pool types to band numbers
    poolTypes = {'L':1, 'A':2, 'H':3}
    pools = {}

    uncertaintyRank = None

    for poolType in poolTypes:
        pools[poolType] = build_uncertainty_pools_dict(args['carbon_pools'],
                                       poolType, area, inNoData, outNoData)
        maxValue, minValue = max(pools[poolType].values()), \
                             min(pools[poolType].values())
        if minValue == None:
            minValue = 0

        #create uncertainty dictionary with most recent dictionary as 
        #reference for keys
        if uncertaintyRank == None:
            uncertaintyRank = {}.fromkeys(pools[poolType].keys(), 0.0)

        #rank each pooltype
        for type, value in pools[poolType].iteritems():
            if maxValue != minValue and value != None:
                uncertaintyRank[type] += (value - minValue) / \
                    (maxValue - minValue) / len(poolTypes)

    #add the uncertainty pool so it gets iterated over on the map step
    poolTypes['uncertainty'] = 4
    pools['uncertainty'] = uncertaintyRank

    #map each row in the lulc raster
    for rowNumber in range(0, lulc.YSize):
        data = lulc.ReadAsArray(0, rowNumber, lulc.XSize, 1)
        #create a seq map for each pooltype 
        for poolType, index in poolTypes.iteritems():
            out_array = carbon_core.carbon_seq(data, pools[poolType])
            args['output'].GetRasterBand(index).WriteArray(out_array, 0,
                                                           rowNumber)


def build_uncertainty_pools_dict(dbf, poolType, area, inNoData, outNoData):
    """Build a dict for the carbon pool data accessible for each lulc 
        classification.
    
        dbf - the database file describing pools
        poolType - one of 'L', 'A', or 'H' indicating low average or high
                   pool data
        area - the area in Ha of each pixel
        inNoData - the no data value for the input map
        outNoData - the no data value for the output map
    
        returns a dictionary calculating total carbon sequestered per lulc 
            type"""

    poolsDict = {int(inNoData): outNoData}
    for i in range(dbf.recordCount):
        sum = 0
        for field in [ x + '_' + poolType for x in ('C_ABOVE', 'C_BELOW',
                                                    'C_SOIL', 'C_DEAD')]:
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
        args['carbon_pools'] - is an uncertainty dictionary that maps LULC 
                               type to Mg/Ha of carbon where the field names 
                               are appended by 'L', 'A', or 'H', for low, 
                               average, and high measurements.
        args['percentile'] - cuts the output to be the top and bottom
                             percentile of sequestered carbon based on
                             the uncertainty scenarios
        args['output_seq'] - a GDAL raster dataset for outputting the 
                             conservative amount of carbon sequestered.
        args['output_map'] - a colorized map indicating the regions of
                            output_seq that fall into the percentile
                            ranges given in args['percentile'].  Green
                            is carbon sequestered increase and red is a
                            decrease.
        
        returns nothing"""

    area = invest_core.pixelArea(args['lulc_cur'])
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
        dataCurrent = \
            lulcCurrent.ReadAsArray(0, rowNumber, lulcCurrent.XSize, 1)
        dataFuture = lulcFuture.ReadAsArray(0, rowNumber, lulcFuture.XSize, 1)
        #create a seqestration map for high-low, low-high, and average-average
        sequesteredChangeArray = []
        for poolTypeA, poolTypeB in [('L', 'H'), ('H', 'L'), ('A', 'A')]:
            sequesteredCurrent = \
                carbon_core.carbon_seq(dataCurrent, pools[poolTypeA])
            sequesteredFuture = \
                carbon_core.carbon_seq(dataFuture, pools[poolTypeB])
            sequesteredChange = sequesteredCurrent - sequesteredFuture

            if maxMin is None:
                maxMin = (np.max(sequesteredChange), np.min(sequesteredChange))
            else:
                maxMin = (max(np.max(sequesteredChange), maxMin[0]),
                      min(np.min(sequesteredChange), maxMin[1]))

            sequesteredChangeArray.append(sequesteredChange)

        #Output the min value of l-h or h-l if average is >=0 or 
        #max value if < 0
        output_seq.WriteArray(vectorSelector(sequesteredChangeArray[0],
                                             sequesteredChangeArray[1],
                                             sequesteredChangeArray[2]), 0,
                                             rowNumber)

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
        colorTable.SetColorEntry(i, (int(negColor[0] * frac),
                                     int(negColor[1] * frac),
                                     int(negColor[2] * frac)))
        colorTable.SetColorEntry(steps - i, (int(posColor[0] * frac),
                                             int(posColor[1] * frac),
                                             int(posColor[2] * frac)))
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
        seqRow = percentileCutoffFun(seqRow, args['percentile'],
                                     maxMin[0], maxMin[1])
        #map them to colors
        args['output_map'].GetRasterBand(1).WriteArray(maxIndex(seqRow), 0,
                                                       rowNumber)

def valuation(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with the following entries:
        args['sequest'] - a single band GDAL raster dataset describing the
            amount of carbon sequestered
        args['V'] - value of a sequestered ton of carbon in dollars per metric
            ton
        args['r'] - the market discount rate in terms of a percentage
        args['c'] - the annual rate of change in the price of carbon
        args['yr_cur'] - the year at which the sequestration measurement 
            started
        args['yr_fut'] - the year at which the sequestration measurement ended
        args['value_seq'] - a single band output GDAL   
        
        returns nothing"""

    LOGGER.debug('constructing valuation formula')
    n = args['yr_fut'] - args['yr_cur'] - 1
    ratio = 1.0 / ((1 + args['r'] / 100.0) * (1 + args['c'] / 100.0))
    valuationConstant = args['V'] / (args['yr_fut'] - args['yr_cur']) * \
        (1.0 - ratio ** (n + 1)) / (1.0 - ratio)

    noDataIn = args['sequest'].GetRasterBand(1).GetNoDataValue()
    noDataOut = args['value_seq'].GetRasterBand(1).GetNoDataValue()

    def valueOp(sequest):
        if sequest != noDataIn:
            return sequest * valuationConstant
        else:
            return noDataOut

    LOGGER.debug('finished constructing valuation formula')

    LOGGER.info('starting valuation of each pixel')
    invest_core.vectorize1ArgOp(args['sequest'].GetRasterBand(1), valueOp,
                                args['value_seq'].GetRasterBand(1))
    LOGGER.info('calculating raster stats for value_seq')
    invest_core.calculateRasterStats(args['value_seq'].GetRasterBand(1))
    LOGGER.info('finished valuation of each pixel')

def calculate_summary(args):
    """Dumps information about total carbon summaries from the past run
        in the form

        Total current carbon: xxx Mg
        Total scenario carbon: yyy Mg
        Total sequestered carbon: zzz Mg

        args - a dictionary of arguments defined as follows:

        args['tot_C_cur'] - a gdal dataset that contains pixels with
            total Mg of carbon per cell on current landscape (required)
        args['tot_C_fut'] - a gdal dataset that contains pixels with
            total Mg of carbon per cell on future landscape (optional)
        args['sequest'] - a gdal dataset that contains pixels with
            total Mg of carbon sequestered per cell (optional)

        returns nothing
        """
    LOGGER.debug('calculate summary')
    raster_key_messages = [('tot_C_cur', 'Total current carbon: '),
                           ('tot_C_fut', 'Total scenario carbon: '),
                           ('sequest', 'Total sequestered carbon: ')]

    for raster_key, message in raster_key_messages:
        #Make sure we passed in the dictionary, and gracefully continue
        #if we didn't.
        if raster_key not in args:
            continue
        dataset = args[raster_key]
        band, nodata = raster_utils.extract_band_and_nodata(dataset)
        total_sum = 0.0
        #Loop over each row in out_band
        for row_index in range(band.YSize):
            row_array = band.ReadAsArray(0, row_index, band.XSize, 1)
            total_sum += np.sum(row_array[row_array != nodata])
        LOGGER.info("%s %s Mg" % (message, total_sum))
